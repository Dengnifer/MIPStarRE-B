from __future__ import annotations

import copy
from contextlib import contextmanager
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "materialize_lake_packages", ROOT / "scripts" / "materialize_lake_packages.py"
)
assert SPEC and SPEC.loader
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)

FIXTURE_WIDGET_TARGET_PATH = "widget/package-lock.json"
FIXTURE_WIDGET_SIDECAR_PATH = "widget/package-lock.json.hash"
FIXTURE_WIDGET_TRACE_PATH = "widget/package-lock.json.trace"
FIXTURE_WIDGET_TARGET = b"fixture package lock\n"
FIXTURE_LAKE_HASH = b"179e66574f04806e"
FIXTURE_WIDGET_TRACE = b'{"outputs":"179e66574f04806e.art"}\n'


def is_transaction_stage(path: Path) -> bool:
    try:
        return Path(os.readlink(path.parent)).name == "new"
    except OSError:
        return path.parent.name == "new"


def pax_record(key: str, value: str) -> bytes:
    body = f"{key}={value}\n".encode()
    length = len(body) + 2
    while True:
        record = f"{length} ".encode() + body
        if len(record) == length:
            return record
        length = len(record)


def tar_header(
    name: str,
    kind: bytes,
    size: int = 0,
    *,
    mode: int = 0o644,
    link: str = "",
) -> bytes:
    encoded_name = name.encode()
    if len(encoded_name) > 100:
        raise ValueError("fixture path is too long")
    header = bytearray(512)
    header[: len(encoded_name)] = encoded_name
    header[100:108] = f"{mode:07o}\0".encode()
    header[108:116] = b"0000000\0"
    header[116:124] = b"0000000\0"
    header[124:136] = f"{size:011o}\0".encode()
    header[136:148] = b"00000000000\0"
    header[148:156] = b"        "
    header[156:157] = kind
    encoded_link = link.encode()
    header[157 : 157 + len(encoded_link)] = encoded_link
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    checksum = sum(header)
    header[148:156] = f"{checksum:06o}\0 ".encode()
    return bytes(header)


def tar_member(name: str, kind: bytes, payload: bytes = b"", *, mode: int = 0o644, link: str = "") -> bytes:
    return (
        tar_header(name, kind, len(payload), mode=mode, link=link)
        + payload
        + bytes((-len(payload)) % 512)
    )


def make_archive(
    package: dict,
    *,
    extra: list[tuple[str, bytes, bytes, int, str]] | None = None,
    replace_entries: list[tuple[str, bytes, bytes, int, str]] | None = None,
    directory_mode: int = 0o775,
) -> tuple[bytes, bytes]:
    prefix = package["archive"]["exact_prefix"]
    config = package["config_file"]
    entries = replace_entries or [
        (prefix, b"5", b"", directory_mode, ""),
        (prefix + config, b"0", f"name = \"{package['name']}\"\n".encode(), 0o664, ""),
        (prefix + "lake-manifest.json", b"0", b"{}\n", 0o664, ""),
        (prefix + "src/", b"5", b"", directory_mode, ""),
        (prefix + "src/source.txt", b"0", f"{package['name']}\n".encode(), 0o664, ""),
        (prefix + "tool", b"0", b"#!/bin/sh\nexit 0\n", 0o775, ""),
        (prefix + "src/source-link", b"2", b"", 0o777, "source.txt"),
    ]
    if replace_entries is None and package["name"] == "proofwidgets":
        entries += [
            (prefix + "widget/", b"5", b"", directory_mode, ""),
            (prefix + FIXTURE_WIDGET_TARGET_PATH, b"0", FIXTURE_WIDGET_TARGET, 0o664, ""),
            (prefix + FIXTURE_WIDGET_TRACE_PATH, b"0", FIXTURE_WIDGET_TRACE, 0o664, ""),
            (prefix + "widget/package.json", b"0", b"{}\n", 0o664, ""),
        ]
    if extra:
        entries += extra
    pax = pax_record("comment", package["revision"])
    raw = tar_member("pax_global_header", b"g", pax)
    for name, kind, payload, mode, link in entries:
        raw += tar_member(name, kind, payload, mode=mode, link=link)
    raw += bytes(1024)
    return gzip.compress(raw, mtime=0), raw


def manifest_entry(package: dict, *, inherited: bool) -> dict:
    return {
        "url": package["repository_url"],
        "type": "git",
        "subDir": None,
        "scope": package["scope"],
        "rev": package["revision"],
        "name": package["name"],
        "manifestFile": package["manifest_file"],
        "inputRev": package["input_revision"],
        "inherited": inherited,
        "configFile": package["config_file"],
    }


class LakePackageMaterializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        self.archives = Path(self.temporary.name) / "archives"
        self.archives.mkdir()
        specifications = [
            ("plausible", "leanprover-community/plausible", "lakefile.toml", False),
            ("LeanSearchClient", "leanprover-community/LeanSearchClient", "lakefile.toml", False),
            ("importGraph", "leanprover-community/import-graph", "lakefile.toml", False),
            ("proofwidgets", "leanprover-community/ProofWidgets4", "lakefile.lean", False),
            ("aesop", "leanprover-community/aesop", "lakefile.toml", False),
            ("Qq", "leanprover-community/quote4", "lakefile.toml", False),
            ("batteries", "leanprover-community/batteries", "lakefile.toml", False),
            ("Cli", "leanprover/lean4-cli", "lakefile.toml", True),
        ]
        self.packages: list[dict] = []
        self.archive_bytes: dict[str, bytes] = {}
        for index, (name, repository, config, mathlib_inherited) in enumerate(specifications, 1):
            revision = f"{index:x}" * 40
            scope = repository.split("/")[0]
            package = {
                "name": name,
                "scope": scope,
                "repository": repository,
                "repository_url": f"https://github.com/{repository}",
                "revision": revision,
                "input_revision": "main",
                "config_file": config,
                "manifest_file": "lake-manifest.json",
                "root_inherited": True,
                "mathlib_inherited": mathlib_inherited,
                "archive_url": f"https://codeload.github.com/{repository}/tar.gz/{revision}",
                "archive": {
                    "sha256": None,
                    "bytes": None,
                    "tar_sha256": None,
                    "tar_bytes": None,
                    "exact_prefix": f"{repository.split('/')[1]}-{revision}/",
                    "members": None,
                    "directories": None,
                    "regular_files": None,
                    "symlinks": None,
                    "regular_bytes": None,
                    "max_member_bytes": None,
                },
                "output": {
                    "directories": None,
                    "files": None,
                    "regular_files": None,
                    "symlinks": None,
                    "bytes": None,
                    "max_file_bytes": None,
                    "inventory_sha256": None,
                    "archive_tree_sha": None,
                    "tree_sha": None,
                    "gitlinks": [],
                },
                "pending_reason": None,
            }
            compressed, raw = make_archive(package)
            package["archive"]["tar_bytes"] = len(raw)
            facts, entries = source.inspect_archive_bytes(compressed, package)
            with tempfile.TemporaryDirectory() as tree_temporary:
                tree_root = Path(tree_temporary)
                extracted = tree_root / "source"
                source._write_entries(extracted, entries)
                tree_sha = source.compute_tree_sha(extracted, tree_root / "scratch", [])
            facts["output"]["archive_tree_sha"] = tree_sha
            facts["output"]["tree_sha"] = tree_sha
            package["archive"] = facts["archive"]
            package["output"] = facts["output"]
            self.packages.append(package)
            self.archive_bytes[name] = compressed
            (self.archives / f"{name}-{revision}.tar.gz").write_bytes(compressed)
        mathlib_entry = {
            "url": "https://github.com/leanprover-community/mathlib4",
            "type": "git",
            "subDir": None,
            "scope": "leanprover-community",
            "rev": "f" * 40,
            "name": "mathlib",
            "manifestFile": "lake-manifest.json",
            "inputRev": "v4.fixture",
            "inherited": False,
            "configFile": "lakefile.lean",
        }
        self.root_manifest = {
            "version": "1.2.0",
            "packagesDir": ".lake/packages",
            "packages": [mathlib_entry] + [manifest_entry(p, inherited=p["root_inherited"]) for p in self.packages],
            "name": "QPBT",
            "lakeDir": ".lake",
            "fixedToolchain": False,
        }
        self.mathlib_manifest = {
            "version": "1.2.0",
            "packagesDir": ".lake/packages",
            "packages": [manifest_entry(p, inherited=p["mathlib_inherited"]) for p in self.packages],
            "name": "mathlib",
            "lakeDir": ".lake",
            "fixedToolchain": True,
        }
        self.root_manifest_path = self.root / "lake-manifest.json"
        self.mathlib_manifest_path = self.root / source.MATHLIB_MANIFEST_SNAPSHOT
        self._write_json(self.root_manifest_path, self.root_manifest)
        self._write_json(self.mathlib_manifest_path, self.mathlib_manifest)
        self.pin = {
            "schema_version": source.SCHEMA_VERSION,
            "lake_manifest_version": "1.2.0",
            "packages_directory": ".lake/packages",
            "override_path": ".lake/package-overrides.json",
            "root_manifest_sha256": source._file_sha256(self.root_manifest_path),
            "mathlib_manifest_sha256": source._file_sha256(self.mathlib_manifest_path),
            "packages": self.packages,
        }
        self.pin_path = self.root / "references" / "lake-packages.json"
        self._write_json(self.pin_path, self.pin)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def _materialize(self, **kwargs: object) -> dict:
        return source.materialize(self.root, self.pin_path, self.archives, **kwargs)

    def _proofwidgets_package(self) -> dict:
        return next(package for package in self.packages if package["name"] == "proofwidgets")

    def _proofwidgets_root(self) -> Path:
        return self.root / ".lake/packages/proofwidgets"

    def _fixture_sidecar_contract(
        self,
        *,
        package: str = "proofwidgets",
        revision: str | None = None,
        target: str = FIXTURE_WIDGET_TARGET_PATH,
        target_sha256: str | None = None,
        sidecar: str = FIXTURE_WIDGET_SIDECAR_PATH,
    ) -> source.GeneratedSidecarContract:
        proofwidgets = self._proofwidgets_package()
        return source.GeneratedSidecarContract(
            package=package,
            revision=revision or proofwidgets["revision"],
            target=target,
            target_sha256=target_sha256 or hashlib.sha256(FIXTURE_WIDGET_TARGET).hexdigest(),
            sidecar=sidecar,
            sidecar_bytes=FIXTURE_LAKE_HASH,
        )

    @contextmanager
    def _fixture_sidecar_policy(
        self, contract: source.GeneratedSidecarContract | None = None
    ):
        selected = contract or self._fixture_sidecar_contract()
        with mock.patch.object(source, "GENERATED_SIDECAR_CONTRACTS", (selected,)):
            yield selected

    def _write_sidecar(self, payload: bytes = FIXTURE_LAKE_HASH) -> Path:
        sidecar = self._proofwidgets_root() / FIXTURE_WIDGET_SIDECAR_PATH
        sidecar.write_bytes(payload)
        return sidecar

    def _replace_fixture_archive(
        self,
        name: str,
        *,
        extra: list[tuple[str, bytes, bytes, int, str]] | None = None,
        replace_entries: list[tuple[str, bytes, bytes, int, str]] | None = None,
    ) -> None:
        package = next(package for package in self.packages if package["name"] == name)
        compressed, raw = make_archive(
            package,
            extra=extra,
            replace_entries=replace_entries,
        )
        package["archive"]["tar_bytes"] = len(raw)
        facts, entries = source.inspect_archive_bytes(compressed, package)
        with tempfile.TemporaryDirectory() as tree_temporary:
            tree_root = Path(tree_temporary)
            extracted = tree_root / "source"
            source._write_entries(extracted, entries)
            archive_tree_sha = source.compute_tree_sha(
                extracted, tree_root / "archive-scratch", []
            )
            tree_sha = source.compute_tree_sha(
                extracted,
                tree_root / "tree-scratch",
                package["output"]["gitlinks"],
            )
        facts["output"]["archive_tree_sha"] = archive_tree_sha
        facts["output"]["tree_sha"] = tree_sha
        package["archive"] = facts["archive"]
        package["output"] = facts["output"]
        self.archive_bytes[name] = compressed
        (self.archives / f"{name}-{package['revision']}.tar.gz").write_bytes(compressed)
        self._write_json(self.pin_path, self.pin)

    def test_replaced_lock_path_cannot_admit_concurrent_materializer(self) -> None:
        runtime = self.root / source.RUNTIME_DIRECTORY
        runtime.mkdir(parents=True)
        lock = runtime / "lock"
        first_entered = threading.Event()
        release = threading.Event()
        second_entered = threading.Event()

        def hold_lock() -> None:
            with source._locked(lock):
                first_entered.set()
                release.wait(3)

        def contend() -> None:
            with source._locked(lock):
                second_entered.set()

        first = threading.Thread(target=hold_lock)
        first.start()
        self.assertTrue(first_entered.wait(2))
        lock.rename(runtime / "old-lock")
        lock.write_text("", encoding="ascii")
        second = threading.Thread(target=contend)
        second.start()
        self.assertFalse(second_entered.wait(0.2))
        release.set()
        first.join(2)
        second.join(2)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertTrue(second_entered.is_set())

    def _seed_prior_publication(self) -> Path:
        (self.root / ".lake/packages").mkdir(parents=True)
        for package in self.packages:
            destination = self.root / ".lake/packages" / package["name"]
            destination.mkdir()
            (destination / "old").write_text(package["name"])
        override = self.root / ".lake/package-overrides.json"
        override.write_text('{"old":true}\n')
        return override

    def _assert_prior_publication_restored(self, override: Path) -> None:
        for package in self.packages:
            destination = self.root / ".lake/packages" / package["name"]
            self.assertEqual(["old"], sorted(path.name for path in destination.iterdir()))
            self.assertEqual(package["name"], (destination / "old").read_text())
        self.assertEqual('{"old":true}\n', override.read_text())

    def _exercise_selected_transaction_replacement(self, component: str) -> None:
        override = self._seed_prior_publication()
        replaced = False
        replacement: Path | None = None

        def swapping_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal replaced, replacement
            old_path, new_path = Path(old), Path(new)
            if not replaced and new_path.name == "plausible":
                runtime = self.root / source.RUNTIME_DIRECTORY
                transaction = runtime / source.TRANSACTION_NAME
                backup_move = Path(os.readlink(new_path.parent)).name == "backup"
                stage_move = is_transaction_stage(old_path)
                selected: Path | None = None
                if component == "transaction" and backup_move:
                    selected = transaction
                elif component == "backup" and backup_move:
                    selected = transaction / "backup"
                elif component == "stage" and stage_move:
                    selected = transaction / "new"
                if selected is not None:
                    replacement = selected
                    selected.rename(selected.with_name(selected.name + "-selected"))
                    selected.mkdir()
                    (selected / "replacement-sentinel").write_text("untouched\n")
                    replaced = True
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "rolled back"):
            self._materialize(replace_existing=True, _replace=swapping_replace)
        self.assertTrue(replaced)
        assert replacement is not None
        self.assertEqual(
            ["replacement-sentinel"], sorted(path.name for path in replacement.iterdir())
        )
        self.assertEqual("untouched\n", (replacement / "replacement-sentinel").read_text())
        self._assert_prior_publication_restored(override)

    def test_publish_verify_override_and_file_modes(self) -> None:
        self.assertFalse((self.root / ".lake").exists())
        result = self._materialize()
        self.assertEqual("published", result["status"])
        self.assertEqual([p["name"] for p in self.packages], result["packages"])
        override = json.loads((self.root / ".lake/package-overrides.json").read_text())
        self.assertEqual(source.override_document(self.pin), override)
        self.assertEqual(8, len(override["packages"]))
        for package in self.packages:
            package_root = self.root / ".lake/packages" / package["name"]
            self.assertTrue((package_root / "tool").stat().st_mode & 0o111)
            self.assertTrue((package_root / "src/source-link").is_symlink())
            self.assertEqual("source.txt", os.readlink(package_root / "src/source-link"))
        self.assertEqual("verified", source.verify(self.root, self.pin_path)["status"])
        (self.root / ".lake/packages/plausible/src/source.txt").write_text("tampered\n")
        with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
            source.verify(self.root, self.pin_path)

    def test_proofwidgets_sidecar_absent_or_exact_is_safely_removed(self) -> None:
        with self._fixture_sidecar_policy():
            self._materialize()
            target = self._proofwidgets_root() / FIXTURE_WIDGET_TARGET_PATH
            before = target.stat()
            absent_fsync_targets: list[str] = []
            real_fsync = os.fsync

            def record_absent_fsync(descriptor: int) -> None:
                absent_fsync_targets.append(os.readlink(f"/proc/self/fd/{descriptor}"))
                real_fsync(descriptor)

            with mock.patch.object(os, "fsync", side_effect=record_absent_fsync):
                absent = source.verify(
                    self.root,
                    self.pin_path,
                    remove_validated_generated_sidecars=True,
                )
            self.assertEqual([], absent["removed_generated_sidecars"])
            self.assertTrue(absent["remove_validated_generated_sidecars"])
            self.assertEqual(before, target.stat())
            self.assertFalse(
                any(path.endswith("/proofwidgets/widget") for path in absent_fsync_targets)
            )

            build_output = self._proofwidgets_root() / ".lake/build/ProofWidgets.olean"
            build_output.parent.mkdir(parents=True)
            build_output.write_bytes(b"compiled")
            sidecar = self._write_sidecar()
            with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                source.verify(self.root, self.pin_path)
            self.assertEqual(FIXTURE_LAKE_HASH, sidecar.read_bytes())

            fsync_targets: list[str] = []

            def recording_fsync(descriptor: int) -> None:
                fsync_targets.append(os.readlink(f"/proc/self/fd/{descriptor}"))
                real_fsync(descriptor)

            with mock.patch.object(os, "fsync", side_effect=recording_fsync):
                exact = source.verify(
                    self.root,
                    self.pin_path,
                    remove_validated_generated_sidecars=True,
                )
            self.assertEqual(
                ["proofwidgets/widget/package-lock.json.hash"],
                exact["removed_generated_sidecars"],
            )
            self.assertFalse(sidecar.exists())
            self.assertEqual(b"compiled", build_output.read_bytes())
            after = target.stat()
            self.assertEqual((before.st_dev, before.st_ino, before.st_mode),
                             (after.st_dev, after.st_ino, after.st_mode))
            self.assertTrue(
                any(path.endswith("/proofwidgets/widget") for path in fsync_targets)
            )

        parser = source.build_parser()
        parsed = parser.parse_args(["verify", "--remove-validated-generated-sidecars"])
        self.assertTrue(parsed.remove_validated_generated_sidecars)
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["verify", "--remove-validated-generated-sidecars=widget/other.hash"]
            )
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["verify", "--remove-validated-generated-sidecars", "proofwidgets"]
            )

    def test_proofwidgets_sidecar_rejects_malformed_payloads(self) -> None:
        malformed = (
            b"0000000000000000",
            b"179E66574F04806E",
            b"179e66574f04806",
            b"179e66574f04806e0",
            b"179e66574f04806e\n",
            b"179e66574f04806g",
        )
        with self._fixture_sidecar_policy():
            self._materialize()
            target = self._proofwidgets_root() / FIXTURE_WIDGET_TARGET_PATH
            target_bytes = target.read_bytes()
            for payload in malformed:
                with self.subTest(payload=payload):
                    sidecar = self._write_sidecar(payload)
                    with self.assertRaises(source.MaterializationError):
                        source.verify(
                            self.root,
                            self.pin_path,
                            remove_validated_generated_sidecars=True,
                        )
                    self.assertEqual(payload, sidecar.read_bytes())
                    self.assertEqual(target_bytes, target.read_bytes())
                    sidecar.unlink()

    def test_proofwidgets_sidecar_rejects_unsafe_types_links_and_modes(self) -> None:
        with self._fixture_sidecar_policy():
            self._materialize()
            sidecar = self._proofwidgets_root() / FIXTURE_WIDGET_SIDECAR_PATH
            outside = Path(self.temporary.name) / "sidecar-outside"
            outside.write_bytes(FIXTURE_LAKE_HASH)

            def verify_fails() -> None:
                with self.assertRaises(source.MaterializationError):
                    source.verify(
                        self.root,
                        self.pin_path,
                        remove_validated_generated_sidecars=True,
                    )

            sidecar.symlink_to(outside)
            verify_fails()
            self.assertEqual(FIXTURE_LAKE_HASH, outside.read_bytes())
            sidecar.unlink()

            sidecar.mkdir()
            verify_fails()
            sidecar.rmdir()

            os.mkfifo(sidecar)
            verify_fails()
            sidecar.unlink()

            listener = socket.socket(socket.AF_UNIX)
            listener.bind(str(sidecar))
            try:
                verify_fails()
            finally:
                listener.close()
                sidecar.unlink()

            peer = Path(self.temporary.name) / "sidecar-peer"
            peer.write_bytes(FIXTURE_LAKE_HASH)
            os.link(peer, sidecar)
            verify_fails()
            self.assertEqual(FIXTURE_LAKE_HASH, peer.read_bytes())
            sidecar.unlink()
            peer.unlink()

            for mode in (0o755, 0o4644, 0o2644, 0o1644):
                with self.subTest(mode=oct(mode)):
                    sidecar.write_bytes(FIXTURE_LAKE_HASH)
                    sidecar.chmod(mode)
                    verify_fails()
                    self.assertTrue(sidecar.exists())
                    sidecar.unlink()

            for kind in (stat.S_IFCHR, stat.S_IFBLK):
                metadata = mock.Mock(
                    st_mode=kind | 0o600,
                    st_nlink=1,
                    st_size=len(FIXTURE_LAKE_HASH),
                )
                with self.subTest(kind=kind), self.assertRaisesRegex(
                    source.MaterializationError, "unsafe metadata"
                ):
                    source._validate_generated_sidecar_metadata(
                        metadata, len(FIXTURE_LAKE_HASH)
                    )

    def test_proofwidgets_sidecar_rejects_target_path_and_substitution_races(self) -> None:
        with self._fixture_sidecar_policy() as contract:
            self._materialize()

            for target_kind in ("symlink", "directory", "fifo", "socket", "hardlink", "bytes"):
                with self.subTest(target_kind=target_kind):
                    self._materialize(replace_existing=True)
                    target = self._proofwidgets_root() / FIXTURE_WIDGET_TARGET_PATH
                    target.unlink()
                    listener = None
                    peer = None
                    if target_kind == "symlink":
                        outside = Path(self.temporary.name) / "target-outside"
                        outside.write_bytes(FIXTURE_WIDGET_TARGET)
                        target.symlink_to(outside)
                    elif target_kind == "directory":
                        target.mkdir()
                    elif target_kind == "fifo":
                        os.mkfifo(target)
                    elif target_kind == "socket":
                        listener = socket.socket(socket.AF_UNIX)
                        listener.bind(str(target))
                    elif target_kind == "hardlink":
                        peer = Path(self.temporary.name) / "target-peer"
                        peer.write_bytes(FIXTURE_WIDGET_TARGET)
                        os.link(peer, target)
                    else:
                        target.write_bytes(b"wrong target\n")
                    sidecar = self._write_sidecar()
                    try:
                        with self.assertRaises(source.MaterializationError):
                            source.verify(
                                self.root,
                                self.pin_path,
                                remove_validated_generated_sidecars=True,
                            )
                        self.assertTrue(sidecar.exists())
                        if peer is not None:
                            self.assertEqual(FIXTURE_WIDGET_TARGET, peer.read_bytes())
                    finally:
                        if listener is not None:
                            listener.close()
                        if peer is not None:
                            peer.unlink()

            self._materialize(replace_existing=True)
            package_root = self._proofwidgets_root()
            widget = package_root / "widget"
            widget.rename(package_root / "widget-bound")
            outside_widget = Path(self.temporary.name) / "outside-widget"
            outside_widget.mkdir()
            (outside_widget / "package-lock.json").write_bytes(FIXTURE_WIDGET_TARGET)
            (outside_widget / "package-lock.json.hash").write_bytes(FIXTURE_LAKE_HASH)
            sentinel = outside_widget / "sentinel"
            sentinel.write_text("untouched\n")
            widget.symlink_to(outside_widget, target_is_directory=True)
            with self.assertRaises(source.MaterializationError):
                source.verify(
                    self.root,
                    self.pin_path,
                    remove_validated_generated_sidecars=True,
                )
            self.assertEqual("untouched\n", sentinel.read_text())
            self.assertEqual(FIXTURE_LAKE_HASH, (outside_widget / "package-lock.json.hash").read_bytes())

            race_cases = (
                "target_name",
                "sidecar_after_read",
                "sidecar_mode",
                "sidecar_name",
                "widget_parent",
                "package_root",
                "sidecar_reappears",
            )
            for race in race_cases:
                with self.subTest(race=race):
                    self._materialize(replace_existing=True)
                    package_root = self._proofwidgets_root()
                    widget = package_root / "widget"
                    target = package_root / FIXTURE_WIDGET_TARGET_PATH
                    sidecar = self._write_sidecar()
                    fired = False

                    def inject(phase: str) -> None:
                        nonlocal fired
                        selected_phase = {
                            "target_name": "after_target_authenticated",
                            "sidecar_after_read": "after_sidecar_authenticated",
                            "sidecar_mode": "after_sidecar_authenticated",
                            "sidecar_name": "before_unlink",
                            "widget_parent": "before_unlink",
                            "package_root": "after_unlink",
                            "sidecar_reappears": "after_unlink",
                        }[race]
                        if fired or phase != selected_phase:
                            return
                        fired = True
                        if race == "target_name":
                            target.rename(widget / "target-bound")
                            target.write_bytes(FIXTURE_WIDGET_TARGET)
                        elif race == "sidecar_after_read":
                            sidecar.rename(widget / "sidecar-after-read-bound")
                            sidecar.write_bytes(FIXTURE_LAKE_HASH)
                        elif race == "sidecar_mode":
                            sidecar.chmod(0o755)
                        elif race == "sidecar_name":
                            sidecar.rename(widget / "sidecar-bound")
                            sidecar.write_bytes(FIXTURE_LAKE_HASH)
                        elif race == "widget_parent":
                            widget.rename(package_root / "widget-bound")
                            widget.mkdir()
                            (widget / "sentinel").write_text("untouched\n")
                        elif race == "package_root":
                            package_root.rename(package_root.with_name("proofwidgets-bound"))
                            package_root.mkdir()
                            (package_root / "sentinel").write_text("untouched\n")
                        else:
                            sidecar.write_bytes(FIXTURE_LAKE_HASH)

                    with mock.patch.object(source, "_generated_sidecar_phase", side_effect=inject):
                        with self.assertRaises(source.MaterializationError):
                            source.verify(
                                self.root,
                                self.pin_path,
                                remove_validated_generated_sidecars=True,
                            )
                    self.assertTrue(fired)
                    if race in {"widget_parent", "package_root"}:
                        self.assertEqual(
                            "untouched\n",
                            (widget / "sentinel" if race == "widget_parent" else package_root / "sentinel").read_text(),
                        )

            self._materialize(replace_existing=True)
            self._write_sidecar()
            unsafe = source.GeneratedSidecarContract(
                package=contract.package,
                revision=contract.revision,
                target="../package-lock.json",
                target_sha256=contract.target_sha256,
                sidecar="../package-lock.json.hash",
                sidecar_bytes=contract.sidecar_bytes,
            )
            with mock.patch.object(source, "GENERATED_SIDECAR_CONTRACTS", (unsafe,)):
                with self.assertRaisesRegex(source.MaterializationError, "paths are unsafe"):
                    source.verify(
                        self.root,
                        self.pin_path,
                        remove_validated_generated_sidecars=True,
                    )

            unsafe_paths = (
                ("widget//package-lock.json", "widget//package-lock.json.hash"),
                ("widget/./package-lock.json", "widget/./package-lock.json.hash"),
                ("widget/package\0-lock.json", "widget/package\0-lock.json.hash"),
                ("widget\\package-lock.json", "widget\\package-lock.json.hash"),
                ("widget/package-lock.json", "widget/other.hash"),
            )
            for unsafe_target, unsafe_sidecar in unsafe_paths:
                with self.subTest(
                    unsafe_target=unsafe_target, unsafe_sidecar=unsafe_sidecar
                ):
                    candidate = contract._replace(
                        target=unsafe_target, sidecar=unsafe_sidecar
                    )
                    with mock.patch.object(
                        source, "GENERATED_SIDECAR_CONTRACTS", (candidate,)
                    ), self.assertRaises(source.MaterializationError):
                        source._generated_sidecar_contract_for(
                            self._proofwidgets_package()
                        )

            wrong_revision = contract._replace(revision="0" * 40)
            with mock.patch.object(source, "GENERATED_SIDECAR_CONTRACTS", (wrong_revision,)):
                with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                    source.verify(
                        self.root,
                        self.pin_path,
                        remove_validated_generated_sidecars=True,
                    )
            self.assertTrue(self._proofwidgets_root().joinpath(FIXTURE_WIDGET_SIDECAR_PATH).exists())

            self._materialize(replace_existing=True)
            plausible = self.root / ".lake/packages/plausible/widget"
            plausible.mkdir()
            (plausible / "package-lock.json").write_bytes(FIXTURE_WIDGET_TARGET)
            other_sidecar = plausible / "package-lock.json.hash"
            other_sidecar.write_bytes(FIXTURE_LAKE_HASH)
            with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                source.verify(
                    self.root,
                    self.pin_path,
                    remove_validated_generated_sidecars=True,
                )
            self.assertTrue(other_sidecar.exists())

    def test_proofwidgets_sidecar_cleanup_does_not_mask_tree_drift(self) -> None:
        mutations = (
            (FIXTURE_WIDGET_TARGET_PATH, b"wrong target\n", True),
            (FIXTURE_WIDGET_TRACE_PATH, b"{}\n", False),
            ("widget/package.json", b'{"changed":true}\n', False),
            ("lakefile.lean", b'name = "changed"\n', False),
            ("lake-manifest.json", b'{"changed":true}\n', False),
            ("src/source.txt", b"changed\n", False),
        )
        with self._fixture_sidecar_policy():
            for relative, payload, sidecar_remains in mutations:
                with self.subTest(relative=relative):
                    self._materialize(replace_existing=True)
                    changed = self._proofwidgets_root() / relative
                    changed.write_bytes(payload)
                    sidecar = self._write_sidecar()
                    with self.assertRaises(source.MaterializationError):
                        source.verify(
                            self.root,
                            self.pin_path,
                            remove_validated_generated_sidecars=True,
                        )
                    self.assertEqual(sidecar_remains, sidecar.exists())

            self._materialize(replace_existing=True)
            target = self._proofwidgets_root() / FIXTURE_WIDGET_TARGET_PATH
            target.chmod(0o755)
            sidecar = self._write_sidecar()
            with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                source.verify(
                    self.root,
                    self.pin_path,
                    remove_validated_generated_sidecars=True,
                )
            self.assertFalse(sidecar.exists())

            for relative in (
                "widget/other.hash",
                "widget/package-lock.json.hash.extra",
                "widget/nested/package-lock.json.hash",
            ):
                with self.subTest(relative=relative):
                    self._materialize(replace_existing=True)
                    lookalike = self._proofwidgets_root() / relative
                    lookalike.parent.mkdir(parents=True, exist_ok=True)
                    lookalike.write_bytes(FIXTURE_LAKE_HASH)
                    self._write_sidecar()
                    with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                        source.verify(
                            self.root,
                            self.pin_path,
                            remove_validated_generated_sidecars=True,
                        )
                    self.assertTrue(lookalike.exists())

    def test_proofwidgets_sidecar_archive_provenance_is_exact(self) -> None:
        proofwidgets = self._proofwidgets_package()
        prefix = proofwidgets["archive"]["exact_prefix"]
        contract = self._fixture_sidecar_contract()
        with self._fixture_sidecar_policy(contract):
            self._replace_fixture_archive(
                "proofwidgets",
                extra=[
                    (prefix + "docs/", b"5", b"", 0o775, ""),
                    (prefix + "docs/reference.hash", b"0", b"archive-owned\n", 0o664, ""),
                ],
            )
            self._materialize()
            archive_hash = self._proofwidgets_root() / "docs/reference.hash"
            self.assertEqual(b"archive-owned\n", archive_hash.read_bytes())
            source.verify(
                self.root,
                self.pin_path,
                remove_validated_generated_sidecars=True,
            )
            archive_hash.write_bytes(b"changed\n")
            with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                source.verify(self.root, self.pin_path)
            self._materialize(replace_existing=True)
            archive_hash = self._proofwidgets_root() / "docs/reference.hash"
            archive_hash.unlink()
            with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                source.verify(self.root, self.pin_path)

            def archive_entries(
                target_kind: bytes, target_payload: bytes, target_mode: int, target_link: str
            ) -> list[tuple[str, bytes, bytes, int, str]]:
                return [
                    (prefix, b"5", b"", 0o775, ""),
                    (prefix + "lakefile.lean", b"0", b'name = "proofwidgets"\n', 0o664, ""),
                    (prefix + "lake-manifest.json", b"0", b"{}\n", 0o664, ""),
                    (prefix + "src/", b"5", b"", 0o775, ""),
                    (prefix + "src/source.txt", b"0", b"proofwidgets\n", 0o664, ""),
                    (prefix + "tool", b"0", b"#!/bin/sh\nexit 0\n", 0o775, ""),
                    (prefix + "src/source-link", b"2", b"", 0o777, "source.txt"),
                    (prefix + "widget/", b"5", b"", 0o775, ""),
                    (
                        prefix + FIXTURE_WIDGET_TARGET_PATH,
                        target_kind,
                        target_payload,
                        target_mode,
                        target_link,
                    ),
                    (prefix + FIXTURE_WIDGET_TRACE_PATH, b"0", FIXTURE_WIDGET_TRACE, 0o664, ""),
                    (prefix + "widget/package.json", b"0", b"{}\n", 0o664, ""),
                ]

            for label, entries in (
                (
                    "wrong-digest",
                    archive_entries(b"0", b"wrong target\n", 0o664, ""),
                ),
                (
                    "wrong-type",
                    archive_entries(b"2", b"", 0o777, "package.json"),
                ),
            ):
                with self.subTest(archive_target=label):
                    malformed, malformed_raw = make_archive(
                        proofwidgets, replace_entries=entries
                    )
                    malformed_package = copy.deepcopy(proofwidgets)
                    malformed_package["archive"]["tar_bytes"] = len(malformed_raw)
                    with self.assertRaisesRegex(
                        source.MaterializationError, "target differs"
                    ):
                        source.inspect_archive_bytes(malformed, malformed_package)

            compressed, raw = make_archive(
                proofwidgets,
                extra=[
                    (
                        prefix + FIXTURE_WIDGET_SIDECAR_PATH,
                        b"0",
                        FIXTURE_LAKE_HASH,
                        0o664,
                        "",
                    )
                ],
            )
            candidate = copy.deepcopy(proofwidgets)
            candidate["archive"]["tar_bytes"] = len(raw)
            with self.assertRaisesRegex(source.MaterializationError, "archive-owned"):
                source.inspect_archive_bytes(compressed, candidate)

            for payload in (b"179E66574F04806E", b"179e66574f04806"):
                malformed_contract = contract._replace(sidecar_bytes=payload)
                with self.subTest(contract_payload=payload), mock.patch.object(
                    source,
                    "GENERATED_SIDECAR_CONTRACTS",
                    (malformed_contract,),
                ), self.assertRaisesRegex(
                    source.MaterializationError, "not canonical"
                ):
                    source._generated_sidecar_contract_for(proofwidgets)

        production = source.GENERATED_SIDECAR_CONTRACTS
        self.assertEqual(1, len(production))
        self.assertEqual(
            (
                "proofwidgets",
                "6e311e2a844da9b2cc3971187df2fe0066947b93",
                "widget/package-lock.json",
                "3850e21b0823d6200db6da336ce1bd17a463db97ce314585ae47ed81a7327a7d",
                "widget/package-lock.json.hash",
                b"179e66574f04806e",
            ),
            (
                production[0].package,
                production[0].revision,
                production[0].target,
                production[0].target_sha256,
                production[0].sidecar,
                production[0].sidecar_bytes,
            ),
        )
        real_pin = source.load_pin(ROOT / "references/lake-packages.json")
        real_proofwidgets = next(
            package for package in real_pin["packages"] if package["name"] == "proofwidgets"
        )
        self.assertEqual(production[0].revision, real_proofwidgets["revision"])
        self.assertEqual(3_896_457, real_proofwidgets["archive"]["bytes"])
        self.assertEqual(
            "dffb4652003f31f8e393e0f2887526ec4b6cc8244b960afa8dcbc1918b020c68",
            real_proofwidgets["archive"]["sha256"],
        )
        self.assertEqual(
            "bec90bac5dd8afade168e76c5b508482f9043b26",
            real_proofwidgets["output"]["archive_tree_sha"],
        )

    def test_verify_projects_only_validated_generated_build_output(self) -> None:
        self._materialize()
        package_root = self.root / ".lake/packages/plausible"
        build = package_root / ".lake/build"
        lean_output = build / "lib/lean/Plausible.olean"
        ir_output = build / "ir/Plausible.c"
        lean_output.parent.mkdir(parents=True)
        ir_output.parent.mkdir(parents=True)
        lean_output.write_bytes(b"olean")
        ir_output.write_bytes(b"generated C")
        lean_output.chmod(0o600)
        self.assertEqual("verified", source.verify(self.root, self.pin_path)["status"])

        source_file = package_root / "src/source.txt"
        source_file.write_text("tampered\n")
        with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
            source.verify(self.root, self.pin_path)
        source_file.write_text("plausible\n")

        config = package_root / "lakefile.toml"
        config.write_text("name = \"tampered\"\n")
        with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
            source.verify(self.root, self.pin_path)
        config.write_text("name = \"plausible\"\n")

        manifest = package_root / "lake-manifest.json"
        manifest.write_text('{"tampered": true}\n')
        with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
            source.verify(self.root, self.pin_path)
        manifest.write_text("{}\n")

        exact_scope_drifts = (
            (package_root / ".lake/not-build/metadata", package_root / ".lake/not-build"),
            (package_root / ".lake/build-sibling/output", package_root / ".lake/build-sibling"),
            (package_root / "src/.lake/build/output", package_root / "src/.lake"),
        )
        for drift, cleanup in exact_scope_drifts:
            with self.subTest(drift=drift.relative_to(package_root)):
                drift.parent.mkdir(parents=True)
                drift.write_text("drift\n")
                with self.assertRaisesRegex(source.MaterializationError, "tree differs"):
                    source.verify(self.root, self.pin_path)
                shutil.rmtree(cleanup)
        self.assertEqual("verified", source.verify(self.root, self.pin_path)["status"])

    def test_verify_rejects_malformed_generated_build_boundaries(self) -> None:
        self._materialize()
        package_root = self.root / ".lake/packages/plausible"
        lake = package_root / ".lake"
        lake.mkdir()
        build = lake / "build"
        outside = Path(self.temporary.name) / "generated-outside"
        outside.mkdir()

        build.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(source.MaterializationError, "not a real directory"):
            source.verify(self.root, self.pin_path)
        build.unlink()

        build.write_text("not a directory\n")
        with self.assertRaisesRegex(source.MaterializationError, "not a real directory"):
            source.verify(self.root, self.pin_path)
        build.unlink()

        os.mkfifo(build)
        with self.assertRaisesRegex(source.MaterializationError, "special file|not a real directory"):
            source.verify(self.root, self.pin_path)
        build.unlink()

        build.mkdir()
        (build / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(source.MaterializationError, "contains a symlink"):
            source.verify(self.root, self.pin_path)
        (build / "link").unlink()

        os.mkfifo(build / "fifo")
        with self.assertRaisesRegex(source.MaterializationError, "special file"):
            source.verify(self.root, self.pin_path)
        (build / "fifo").unlink()

        first = build / "first"
        first.write_text("generated\n")
        os.link(first, build / "second")
        with self.assertRaisesRegex(source.MaterializationError, "multiply-linked"):
            source.verify(self.root, self.pin_path)
        shutil.rmtree(lake)

        lake.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(source.MaterializationError, "not a real directory"):
            source.verify(self.root, self.pin_path)
        lake.unlink()

        lake.write_text("not a directory\n")
        with self.assertRaisesRegex(source.MaterializationError, "not a real directory"):
            source.verify(self.root, self.pin_path)

    def test_archive_generated_build_output_is_rejected(self) -> None:
        package = copy.deepcopy(self.packages[0])
        prefix = package["archive"]["exact_prefix"]
        compressed, raw = make_archive(
            package,
            extra=[
                (prefix + ".lake/", b"5", b"", 0o775, ""),
                (prefix + ".lake/build/", b"5", b"", 0o775, ""),
                (prefix + ".lake/build/output", b"0", b"generated", 0o664, ""),
            ],
        )
        package["archive"]["tar_bytes"] = len(raw)
        with self.assertRaisesRegex(source.MaterializationError, "generated .lake/build"):
            source.inspect_archive_bytes(compressed, package)

    def test_manifest_semantic_tampering_fails_after_checksum_is_rebound(self) -> None:
        document = copy.deepcopy(self.root_manifest)
        document["packages"][1]["rev"] = "0" * 40
        self._write_json(self.root_manifest_path, document)
        pin = copy.deepcopy(self.pin)
        pin["root_manifest_sha256"] = source._file_sha256(self.root_manifest_path)
        self._write_json(self.pin_path, pin)
        with self.assertRaisesRegex(source.MaterializationError, "entry differs"):
            source.materialize(self.root, self.pin_path, self.archives)

    def test_package_names_are_closed_safe_path_components(self) -> None:
        for unsafe_name in (
            "../escape", "/absolute", "nested/name", ".hidden", "name with space",
            "name\\component", "package$", "e" + chr(233),
        ):
            with self.subTest(name=unsafe_name):
                pin = copy.deepcopy(self.pin)
                pin["packages"][0]["name"] = unsafe_name
                self._write_json(self.pin_path, pin)
                with self.assertRaisesRegex(source.MaterializationError, "safe ASCII path component"):
                    source.load_pin(self.pin_path)
        self._write_json(self.pin_path, self.pin)

    def test_symlinked_lake_intermediates_fail_before_external_writes(self) -> None:
        cases = ("lake", "packages", "runtime", "override", "lock", "transaction")
        for case in cases:
            with self.subTest(case=case):
                lake = self.root / ".lake"
                if lake.is_symlink():
                    lake.unlink()
                elif lake.exists():
                    shutil.rmtree(lake)
                outside = Path(self.temporary.name) / f"outside-{case}"
                outside.mkdir()
                sentinel = outside / "sentinel"
                sentinel.write_text("unchanged\n")
                if case == "lake":
                    lake.symlink_to(outside, target_is_directory=True)
                else:
                    lake.mkdir()
                    if case == "packages":
                        (lake / "packages").symlink_to(outside, target_is_directory=True)
                    elif case == "runtime":
                        (lake / "lake-package-materialization").symlink_to(
                            outside, target_is_directory=True
                        )
                    elif case == "override":
                        (lake / "package-overrides.json").symlink_to(sentinel)
                    else:
                        (lake / "packages").mkdir()
                        runtime = lake / "lake-package-materialization"
                        runtime.mkdir()
                        target = sentinel if case == "lock" else outside
                        (runtime / case).symlink_to(
                            target, target_is_directory=case == "transaction"
                        )
                with self.assertRaises(source.MaterializationError):
                    self._materialize()
                self.assertEqual("unchanged\n", sentinel.read_text())
                self.assertEqual(["sentinel"], sorted(path.name for path in outside.iterdir()))

    def test_package_root_incarnation_swap_is_detected_and_confined(self) -> None:
        swapped = False

        def swapping_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal swapped
            old_path, new_path = Path(old), Path(new)
            if not swapped and new_path.name == "plausible" and is_transaction_stage(old_path):
                swapped = True
                packages = self.root / ".lake/packages"
                packages.rename(self.root / ".lake/packages-bound")
                packages.mkdir()
                (packages / "replacement-sentinel").write_text("untouched\n")
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "incarnation changed"):
            self._materialize(_replace=swapping_replace)
        replacement = self.root / ".lake/packages"
        self.assertEqual(
            ["replacement-sentinel"], sorted(path.name for path in replacement.iterdir())
        )
        self.assertEqual("untouched\n", (replacement / "replacement-sentinel").read_text())
        self.assertFalse((self.root / ".lake/packages-bound/plausible").exists())

    def test_lake_root_incarnation_swap_is_detected_and_confined(self) -> None:
        swapped = False

        def swapping_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal swapped
            old_path, new_path = Path(old), Path(new)
            if not swapped and new_path.name == "plausible" and is_transaction_stage(old_path):
                swapped = True
                lake = self.root / ".lake"
                lake.rename(self.root / ".lake-bound")
                lake.mkdir()
                (lake / "replacement-sentinel").write_text("untouched\n")
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "incarnation changed"):
            self._materialize(_replace=swapping_replace)
        replacement = self.root / ".lake"
        self.assertEqual(
            ["replacement-sentinel"], sorted(path.name for path in replacement.iterdir())
        )
        self.assertEqual("untouched\n", (replacement / "replacement-sentinel").read_text())
        self.assertFalse((self.root / ".lake-bound/packages/plausible").exists())

    def test_archive_checksum_and_git_tree_mismatches_fail(self) -> None:
        archive = self.archives / f"plausible-{self.packages[0]['revision']}.tar.gz"
        payload = bytearray(archive.read_bytes())
        payload[-1] ^= 1
        archive.write_bytes(payload)
        with self.assertRaises(source.MaterializationError):
            self._materialize()
        archive.write_bytes(self.archive_bytes["plausible"])
        pin = copy.deepcopy(self.pin)
        pin["packages"][0]["output"]["tree_sha"] = "0" * 40
        self._write_json(self.pin_path, pin)
        with self.assertRaisesRegex(source.MaterializationError, "Git tree differs"):
            self._materialize()

    def test_canonical_codeload_modes_normalize_to_exact_git_tree(self) -> None:
        package = copy.deepcopy(self.packages[0])
        compressed, raw = make_archive(package, directory_mode=0o775)
        package["archive"]["tar_bytes"] = len(raw)
        _, entries = source.inspect_archive_bytes(compressed, package)
        file_modes = {
            entry["path"]: entry["mode"] for entry in entries if entry["kind"] == "file"
        }
        self.assertEqual(0o644, file_modes[package["config_file"]])
        self.assertEqual(0o755, file_modes["tool"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            extracted = root / "source"
            source._write_entries(extracted, entries)
            self.assertEqual(
                package["output"]["tree_sha"],
                source.compute_tree_sha(extracted, root / "scratch", []),
            )

    def test_exact_gitlink_placeholder_reconstructs_tree_and_rejects_omissions(self) -> None:
        package = copy.deepcopy(self.packages[0])
        prefix = package["archive"]["exact_prefix"]
        gitlink = {
            "path": "vendor/std",
            "mode": "160000",
            "type": "commit",
            "sha": "a" * 40,
        }
        package["output"]["gitlinks"] = [gitlink]
        compressed, raw = make_archive(
            package,
            extra=[(prefix + "vendor/", b"5", b"", 0o775, ""),
                   (prefix + "vendor/std/", b"5", b"", 0o775, "")],
        )
        package["archive"]["tar_bytes"] = len(raw)
        _, entries = source.inspect_archive_bytes(compressed, package)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            extracted = root / "source"
            source._write_entries(extracted, entries)
            first = source.compute_tree_sha(extracted, root / "first", [gitlink])
            generated = extracted / ".lake/build/output"
            generated.parent.mkdir(parents=True)
            generated.write_text("generated\n")
            self.assertEqual(
                first,
                source.compute_source_tree_sha(extracted, root / "projected", [gitlink]),
            )
            changed = dict(gitlink, sha="b" * 40)
            second = source.compute_source_tree_sha(extracted, root / "second", [changed])
            self.assertNotEqual(first, second)

        live_package = self.packages[0]
        live_package["output"]["gitlinks"] = [gitlink]
        live_prefix = live_package["archive"]["exact_prefix"]
        self._replace_fixture_archive(
            live_package["name"],
            extra=[
                (live_prefix + "vendor/", b"5", b"", 0o775, ""),
                (live_prefix + "vendor/std/", b"5", b"", 0o775, ""),
            ],
        )
        self._materialize()
        self.assertEqual("verified", source.verify(self.root, self.pin_path)["status"])
        archive_tree = live_package["output"]["archive_tree_sha"]
        gitlink_tree = live_package["output"]["tree_sha"]
        self.assertNotEqual(archive_tree, gitlink_tree)
        live_package["output"]["archive_tree_sha"] = "0" * 40
        self._write_json(self.pin_path, self.pin)
        with self.assertRaisesRegex(source.MaterializationError, "archive tree differs"):
            source.verify(self.root, self.pin_path)
        live_package["output"]["archive_tree_sha"] = archive_tree
        live_package["output"]["tree_sha"] = "0" * 40
        self._write_json(self.pin_path, self.pin)
        with self.assertRaisesRegex(source.MaterializationError, "Git tree differs"):
            source.verify(self.root, self.pin_path)
        live_package["output"]["tree_sha"] = gitlink_tree
        self._write_json(self.pin_path, self.pin)

        unpinned = copy.deepcopy(package)
        unpinned["output"]["gitlinks"] = []
        with self.assertRaisesRegex(source.MaterializationError, "unpinned empty"):
            source.inspect_archive_bytes(compressed, unpinned)

        nonempty, nonempty_raw = make_archive(
            package,
            extra=[(prefix + "vendor/", b"5", b"", 0o775, ""),
                   (prefix + "vendor/std/", b"5", b"", 0o775, ""),
                   (prefix + "vendor/std/file", b"0", b"unexpected", 0o664, "")],
        )
        package["archive"]["tar_bytes"] = len(nonempty_raw)
        with self.assertRaisesRegex(source.MaterializationError, "missing or nonempty"):
            source.inspect_archive_bytes(nonempty, package)

    def test_traversal_duplicate_special_gitlink_and_oversize_are_rejected(self) -> None:
        package = copy.deepcopy(self.packages[0])
        prefix = package["archive"]["exact_prefix"]
        attacks = [
            [(prefix + "../escape", b"0", b"x", 0o644, "")],
            [(prefix + "same", b"0", b"x", 0o644, ""), (prefix + "same", b"0", b"x", 0o644, "")],
            [(prefix + "device", b"3", b"", 0o644, "")],
            [(prefix + ".gitmodules", b"0", b"[submodule]\n", 0o644, "")],
            [(prefix + "hard", b"1", b"", 0o644, "target")],
            [
                (prefix, b"5", b"", 0o755, ""),
                (prefix + "redirect", b"2", b"", 0o777, "src"),
                (prefix + "redirect/child", b"0", b"x", 0o644, ""),
            ],
        ]
        for entries in attacks:
            with self.subTest(entries=entries):
                compressed, raw = make_archive(package, replace_entries=entries)
                candidate = copy.deepcopy(package)
                candidate["archive"]["tar_bytes"] = len(raw)
                with self.assertRaises(source.MaterializationError):
                    source.inspect_archive_bytes(compressed, candidate)
        compressed, raw = make_archive(
            package,
            replace_entries=[(prefix + "large", b"0", b"x" * 33, 0o644, "")],
        )
        candidate = copy.deepcopy(package)
        candidate["archive"]["tar_bytes"] = len(raw)
        with mock.patch.object(source, "HARD_MAX_MEMBER_BYTES", 32), self.assertRaisesRegex(
            source.MaterializationError, "hard size"
        ):
            source.inspect_archive_bytes(compressed, candidate)

    def test_unsafe_symlink_is_rejected_but_safe_symlink_text_is_preserved(self) -> None:
        package = copy.deepcopy(self.packages[0])
        prefix = package["archive"]["exact_prefix"]
        compressed, raw = make_archive(
            package,
            replace_entries=[(prefix + "escape", b"2", b"", 0o777, "../../outside")],
        )
        package["archive"]["tar_bytes"] = len(raw)
        with self.assertRaisesRegex(source.MaterializationError, "escapes"):
            source.inspect_archive_bytes(compressed, package)

    def test_publication_failure_restores_all_existing_packages_and_override(self) -> None:
        override = self._seed_prior_publication()
        failed = False

        def flaky_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal failed
            old_path, new_path = Path(old), Path(new)
            if not failed and new_path.name == "LeanSearchClient" and is_transaction_stage(old_path):
                failed = True
                raise OSError("injected publication failure")
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "rolled back"):
            self._materialize(replace_existing=True, _replace=flaky_replace)
        self._assert_prior_publication_restored(override)

    def test_transaction_instance_replacement_rolls_back_through_selected_descriptors(self) -> None:
        self._exercise_selected_transaction_replacement("transaction")

    def test_backup_instance_replacement_rolls_back_through_selected_descriptors(self) -> None:
        self._exercise_selected_transaction_replacement("backup")

    def test_stage_instance_replacement_rolls_back_through_selected_descriptors(self) -> None:
        self._exercise_selected_transaction_replacement("stage")

    def test_existing_package_substitution_restores_selected_original(self) -> None:
        override = self._seed_prior_publication()
        substituted = False

        def swapping_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal substituted
            old_path, new_path = Path(old), Path(new)
            backup_move = Path(os.readlink(new_path.parent)).name == "backup"
            if not substituted and old_path.name == "plausible" and backup_move:
                selected = self.root / ".lake/packages/plausible-selected"
                old_path.rename(selected)
                old_path.mkdir()
                (old_path / "replacement-sentinel").write_text("untouched\n")
                substituted = True
            if new_path.name == "LeanSearchClient" and is_transaction_stage(old_path):
                raise OSError("injected publication failure")
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "rolled back"):
            self._materialize(replace_existing=True, _replace=swapping_replace)
        self.assertTrue(substituted)
        self._assert_prior_publication_restored(override)
        self.assertFalse((self.root / ".lake/packages/plausible-selected").exists())
        rejected = list(
            (self.root / source.RUNTIME_DIRECTORY).glob("rejected-backup-package-plausible-*")
        )
        self.assertEqual(1, len(rejected))
        self.assertEqual(
            ["replacement-sentinel"], sorted(path.name for path in rejected[0].iterdir())
        )
        self.assertEqual("untouched\n", (rejected[0] / "replacement-sentinel").read_text())

    def test_override_substitution_restores_selected_original(self) -> None:
        override = self._seed_prior_publication()
        substituted = False

        def swapping_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal substituted
            old_path, new_path = Path(old), Path(new)
            if old_path.name == "package-overrides.json" and new_path.name == "override.json":
                selected = self.root / ".lake/package-overrides-selected.json"
                old_path.rename(selected)
                old_path.write_text("replacement\n")
                os.replace(old, new)
                substituted = True
                raise OSError("injected override failure")
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "rolled back"):
            self._materialize(replace_existing=True, _replace=swapping_replace)
        self.assertTrue(substituted)
        self._assert_prior_publication_restored(override)
        self.assertFalse((self.root / ".lake/package-overrides-selected.json").exists())
        rejected = list(
            (self.root / source.RUNTIME_DIRECTORY).glob("rejected-backup-override-*")
        )
        self.assertEqual(1, len(rejected))
        self.assertEqual("replacement\n", rejected[0].read_text())

    def test_staged_package_substitution_never_publishes_replacement(self) -> None:
        substituted = False

        def swapping_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal substituted
            old_path, new_path = Path(old), Path(new)
            if (
                not substituted
                and old_path.name == new_path.name == "plausible"
                and is_transaction_stage(old_path)
            ):
                old_path.rename(old_path.with_name("plausible-selected"))
                old_path.mkdir()
                (old_path / "replacement-sentinel").write_text("untouched\n")
                substituted = True
            os.replace(old, new)

        with self.assertRaisesRegex(source.MaterializationError, "rolled back"):
            self._materialize(_replace=swapping_replace)
        self.assertTrue(substituted)
        self.assertFalse((self.root / ".lake/packages/plausible").exists())
        rejected = list(
            (self.root / source.RUNTIME_DIRECTORY).glob("rejected-package-plausible-*")
        )
        self.assertEqual(1, len(rejected))
        self.assertEqual(
            ["replacement-sentinel"], sorted(path.name for path in rejected[0].iterdir())
        )
        self.assertEqual("untouched\n", (rejected[0] / "replacement-sentinel").read_text())

    def test_interrupted_publication_is_recovered_before_retry(self) -> None:
        (self.root / ".lake/packages").mkdir(parents=True)
        for package in self.packages:
            destination = self.root / ".lake/packages" / package["name"]
            destination.mkdir()
            (destination / "old").write_text(package["name"])
        override = self.root / ".lake/package-overrides.json"
        override.write_text('{"old":true}\n')
        interrupted = False

        def interrupting_replace(old: os.PathLike[str] | str, new: os.PathLike[str] | str) -> None:
            nonlocal interrupted
            old_path, new_path = Path(old), Path(new)
            if not interrupted and new_path.name == "LeanSearchClient" and is_transaction_stage(old_path):
                interrupted = True
                raise KeyboardInterrupt("injected process interruption")
            os.replace(old, new)

        with self.assertRaisesRegex(KeyboardInterrupt, "process interruption"):
            self._materialize(replace_existing=True, _replace=interrupting_replace)
        transaction = self.root / source.RUNTIME_DIRECTORY / source.TRANSACTION_NAME
        self.assertTrue(transaction.is_dir())
        self.assertFalse((self.root / ".lake/packages/plausible/old").exists())

        self.assertEqual("published", self._materialize(replace_existing=True)["status"])
        self.assertFalse(transaction.exists())
        self.assertEqual("verified", source.verify(self.root, self.pin_path)["status"])
        for package in self.packages:
            self.assertFalse((self.root / ".lake/packages" / package["name"] / "old").exists())

    def test_pending_pin_fails_closed_and_production_pin_is_complete(self) -> None:
        pending = copy.deepcopy(self.pin)
        for package in pending["packages"]:
            package["archive"] = {
                key: value if key == "exact_prefix" else None
                for key, value in package["archive"].items()
            }
            package["output"] = {key: None for key in package["output"]}
            package["pending_reason"] = "Facts unavailable in test."
        self._write_json(self.pin_path, pending)
        with self.assertRaisesRegex(source.MaterializationError, "pending"):
            source.load_pin(self.pin_path)
        pending = source.load_pin(self.pin_path, allow_pending=True)
        self.assertEqual(8, len(pending["packages"]))
        production = source.load_pin(ROOT / "references/lake-packages.json")
        self.assertEqual(8, len(production["packages"]))
        source.validate_manifests(ROOT, production)

    def test_transport_is_direct_argv_bounded_and_contains_no_credentials(self) -> None:
        download = Path(self.temporary.name) / "downloads"
        calls: list[list[str]] = []

        def runner(argv: list[str], timeout: float) -> None:
            calls.append(list(argv))
            url = argv[3]
            output = Path(argv[4])
            package = next(package for package in self.packages if package["archive_url"] == url)
            output.write_bytes(self.archive_bytes[package["name"]])
            self.assertEqual(17.0, timeout)

        template = ["transport", "--config", "auth.cfg", "{url}", "{output}", "{max_bytes}", "{timeout_seconds}"]
        outputs = source.fetch_archives(
            self.root, self.pin_path, download, template, timeout_seconds=17, runner=runner
        )
        self.assertEqual(8, len(outputs))
        self.assertEqual(8, len(calls))
        self.assertFalse(
            any(
                "token" in token.lower() or "bearer" in token.lower()
                for call in calls for token in call
            )
        )
        with self.assertRaisesRegex(source.MaterializationError, "credentials"):
            source._safe_transport_argv(
                ["curl", "Authorization: Bearer secret", "{url}", "{output}"],
                self.packages[0], download / "bad", 1,
            )
        process = mock.Mock(returncode=0)
        process.wait.return_value = None
        with mock.patch.object(source.subprocess, "Popen", return_value=process) as popen:
            source._run_bounded_argv(["transport", "arg"], 1, cwd=self.root)
        self.assertIs(popen.call_args.kwargs["shell"], False)
        self.assertEqual(["transport", "arg"], popen.call_args.args[0])
        self.assertEqual((), popen.call_args.kwargs["pass_fds"])

        with source._bound_existing_directory(download, "test archive output") as bound:
            output = bound.path / "descriptor-output"
            source._run_bounded_argv(
                [
                    sys.executable,
                    "-c",
                    "import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(b'bound\\n')",
                    str(output),
                ],
                2,
                cwd=self.root,
                pass_fds=(bound.descriptor,),
            )
            bound.assert_current()
        self.assertEqual(b"bound\n", (download / "descriptor-output").read_bytes())

    def test_transport_timeout_waits_for_descendant_process_group(self) -> None:
        descendant_pid_path = Path(self.temporary.name) / "descendant.pid"
        program = """
import os, pathlib, signal, sys, time
child = os.fork()
if child == 0:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    pathlib.Path(sys.argv[1]).write_text(str(os.getpid()))
    time.sleep(0.6)
    os._exit(0)
while True:
    time.sleep(1)
"""
        started = time.monotonic()
        with self.assertRaisesRegex(source.MaterializationError, "exceeded its timeout"):
            source._run_bounded_argv(
                [sys.executable, "-c", program, str(descendant_pid_path)],
                0.2,
                cwd=self.root,
            )
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 0.5)
        descendant_pid = int(descendant_pid_path.read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(descendant_pid, 0)

    def test_transport_timeout_escalates_a_remaining_process_group(self) -> None:
        process = mock.Mock(pid=4242)
        process.wait.side_effect = source.subprocess.TimeoutExpired(["transport"], 1)
        process.poll.return_value = 0
        group_alive = True
        signals: list[int] = []

        def kill_group(_pid: int, sent_signal: int) -> None:
            nonlocal group_alive
            if sent_signal == 0:
                if not group_alive:
                    raise ProcessLookupError
                return
            signals.append(sent_signal)
            if sent_signal == source.signal.SIGKILL:
                group_alive = False

        with (
            mock.patch.object(source.subprocess, "Popen", return_value=process),
            mock.patch.object(source.os, "killpg", side_effect=kill_group),
            mock.patch.object(source.time, "monotonic", side_effect=[0.0, 3.0, 4.0]),
            self.assertRaisesRegex(source.MaterializationError, "exceeded its timeout"),
        ):
            source._run_bounded_argv(["transport"], 1, cwd=self.root)
        self.assertEqual([source.signal.SIGTERM, source.signal.SIGKILL], signals)

    def test_duplicate_pin_key_and_incomplete_override_are_rejected(self) -> None:
        duplicate = self.pin_path.read_text().replace(
            '"schema_version": 2,', '"schema_version": 2, "schema_version": 2,', 1
        )
        self.pin_path.write_text(duplicate)
        with self.assertRaisesRegex(source.MaterializationError, "duplicate JSON key"):
            source.load_pin(self.pin_path)
        self._write_json(self.pin_path, self.pin)
        self._materialize()
        override = self.root / ".lake/package-overrides.json"
        document = json.loads(override.read_text())
        document["packages"].pop()
        self._write_json(override, document)
        with self.assertRaisesRegex(source.MaterializationError, "override differs"):
            source.verify(self.root, self.pin_path)


if __name__ == "__main__":
    unittest.main()
