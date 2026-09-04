from __future__ import annotations

import ctypes
import errno
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import materialize_mipstarre as source  # noqa: E402


COMMIT = "1" * 40
PREFIX = f"MIPStarRE-{COMMIT}/"


def pax_record(key: str, value: str) -> bytes:
    body = f" {key}={value}\n".encode()
    length = len(body) + 1
    while True:
        record = str(length).encode() + body
        if len(record) == length:
            return record
        length = len(record)


def tar_header(name: str, kind: bytes, size: int = 0, link: str = "") -> bytes:
    header = bytearray(512)

    def field(start: int, width: int, value: bytes) -> None:
        if len(value) > width:
            raise ValueError(value)
        header[start : start + len(value)] = value

    field(0, 100, name.encode())
    field(100, 8, b"0000755\0")
    field(108, 8, b"0000000\0")
    field(116, 8, b"0000000\0")
    field(124, 12, f"{size:011o}\0".encode())
    field(136, 12, b"00000000000\0")
    field(148, 8, b"        ")
    field(156, 1, kind)
    field(157, 100, link.encode())
    field(257, 6, b"ustar\0")
    field(263, 2, b"00")
    checksum = sum(header)
    field(148, 8, f"{checksum:06o}\0 ".encode())
    return bytes(header)


def make_archive(entries: list[tuple[str, bytes, bytes, str]] | None = None) -> tuple[bytes, bytes]:
    if entries is None:
        entries = [
            (PREFIX, b"5", b"", ""),
            (PREFIX + "MIPStarRE/", b"5", b"", ""),
            (PREFIX + "MIPStarRE/Quantum/", b"5", b"", ""),
            (PREFIX + "MIPStarRE/Quantum/Measurement.lean", b"0", b"def pinned := 1\n", ""),
        ]
    pax = pax_record("comment", COMMIT)
    blocks = [tar_header("pax_global_header", b"g", len(pax)), pax]
    blocks.append(bytes((-len(pax)) % 512))
    for name, kind, payload, link in entries:
        blocks.extend((tar_header(name, kind, len(payload), link), payload, bytes((-len(payload)) % 512)))
    blocks.append(bytes(1024))
    raw = b"".join(blocks)
    return gzip.compress(raw, mtime=0), raw


class MaterializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        (self.root / "references").mkdir()
        (self.root / "lean-toolchain").write_text("leanprover/lean4:v4.32.0\n", encoding="ascii")
        (self.root / "lake-manifest.json").write_text(
            json.dumps(
                {
                    "packages": [
                        {"name": "mathlib", "inputRev": "v4.32.0", "rev": "2" * 40}
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.compressed, self.raw = make_archive()
        facts, _, files = source.inspect_archive_bytes(
            self.compressed,
            commit=COMMIT,
            exact_prefix=PREFIX,
            expected_tar_bytes=len(self.raw),
        )
        foundation = dict(files)["Quantum/Measurement.lean"]
        self.pin = {
            "schema_version": 1,
            "source": {
                "id": "test",
                "repository": "owner/repo",
                "repository_url": "https://example.invalid/owner/repo",
                "commit": COMMIT,
                "archive_url": "https://example.invalid/archive",
                "acquisition_evidence": "test fixture",
            },
            "rights": {
                "license_file": None,
                "redistribution_permission": "not-established",
                "policy": "local verification only",
            },
            "archive": {
                "format": "gzip-ustar-with-exact-global-pax-comment",
                **facts["archive"],
                "exact_prefix": PREFIX,
                "global_pax_comment": COMMIT,
            },
            "output": {
                "path": "MIPStarRE",
                "archive_subtree": "MIPStarRE/",
                "reserved_authored_subtree": "QPBT/",
                **facts["output"],
            },
            "lean_pins": {
                "toolchain": "leanprover/lean4:v4.32.0",
                "mathlib_input_revision": "v4.32.0",
                "mathlib_commit": "2" * 40,
            },
            "foundations": [
                {
                    "module": "MIPStarRE.Quantum.Measurement",
                    "path": "MIPStarRE/Quantum/Measurement.lean",
                    "sha256": hashlib.sha256(foundation).hexdigest(),
                    "purpose": "test",
                }
            ],
        }
        self.pin_path = self.root / "references" / "mipstarre-upstream.json"
        self.pin_path.write_text(json.dumps(self.pin), encoding="utf-8")
        self.archive = Path(self.temporary.name) / "source.tar.gz"
        self.archive.write_bytes(self.compressed)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inspect_bytes(self, compressed: bytes, raw: bytes) -> None:
        source.inspect_archive_bytes(
            compressed,
            commit=COMMIT,
            exact_prefix=PREFIX,
            expected_tar_bytes=len(raw),
        )

    def test_shared_hub_retains_more_than_128_real_monitors(self) -> None:
        watch_root = Path(self.temporary.name) / "many-watches"
        watch_root.mkdir()
        descriptors: list[int] = []
        monitors: list[source._BoundNameMonitor] = []
        hub_descriptor = -1
        try:
            with source._monitor_authority() as hub:
                hub_descriptor = hub.descriptor
                for index in range(160):
                    directory = watch_root / f"watch-{index:03d}"
                    directory.mkdir()
                    descriptor = os.open(directory, source._directory_flags())
                    descriptors.append(descriptor)
                    monitors.append(source._BoundNameMonitor(descriptor, None))

                self.assertEqual(160, len(monitors))
                self.assertEqual({hub_descriptor}, {monitor.hub.descriptor for monitor in monitors})
                for monitor in monitors:
                    monitor.assert_clean()

                os.mkdir("owned", dir_fd=descriptors[0])
                monitors[-1].assert_clean()
                monitors[0].accept_owned_change((("owned", source._IN_CREATE),))
        finally:
            for monitor in reversed(monitors):
                monitor.close()
            for descriptor in reversed(descriptors):
                os.close(descriptor)
        with self.assertRaises(OSError):
            os.fstat(hub_descriptor)

    def test_shared_hub_routes_cross_watch_events_independently_of_poll_order(self) -> None:
        first_path = Path(self.temporary.name) / "route-first"
        second_path = Path(self.temporary.name) / "route-second"
        first_path.mkdir()
        second_path.mkdir()
        first_descriptor = os.open(first_path, source._directory_flags())
        second_descriptor = os.open(second_path, source._directory_flags())
        first_monitor: source._BoundNameMonitor | None = None
        second_monitor: source._BoundNameMonitor | None = None
        try:
            with source._monitor_authority():
                first_monitor = source._BoundNameMonitor(first_descriptor, ("first",))
                second_monitor = source._BoundNameMonitor(second_descriptor, ("second",))

                os.mkdir("first", dir_fd=first_descriptor)
                second_monitor.assert_clean()
                first_monitor.accept_owned_change((("first", source._IN_CREATE),))

                os.mkdir("second", dir_fd=second_descriptor)
                first_monitor.assert_clean()
                second_monitor.accept_owned_change((("second", source._IN_CREATE),))
        finally:
            if second_monitor is not None:
                second_monitor.close()
            if first_monitor is not None:
                first_monitor.close()
            os.close(second_descriptor)
            os.close(first_descriptor)

    def test_duplicate_watch_subscribers_fan_out_and_close_independently(self) -> None:
        watched = Path(self.temporary.name) / "duplicate-watch"
        watched.mkdir()
        descriptor = os.open(watched, source._directory_flags())
        first: source._BoundNameMonitor | None = None
        second: source._BoundNameMonitor | None = None
        try:
            with source._monitor_authority() as hub:
                first = source._BoundNameMonitor(descriptor, None)
                second = source._BoundNameMonitor(descriptor, None)
                self.assertEqual(first.watch, second.watch)

                os.mkdir("fanout", dir_fd=descriptor)
                second.accept_owned_change((("fanout", source._IN_CREATE),))
                first.accept_owned_change((("fanout", source._IN_CREATE),))

                second.close()
                second.close()
                os.mkdir("survivor", dir_fd=descriptor)
                with self.assertRaisesRegex(source.MaterializationError, "became ambiguous"):
                    second.assert_clean()
                with self.assertRaisesRegex(
                    source.MaterializationError, "lacked its exact monitor events"
                ):
                    second.accept_owned_change(())
                first.accept_owned_change((("survivor", source._IN_CREATE),))
                os.fstat(hub.descriptor)
        finally:
            if second is not None:
                second.close()
            if first is not None:
                first.close()
            os.close(descriptor)

    def test_watch_local_terminal_events_do_not_poison_other_watches(self) -> None:
        removed_path = Path(self.temporary.name) / "removed-watch"
        survivor_path = Path(self.temporary.name) / "surviving-watch"
        removed_path.mkdir()
        survivor_path.mkdir()
        removed_descriptor = os.open(removed_path, source._directory_flags())
        survivor_descriptor = os.open(survivor_path, source._directory_flags())
        removed_monitor: source._BoundNameMonitor | None = None
        survivor_monitor: source._BoundNameMonitor | None = None
        try:
            with source._monitor_authority():
                removed_monitor = source._BoundNameMonitor(removed_descriptor, None)
                survivor_monitor = source._BoundNameMonitor(survivor_descriptor, None)
                remove_watch = getattr(source._linux_libc(), "inotify_rm_watch")
                remove_watch.argtypes = [ctypes.c_int, ctypes.c_int]
                remove_watch.restype = ctypes.c_int
                self.assertEqual(
                    0,
                    remove_watch(
                        removed_monitor.hub.descriptor,
                        removed_monitor.watch,
                    ),
                )

                survivor_monitor.assert_clean()
                with self.assertRaisesRegex(source.MaterializationError, "became ambiguous"):
                    removed_monitor.assert_clean()

                os.mkdir("still-routed", dir_fd=survivor_descriptor)
                survivor_monitor.accept_owned_change((("still-routed", source._IN_CREATE),))
        finally:
            if survivor_monitor is not None:
                survivor_monitor.close()
            if removed_monitor is not None:
                removed_monitor.close()
            os.close(survivor_descriptor)
            os.close(removed_descriptor)

    def test_real_queue_overflow_permanently_poisons_every_subscriber(self) -> None:
        queue_limit = int(Path("/proc/sys/fs/inotify/max_queued_events").read_text())
        if queue_limit > 65536:
            self.skipTest("inotify queue limit exceeds the bounded real-overflow workload")
        noisy_path = Path(self.temporary.name) / "overflow-noisy"
        quiet_path = Path(self.temporary.name) / "overflow-quiet"
        noisy_path.mkdir()
        quiet_path.mkdir()
        noisy_descriptor = os.open(noisy_path, source._directory_flags())
        quiet_descriptor = os.open(quiet_path, source._directory_flags())
        noisy_monitor: source._BoundNameMonitor | None = None
        quiet_monitor: source._BoundNameMonitor | None = None
        try:
            with source._monitor_authority() as hub:
                noisy_monitor = source._BoundNameMonitor(noisy_descriptor, None)
                quiet_monitor = source._BoundNameMonitor(quiet_descriptor, None)
                descriptor = os.open(
                    "left",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=noisy_descriptor,
                )
                os.close(descriptor)
                noisy_monitor.accept_owned_change((("left", source._IN_CREATE),))

                current, destination = "left", "right"
                for _ in range(queue_limit // 2 + 1024):
                    os.rename(
                        current,
                        destination,
                        src_dir_fd=noisy_descriptor,
                        dst_dir_fd=noisy_descriptor,
                    )
                    current, destination = destination, current

                with self.assertRaisesRegex(source.MaterializationError, "became ambiguous"):
                    quiet_monitor.assert_clean()
                self.assertTrue(hub.poisoned)
                with self.assertRaisesRegex(source.MaterializationError, "became ambiguous"):
                    noisy_monitor.assert_clean()
        finally:
            if quiet_monitor is not None:
                quiet_monitor.close()
            if noisy_monitor is not None:
                noisy_monitor.close()
            os.close(quiet_descriptor)
            os.close(noisy_descriptor)

    def test_stream_failures_globally_poison_all_subscribers(self) -> None:
        first_path = Path(self.temporary.name) / "stream-first"
        second_path = Path(self.temporary.name) / "stream-second"
        first_path.mkdir()
        second_path.mkdir()
        first_descriptor = os.open(first_path, source._directory_flags())
        second_descriptor = os.open(second_path, source._directory_flags())
        try:
            for label in ("short-header", "unterminated-name", "empty", "read-error"):
                with self.subTest(label=label), source._monitor_authority() as hub:
                    first = source._BoundNameMonitor(first_descriptor, None)
                    second = source._BoundNameMonitor(second_descriptor, None)

                    def failure(_descriptor: int, _size: int) -> bytes:
                        if label == "short-header":
                            return b"\0"
                        if label == "unterminated-name":
                            return source._INOTIFY_EVENT.pack(
                                first.watch, source._IN_CREATE, 0, 4
                            ) + b"name"
                        if label == "empty":
                            return b""
                        raise OSError(errno.EIO, "injected read failure")

                    try:
                        with mock.patch.object(source.os, "read", side_effect=failure):
                            with self.assertRaisesRegex(
                                source.MaterializationError, "became ambiguous"
                            ):
                                first.assert_clean()
                        self.assertTrue(hub.poisoned)
                        with self.assertRaisesRegex(
                            source.MaterializationError, "became ambiguous"
                        ):
                            second.assert_clean()
                    finally:
                        second.close()
                        first.close()
        finally:
            os.close(second_descriptor)
            os.close(first_descriptor)

    def test_reused_watch_descriptor_is_permanently_ambiguous(self) -> None:
        first_path = Path(self.temporary.name) / "reuse-first"
        second_path = Path(self.temporary.name) / "reuse-second"
        first_path.mkdir()
        second_path.mkdir()
        first_descriptor = os.open(first_path, source._directory_flags())
        second_descriptor = os.open(second_path, source._directory_flags())
        first: source._BoundNameMonitor | None = None
        second: source._BoundNameMonitor | None = None
        try:
            with source._monitor_authority() as hub:
                first = source._BoundNameMonitor(first_descriptor, None)
                reused_watch = first.watch
                real_add_watch = hub._add_watch_call

                def reuse_watch(_descriptor: int, _path: bytes, _mask: int) -> int:
                    return reused_watch

                hub._add_watch_call = reuse_watch
                try:
                    second = source._BoundNameMonitor(second_descriptor, None)
                finally:
                    hub._add_watch_call = real_add_watch
                self.assertTrue(first.poisoned)
                self.assertTrue(second.poisoned)
                with self.assertRaisesRegex(source.MaterializationError, "became ambiguous"):
                    second.assert_clean()
        finally:
            if second is not None:
                second.close()
            if first is not None:
                first.close()
            os.close(second_descriptor)
            os.close(first_descriptor)

    def test_shared_hub_closes_after_partial_monitor_construction_failure(self) -> None:
        watched = Path(self.temporary.name) / "partial-monitor"
        watched.mkdir()
        descriptor = os.open(watched, source._directory_flags())
        hub_descriptor = -1
        monitor: source._BoundNameMonitor | None = None
        try:
            with self.assertRaisesRegex(source.MaterializationError, "Too many open files"):
                with source._monitor_authority() as hub:
                    hub_descriptor = hub.descriptor
                    monitor = source._BoundNameMonitor(descriptor, None)

                    def fail_add_watch(_descriptor: int, _path: bytes, _mask: int) -> int:
                        ctypes.set_errno(errno.EMFILE)
                        return -1

                    hub._add_watch_call = fail_add_watch
                    source._BoundNameMonitor(descriptor, None)
        finally:
            if monitor is not None:
                monitor.close()
            os.close(descriptor)
        self.assertIsNone(source._ACTIVE_INOTIFY_HUB.get())
        with self.assertRaises(OSError):
            os.fstat(hub_descriptor)

    def test_publish_verify_and_cached_rerun_preserve_authored_tree(self) -> None:
        authored = self.root / "MIPStarRE" / "QPBT"
        authored.mkdir(parents=True)
        (authored / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        (self.root / "MIPStarRE" / "untrusted").write_text("replace me", encoding="utf-8")

        published = source.materialize(
            self.root, self.pin_path, self.archive, replace_existing=True
        )
        self.assertEqual("published", published["status"])
        self.assertEqual("def owned := true\n", (authored / "Owned.lean").read_text())
        self.assertFalse((self.root / "MIPStarRE" / "untrusted").exists())
        self.assertEqual(
            "cached", source.materialize(self.root, self.pin_path, self.archive)["status"]
        )
        self.assertEqual("verified", source.verify_materialized(self.root, self.pin)["status"])

    def test_publication_uses_atomic_exchange_or_no_replace_and_retains_evidence(self) -> None:
        calls: list[tuple[str, str, int]] = []
        real_rename = source._linux_renameat2

        def recording_rename(
            source_parent: int,
            source_name: str,
            destination_parent: int,
            destination_name: str,
            flags: int,
        ) -> None:
            calls.append((source_name, destination_name, flags))
            real_rename(
                source_parent,
                source_name,
                destination_parent,
                destination_name,
                flags,
            )

        with mock.patch.object(source, "_linux_renameat2", side_effect=recording_rename):
            first = source.materialize(self.root, self.pin_path, self.archive)
            (self.root / "MIPStarRE" / "untrusted").write_bytes(b"replace")
            second = source.materialize(
                self.root, self.pin_path, self.archive, replace_existing=True
            )
        self.assertIn(("MIPStarRE", "MIPStarRE", source.RENAME_NOREPLACE), calls)
        self.assertIn(("MIPStarRE", "MIPStarRE", source.RENAME_EXCHANGE), calls)
        for result in (first, second):
            evidence = Path(result["transaction_evidence"])
            self.assertTrue(evidence.is_dir())
            self.assertFalse((evidence.parent / "MIPStarRE.transaction").exists())

    def test_raw_traversal_duplicate_and_reserved_namespace_are_rejected(self) -> None:
        attacks = [
            [(PREFIX, b"5", b"", ""), (PREFIX + "MIPStarRE/../escape", b"0", b"x", "")],
            [(PREFIX, b"5", b"", ""), (PREFIX, b"5", b"", "")],
            [(PREFIX, b"5", b"", ""), (PREFIX + "MIPStarRE/QPBT/", b"5", b"", "")],
        ]
        for entries in attacks:
            with self.subTest(entries=entries):
                compressed, raw = make_archive(entries)
                with self.assertRaises(source.MaterializationError):
                    self.inspect_bytes(compressed, raw)

    def test_links_devices_and_tar_extensions_are_rejected(self) -> None:
        for kind in (b"1", b"2", b"3", b"4", b"6", b"x", b"L", b"K"):
            with self.subTest(kind=kind):
                compressed, raw = make_archive([(PREFIX + "bad", kind, b"", "target")])
                with self.assertRaisesRegex(source.MaterializationError, "forbidden"):
                    self.inspect_bytes(compressed, raw)

    def test_wrong_prefix_checksum_and_concatenated_gzip_are_rejected(self) -> None:
        wrong, wrong_raw = make_archive([("other/file", b"0", b"x", "")])
        with self.assertRaisesRegex(source.MaterializationError, "outside exact prefix"):
            self.inspect_bytes(wrong, wrong_raw)

        damaged = bytearray(self.raw)
        damaged[0] ^= 1
        with self.assertRaisesRegex(source.MaterializationError, "checksum"):
            self.inspect_bytes(gzip.compress(bytes(damaged), mtime=0), bytes(damaged))
        with self.assertRaisesRegex(source.MaterializationError, "concatenated|trailing"):
            self.inspect_bytes(self.compressed + gzip.compress(b"extra", mtime=0), self.raw)

    def test_decompression_bound_and_truncation_are_rejected(self) -> None:
        with self.assertRaisesRegex(source.MaterializationError, "exceeds"):
            source._decompress_gzip_exact(gzip.compress(b"A" * 1024, mtime=0), 10)
        with self.assertRaisesRegex(source.MaterializationError, "ended|truncated"):
            source._decompress_gzip_exact(self.compressed[:-4], len(self.raw))

        oversized = b"x" * (source.HARD_MAX_MEMBER_BYTES + 1)
        raw = (
            tar_header("pax_global_header", b"g", len(oversized))
            + oversized
            + bytes((-len(oversized)) % 512)
            + bytes(1024)
        )
        with self.assertRaisesRegex(source.MaterializationError, "member exceeds"):
            self.inspect_bytes(gzip.compress(raw, mtime=0), raw)

    def test_archive_symlink_and_pin_mismatch_preserve_destination(self) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        (destination / "keep").write_text("original", encoding="utf-8")
        link = Path(self.temporary.name) / "archive-link"
        link.symlink_to(self.archive)
        with self.assertRaises(source.MaterializationError):
            source.materialize(self.root, self.pin_path, link, replace_existing=True)
        self.assertEqual("original", (destination / "keep").read_text())

        self.archive.write_bytes(self.compressed[:-1] + bytes([self.compressed[-1] ^ 1]))
        with self.assertRaises(source.MaterializationError):
            source.materialize(self.root, self.pin_path, self.archive, replace_existing=True)
        self.assertEqual("original", (destination / "keep").read_text())

    def test_runtime_parent_symlink_is_rejected_before_transaction_writes(self) -> None:
        redirected = Path(self.temporary.name) / "redirected-runtime"
        redirected.mkdir()
        (self.root / ".workflow-runtime").symlink_to(redirected, target_is_directory=True)
        with self.assertRaisesRegex(source.MaterializationError, "symlink component"):
            source.materialize(self.root, self.pin_path, self.archive)
        self.assertEqual([], list(redirected.iterdir()))

    def test_existing_runtime_substitution_is_rejected_before_child_mutation(self) -> None:
        workflow = self.root / ".workflow-runtime"
        workflow.mkdir()
        (workflow / "owned").write_bytes(b"original")
        parked = self.root / ".workflow-runtime-attacker-parked"
        real_open = source.os.open
        injected = False

        def substitute_after_open(
            path: object,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal injected
            descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
            if path == ".workflow-runtime" and dir_fd is not None and not injected:
                injected = True
                os.rename(
                    path,
                    parked.name,
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                os.mkdir(path, dir_fd=dir_fd)
                (self.root / ".workflow-runtime" / "unrelated").write_bytes(b"preserve")
            return descriptor

        with mock.patch.object(
            source.os, "open", side_effect=substitute_after_open
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(source.MaterializationError, "identity changed"):
                source.materialize(self.root, self.pin_path, self.archive)
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (workflow / "unrelated").read_bytes())
        self.assertEqual({"unrelated"}, {path.name for path in workflow.iterdir()})
        self.assertEqual(b"original", (parked / "owned").read_bytes())

    def test_post_publication_failure_rolls_back_existing_tree(self) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        (destination / "keep").write_text("original", encoding="utf-8")
        real_verify = source.verify_materialized
        calls = 0

        def fail_after_publish(repo: Path, pin: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise source.MaterializationError("injected verification failure")
            return real_verify(repo, pin)

        rename_flags: list[int] = []
        real_rename = source._linux_renameat2

        def recording_rename(*args: object) -> None:
            rename_flags.append(int(args[-1]))
            real_rename(*args)  # type: ignore[arg-type]

        with mock.patch.object(
            source, "verify_materialized", side_effect=fail_after_publish
        ), mock.patch.object(source, "_linux_renameat2", side_effect=recording_rename):
            with self.assertRaisesRegex(source.MaterializationError, "injected"):
                source.materialize(self.root, self.pin_path, self.archive, replace_existing=True)
        self.assertEqual("original", (destination / "keep").read_text())
        self.assertGreaterEqual(rename_flags.count(source.RENAME_EXCHANGE), 2)
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        self.assertFalse((runtime / "MIPStarRE.transaction").exists())

    def test_hostile_substitution_during_success_retention_is_preserved(self) -> None:
        real_move = source._atomic_move_bound
        injected = False

        def substitute_before_retention(
            source_parent: int,
            source_name: str,
            source_descriptor: int,
            destination_parent: int,
            destination_name: str,
            label: str,
            renamed: object = None,
        ) -> None:
            nonlocal injected
            if label == "materialization transaction retention" and not injected:
                injected = True
                os.rename(
                    source_name,
                    "attacker-parked",
                    src_dir_fd=source_parent,
                    dst_dir_fd=source_parent,
                )
                os.mkdir(source_name, dir_fd=source_parent)
                substitute = Path("/proc/self/fd") / str(source_parent) / source_name
                (substitute / "unrelated").write_bytes(b"preserve")
            real_move(
                source_parent,
                source_name,
                source_descriptor,
                destination_parent,
                destination_name,
                label,
                renamed,  # type: ignore[arg-type]
            )

        with mock.patch.object(
            source, "_atomic_move_bound", side_effect=substitute_before_retention
        ):
            with self.assertRaises(source.MaterializationError):
                source.materialize(self.root, self.pin_path, self.archive)
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        self.assertTrue(injected)
        self.assertEqual(
            b"preserve", (runtime / "MIPStarRE.transaction" / "unrelated").read_bytes()
        )
        self.assertTrue((runtime / "attacker-parked").is_dir())

    def test_queued_stage_substitution_after_retention_prevents_success(self) -> None:
        real_move = source._atomic_move_bound
        injected = False

        def substitute_after_retention(
            source_parent: int,
            source_name: str,
            source_descriptor: int,
            destination_parent: int,
            destination_name: str,
            label: str,
            renamed: object = None,
        ) -> None:
            nonlocal injected
            real_move(
                source_parent,
                source_name,
                source_descriptor,
                destination_parent,
                destination_name,
                label,
                renamed,  # type: ignore[arg-type]
            )
            if label == "materialization transaction retention" and not injected:
                injected = True
                retained = Path("/proc/self/fd") / str(destination_parent) / destination_name
                stage = retained / "stage"
                parked = retained / "attacker-stage-parked"
                stage.rename(parked)
                stage.mkdir()
                (stage / "substitute").write_bytes(b"preserve")

        with mock.patch.object(
            source, "_atomic_move_bound", side_effect=substitute_after_retention
        ):
            with self.assertRaisesRegex(source.MaterializationError, "rollback is incomplete"):
                source.materialize(self.root, self.pin_path, self.archive)

        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        evidence = next(runtime.glob("MIPStarRE.transaction.retained-*"))
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (evidence / "stage" / "substitute").read_bytes())
        self.assertTrue((evidence / "attacker-stage-parked").is_dir())
        self.assertTrue((self.root / "MIPStarRE" / "Quantum" / "Measurement.lean").is_file())

    def test_queued_stage_slot_aba_after_retention_prevents_success(self) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        (destination / "original").write_bytes(b"original")
        real_move = source._atomic_move_bound
        injected = False

        def aba_after_retention(
            source_parent: int,
            source_name: str,
            source_descriptor: int,
            destination_parent: int,
            destination_name: str,
            label: str,
            renamed: object = None,
        ) -> None:
            nonlocal injected
            real_move(
                source_parent,
                source_name,
                source_descriptor,
                destination_parent,
                destination_name,
                label,
                renamed,  # type: ignore[arg-type]
            )
            if label == "materialization transaction retention" and not injected:
                injected = True
                retained = Path("/proc/self/fd") / str(destination_parent) / destination_name
                stage = retained / "stage"
                parked = stage / "attacker-original-parked"
                substitute = stage / "attacker-substitute"
                substitute.mkdir()
                (substitute / "substitute").write_bytes(b"preserve")
                (stage / "MIPStarRE").rename(parked)
                substitute.rename(stage / "MIPStarRE")
                (stage / "MIPStarRE").rename(substitute)
                parked.rename(stage / "MIPStarRE")

        with mock.patch.object(source, "_atomic_move_bound", side_effect=aba_after_retention):
            with self.assertRaisesRegex(source.MaterializationError, "rollback is incomplete"):
                source.materialize(
                    self.root, self.pin_path, self.archive, replace_existing=True
                )

        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        evidence = next(runtime.glob("MIPStarRE.transaction.retained-*"))
        self.assertTrue(injected)
        self.assertEqual(
            b"original", (evidence / "stage" / "MIPStarRE" / "original").read_bytes()
        )
        self.assertEqual(
            b"preserve",
            (evidence / "stage" / "attacker-substitute" / "substitute").read_bytes(),
        )
        self.assertTrue((destination / "Quantum" / "Measurement.lean").is_file())

    def test_retained_marker_and_unexpected_stage_child_prevent_success(self) -> None:
        real_move = source._atomic_move_bound
        injected = False

        def contaminate_after_retention(
            source_parent: int,
            source_name: str,
            source_descriptor: int,
            destination_parent: int,
            destination_name: str,
            label: str,
            renamed: object = None,
        ) -> None:
            nonlocal injected
            real_move(
                source_parent,
                source_name,
                source_descriptor,
                destination_parent,
                destination_name,
                label,
                renamed,  # type: ignore[arg-type]
            )
            if label == "materialization transaction retention" and not injected:
                injected = True
                retained = Path("/proc/self/fd") / str(destination_parent) / destination_name
                (retained / "transaction.json").write_bytes(b"corrupt\n")
                (retained / "stage" / "unexpected").write_bytes(b"preserve")

        with mock.patch.object(
            source, "_atomic_move_bound", side_effect=contaminate_after_retention
        ):
            with self.assertRaises(source.MaterializationError):
                source.materialize(self.root, self.pin_path, self.archive)

        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        evidence = next(runtime.glob("MIPStarRE.transaction.retained-*"))
        self.assertTrue(injected)
        self.assertEqual(b"corrupt\n", (evidence / "transaction.json").read_bytes())
        self.assertEqual(b"preserve", (evidence / "stage" / "unexpected").read_bytes())

    def test_post_rename_monitor_failure_is_not_misclassified_as_unpublished(self) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        (destination / "keep").write_bytes(b"original")
        real_exchange = source._atomic_exchange_bound

        def fail_after_exchange(*args: object) -> None:
            callback = args[-1]
            real_exchange(*args)  # type: ignore[arg-type]
            if callable(callback):
                raise source.MaterializationError("injected post-rename monitor failure")

        with mock.patch.object(
            source, "_atomic_exchange_bound", side_effect=fail_after_exchange
        ):
            with self.assertRaisesRegex(source.MaterializationError, "rollback is incomplete"):
                source.materialize(self.root, self.pin_path, self.archive, replace_existing=True)
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        self.assertTrue((runtime / "MIPStarRE.transaction").is_dir())
        self.assertTrue(destination.is_dir())

    def test_transaction_retention_collision_preserves_both_objects(self) -> None:
        token = "a" * 32
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        runtime.mkdir(parents=True)
        collision = runtime / f"MIPStarRE.transaction.retained-{token}"
        collision.mkdir()
        (collision / "unrelated").write_bytes(b"preserve")
        with mock.patch.object(source.secrets, "token_hex", return_value=token):
            with self.assertRaises(source.MaterializationError):
                source.materialize(self.root, self.pin_path, self.archive)
        self.assertEqual(b"preserve", (collision / "unrelated").read_bytes())
        self.assertFalse((self.root / "MIPStarRE").exists())
        self.assertTrue((runtime / f"MIPStarRE.transaction.failed-{token}").is_dir())

    def test_hostile_substitution_during_rollback_is_preserved(self) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        (destination / "keep").write_bytes(b"original")
        real_verify = source.verify_materialized
        verify_calls = 0

        def fail_after_publish(repo: Path, pin: dict[str, object]) -> dict[str, object]:
            nonlocal verify_calls
            verify_calls += 1
            if verify_calls <= 2:
                raise source.MaterializationError("injected verification failure")
            return real_verify(repo, pin)

        real_exchange = source._atomic_exchange_bound
        injected = False

        def substitute_before_rollback(*args: object) -> None:
            nonlocal injected
            label = str(args[-1])
            if label == "MIPStarRE foundation rollback" and not injected:
                injected = True
                root_descriptor = int(args[0])
                os.rename(
                    "MIPStarRE",
                    "attacker-published",
                    src_dir_fd=root_descriptor,
                    dst_dir_fd=root_descriptor,
                )
                os.mkdir("MIPStarRE", dir_fd=root_descriptor)
                substitute = Path("/proc/self/fd") / str(root_descriptor) / "MIPStarRE"
                (substitute / "unrelated").write_bytes(b"preserve")
            real_exchange(*args)  # type: ignore[arg-type]

        with mock.patch.object(
            source, "verify_materialized", side_effect=fail_after_publish
        ), mock.patch.object(
            source, "_atomic_exchange_bound", side_effect=substitute_before_rollback
        ):
            with self.assertRaisesRegex(source.MaterializationError, "rollback is incomplete"):
                source.materialize(self.root, self.pin_path, self.archive, replace_existing=True)
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (destination / "unrelated").read_bytes())
        self.assertTrue((self.root / "attacker-published").is_dir())

    def test_hostile_substitution_during_preparation_error_is_preserved(self) -> None:
        real_create = source._create_new_file
        injected = False

        def fail_transaction_write(
            parent_descriptor: int,
            name: str,
            payload: bytes,
            *,
            readable: bool = False,
            monitor: object = None,
        ) -> int:
            nonlocal injected
            if name == "transaction.json" and not injected:
                injected = True
                transaction = Path(os.readlink(f"/proc/self/fd/{parent_descriptor}"))
                runtime = transaction.parent
                transaction.rename(runtime / "attacker-preparation")
                transaction.mkdir()
                (transaction / "unrelated").write_bytes(b"preserve")
                raise OSError("injected preparation failure")
            return real_create(
                parent_descriptor,
                name,
                payload,
                readable=readable,
                monitor=monitor,  # type: ignore[arg-type]
            )

        with mock.patch.object(source, "_create_new_file", side_effect=fail_transaction_write):
            with self.assertRaisesRegex(source.MaterializationError, "ambiguous state"):
                source.materialize(self.root, self.pin_path, self.archive)
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        self.assertTrue(injected)
        self.assertEqual(
            b"preserve", (runtime / "MIPStarRE.transaction" / "unrelated").read_bytes()
        )
        self.assertTrue((runtime / "attacker-preparation").is_dir())

    def test_creation_event_batch_rejects_move_and_substitute(self) -> None:
        real_mkdir = source.os.mkdir
        injected = False

        def substitute_after_mkdir(
            path: object,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal injected
            real_mkdir(path, mode, dir_fd=dir_fd)
            if path == "MIPStarRE.transaction" and dir_fd is not None and not injected:
                injected = True
                os.rename(
                    path,
                    "attacker-created",
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                real_mkdir(path, mode, dir_fd=dir_fd)
                substitute = Path("/proc/self/fd") / str(dir_fd) / str(path)
                (substitute / "unrelated").write_bytes(b"preserve")

        with mock.patch.object(
            source.os, "mkdir", side_effect=substitute_after_mkdir
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(source.MaterializationError, "exact monitor events"):
                source.materialize(self.root, self.pin_path, self.archive)
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        self.assertTrue(injected)
        self.assertEqual(
            b"preserve", (runtime / "MIPStarRE.transaction" / "unrelated").read_bytes()
        )
        self.assertTrue((runtime / "attacker-created").is_dir())

    def test_transaction_document_creation_aba_is_detected_before_write(self) -> None:
        real_open = source.os.open
        injected = False
        substitute_path: Path | None = None

        def substitute_after_open(
            path: object,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal injected, substitute_path
            descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
            if path == "transaction.json" and dir_fd is not None and not injected:
                injected = True
                transaction = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                runtime = transaction.parent
                parked = transaction / "attacker-document-parked"
                os.rename(
                    "transaction.json",
                    parked.name,
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                substitute = real_open(
                    "transaction.json",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=dir_fd,
                )
                os.write(substitute, b"preserve")
                os.close(substitute)
                substitute_path = runtime / "attacker-document-substitute"
                runtime_descriptor = real_open(runtime, source._directory_flags())
                try:
                    os.rename(
                        "transaction.json",
                        substitute_path.name,
                        src_dir_fd=dir_fd,
                        dst_dir_fd=runtime_descriptor,
                    )
                finally:
                    os.close(runtime_descriptor)
                os.rename(
                    parked.name,
                    "transaction.json",
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
            return descriptor

        with mock.patch.object(
            source.os, "open", side_effect=substitute_after_open
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(source.MaterializationError, "ambiguous state"):
                source.materialize(self.root, self.pin_path, self.archive)

        self.assertTrue(injected)
        assert substitute_path is not None
        self.assertEqual(b"preserve", substitute_path.read_bytes())

    def test_archive_descendant_substitution_cannot_receive_output_bytes(self) -> None:
        external = Path(self.temporary.name) / "external-archive-target"
        external.mkdir()
        real_mkdir = source.os.mkdir
        injected = False

        def substitute_after_mkdir(
            path: object,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal injected
            real_mkdir(path, mode, dir_fd=dir_fd)
            if path == "Quantum" and dir_fd is not None and not injected:
                injected = True
                os.rename(
                    "Quantum",
                    "attacker-created-Quantum",
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                os.symlink(str(external), "Quantum", target_is_directory=True, dir_fd=dir_fd)

        with mock.patch.object(
            source.os, "mkdir", side_effect=substitute_after_mkdir
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                source.materialize(self.root, self.pin_path, self.archive)

        self.assertTrue(injected)
        self.assertEqual([], list(external.iterdir()))
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        evidence = next(runtime.glob("MIPStarRE.transaction.failed-*"))
        candidate = evidence / "stage" / "MIPStarRE"
        self.assertTrue((candidate / "Quantum").is_symlink())
        self.assertTrue((candidate / "attacker-created-Quantum").is_dir())

    def test_authored_descendant_substitution_cannot_receive_output_bytes(self) -> None:
        destination = self.root / "MIPStarRE"
        authored = destination / "QPBT" / "Nested"
        authored.mkdir(parents=True)
        (authored / "Owned.lean").write_bytes(b"def owned := true\n")
        (destination / "untrusted").write_bytes(b"replace")
        external = Path(self.temporary.name) / "external-authored-target"
        external.mkdir()
        real_mkdir = source.os.mkdir
        injected = False

        def substitute_after_mkdir(
            path: object,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal injected
            real_mkdir(path, mode, dir_fd=dir_fd)
            if path == "Nested" and dir_fd is not None and not injected:
                injected = True
                os.rename(
                    "Nested",
                    "attacker-created-Nested",
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                os.symlink(str(external), "Nested", target_is_directory=True, dir_fd=dir_fd)

        with mock.patch.object(
            source.os, "mkdir", side_effect=substitute_after_mkdir
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                source.materialize(
                    self.root, self.pin_path, self.archive, replace_existing=True
                )

        self.assertTrue(injected)
        self.assertEqual([], list(external.iterdir()))
        self.assertEqual(b"def owned := true\n", (authored / "Owned.lean").read_bytes())
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        evidence = next(runtime.glob("MIPStarRE.transaction.failed-*"))
        staged_authored = evidence / "stage" / "MIPStarRE" / "QPBT"
        self.assertTrue((staged_authored / "Nested").is_symlink())
        self.assertTrue((staged_authored / "attacker-created-Nested").is_dir())

    def test_archive_directory_creation_handoff_relocation_is_detected_before_population(
        self,
    ) -> None:
        external = Path(self.temporary.name) / "external-archive-directory"
        external.mkdir()
        external_descriptor = os.open(external, source._directory_flags())
        real_create = source._create_continuous_directory
        injected = False

        def relocate_after_handoff(
            parent_descriptor: int,
            name: str,
            label: str,
            parent_monitor: object,
        ) -> object:
            nonlocal injected
            binding = real_create(
                parent_descriptor, name, label, parent_monitor  # type: ignore[arg-type]
            )
            if name == "Quantum" and not injected:
                injected = True
                os.rename(
                    name,
                    "relocated-Quantum",
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=external_descriptor,
                )
            return binding

        try:
            with mock.patch.object(
                source, "_create_continuous_directory", side_effect=relocate_after_handoff
            ), mock.patch.object(source, "_require_transaction_capabilities"):
                with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                    source.materialize(self.root, self.pin_path, self.archive)
        finally:
            os.close(external_descriptor)
        self.assertTrue(injected)
        relocated = external / "relocated-Quantum"
        self.assertTrue(relocated.is_dir())
        self.assertEqual([], list(relocated.iterdir()))

    def test_authored_directory_creation_handoff_relocation_is_detected_before_population(
        self,
    ) -> None:
        destination = self.root / "MIPStarRE"
        authored = destination / "QPBT" / "Nested"
        authored.mkdir(parents=True)
        (authored / "Owned.lean").write_bytes(b"def owned := true\n")
        (destination / "untrusted").write_bytes(b"replace")
        external = Path(self.temporary.name) / "external-authored-directory"
        external.mkdir()
        external_descriptor = os.open(external, source._directory_flags())
        real_create = source._create_continuous_directory
        injected = False

        def relocate_after_handoff(
            parent_descriptor: int,
            name: str,
            label: str,
            parent_monitor: object,
        ) -> object:
            nonlocal injected
            binding = real_create(
                parent_descriptor, name, label, parent_monitor  # type: ignore[arg-type]
            )
            if name == "Nested" and not injected:
                injected = True
                os.rename(
                    name,
                    "relocated-Nested",
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=external_descriptor,
                )
            return binding

        try:
            with mock.patch.object(
                source, "_create_continuous_directory", side_effect=relocate_after_handoff
            ), mock.patch.object(source, "_require_transaction_capabilities"):
                with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                    source.materialize(
                        self.root, self.pin_path, self.archive, replace_existing=True
                    )
        finally:
            os.close(external_descriptor)
        self.assertTrue(injected)
        relocated = external / "relocated-Nested"
        self.assertTrue(relocated.is_dir())
        self.assertEqual([], list(relocated.iterdir()))
        self.assertEqual(b"def owned := true\n", (authored / "Owned.lean").read_bytes())

    def test_archive_file_post_link_relocation_receives_complete_stable_bytes(self) -> None:
        external = Path(self.temporary.name) / "external-archive-file"
        external.mkdir()
        external_descriptor = os.open(external, source._directory_flags())
        real_link = source._linux_link_unnamed_file
        real_write = source.os.write
        injected = False
        payload_was_unnamed = False

        def assert_unnamed_write(descriptor: int, payload: object) -> int:
            nonlocal payload_was_unnamed
            if bytes(payload) == b"def pinned := 1\n":  # type: ignore[arg-type]
                payload_was_unnamed = True
                self.assertEqual(0, os.fstat(descriptor).st_nlink)
            return real_write(descriptor, payload)  # type: ignore[arg-type]

        def relocate_after_link(
            descriptor: int, parent_descriptor: int, name: str
        ) -> None:
            nonlocal injected
            real_link(descriptor, parent_descriptor, name)
            if name == "Measurement.lean" and not injected:
                injected = True
                os.rename(
                    name,
                    "relocated-Measurement.lean",
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=external_descriptor,
                )

        try:
            with mock.patch.object(
                source, "_linux_link_unnamed_file", side_effect=relocate_after_link
            ), mock.patch.object(
                source.os, "write", side_effect=assert_unnamed_write
            ), mock.patch.object(source, "_require_transaction_capabilities"):
                with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                    source.materialize(self.root, self.pin_path, self.archive)
        finally:
            os.close(external_descriptor)
        self.assertTrue(injected)
        self.assertTrue(payload_was_unnamed)
        self.assertEqual(
            b"def pinned := 1\n",
            (external / "relocated-Measurement.lean").read_bytes(),
        )

    def test_authored_file_post_link_relocation_receives_complete_stable_bytes(self) -> None:
        destination = self.root / "MIPStarRE"
        authored = destination / "QPBT"
        authored.mkdir(parents=True)
        (authored / "Owned.lean").write_bytes(b"def owned := true\n")
        (destination / "untrusted").write_bytes(b"replace")
        external = Path(self.temporary.name) / "external-authored-file"
        external.mkdir()
        external_descriptor = os.open(external, source._directory_flags())
        real_link = source._linux_link_unnamed_file
        real_write = source.os.write
        injected = False
        payload_was_unnamed = False

        def assert_unnamed_write(descriptor: int, payload: object) -> int:
            nonlocal payload_was_unnamed
            if bytes(payload) == b"def owned := true\n":  # type: ignore[arg-type]
                payload_was_unnamed = True
                self.assertEqual(0, os.fstat(descriptor).st_nlink)
            return real_write(descriptor, payload)  # type: ignore[arg-type]

        def relocate_after_link(
            descriptor: int, parent_descriptor: int, name: str
        ) -> None:
            nonlocal injected
            real_link(descriptor, parent_descriptor, name)
            if name == "Owned.lean" and not injected:
                injected = True
                os.rename(
                    name,
                    "relocated-Owned.lean",
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=external_descriptor,
                )

        try:
            with mock.patch.object(
                source, "_linux_link_unnamed_file", side_effect=relocate_after_link
            ), mock.patch.object(
                source.os, "write", side_effect=assert_unnamed_write
            ), mock.patch.object(source, "_require_transaction_capabilities"):
                with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                    source.materialize(
                        self.root, self.pin_path, self.archive, replace_existing=True
                    )
        finally:
            os.close(external_descriptor)
        self.assertTrue(injected)
        self.assertTrue(payload_was_unnamed)
        self.assertEqual(
            b"def owned := true\n", (external / "relocated-Owned.lean").read_bytes()
        )
        self.assertEqual(b"def owned := true\n", (authored / "Owned.lean").read_bytes())

    def _assert_live_detached_failure_preserves_destination(self, failure_kind: str) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        marker = destination / "original-marker"
        marker.write_bytes(b"preserve")
        destination_identity = (destination.stat().st_dev, destination.stat().st_ino)
        route_calls: list[tuple[int, bytes, int, bytes, int]] = []

        if failure_kind == "tmpfile":
            real_open = source.os.open

            def fail_tmpfile(
                path: object,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                if (flags & source.os.O_TMPFILE) == source.os.O_TMPFILE:
                    raise OSError(errno.EOPNOTSUPP, "injected O_TMPFILE refusal")
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(source.os, "open", side_effect=fail_tmpfile) as patched_open:
                supported = set(source.os.supports_dir_fd)
                supported.add(patched_open)
                with mock.patch.object(source.os, "supports_dir_fd", supported):
                    with self.assertRaisesRegex(
                        source.MaterializationError,
                        "could not prepare materialization transaction",
                    ) as raised:
                        source.materialize(
                            self.root, self.pin_path, self.archive, replace_existing=True
                        )
            self.assertIsNotNone(raised.exception.__cause__)
            self.assertIn("requires O_TMPFILE", str(raised.exception.__cause__))
        elif failure_kind == "linkat":
            real_link = source._linux_link_unnamed_file

            def fail_both_linkat_routes(
                descriptor: int, parent_descriptor: int, name: str
            ) -> None:
                real_libc = source._linux_libc()

                def fail_linkat(*arguments: object) -> int:
                    old_descriptor, old_name, new_descriptor, new_name, flags = arguments
                    route_calls.append(
                        (
                            int(old_descriptor),
                            bytes(old_name),
                            int(new_descriptor),
                            bytes(new_name),
                            int(flags),
                        )
                    )
                    error_number = (
                        errno.EPERM if len(route_calls) == 1 else errno.EOPNOTSUPP
                    )
                    ctypes.set_errno(error_number)
                    return -1

                linkat = mock.Mock(side_effect=fail_linkat)

                class LibcProxy:
                    def __getattr__(self, attribute: str) -> object:
                        return getattr(real_libc, attribute)

                proxy = LibcProxy()
                proxy.linkat = linkat  # type: ignore[attr-defined]
                with mock.patch.object(source, "_linux_libc", return_value=proxy):
                    real_link(descriptor, parent_descriptor, name)

            with mock.patch.object(
                source,
                "_linux_link_unnamed_file",
                side_effect=fail_both_linkat_routes,
            ):
                with self.assertRaisesRegex(
                    source.MaterializationError,
                    "could not prepare materialization transaction",
                ) as raised:
                    source.materialize(
                        self.root, self.pin_path, self.archive, replace_existing=True
                    )
            self.assertIsNotNone(raised.exception.__cause__)
            self.assertIn(
                "could not publish unnamed materialized output",
                str(raised.exception.__cause__),
            )
            self.assertEqual(2, len(route_calls))
            self.assertEqual(
                (b"", source.AT_EMPTY_PATH),
                (route_calls[0][1], route_calls[0][4]),
            )
            self.assertTrue(route_calls[1][1].startswith(b"/proc/self/fd/"))
            self.assertEqual(
                getattr(source.os, "AT_SYMLINK_FOLLOW", 0x400), route_calls[1][4]
            )
        else:
            raise AssertionError(f"unknown failure kind: {failure_kind}")

        self.assertEqual(
            destination_identity, (destination.stat().st_dev, destination.stat().st_ino)
        )
        self.assertEqual(b"preserve", marker.read_bytes())
        self.assertEqual(
            ["original-marker"], sorted(path.name for path in destination.iterdir())
        )
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        failed = list(runtime.glob("MIPStarRE.transaction.failed-*"))
        self.assertEqual(1, len(failed))
        self.assertTrue((failed[0] / "transaction.json").is_file())
        self.assertTrue((failed[0] / "stage" / "MIPStarRE" / "Quantum").is_dir())
        self.assertFalse(
            (failed[0] / "stage" / "MIPStarRE" / "Quantum" / "Measurement.lean").exists()
        )
        self.assertFalse((runtime / "MIPStarRE.transaction").exists())

    def test_live_tmpfile_failure_preserves_destination_and_transaction(self) -> None:
        self._assert_live_detached_failure_preserves_destination("tmpfile")

    def test_live_both_linkat_route_failures_preserve_destination_and_transaction(self) -> None:
        self._assert_live_detached_failure_preserves_destination("linkat")

    def test_retained_backup_contamination_is_refused_and_preserved(self) -> None:
        real_inventory = source._retained_transaction_inventory
        injected = False

        def contaminate_backup(*args: object) -> dict[str, object]:
            nonlocal injected
            backup_descriptor = int(args[4])
            if not injected:
                injected = True
                descriptor = os.open(
                    "unexpected",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=backup_descriptor,
                )
                try:
                    os.write(descriptor, b"preserve")
                finally:
                    os.close(descriptor)
            return real_inventory(*args)  # type: ignore[arg-type,return-value]

        with mock.patch.object(
            source, "_retained_transaction_inventory", side_effect=contaminate_backup
        ):
            with self.assertRaises(source.MaterializationError):
                source.materialize(self.root, self.pin_path, self.archive)
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        evidence = next(runtime.glob("MIPStarRE.transaction.failed-*"))
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (evidence / "backup" / "unexpected").read_bytes())

    def test_post_population_archive_and_authored_hard_links_prevent_publication(self) -> None:
        destination = self.root / "MIPStarRE"
        authored = destination / "QPBT"
        authored.mkdir(parents=True)
        (authored / "Owned.lean").write_bytes(b"def owned := true\n")
        (destination / "untrusted").write_bytes(b"replace")
        external = Path(self.temporary.name) / "late-output-links"
        external.mkdir()
        real_populate = source._populate_bound_tree
        injected: list[str] = []

        def link_after_population(
            root_descriptor: int,
            directories: object,
            files: object,
            *,
            root_binding: object = None,
        ) -> None:
            real_populate(
                root_descriptor,
                directories,  # type: ignore[arg-type]
                files,  # type: ignore[arg-type]
                root_binding=root_binding,  # type: ignore[arg-type]
            )
            if root_binding is None:
                quantum = os.open("Quantum", source._directory_flags(), dir_fd=root_descriptor)
                try:
                    os.link(
                        "Measurement.lean",
                        external / "archive.lean",
                        src_dir_fd=quantum,
                        follow_symlinks=False,
                    )
                finally:
                    os.close(quantum)
                injected.append("archive")
            else:
                os.link(
                    "Owned.lean",
                    external / "authored.lean",
                    src_dir_fd=root_descriptor,
                    follow_symlinks=False,
                )
                injected.append("authored")

        with mock.patch.object(
            source, "_populate_bound_tree", side_effect=link_after_population
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                source.materialize(
                    self.root, self.pin_path, self.archive, replace_existing=True
                )
        self.assertEqual(["archive", "authored"], injected)
        self.assertEqual(b"def pinned := 1\n", (external / "archive.lean").read_bytes())
        self.assertEqual(
            b"def owned := true\n", (external / "authored.lean").read_bytes()
        )
        self.assertEqual(b"def owned := true\n", (authored / "Owned.lean").read_bytes())

    def test_retained_backup_post_inventory_contamination_prevents_success(self) -> None:
        real_inventory = source._retained_transaction_inventory
        injected = False

        def contaminate_after_inventory(*args: object) -> dict[str, object]:
            nonlocal injected
            result = real_inventory(*args)
            if not injected:
                injected = True
                backup_descriptor = int(args[4])
                descriptor = os.open(
                    "post-scan",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=backup_descriptor,
                )
                try:
                    os.write(descriptor, b"preserve")
                finally:
                    os.close(descriptor)
            return result

        with mock.patch.object(
            source,
            "_retained_transaction_inventory",
            side_effect=contaminate_after_inventory,
        ), mock.patch.object(source, "_require_transaction_capabilities"):
            with self.assertRaisesRegex(
                source.MaterializationError,
                "object changed|backup is not empty|changed after result construction",
            ):
                source.materialize(self.root, self.pin_path, self.archive)
        evidence = next(
            (self.root / ".workflow-runtime" / "mipstarre-materialization").glob(
                "MIPStarRE.transaction.failed-*"
            )
        )
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (evidence / "backup" / "post-scan").read_bytes())

    def test_retained_original_descendant_mutation_is_refused_and_preserved(self) -> None:
        destination = self.root / "MIPStarRE"
        destination.mkdir()
        original = destination / "keep"
        original.write_bytes(b"original")
        real_inventory = source._retained_transaction_inventory
        injected = False

        def mutate_original(*args: object) -> dict[str, object]:
            nonlocal injected
            original_descriptor = int(args[5])
            if not injected:
                injected = True
                descriptor = os.open(
                    "keep", os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW, dir_fd=original_descriptor
                )
                try:
                    os.write(descriptor, b"modified")
                finally:
                    os.close(descriptor)
            return real_inventory(*args)  # type: ignore[arg-type,return-value]

        with mock.patch.object(
            source, "_retained_transaction_inventory", side_effect=mutate_original
        ):
            with self.assertRaisesRegex(
                source.MaterializationError, "recursive inventory changed"
            ):
                source.materialize(
                    self.root, self.pin_path, self.archive, replace_existing=True
                )
        self.assertTrue(injected)
        self.assertEqual(b"modified", original.read_bytes())

    def test_authored_source_namespace_substitution_prevents_publication(self) -> None:
        destination = self.root / "MIPStarRE"
        authored = destination / "QPBT"
        authored.mkdir(parents=True)
        (authored / "Owned.lean").write_bytes(b"def owned := true\n")
        (destination / "untrusted").write_bytes(b"replace")
        parked = destination / "attacker-original-QPBT"
        real_snapshot = source._snapshot_bound_tree
        injected = False

        def substitute_before_snapshot(
            descriptor: int,
        ) -> tuple[list[str], list[tuple[str, bytes]], list[object]]:
            nonlocal injected
            if not injected:
                injected = True
                authored.rename(parked)
                authored.mkdir()
                (authored / "Substitute.lean").write_bytes(b"def substitute := true\n")
            return real_snapshot(descriptor)  # type: ignore[return-value]

        with mock.patch.object(
            source, "_snapshot_bound_tree", side_effect=substitute_before_snapshot
        ):
            with self.assertRaisesRegex(source.MaterializationError, "could not prepare"):
                source.materialize(
                    self.root, self.pin_path, self.archive, replace_existing=True
                )

        self.assertTrue(injected)
        self.assertEqual(b"def owned := true\n", (parked / "Owned.lean").read_bytes())
        self.assertEqual(
            b"def substitute := true\n", (authored / "Substitute.lean").read_bytes()
        )
        self.assertFalse((destination / "Quantum" / "Measurement.lean").exists())

    def test_legacy_rollback_refuses_without_live_descriptors(self) -> None:
        transaction = self.root / "transaction"
        transaction.mkdir()
        errors = source._rollback(transaction, self.root / "MIPStarRE", True)
        self.assertTrue(errors)
        self.assertTrue(transaction.exists())
        self.assertIn("live rollback requires held descriptors", errors[0])

    def test_stale_transaction_is_preserved_and_refused(self) -> None:
        runtime = self.root / ".workflow-runtime" / "mipstarre-materialization"
        transaction = runtime / "MIPStarRE.transaction"
        backup = transaction / "backup" / "MIPStarRE" / "QPBT"
        backup.mkdir(parents=True)
        (backup / "Owned.lean").write_text("def recovered := true\n", encoding="utf-8")
        (transaction / "stage" / "MIPStarRE").mkdir(parents=True)
        (transaction / "transaction.json").write_bytes(
            source._transaction_document(self.root / "MIPStarRE", True)
        )

        before = (transaction / "transaction.json").read_bytes()
        with self.assertRaisesRegex(source.MaterializationError, "no live authority"):
            source.materialize(self.root, self.pin_path, self.archive, replace_existing=True)
        self.assertEqual(before, (transaction / "transaction.json").read_bytes())
        self.assertFalse((self.root / "MIPStarRE").exists())

    def test_verify_rejects_symlink_inside_authored_tree(self) -> None:
        source.materialize(self.root, self.pin_path, self.archive)
        authored = self.root / "MIPStarRE" / "QPBT"
        authored.mkdir()
        (authored / "escape").symlink_to(self.root / "lean-toolchain")
        with self.assertRaises(source.MaterializationError):
            source.verify_materialized(self.root, self.pin)


if __name__ == "__main__":
    unittest.main()
