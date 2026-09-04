from __future__ import annotations

from contextlib import redirect_stderr
import fcntl
import gzip
import hashlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import types
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import hot_main_cache as cache_module  # noqa: E402


TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
)

MATERIALIZING_TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    materialize_command=("fake", "materialize"),
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
    additional_identity_files=(
        "references/mipstarre-upstream.json",
        "scripts/materialize_mipstarre.py",
    ),
    recipe_id="test-fake-materializing-build",
)

CANONICAL_MATERIALIZE_V5_COMMAND = (
    "python3",
    "scripts/materialize_mipstarre.py",
    "materialize",
    "--archive-env",
    "MIPSTARRE_ARCHIVE",
)
CANONICAL_MATERIALIZE_V7_COMMAND = (
    *CANONICAL_MATERIALIZE_V5_COMMAND,
    "--replace-existing",
)
PRESERVING_TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    materialize_command=CANONICAL_MATERIALIZE_V7_COMMAND,
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
    additional_identity_files=(
        "references/mipstarre-upstream.json",
        "scripts/materialize_mipstarre.py",
    ),
    recipe_id="test-preserving-materializing-build",
    version=7,
)
LEGACY_V5_TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    materialize_command=CANONICAL_MATERIALIZE_V5_COMMAND,
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
    additional_identity_files=(
        "references/mipstarre-upstream.json",
        "scripts/materialize_mipstarre.py",
    ),
    recipe_id="test-recipe-v5-preservation-omission",
    version=5,
)

PACKAGE_MATERIALIZING_TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    package_materialize_command=("fake", "package-materialize"),
    package_verify_command=(
        "fake",
        "package-verify",
        "--remove-validated-generated-sidecars",
    ),
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
    additional_identity_files=(
        "references/lake-packages.json",
        "references/mathlib-lake-manifest.json",
        "scripts/materialize_lake_packages.py",
    ),
    recipe_id="test-fake-package-materializing-build",
)

FAKE_PACKAGE_VERIFY_COMMAND = [
    "fake",
    "package-verify",
    "--remove-validated-generated-sidecars",
]
FAKE_WIDGET_TARGET = Path(".lake/packages/fixture/widget/package-lock.json")
FAKE_WIDGET_SIDECAR = Path(".lake/packages/fixture/widget/package-lock.json.hash")
FAKE_WIDGET_TARGET_BYTES = b"fixture package lock\n"
FAKE_WIDGET_SIDECAR_BYTES = b"179e66574f04806e"


PRODUCTION_PROBE_RECIPE = cache_module.BuildRecipe(
    recipe_id="test-production-mathlib-probe",
    version=1,
    dependency_command=("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "exe", "cache", "get"),
    build_command=("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build"),
    test_only=False,
)

PRODUCTION_SETUP_PROBE_RECIPE = cache_module.BuildRecipe(
    recipe_id="test-production-mathlib-setup-probe",
    version=1,
    package_materialize_command=("python3", "probe-package-materialize"),
    package_verify_command=("python3", "probe-package-verify"),
    dependency_command=("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "exe", "cache", "get"),
    build_command=("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build"),
    test_only=False,
)


def run_git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        text=True,
        capture_output=True,
        check=True,
        shell=False,
    )
    return result.stdout.strip()


def byte_snapshot(root: Path) -> dict[str, tuple[object, ...]]:
    snapshot: dict[str, tuple[object, ...]] = {}
    for path in [root, *sorted(root.rglob("*"))]:
        relative = path.relative_to(root).as_posix()
        metadata = path.stat(follow_symlinks=False)
        common = (
            stat.S_IMODE(metadata.st_mode),
            metadata.st_size,
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_nlink,
        )
        if path.is_symlink():
            snapshot[relative] = ("symlink", os.readlink(path), *common)
        elif path.is_file():
            payload = path.read_bytes()
            snapshot[relative] = (
                "file",
                hashlib.sha256(payload).hexdigest(),
                payload,
                *common,
            )
        elif path.is_dir():
            snapshot[relative] = ("directory", *common)
    return snapshot


def adaptable_materializer(**attributes: object) -> types.SimpleNamespace:
    defaults: dict[str, object] = {
        "MaterializationError": RuntimeError,
        "TRANSACTION_SAFETY_VERSION": 2,
        "_assert_real_directory": lambda _path: None,
        "_reject_symlink_components": lambda _path: None,
        "_finish_cleanup": lambda _path: None,
        "_recover": lambda *_args: None,
        "_require_transaction_capabilities": lambda _descriptor: None,
    }
    defaults.update(attributes)
    return types.SimpleNamespace(**defaults)


def fake_materializer_evidence(
    root: Path, retained_name: str, *, staged_original: bytes | None = None
) -> dict[str, object]:
    evidence = root / ".workflow-runtime" / "mipstarre-materialization" / retained_name
    evidence.mkdir(parents=True)
    document = b'{"fixture":true}\n'
    (evidence / "transaction.json").write_bytes(document)
    (evidence / "stage").mkdir()
    (evidence / "backup").mkdir()
    if staged_original is not None:
        staged = evidence / "stage" / "MIPStarRE"
        staged.mkdir()
        (staged / "original").write_bytes(staged_original)

    def identity(path: Path) -> dict[str, int]:
        metadata = path.stat(follow_symlinks=False)
        return {
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "type": stat.S_IFMT(metadata.st_mode),
        }

    stage_destination: dict[str, object] | None = None
    if staged_original is not None:
        staged_descriptor = os.open(
            evidence / "stage" / "MIPStarRE", cache_module._authored_directory_flags()
        )
        try:
            stage_destination = {
                **identity(evidence / "stage" / "MIPStarRE"),
                "inventory": cache_module._descriptor_tree_inventory(
                    staged_descriptor, "fixture staged destination"
                ),
            }
        finally:
            os.close(staged_descriptor)

    return {
        "status": "published",
        "transaction_evidence": str(evidence),
        "transaction_evidence_identity": identity(evidence),
        "transaction_evidence_inventory": {
            "schema_version": 1,
            "transaction_entries": ["backup", "stage", "transaction.json"],
            "transaction_document": {
                **identity(evidence / "transaction.json"),
                "size": len(document),
                "sha256": hashlib.sha256(document).hexdigest(),
            },
            "stage": {
                **identity(evidence / "stage"),
                "entries": ["MIPStarRE"] if staged_original is not None else [],
            },
            "backup": {**identity(evidence / "backup"), "entries": []},
            "stage_destination": stage_destination,
        },
    }


def snapshot_subtree(
    snapshot: dict[str, tuple[object, ...]], prefix: str
) -> dict[str, tuple[object, ...]]:
    result: dict[str, tuple[object, ...]] = {}
    for relative, facts in snapshot.items():
        if relative == prefix:
            result["."] = facts
        elif relative.startswith(prefix + "/"):
            result[relative[len(prefix) + 1 :]] = facts
    return result


def initialize_repository(root: Path) -> str:
    root.mkdir(parents=True)
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.name", "Workflow Test")
    run_git(root, "config", "user.email", "workflow@example.invalid")
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.19.0\n", encoding="utf-8")
    (root / "lakefile.toml").write_text("name = \"QPBT\"\n", encoding="utf-8")
    (root / "lake-manifest.json").write_text("{\"version\": 1}\n", encoding="utf-8")
    (root / "MIPStarRE").mkdir()
    (root / "MIPStarRE" / "Basic.lean").write_text("def answer := 42\n", encoding="utf-8")
    (root / ".gitignore").write_text(
        ".lake/\nMIPStarRE/materialized-marker\n", encoding="utf-8"
    )
    (root / "references").mkdir()
    (root / "references" / "mipstarre-upstream.json").write_text(
        json.dumps(
            {
                "source": {"commit": "1" * 40},
                "output": {
                    "inventory_sha256": hashlib.sha256(b"materialized\n").hexdigest(),
                    "files": 1,
                    "bytes": len(b"materialized\n"),
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "materialize_mipstarre.py").write_text("# test materializer\n", encoding="utf-8")
    (root / "references" / "lake-packages.json").write_text("{}\n", encoding="ascii")
    (root / "references" / "mathlib-lake-manifest.json").write_text(
        "{\"name\":\"mathlib\"}\n", encoding="ascii"
    )
    (root / "scripts" / "materialize_lake_packages.py").write_text(
        "# test package materializer\n", encoding="ascii"
    )
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "initial")
    return run_git(root, "rev-parse", "HEAD")


def initialize_mathlib_source(root: Path) -> tuple[str, str]:
    """Create a standalone local Git source suitable for source-auth tests."""

    root.mkdir(parents=True)
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.name", "Mathlib Fixture")
    run_git(root, "config", "user.email", "mathlib@example.invalid")
    (root / "Mathlib").mkdir()
    (root / "Mathlib" / "Fixture.lean").write_text(
        "namespace Mathlib\ndef fixture := 1\nend Mathlib\n", encoding="utf-8"
    )
    (root / "lakefile.lean").write_text("package mathlib\n", encoding="utf-8")
    (root / "README.md").write_text("local fixture\n", encoding="utf-8")
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "mathlib fixture")
    return run_git(root, "rev-parse", "HEAD"), run_git(root, "rev-parse", "HEAD^{tree}")


def write_mathlib_pin(project: Path, commit: str) -> None:
    manifest = {
        "version": 1,
        "packages": [
            {
                "url": cache_module.MATHLIB_REPOSITORY_URL,
                "type": "git",
                "rev": commit,
                "name": "mathlib",
            }
        ],
    }
    (project / "lake-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
    )


def pack_mathlib_archive(source: Path, archive: Path) -> dict[str, object]:
    """Emit a deterministic test archive and return its digest facts."""

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        tar.add(source, arcname="mathlib", recursive=True)
    tar_bytes = tar_buffer.getvalue()
    payload = gzip.compress(tar_bytes, mtime=0)
    archive.write_bytes(payload)
    return {
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "archive_bytes": len(payload),
        "tar_sha256": hashlib.sha256(tar_bytes).hexdigest(),
        "tar_bytes": len(tar_bytes),
    }


def pack_mathlib_tar_members(
    archive: Path,
    members: list[tuple[tarfile.TarInfo, bytes | None]],
) -> dict[str, object]:
    """Emit a deterministic test archive from exact tar records."""

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for member, payload in members:
            if payload is not None:
                member.size = len(payload)
                tar.addfile(member, io.BytesIO(payload))
            else:
                tar.addfile(member)
    tar_bytes = tar_buffer.getvalue()
    payload = gzip.compress(tar_bytes, mtime=0)
    archive.write_bytes(payload)
    return {
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "archive_bytes": len(payload),
        "tar_sha256": hashlib.sha256(tar_bytes).hexdigest(),
        "tar_bytes": len(tar_bytes),
    }


def fake_success(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
    if list(command) == ["fake", "materialize"]:
        (project / "MIPStarRE" / "materialized-marker").write_text(
            "materialized\n", encoding="utf-8"
        )
    elif list(command) == ["fake", "package-materialize"]:
        if not (project / "references" / "mathlib-lake-manifest.json").is_file():
            return 8
        if (project / ".lake" / "packages" / "mathlib" / "lake-manifest.json").exists():
            return 8
        packages = project / ".lake" / "packages" / "fixture"
        packages.mkdir(parents=True, exist_ok=True)
        (packages / "marker").write_text("package\n", encoding="ascii")
        target = project / FAKE_WIDGET_TARGET
        target.parent.mkdir()
        target.write_bytes(FAKE_WIDGET_TARGET_BYTES)
        (project / ".lake" / "package-overrides.json").write_text("{}\n", encoding="ascii")
    elif list(command) == FAKE_PACKAGE_VERIFY_COMMAND:
        marker = project / ".lake" / "packages" / "fixture" / "marker"
        target = project / FAKE_WIDGET_TARGET
        if not target.is_file() or target.read_bytes() != FAKE_WIDGET_TARGET_BYTES:
            return 9
        sidecar = project / FAKE_WIDGET_SIDECAR
        if sidecar.exists() or sidecar.is_symlink():
            if not sidecar.is_file() or sidecar.read_bytes() != FAKE_WIDGET_SIDECAR_BYTES:
                return 9
            sidecar.unlink()
        if not marker.is_file() or marker.read_text(encoding="ascii") != "package\n":
            return 9
    elif list(command) == ["fake", "deps"]:
        package = project / ".lake" / "packages" / "mathlib"
        package.mkdir(parents=True, exist_ok=True)
        (package / "marker").write_text("dependency\n", encoding="utf-8")
        generated = project / ".lake" / "packages" / "fixture" / ".lake" / "build"
        generated.mkdir(parents=True, exist_ok=True)
        (generated / "Fixture.olean").write_text("compiled-package\n", encoding="utf-8")
    elif list(command) == ["fake", "build"]:
        build = project / ".lake" / "build"
        build.mkdir(parents=True, exist_ok=True)
        (build / "QPBT.olean").write_text("compiled-main\n", encoding="utf-8")
        target = project / FAKE_WIDGET_TARGET
        if target.is_file():
            (project / FAKE_WIDGET_SIDECAR).write_bytes(FAKE_WIDGET_SIDECAR_BYTES)
    return 0


def fake_source_verifier(project: Path) -> dict[str, object]:
    marker = (project / "MIPStarRE" / "materialized-marker").read_bytes()
    if marker != b"materialized\n":
        raise cache_module.CacheError("fake foundation source verification failed")
    pin_sha256 = cache_module.sha256_file(project / "references" / "mipstarre-upstream.json")
    return {
        "schema_version": cache_module.SOURCE_EVIDENCE_SCHEMA_VERSION,
        "pin_sha256": pin_sha256,
        "source_commit": "1" * 40,
        "inventory_sha256": hashlib.sha256(marker).hexdigest(),
        "files": 1,
        "bytes": len(marker),
        **cache_module.authored_tree_facts_on_disk(project),
    }


def fake_preserving_success(
    project: Path,
    command: list[str] | tuple[str, ...],
    log_path: Path,
) -> int:
    if tuple(command) == CANONICAL_MATERIALIZE_V7_COMMAND:
        upstream = project / "MIPStarRE" / "Basic.lean"
        upstream.write_bytes(upstream.read_bytes())
        (project / "MIPStarRE" / "materialized-marker").write_text(
            "materialized\n", encoding="utf-8"
        )
        return 0
    return fake_success(project, command, log_path)


def contention_worker(repo: str, runtime: str, counter: str) -> None:
    manager = cache_module.HotMainCache(
        Path(repo),
        Path(repo),
        Path(runtime),
        _test_recipe=MATERIALIZING_TEST_RECIPE,
    )

    def callback(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
        if list(command) in (["fake", "materialize"], ["fake", "build"]):
            with Path(counter).open("a+", encoding="utf-8") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                stream.write(f"{command[1]}\n")
                stream.flush()
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            time.sleep(0.25)
        return fake_success(project, command, log_path)

    manager.warm(
        _test_command_callback=callback,
        _test_source_verifier=fake_source_verifier,
    )


def linked_worktree_contention_worker(worktree: str, counter: str) -> None:
    """Warm from a linked checkout using its omitted-runtime default."""

    project = Path(worktree)
    runtime = cache_module.default_runtime_dir(project)
    manager = cache_module.HotMainCache(
        project,
        project,
        runtime,
        _test_recipe=TEST_RECIPE,
    )

    def callback(
        callback_project: Path,
        command: list[str] | tuple[str, ...],
        log_path: Path,
    ) -> int:
        if list(command) == ["fake", "build"]:
            with Path(counter).open("a+", encoding="utf-8") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                stream.write("build\n")
                stream.flush()
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            time.sleep(0.25)
        return fake_success(callback_project, command, log_path)

    manager.warm(_test_command_callback=callback)


def failing_metric_writer(
    repo: str,
    runtime: str,
    failure_mode: str,
    rollback_started: multiprocessing.synchronize.Event,
    release_rollback: multiprocessing.synchronize.Event,
    outcome: multiprocessing.queues.Queue,
) -> None:
    manager = cache_module.HotMainCache(
        Path(repo), Path(repo), Path(runtime), _test_recipe=TEST_RECIPE
    )
    real_rollback = manager._rollback_metric_append_locked

    def pause_rollback(descriptor: int, checkpoint: int) -> None:
        rollback_started.set()
        if not release_rollback.wait(10):
            raise RuntimeError("timed out waiting to finish metric rollback")
        real_rollback(descriptor, checkpoint)

    try:
        with mock.patch.object(
            manager, "_rollback_metric_append_locked", side_effect=pause_rollback
        ):
            if failure_mode == "short-write":
                real_write = cache_module.os.write
                injected = False

                def short_write(descriptor: int, payload: bytes) -> int:
                    nonlocal injected
                    if not injected:
                        injected = True
                        count = max(1, len(payload) // 2)
                        real_write(descriptor, payload[:count])
                        return count
                    return real_write(descriptor, payload)

                with mock.patch.object(cache_module.os, "write", side_effect=short_write):
                    manager._append_metric({"action": "test", "result": "writer-a"})
            else:
                real_fsync = cache_module.os.fsync
                injected = False

                def fail_fsync(descriptor: int) -> None:
                    nonlocal injected
                    if not injected:
                        injected = True
                        raise OSError("injected metric fsync failure")
                    real_fsync(descriptor)

                with mock.patch.object(cache_module.os, "fsync", side_effect=fail_fsync):
                    manager._append_metric({"action": "test", "result": "writer-a"})
    except OSError:
        outcome.put("rolled-back")
    else:
        outcome.put("unexpected-success")


def successful_metric_writer(
    repo: str,
    runtime: str,
    started: multiprocessing.synchronize.Event,
    completed: multiprocessing.synchronize.Event,
    expected_line: multiprocessing.queues.Queue,
) -> None:
    manager = cache_module.HotMainCache(
        Path(repo), Path(repo), Path(runtime), _test_recipe=TEST_RECIPE
    )
    metric = {"action": "test", "result": "writer-b"}
    timestamp = "2026-09-03T00:00:00+00:00"
    envelope = {
        "schema_version": cache_module.SCHEMA_VERSION,
        "timestamp": timestamp,
        "pid": os.getpid(),
        "cache_key": manager.identity.cache_key,
        "main_commit": manager.identity.main_commit,
        **metric,
    }
    expected_line.put(
        (json.dumps(envelope, ensure_ascii=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )
    )
    started.set()
    with mock.patch.object(cache_module, "utc_now", return_value=timestamp):
        manager._append_metric(metric)
    completed.set()


class HotMainCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.commit = initialize_repository(self.repo)
        self.runtime = self.base / "runtime"

    def tearDown(self) -> None:
        if self.base.exists():
            cache_module.make_owner_writable(self.base)
        self.temporary.cleanup()

    def manager(
        self,
        *,
        runtime: Path | None = None,
        recipe: cache_module.BuildRecipe = TEST_RECIPE,
    ) -> cache_module.HotMainCache:
        return cache_module.HotMainCache(
            self.repo,
            self.repo,
            runtime or self.runtime,
            _test_recipe=recipe,
        )

    def issue_worktree(self, name: str = "issue-worktree") -> Path:
        target = self.base / name
        run_git(self.repo, "worktree", "add", "--detach", str(target), self.commit)
        return target

    @staticmethod
    def metric_records(manager: cache_module.HotMainCache) -> list[dict[str, object]]:
        if not manager.metrics_path.exists():
            return []
        return [
            json.loads(line)
            for line in manager.metrics_path.read_text(encoding="utf-8").splitlines()
        ]

    def mathlib_fixture(self) -> tuple[Path, str, str]:
        source = self.base / "mathlib-source"
        commit, tree = initialize_mathlib_source(source)
        write_mathlib_pin(self.repo, commit)
        run_git(self.repo, "add", "lake-manifest.json")
        run_git(self.repo, "commit", "-m", "pin mathlib fixture")
        return source, commit, tree

    def test_renameat2_wrapper_restricts_flags_and_child_names(self) -> None:
        with self.assertRaisesRegex(cache_module.CacheError, "no-replace or exchange"):
            cache_module._linux_renameat2(-1, "source", -1, "destination", 0)
        for unsafe_name in ("", ".", "..", "parent/child", "nul\0child"):
            with self.subTest(name=unsafe_name), self.assertRaisesRegex(
                cache_module.CacheError, "single child names"
            ):
                cache_module._linux_renameat2(
                    -1,
                    unsafe_name,
                    -1,
                    "destination",
                    cache_module.RENAME_NOREPLACE,
                )

    def test_renameat2_semantic_probe_retains_evidence_without_recursive_delete(self) -> None:
        target_descriptor = os.open(self.repo, cache_module._authored_directory_flags())
        before = set(Path("/tmp").glob("mipstarre-renameat2-probe-retained-*"))
        try:
            with mock.patch.object(
                cache_module.shutil,
                "rmtree",
                side_effect=AssertionError("semantic probe recursively deleted a pathname"),
            ):
                cache_module._probe_renameat2_semantics(target_descriptor)
        finally:
            os.close(target_descriptor)
        retained = set(Path("/tmp").glob("mipstarre-renameat2-probe-retained-*")) - before
        self.assertEqual(1, len(retained))
        evidence = retained.pop()
        self.assertEqual({"first", "second", "moved"}, {path.name for path in evidence.iterdir()})

    def test_renameat2_probe_rejects_root_substitution_before_child_writes(self) -> None:
        token = hashlib.sha256(str(self.base).encode("utf-8")).hexdigest()[:32]
        root_name = f"mipstarre-renameat2-probe-retained-{token}"
        parked_name = f"{root_name}-attacker-parked"
        real_mkdir = cache_module.os.mkdir
        injected = False

        def substitute_after_root_create(
            path: object,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            nonlocal injected
            real_mkdir(path, mode, dir_fd=dir_fd)
            if path == root_name and dir_fd is not None and not injected:
                injected = True
                os.rename(path, parked_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                real_mkdir(path, mode, dir_fd=dir_fd)
                substitute = Path("/tmp") / root_name
                (substitute / "unrelated").write_bytes(b"preserve")

        target_descriptor = os.open(self.repo, cache_module._authored_directory_flags())
        try:
            with mock.patch.object(
                cache_module.secrets, "token_hex", return_value=token
            ), mock.patch.object(cache_module.os, "mkdir", side_effect=substitute_after_root_create):
                with self.assertRaisesRegex(cache_module.CacheError, "exact monitor events"):
                    cache_module._probe_renameat2_semantics(target_descriptor)
        finally:
            os.close(target_descriptor)
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (Path("/tmp") / root_name / "unrelated").read_bytes())
        self.assertEqual([], list((Path("/tmp") / parked_name).iterdir()))

    def test_identity_comes_from_exact_main_not_dirty_worktree(self) -> None:
        first = self.manager().identity
        (self.repo / "lakefile.toml").write_text("dirty feature content\n", encoding="utf-8")
        second = self.manager().identity
        self.assertEqual(first.cache_key, second.cache_key)
        self.assertEqual(self.commit, second.main_commit)

    def test_detached_clone_retries_without_local_hardlinks_on_exdev(self) -> None:
        staging = self.base / "staging"
        staging.mkdir()
        log_path = staging / "build.log"
        manager = self.manager()
        commands: list[list[str]] = []

        def fake_run(_root: Path, command: list[str], log: Path) -> int:
            commands.append(list(command))
            if command[0:3] == ["git", "clone", "--local"]:
                with log.open("a", encoding="utf-8") as stream:
                    stream.write("fatal: Invalid cross-device link\n")
                partial = staging / "checkout"
                partial.mkdir()
                (partial / "partial-object").write_text("incomplete\n", encoding="utf-8")
                return 1
            if command[0:3] == ["git", "clone", "--no-local"]:
                self.assertFalse((staging / "checkout").exists())
                (staging / "checkout").mkdir()
            return 0

        with mock.patch.object(cache_module.HotMainCache, "_run_logged", side_effect=fake_run):
            checkout = manager._detached_clone(staging, log_path)

        self.assertEqual(checkout, staging / "checkout")
        self.assertEqual(
            [
                [
                    "git", "clone", "--local", "--no-checkout",
                    str(manager.repo_root), str(checkout),
                ],
                [
                    "git", "clone", "--no-local", "--no-checkout",
                    str(manager.repo_root), str(checkout),
                ],
                [
                    "git", "-C", str(checkout), "checkout", "--detach",
                    manager.identity.main_commit,
                ],
            ],
            commands,
        )
        log = log_path.read_text(encoding="utf-8")
        self.assertIn("Invalid cross-device link", log)
        self.assertIn("retrying --no-local", log)

    def test_detached_clone_ignores_cross_device_text_before_attempt(self) -> None:
        staging = self.base / "stale-log-staging"
        staging.mkdir()
        log_path = staging / "build.log"
        log_path.write_text("old EXDEV diagnostic\n", encoding="utf-8")
        manager = self.manager()
        commands: list[list[str]] = []

        def fake_run(_root: Path, command: list[str], log: Path) -> int:
            commands.append(list(command))
            with log.open("a", encoding="utf-8") as stream:
                stream.write("fatal: unrelated clone failure\n")
            return 9

        with mock.patch.object(cache_module.HotMainCache, "_run_logged", side_effect=fake_run):
            with self.assertRaisesRegex(cache_module.CacheError, "exit code 9"):
                manager._detached_clone(staging, log_path)

        self.assertEqual(
            [[
                "git", "clone", "--local", "--no-checkout",
                str(manager.repo_root), str(staging / "checkout"),
            ]],
            commands,
        )
        self.assertNotIn("retrying --no-local", log_path.read_text(encoding="utf-8"))

    def test_detached_clone_retries_at_most_once_on_exdev(self) -> None:
        staging = self.base / "bounded-retry-staging"
        staging.mkdir()
        log_path = staging / "build.log"
        manager = self.manager()
        commands: list[list[str]] = []

        def fake_run(_root: Path, command: list[str], log: Path) -> int:
            commands.append(list(command))
            if command[0:3] == ["git", "clone", "--local"]:
                with log.open("a", encoding="utf-8") as stream:
                    stream.write("fatal: Invalid cross-device link\n")
                (staging / "checkout").mkdir()
                return 1
            self.assertEqual(command[0:3], ["git", "clone", "--no-local"])
            self.assertFalse((staging / "checkout").exists())
            with log.open("a", encoding="utf-8") as stream:
                stream.write("fatal: fallback clone failed with EXDEV too\n")
            return 23

        with mock.patch.object(cache_module.HotMainCache, "_run_logged", side_effect=fake_run):
            with self.assertRaisesRegex(cache_module.CacheError, "exit code 23"):
                manager._detached_clone(staging, log_path)

        checkout = staging / "checkout"
        self.assertEqual(
            [
                [
                    "git", "clone", "--local", "--no-checkout",
                    str(manager.repo_root), str(checkout),
                ],
                [
                    "git", "clone", "--no-local", "--no-checkout",
                    str(manager.repo_root), str(checkout),
                ],
            ],
            commands,
        )

    def test_warm_exdev_fallback_checkout_failure_publishes_no_snapshot(self) -> None:
        manager = self.manager()
        commands: list[list[str]] = []

        def fake_clone_run(_root: Path, command: list[str], log: Path) -> int:
            commands.append(list(command))
            if command[0:3] == ["git", "clone", "--local"]:
                log.write_text("fatal: Invalid cross-device link\n", encoding="utf-8")
                (log.parent / "checkout").mkdir()
                return 1
            if command[0:3] == ["git", "clone", "--no-local"]:
                (log.parent / "checkout").mkdir()
                return 0
            with log.open("a", encoding="utf-8") as stream:
                stream.write("fatal: detached checkout failed\n")
            return 17

        with mock.patch.object(cache_module.HotMainCache, "_run_logged", side_effect=fake_clone_run):
            with self.assertRaisesRegex(cache_module.CacheError, "exit code 17"):
                manager.warm(_test_command_callback=fake_success)

        checkout = mock.ANY
        self.assertEqual(
            [
                [
                    "git", "clone", "--local", "--no-checkout",
                    str(manager.repo_root), checkout,
                ],
                [
                    "git", "clone", "--no-local", "--no-checkout",
                    str(manager.repo_root), checkout,
                ],
                [
                    "git", "-C", checkout, "checkout", "--detach",
                    manager.identity.main_commit,
                ],
            ],
            commands,
        )
        self.assertEqual(commands[0][-1], commands[1][-1])
        self.assertEqual(commands[0][-1], commands[2][2])
        self.assertFalse(manager.is_ready())
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
        failures = list((self.runtime / "cache" / "failures").iterdir())
        self.assertEqual(len(failures), 1)
        retained = failures[0]
        self.assertFalse((retained / "READY").exists())
        log = (retained / "build.log").read_text(encoding="utf-8")
        self.assertIn("Invalid cross-device link", log)
        self.assertIn("retrying --no-local", log)
        self.assertIn("detached checkout failed", log)
        failure = json.loads((retained / "failure.json").read_text(encoding="utf-8"))
        self.assertIsNone(failure["mathlib_source"])

    def test_warm_hits_then_seed_is_private_and_writable(self) -> None:
        manager = self.manager()
        calls: list[list[str]] = []

        def callback(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            calls.append(list(command))
            return fake_success(project, command, log_path)

        built = manager.warm(_test_command_callback=callback)
        self.assertEqual("built", built["result"])
        self.assertTrue(manager.is_ready())
        hit = manager.warm(_test_command_callback=callback)
        self.assertEqual("hit", hit["result"])
        self.assertEqual([["fake", "deps"], ["fake", "build"]], calls)

        target = self.issue_worktree()
        seeded = manager.seed(target)
        self.assertEqual("seeded", seeded["result"])
        cached_file = manager.build_dir / "QPBT.olean"
        target_file = target / ".lake" / "build" / "QPBT.olean"
        self.assertNotEqual(cached_file.stat().st_ino, target_file.stat().st_ino)
        self.assertTrue(target_file.stat().st_mode & stat.S_IWUSR)
        target_file.write_text("issue change\n", encoding="utf-8")
        self.assertEqual("compiled-main\n", cached_file.read_text(encoding="utf-8"))
        self.assertTrue((target / ".lake" / "packages" / "mathlib" / "marker").is_file())

    def test_elected_builder_materializes_once_and_identity_binds_materializer(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        calls: list[list[str]] = []

        def callback(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            calls.append(list(command))
            return fake_success(project, command, log_path)

        built = manager.warm(
            _test_command_callback=callback,
            _test_source_verifier=fake_source_verifier,
        )
        self.assertEqual("built", built["result"])
        self.assertEqual(
            [["fake", "materialize"], ["fake", "deps"], ["fake", "build"]],
            calls,
        )
        self.assertEqual(
            "hit",
            manager.warm(
                _test_command_callback=callback,
                _test_source_verifier=fake_source_verifier,
            )["result"],
        )
        self.assertEqual(3, len(calls))
        self.assertIn("references/mipstarre-upstream.json", manager.identity.inputs)
        self.assertIn("scripts/materialize_mipstarre.py", manager.identity.inputs)
        self.assertNotIn(str(self.base), json.dumps(manager.identity.recipe))
        self.assertEqual("1" * 40, manager.identity.source_contract["source_commit"])
        self.assertEqual(0, manager.identity.source_contract["authored_qpbt_files"])
        manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("1" * 40, manifest["source_evidence"]["source_commit"])
        self.assertEqual(1, manifest["source_evidence"]["files"])
        self.assertEqual(13, manifest["source_evidence"]["bytes"])
        self.assertEqual(
            {
                "inventory": {
                    "authored_qpbt_files": 0,
                    "authored_qpbt_bytes": 0,
                    "authored_qpbt_sha256": hashlib.sha256().hexdigest(),
                },
                "phases": list(cache_module.AUTHORED_QPBT_CHECK_PHASES),
            },
            manifest["authored_qpbt_verification"],
        )

        original_key = manager.identity.cache_key
        (self.repo / "scripts" / "materialize_mipstarre.py").write_text(
            "# dirty materializer does not affect committed identity\n", encoding="utf-8"
        )
        self.assertEqual(
            original_key,
            self.manager(recipe=MATERIALIZING_TEST_RECIPE).identity.cache_key,
        )
        run_git(self.repo, "add", "scripts/materialize_mipstarre.py")
        run_git(self.repo, "commit", "-m", "change materializer")
        self.assertNotEqual(
            original_key,
            self.manager(recipe=MATERIALIZING_TEST_RECIPE).identity.cache_key,
        )

    def test_recipe_v5_reproduces_nonzero_authored_failure_without_ready(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        (authored / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        manager = self.manager(
            runtime=self.base / "runtime-recipe-v5",
            recipe=LEGACY_V5_TEST_RECIPE,
        )
        calls: list[list[str]] = []

        def reject_existing(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            calls.append(list(command))
            if tuple(command) == CANONICAL_MATERIALIZE_V5_COMMAND:
                return 2
            raise AssertionError(f"unexpected command after failed materialization: {command}")

        with self.assertRaisesRegex(
            cache_module.CacheError,
            "foundation materialization command failed with exit code 2",
        ):
            manager.warm(_test_command_callback=reject_existing)
        self.assertEqual([list(CANONICAL_MATERIALIZE_V5_COMMAND)], calls)
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
        failure_dirs = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failure_dirs))
        failure = json.loads(
            (failure_dirs[0] / "failure.json").read_text(encoding="utf-8")
        )
        self.assertEqual(5, failure["recipe"]["version"])
        self.assertNotIn("--replace-existing", failure["recipe"]["materialize_command"])

    def test_recipe_v7_preserves_nonzero_authored_tree_and_refreshes_upstream(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        payload = b"def owned := true\n"
        (authored / "Owned.lean").write_bytes(payload)
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        manager = self.manager(
            runtime=self.base / "runtime-recipe-v7",
            recipe=PRESERVING_TEST_RECIPE,
        )
        calls: list[list[str]] = []

        def record(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            calls.append(list(command))
            return fake_preserving_success(project, command, log_path)

        built = manager.warm(
            _test_command_callback=record,
            _test_source_verifier=fake_source_verifier,
        )
        self.assertEqual("built", built["result"])
        self.assertEqual(
            [
                list(CANONICAL_MATERIALIZE_V7_COMMAND),
                ["fake", "deps"],
                ["fake", "build"],
            ],
            calls,
        )
        self.assertEqual(
            {
                "authored_qpbt_files": 1,
                "authored_qpbt_bytes": len(payload),
                "authored_qpbt_sha256": manager.identity.source_contract[
                    "authored_qpbt_sha256"
                ],
            },
            built["authored_qpbt_verification"]["inventory"],
        )
        self.assertEqual(
            list(cache_module.AUTHORED_QPBT_CHECK_PHASES),
            built["authored_qpbt_verification"]["phases"],
        )
        manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            manager.identity.source_contract["authored_qpbt_sha256"],
            manifest["source_evidence"]["authored_qpbt_sha256"],
        )
        self.assertTrue(manager.is_ready(deep=True))

    def test_full_warm_accepts_exact_same_stem_authored_tree(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        (authored / "Game").mkdir(parents=True)
        (authored / "Game.lean").write_text(
            "namespace QPBT\ndef game := true\nend QPBT\n",
            encoding="utf-8",
        )
        (authored / "Game" / "Types.lean").write_text(
            "namespace QPBT.Game\ndef types := true\nend QPBT.Game\n",
            encoding="utf-8",
        )
        run_git(self.repo, "add", "MIPStarRE/QPBT")
        run_git(self.repo, "commit", "-m", "add exact same-stem tree")
        manager = self.manager(
            runtime=self.base / "runtime-authored-same-stem",
            recipe=PRESERVING_TEST_RECIPE,
        )

        committed = cache_module.authored_contract_facts(manager.identity.source_contract)
        on_disk = cache_module.authored_tree_facts_on_disk(self.repo)
        self.assertEqual(committed, on_disk)
        self.assertEqual(2, on_disk["authored_qpbt_files"])
        built = manager.warm(
            _test_command_callback=fake_preserving_success,
            _test_source_verifier=fake_source_verifier,
        )
        self.assertEqual("built", built["result"])
        self.assertEqual(
            list(cache_module.AUTHORED_QPBT_CHECK_PHASES),
            built["authored_qpbt_verification"]["phases"],
        )
        self.assertTrue(manager.is_ready(deep=True))

    def test_canonical_recipe_v7_and_version_only_keying_are_deterministic(self) -> None:
        self.assertEqual(7, cache_module.CANONICAL_BUILD_RECIPE.version)
        self.assertEqual(
            CANONICAL_MATERIALIZE_V7_COMMAND,
            cache_module.CANONICAL_BUILD_RECIPE.materialize_command,
        )
        equivalent = cache_module.BuildRecipe.for_testing(
            materialize_command=CANONICAL_MATERIALIZE_V7_COMMAND,
            dependency_command=("fake", "deps"),
            build_command=("fake", "build"),
            additional_identity_files=(
                "references/mipstarre-upstream.json",
                "scripts/materialize_mipstarre.py",
            ),
            recipe_id="test-preserving-materializing-build",
            version=7,
        )
        version_eight = cache_module.BuildRecipe.for_testing(
            materialize_command=CANONICAL_MATERIALIZE_V7_COMMAND,
            dependency_command=("fake", "deps"),
            build_command=("fake", "build"),
            additional_identity_files=(
                "references/mipstarre-upstream.json",
                "scripts/materialize_mipstarre.py",
            ),
            recipe_id="test-preserving-materializing-build",
            version=8,
        )
        first = self.manager(recipe=PRESERVING_TEST_RECIPE).identity.cache_key
        second = self.manager(recipe=equivalent).identity.cache_key
        bumped = self.manager(recipe=version_eight).identity.cache_key
        self.assertEqual(first, second)
        self.assertNotEqual(first, bumped)

    def test_authored_inventory_rejects_drift_at_every_post_clone_boundary(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        (authored / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        cases = (
            ("missing", "after_materialization"),
            ("altered", "after_dependency_retrieval"),
            ("untracked", "after_build"),
            ("symlink", "after_dependency_retrieval"),
            ("generated", "before_publication"),
        )
        for case, phase in cases:
            with self.subTest(case=case):
                manager = self.manager(
                    runtime=self.base / f"runtime-authored-{case}",
                    recipe=PRESERVING_TEST_RECIPE,
                )

                def mutate(
                    project: Path,
                    command: list[str] | tuple[str, ...],
                    log_path: Path,
                ) -> int:
                    result = fake_preserving_success(project, command, log_path)
                    owned = project / "MIPStarRE" / "QPBT" / "Owned.lean"
                    if case == "missing" and tuple(command) == CANONICAL_MATERIALIZE_V7_COMMAND:
                        owned.unlink()
                    elif case == "altered" and list(command) == ["fake", "deps"]:
                        owned.write_text("def owned := false\n", encoding="utf-8")
                    elif case == "untracked" and list(command) == ["fake", "build"]:
                        (owned.parent / "Untracked.lean").write_text(
                            "def untracked := true\n", encoding="utf-8"
                        )
                    elif case == "symlink" and list(command) == ["fake", "deps"]:
                        owned.unlink()
                        owned.symlink_to(project / "lean-toolchain")
                    return result

                def verifier(project: Path) -> dict[str, object]:
                    evidence = fake_source_verifier(project)
                    if case == "generated":
                        (project / "MIPStarRE" / "QPBT" / "Generated.lean").write_text(
                            "def generated := true\n", encoding="utf-8"
                        )
                    return evidence

                with self.assertRaisesRegex(cache_module.CacheError, phase):
                    manager.warm(
                        _test_command_callback=mutate,
                        _test_source_verifier=verifier,
                    )
                self.assertFalse(manager.snapshot_dir.exists())
                self.assertEqual([], list(manager.runtime_dir.rglob("READY")))

    def test_authored_inventory_rejects_drift_before_materialization(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        (authored / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        manager = self.manager(
            runtime=self.base / "runtime-authored-before",
            recipe=PRESERVING_TEST_RECIPE,
        )
        original_clone = manager._detached_clone
        calls: list[list[str]] = []

        def dirty_clone(staging: Path, log_path: Path) -> Path:
            checkout = original_clone(staging, log_path)
            generated = checkout / "MIPStarRE" / "QPBT" / "GeneratedBefore.lean"
            generated.write_text("def generatedBefore := true\n", encoding="utf-8")
            return checkout

        def record(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            calls.append(list(command))
            return fake_preserving_success(project, command, log_path)

        with mock.patch.object(manager, "_detached_clone", side_effect=dirty_clone):
            with self.assertRaisesRegex(cache_module.CacheError, "before_materialization"):
                manager.warm(
                    _test_command_callback=record,
                    _test_source_verifier=fake_source_verifier,
                )
        self.assertEqual([], calls)
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))

    def test_authored_inventory_rejects_root_and_nested_directory_substitution(self) -> None:
        for case in ("root", "nested"):
            with self.subTest(case=case):
                project = self.base / f"directory-substitution-{case}" / "project"
                root = project / "MIPStarRE" / "QPBT"
                root.mkdir(parents=True)
                target = root
                if case == "nested":
                    target = root / "Nested"
                    target.mkdir()
                external = self.base / f"directory-substitution-{case}" / "external"
                external.mkdir()
                sentinel = external / "sentinel"
                sentinel.write_text("unchanged\n", encoding="utf-8")
                bound = target.with_name(f"{target.name}-bound")
                original_scandir = os.scandir
                swapped = False

                def swap_after_bind(path: os.PathLike[str] | str | int):
                    nonlocal swapped
                    current: Path | None = None
                    if isinstance(path, int):
                        try:
                            current = Path(os.readlink(f"/proc/self/fd/{path}"))
                        except OSError:
                            current = None
                    if not swapped and current == target:
                        swapped = True
                        target.rename(bound)
                        target.symlink_to(external, target_is_directory=True)
                    return original_scandir(path)

                with mock.patch.object(
                    cache_module.os,
                    "scandir",
                    side_effect=swap_after_bind,
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError,
                        "path incarnation changed",
                    ):
                        cache_module.authored_tree_facts_on_disk(project)
                self.assertTrue(swapped)
                self.assertTrue(target.is_symlink())
                self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))

    def _assert_full_warm_rejects_directory_substitution(self, case: str) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        target = authored
        suffix = ("MIPStarRE", "QPBT")
        if case == "nested":
            target = authored / "Nested"
            target.mkdir()
            suffix = (*suffix, "Nested")
        (target / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        run_git(self.repo, "add", "MIPStarRE/QPBT")
        run_git(self.repo, "commit", "-m", f"add {case} substitution fixture")
        manager = self.manager(
            runtime=self.base / f"runtime-authored-substitution-{case}",
            recipe=PRESERVING_TEST_RECIPE,
        )
        external = self.base / f"external-authored-substitution-{case}"
        external.mkdir()
        sentinel = external / "sentinel"
        sentinel.write_text("unchanged\n", encoding="utf-8")
        original_scandir = os.scandir
        swapped = False

        def swap_after_bind(path: os.PathLike[str] | str | int):
            nonlocal swapped
            current: Path | None = None
            if isinstance(path, int):
                try:
                    current = Path(os.readlink(f"/proc/self/fd/{path}"))
                except OSError:
                    current = None
            if (
                not swapped
                and current is not None
                and tuple(current.parts[-len(suffix) :]) == suffix
            ):
                swapped = True
                bound = current.with_name(f"{current.name}-bound")
                current.rename(bound)
                current.symlink_to(external, target_is_directory=True)
            return original_scandir(path)

        with mock.patch.object(cache_module.os, "scandir", side_effect=swap_after_bind):
            with self.assertRaisesRegex(cache_module.CacheError, "before_materialization"):
                manager.warm(
                    _test_command_callback=fake_preserving_success,
                    _test_source_verifier=fake_source_verifier,
                )
        self.assertTrue(swapped)
        self.assertEqual("unchanged\n", sentinel.read_text(encoding="utf-8"))
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
        failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        self.assertFalse((failures[0] / "READY").exists())

    def test_full_warm_rejects_root_directory_substitution_without_ready(self) -> None:
        self._assert_full_warm_rejects_directory_substitution("root")

    def test_full_warm_rejects_nested_directory_substitution_without_ready(self) -> None:
        self._assert_full_warm_rejects_directory_substitution("nested")

    def test_authored_inventory_rejects_hard_linked_file(self) -> None:
        project = self.base / "hard-link-helper" / "project"
        authored = project / "MIPStarRE" / "QPBT"
        authored.mkdir(parents=True)
        external = self.base / "hard-link-helper" / "external.lean"
        external.write_text("def owned := true\n", encoding="utf-8")
        os.link(external, authored / "Owned.lean")

        with self.assertRaisesRegex(cache_module.CacheError, "single-link regular file"):
            cache_module.authored_tree_facts_on_disk(project)
        self.assertEqual(2, external.stat().st_nlink)

    def test_git_source_changes_rejects_exit_zero_diagnostics(self) -> None:
        warning = (
            "warning: could not open directory "
            "'MIPStarRE/QPBT/Hidden/': Permission denied\n"
        )
        completed = subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=0,
            stdout="",
            stderr=warning,
        )
        with mock.patch.object(cache_module.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(cache_module.CacheError, "git emitted diagnostics"):
                cache_module.git_source_changes(self.repo)

    def test_git_source_changes_does_not_execute_fsmonitor_hook(self) -> None:
        marker = self.base / "fsmonitor-status-executed"
        hook = self.base / "fsmonitor-status-hook"
        hook.write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="ascii")
        hook.chmod(0o755)
        run_git(self.repo, "config", "core.fsmonitor", str(hook))

        self.assertEqual([], cache_module.git_source_changes(self.repo))
        self.assertFalse(marker.exists())

    def test_full_warm_rejects_exit_zero_git_warning_without_ready(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        (authored / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        manager = self.manager(
            runtime=self.base / "runtime-authored-git-warning",
            recipe=PRESERVING_TEST_RECIPE,
        )
        warning = (
            "warning: could not open directory "
            "'MIPStarRE/QPBT/Hidden/': Permission denied\n"
        )
        original_run = subprocess.run
        injected = False

        def warn_on_cleanliness(command, *args, **kwargs):
            nonlocal injected
            result = original_run(command, *args, **kwargs)
            if (
                not injected
                and isinstance(command, (list, tuple))
                and "status" in command
                and "--porcelain=v1" in command
            ):
                injected = True
                return subprocess.CompletedProcess(
                    args=result.args,
                    returncode=0,
                    stdout=result.stdout,
                    stderr=warning,
                )
            return result

        with mock.patch.object(cache_module.subprocess, "run", side_effect=warn_on_cleanliness):
            with self.assertRaisesRegex(cache_module.CacheError, "git emitted diagnostics"):
                manager.warm(
                    _test_command_callback=fake_preserving_success,
                    _test_source_verifier=fake_source_verifier,
                )
        self.assertTrue(injected)
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
        failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        self.assertFalse((failures[0] / "READY").exists())

    def test_full_warm_rejects_hard_linked_authored_file_without_ready(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        payload = b"def owned := true\n"
        (authored / "Owned.lean").write_bytes(payload)
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        manager = self.manager(
            runtime=self.base / "runtime-authored-hard-link",
            recipe=PRESERVING_TEST_RECIPE,
        )
        external = self.base / "external-owned.lean"
        external.write_bytes(payload)

        def hard_link_after_build(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            result = fake_preserving_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                owned = project / "MIPStarRE" / "QPBT" / "Owned.lean"
                owned.unlink()
                os.link(external, owned)
            return result

        with self.assertRaisesRegex(cache_module.CacheError, "after_build"):
            manager.warm(
                _test_command_callback=hard_link_after_build,
                _test_source_verifier=fake_source_verifier,
            )
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
        failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        self.assertFalse((failures[0] / "READY").exists())

    def test_full_warm_rejects_unreadable_generated_subtree_without_ready(self) -> None:
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        (authored / "Owned.lean").write_text("def owned := true\n", encoding="utf-8")
        run_git(self.repo, "add", "MIPStarRE/QPBT/Owned.lean")
        run_git(self.repo, "commit", "-m", "add authored source")
        manager = self.manager(
            runtime=self.base / "runtime-authored-unreadable",
            recipe=PRESERVING_TEST_RECIPE,
        )

        def generate_unreadable_subtree(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            result = fake_preserving_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                hidden = project / "MIPStarRE" / "QPBT" / "Hidden"
                hidden.mkdir()
                (hidden / "Generated.lean").write_text(
                    "def generated := true\n",
                    encoding="utf-8",
                )
            return result

        original_scandir = os.scandir
        denied = False

        def deny_hidden(path: os.PathLike[str] | str | int):
            nonlocal denied
            current: Path | None = None
            if isinstance(path, int):
                try:
                    current = Path(os.readlink(f"/proc/self/fd/{path}"))
                except OSError:
                    current = None
            elif isinstance(path, (str, os.PathLike)):
                current = Path(path)
            if not denied and current is not None and current.name == "Hidden":
                denied = True
                raise PermissionError("deterministic unreadable generated subtree")
            return original_scandir(path)

        with mock.patch.object(cache_module.os, "scandir", side_effect=deny_hidden):
            with self.assertRaisesRegex(cache_module.CacheError, "after_build"):
                manager.warm(
                    _test_command_callback=generate_unreadable_subtree,
                    _test_source_verifier=fake_source_verifier,
                )
        self.assertTrue(denied)
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
        failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        self.assertFalse((failures[0] / "READY").exists())

    def test_packages_are_identity_bound_materialized_and_verified_before_lake_steps(self) -> None:
        manager = self.manager(recipe=PACKAGE_MATERIALIZING_TEST_RECIPE)
        calls: list[list[str]] = []

        def callback(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            calls.append(list(command))
            return fake_success(project, command, log_path)

        self.assertEqual("built", manager.warm(_test_command_callback=callback)["result"])
        self.assertEqual(
            "compiled-package\n",
            (
                manager.snapshot_dir
                / ".lake/packages/fixture/.lake/build/Fixture.olean"
            ).read_text(encoding="utf-8"),
        )
        self.assertEqual(
            [
                ["fake", "package-materialize"],
                FAKE_PACKAGE_VERIFY_COMMAND,
                ["fake", "deps"],
                ["fake", "build"],
                FAKE_PACKAGE_VERIFY_COMMAND,
            ],
            calls,
        )
        snapshot_sidecar = manager.snapshot_dir / FAKE_WIDGET_SIDECAR
        snapshot_build = (
            manager.snapshot_dir
            / ".lake/packages/fixture/.lake/build/Fixture.olean"
        )
        self.assertFalse(snapshot_sidecar.exists())
        self.assertEqual("compiled-package\n", snapshot_build.read_text(encoding="utf-8"))
        self.assertTrue(manager.is_ready(deep=True))
        self.assertIn("references/lake-packages.json", manager.identity.inputs)
        self.assertIn("references/mathlib-lake-manifest.json", manager.identity.inputs)
        self.assertIn("scripts/materialize_lake_packages.py", manager.identity.inputs)
        manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(manifest["package_materialize_seconds"], 0)
        self.assertGreaterEqual(manifest["package_verify_seconds"], 0)
        self.assertEqual(
            manifest["artifact_inventory"],
            cache_module.artifact_inventory(manager.lake_dir),
        )

        target = self.issue_worktree("package-seed")
        self.assertEqual("seeded", manager.seed(target)["result"])
        self.assertFalse((target / FAKE_WIDGET_SIDECAR).exists())
        self.assertEqual(
            "compiled-package\n",
            (
                target / ".lake/packages/fixture/.lake/build/Fixture.olean"
            ).read_text(encoding="utf-8"),
        )
        self.assertEqual(
            manifest["artifact_inventory"],
            cache_module.artifact_inventory(target / ".lake"),
        )

        original_key = manager.identity.cache_key
        materializer = self.repo / "scripts/materialize_lake_packages.py"
        materializer.write_text("# dirty contract does not redefine main\n", encoding="ascii")
        self.assertEqual(
            original_key,
            self.manager(recipe=PACKAGE_MATERIALIZING_TEST_RECIPE).identity.cache_key,
        )
        run_git(self.repo, "add", "scripts/materialize_lake_packages.py")
        run_git(self.repo, "commit", "-m", "change package sidecar contract")
        self.assertNotEqual(
            original_key,
            self.manager(recipe=PACKAGE_MATERIALIZING_TEST_RECIPE).identity.cache_key,
        )

        cache_module.make_owner_writable(manager.snapshot_dir)
        snapshot_sidecar.write_bytes(FAKE_WIDGET_SIDECAR_BYTES)
        self.assertTrue(manager.is_ready())
        self.assertFalse(manager.is_ready(deep=True))
        snapshot_sidecar.unlink()
        seeded_sidecar = target / FAKE_WIDGET_SIDECAR
        seeded_sidecar.write_bytes(FAKE_WIDGET_SIDECAR_BYTES)
        with self.assertRaisesRegex(cache_module.CacheError, "inventory"):
            manager._validate_seeded_destination(target / ".lake")

    def test_warm_rejects_post_build_package_drift(self) -> None:
        for case in ("malformed-sidecar", "source-drift"):
            with self.subTest(case=case):
                manager = self.manager(
                    runtime=self.base / f"runtime-package-{case}",
                    recipe=PACKAGE_MATERIALIZING_TEST_RECIPE,
                )

                def mutate_package(
                    project: Path,
                    command: list[str] | tuple[str, ...],
                    log_path: Path,
                ) -> int:
                    result = fake_success(project, command, log_path)
                    if list(command) == ["fake", "build"]:
                        if case == "malformed-sidecar":
                            (project / FAKE_WIDGET_SIDECAR).write_bytes(b"0000000000000000")
                        else:
                            (project / ".lake/packages/fixture/marker").write_text(
                                "tampered\n", encoding="ascii"
                            )
                    return result

                with self.assertRaisesRegex(
                    cache_module.CacheError, "Lake package verification command failed"
                ):
                    manager.warm(_test_command_callback=mutate_package)
                self.assertFalse(manager.is_ready())
                self.assertFalse(manager.snapshot_dir.exists())
                self.assertEqual([], list(manager.runtime_dir.rglob("READY")))
                failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
                self.assertEqual(1, len(failures))
                self.assertFalse((failures[0] / "READY").exists())
                failure = json.loads(
                    (failures[0] / "failure.json").read_text(encoding="utf-8")
                )
                self.assertIn("Lake package verification command failed", failure["error"])

    def test_canonical_lake_commands_require_override_and_reject_updates(self) -> None:
        canonical = cache_module.CANONICAL_BUILD_RECIPE
        self.assertEqual(3, cache_module.BUILD_RECIPE_SCHEMA_VERSION)
        self.assertEqual(7, canonical.version)
        self.assertEqual(CANONICAL_MATERIALIZE_V7_COMMAND, canonical.materialize_command)
        self.assertEqual(
            (
                "python3",
                "scripts/materialize_lake_packages.py",
                "materialize",
                "--archive-directory-env",
                "LAKE_PACKAGE_ARCHIVES",
            ),
            canonical.package_materialize_command,
        )
        self.assertEqual(
            (
                "python3",
                "scripts/materialize_lake_packages.py",
                "verify",
                "--remove-validated-generated-sidecars",
            ),
            canonical.package_verify_command,
        )
        self.assertEqual(
            {
                "schema_version",
                "recipe_id",
                "version",
                "dependency_command",
                "build_command",
                "materialize_command",
                "package_materialize_command",
                "package_verify_command",
                "additional_identity_files",
                "test_only",
            },
            set(canonical.identity_payload()),
        )
        unflagged_recipe = cache_module.BuildRecipe.for_testing(
            package_materialize_command=("fake", "package-materialize"),
            package_verify_command=("fake", "package-verify"),
            dependency_command=("fake", "deps"),
            build_command=("fake", "build"),
            additional_identity_files=PACKAGE_MATERIALIZING_TEST_RECIPE.additional_identity_files,
            recipe_id=PACKAGE_MATERIALIZING_TEST_RECIPE.recipe_id,
            version=PACKAGE_MATERIALIZING_TEST_RECIPE.version,
        )
        versioned_recipe = cache_module.BuildRecipe.for_testing(
            package_materialize_command=("fake", "package-materialize"),
            package_verify_command=tuple(FAKE_PACKAGE_VERIFY_COMMAND),
            dependency_command=("fake", "deps"),
            build_command=("fake", "build"),
            additional_identity_files=PACKAGE_MATERIALIZING_TEST_RECIPE.additional_identity_files,
            recipe_id=PACKAGE_MATERIALIZING_TEST_RECIPE.recipe_id,
            version=PACKAGE_MATERIALIZING_TEST_RECIPE.version + 1,
        )
        flagged_key = self.manager(
            runtime=self.base / "runtime-flagged-key",
            recipe=PACKAGE_MATERIALIZING_TEST_RECIPE,
        ).identity.cache_key
        self.assertNotEqual(
            flagged_key,
            self.manager(
                runtime=self.base / "runtime-unflagged-key",
                recipe=unflagged_recipe,
            ).identity.cache_key,
        )
        self.assertNotEqual(
            flagged_key,
            self.manager(
                runtime=self.base / "runtime-versioned-key",
                recipe=versioned_recipe,
            ).identity.cache_key,
        )
        for command in (canonical.dependency_command, canonical.build_command):
            self.assertEqual(1, command.count(cache_module.LAKE_OVERRIDE_ARGUMENT))
            self.assertNotIn("update", command)
            self.assertNotIn("--update", command)
        self.assertEqual(
            {
                "references/lake-packages.json",
                "references/mathlib-lake-manifest.json",
                "scripts/materialize_lake_packages.py",
            },
            set(canonical.additional_identity_files)
            & {
                "references/lake-packages.json",
                "references/mathlib-lake-manifest.json",
                "scripts/materialize_lake_packages.py",
            },
        )
        valid = ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build")
        invalid_commands = (
            ("lake", "build"),
            ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "update"),
            ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build", "--update"),
            ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build", "-U"),
            ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build", "-qU"),
            ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "build", "-Uq"),
            ("lake", cache_module.LAKE_OVERRIDE_ARGUMENT, "--packages=other.json", "build"),
        )
        for invalid in invalid_commands:
            with self.subTest(command=invalid), self.assertRaisesRegex(ValueError, "Lake"):
                cache_module.BuildRecipe.for_testing(
                    dependency_command=invalid,
                    build_command=valid,
                )

    def test_mathlib_source_auth_and_url_map_are_path_independent(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        alternate = self.base / "mathlib-source-alternate"
        shutil.copytree(source, alternate, symlinks=True)
        ambient_marker = self.base / "ambient-git-config-executed"
        ambient_command = f"/usr/bin/touch {ambient_marker}"
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ), mock.patch.object(
            cache_module, "CANONICAL_BUILD_RECIPE", PRODUCTION_PROBE_RECIPE
        ):
            manager = cache_module.HotMainCache(self.repo, self.repo, self.runtime)
            staging = self.base / "source-staging"
            staging.mkdir()
            with mock.patch.dict(
                os.environ,
                {
                    cache_module.MATHLIB_SOURCE_ENV: str(source),
                    cache_module.MATHLIB_ARCHIVE_ENV: "",
                    "LAKE_PKG_URL_MAP": '{"zeta":"file:///z","alpha":"file:///a"}',
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.fsmonitor",
                    "GIT_CONFIG_VALUE_0": ambient_command,
                    "GIT_CONFIG_PARAMETERS": f"'core.fsmonitor={ambient_command}'",
                    "GIT_PAGER": ambient_command,
                },
                clear=False,
            ):
                binding = manager._prepare_mathlib_source(staging, self.repo)
                environment = manager._command_environment_for_mathlib(binding)
                self.assertEqual(
                    '{"alpha":"file:///a","mathlib":"%s","zeta":"file:///z"}'
                    % source.as_uri(),
                    environment["LAKE_PKG_URL_MAP"],
                )
                self.assertEqual("0", environment["GIT_TERMINAL_PROMPT"])
                self.assertEqual(os.devnull, environment["GIT_CONFIG_GLOBAL"])
                self.assertEqual(
                    str(len(cache_module.TRUSTED_GIT_CONFIG_OVERRIDES)),
                    environment["GIT_CONFIG_COUNT"],
                )
                self.assertNotIn("GIT_CONFIG_PARAMETERS", environment)
                self.assertEqual("", environment["GIT_PAGER"])
                self.assertFalse(ambient_marker.exists())
                self.assertEqual(commit, binding.evidence["commit"])
                self.assertEqual(tree, binding.evidence["tree"])
                self.assertEqual("source", binding.evidence["mode"])
                self.assertIsNone(binding.evidence["archive_sha256"])
                self.assertIsNone(binding.evidence["archive_bytes"])
                first_key = manager.identity.cache_key
                with mock.patch.dict(
                    os.environ,
                    {
                        cache_module.MATHLIB_SOURCE_ENV: str(alternate),
                        "LAKE_PKG_URL_MAP": "",
                    },
                    clear=False,
                ):
                    alternate_binding = manager._prepare_mathlib_source(staging, self.repo)
                self.assertEqual(first_key, manager.identity.cache_key)
                self.assertEqual(binding.evidence["commit"], alternate_binding.evidence["commit"])
                self.assertEqual(binding.evidence["tree"], alternate_binding.evidence["tree"])
                with mock.patch.dict(
                    os.environ,
                    {"LAKE_PKG_URL_MAP": '{"mathlib":"file:///different"}'},
                    clear=False,
                ):
                    with self.assertRaisesRegex(cache_module.CacheError, "different URL"):
                        manager._command_environment_for_mathlib(binding)

    def test_project_mathlib_pin_is_derived_from_real_lake_manifest(self) -> None:
        project = self.base / "real-manifest-project"
        project.mkdir()
        real_manifest = Path(__file__).resolve().parents[1] / "lake-manifest.json"
        shutil.copy2(real_manifest, project / "lake-manifest.json")
        pin = cache_module.HotMainCache._validate_project_mathlib_pin(project)
        self.assertEqual(
            {
                "repository_url": "https://github.com/leanprover-community/mathlib4",
                "commit": "81a5d257c8e410db227a6665ed08f64fea08e997",
                "tree": "5ea66b811b8461daae82f14d356fed2a287d7c40",
            },
            pin,
        )

    def test_mathlib_source_preflight_rejects_missing_dirty_and_mismatched_inputs(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ), mock.patch.object(
            cache_module, "CANONICAL_BUILD_RECIPE", PRODUCTION_PROBE_RECIPE
        ):
            manager = cache_module.HotMainCache(self.repo, self.repo, self.runtime)
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(cache_module.CacheError, "set exactly one"):
                    manager.warm()
            self.assertFalse(manager.is_ready())
            self.assertEqual([], list(self.runtime.rglob("READY")))

            dirty = source / "DIRTY"
            dirty.write_text("unexpected\n", encoding="ascii")
            with mock.patch.dict(
                os.environ,
                {cache_module.MATHLIB_SOURCE_ENV: str(source)},
                clear=False,
            ):
                with self.assertRaisesRegex(cache_module.CacheError, "changes"):
                    manager.warm()
            dirty.unlink()

            with mock.patch.object(cache_module, "MATHLIB_COMMIT", "0" * 40):
                with mock.patch.dict(
                    os.environ,
                    {cache_module.MATHLIB_SOURCE_ENV: str(source)},
                    clear=False,
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError, "pin differs|commit differs"
                    ):
                        manager.warm()
            self.assertEqual([], list(self.runtime.rglob("READY")))

    def test_complete_input_preflight_requires_all_three_bindings_before_lock(self) -> None:
        manager = self.manager()
        manager._requires_mathlib_source = mock.Mock(return_value=True)
        manager._preflight_mathlib_input = mock.Mock()
        with mock.patch.dict(
            os.environ,
            {cache_module.MIPSTARRE_ARCHIVE_ENV: "", cache_module.LAKE_PACKAGE_ARCHIVES_ENV: ""},
            clear=True,
        ), mock.patch.object(
            cache_module.ExclusiveLock, "__enter__", side_effect=AssertionError("lock acquired")
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "MIPSTARRE_ARCHIVE"):
                manager.warm()
            os.environ[cache_module.MIPSTARRE_ARCHIVE_ENV] = str(self.base / "missing.tar.gz")
            with self.assertRaisesRegex(cache_module.CacheError, "LAKE_PACKAGE_ARCHIVES"):
                manager.warm()
        self.assertFalse(manager.snapshot_dir.exists())
        self.assertEqual([], list(self.runtime.rglob("READY")))

    def test_complete_input_preflight_authenticates_archive_tuple(self) -> None:
        manager = self.manager()
        manager._requires_mathlib_source = mock.Mock(return_value=True)
        manager._preflight_mathlib_input = mock.Mock()
        mip = self.base / "mip.tar.gz"
        mip.write_bytes(b"mip")
        packages = self.base / "packages"
        packages.mkdir()
        package = packages / ("dep-" + "1" * 40 + ".tar.gz")
        package.write_bytes(b"package")
        mip_module = types.SimpleNamespace(
            load_pin=lambda _path: {"archive": {"bytes": 3, "sha256": hashlib.sha256(b"mip").hexdigest()}},
            validate_project_pins=lambda _root, _pin: None,
        )
        package_module = types.SimpleNamespace(
            load_pin=lambda _path: {"packages": [{
                "name": "dep", "revision": "1" * 40,
                "archive": {"bytes": 7, "sha256": hashlib.sha256(b"package").hexdigest()},
            }]},
            validate_manifests=lambda _root, _pin: None,
        )
        manager._load_identity_module = mock.Mock(side_effect=[mip_module, package_module])
        captured_inputs = {
            "lean-toolchain": b"leanprover/lean4:v4.19.0\n",
            "lake-manifest.json": b"{}\n",
            "references/mipstarre-upstream.json": b"{}\n",
            "scripts/materialize_mipstarre.py": b"# captured\n",
            "references/lake-packages.json": b"{}\n",
            "references/mathlib-lake-manifest.json": b"{}\n",
            "scripts/materialize_lake_packages.py": b"# captured\n",
        }
        with mock.patch.dict(os.environ, {
            cache_module.MATHLIB_ARCHIVE_ENV: str(self.base / "mathlib.tar.gz"),
            cache_module.MIPSTARRE_ARCHIVE_ENV: str(mip),
            cache_module.LAKE_PACKAGE_ARCHIVES_ENV: str(packages),
        }, clear=True), mock.patch.object(
            manager, "_capture_identity_inputs", return_value=captured_inputs
        ):
            result = manager._preflight_authenticated_inputs()
        self.assertTrue(result["required"])
        self.assertEqual(1, result["lake_package_count"])

        package.unlink()
        package.symlink_to(mip)
        with mock.patch.dict(os.environ, {
            cache_module.MIPSTARRE_ARCHIVE_ENV: str(mip),
            cache_module.LAKE_PACKAGE_ARCHIVES_ENV: str(packages),
        }, clear=True), mock.patch.object(
            manager, "_capture_identity_inputs", return_value=captured_inputs
        ):
            manager._load_identity_module = mock.Mock(side_effect=[mip_module, package_module])
            with self.assertRaisesRegex(cache_module.CacheError, "symlink|Too many levels"):
                manager._preflight_authenticated_inputs()

    def test_identity_capture_rejects_every_verifier_pin_and_manifest_substitution(self) -> None:
        manager = cache_module.HotMainCache(self.repo, self.repo, self.runtime)
        for relative in manager.identity.inputs:
            with self.subTest(relative=relative):
                path = self.repo / relative
                original = path.read_bytes()
                substitute = path.with_name(path.name + ".substitute")
                substitute.write_bytes(b"substituted identity input\n")
                os.replace(substitute, path)
                try:
                    with self.assertRaisesRegex(cache_module.CacheError, "exact main cache identity"):
                        manager._capture_identity_inputs(self.repo)
                finally:
                    path.write_bytes(original)
        scripts = self.repo / "scripts"
        real_scripts = self.repo / "scripts.real"
        external_scripts = self.base / "external-scripts"
        shutil.copytree(scripts, external_scripts)
        scripts.rename(real_scripts)
        scripts.symlink_to(external_scripts, target_is_directory=True)
        try:
            with self.assertRaisesRegex(cache_module.CacheError, "without following links"):
                manager._capture_identity_inputs(self.repo)
        finally:
            scripts.unlink()
            real_scripts.rename(scripts)

    def test_warm_rejects_substituted_identity_input_before_hit_or_lock(self) -> None:
        manager = cache_module.HotMainCache(self.repo, self.repo, self.runtime)
        (self.repo / "scripts" / "materialize_mipstarre.py").write_text(
            "raise RuntimeError('must not execute')\n", encoding="ascii"
        )
        with mock.patch.object(
            cache_module.ExclusiveLock,
            "__enter__",
            side_effect=AssertionError("cache lock acquired"),
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "exact main cache identity"):
                manager.warm()
        self.assertFalse(manager.snapshot_dir.exists())

    def test_identity_module_executes_only_captured_authenticated_bytes(self) -> None:
        path = self.repo / "scripts" / "materialize_mipstarre.py"
        path.write_text("VALUE = 'trusted'\n", encoding="ascii")
        run_git(self.repo, "add", "scripts/materialize_mipstarre.py")
        run_git(self.repo, "commit", "-m", "add captured module fixture")
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        captured = manager._capture_identity_inputs(self.repo)
        marker = self.base / "mutable-module-executed"
        path.write_text(
            f"VALUE = 'substituted'\nopen({str(marker)!r}, 'w').write('bad')\n",
            encoding="ascii",
        )

        module = manager._load_identity_module(
            "scripts/materialize_mipstarre.py",
            "_captured_module_regression",
            captured["scripts/materialize_mipstarre.py"],
            self.repo,
        )

        self.assertEqual("trusted", module.VALUE)
        self.assertFalse(marker.exists())
        with self.assertRaisesRegex(cache_module.CacheError, "exact main cache identity"):
            manager._capture_identity_inputs(self.repo)

    def test_captured_pins_and_manifests_never_cross_a_temporary_pathname(self) -> None:
        source_root = Path(__file__).resolve().parents[1]
        relative_paths = (
            "lean-toolchain",
            "lake-manifest.json",
            "references/mipstarre-upstream.json",
            "scripts/materialize_mipstarre.py",
            "references/lake-packages.json",
            "references/mathlib-lake-manifest.json",
            "scripts/materialize_lake_packages.py",
        )
        captured = {
            relative: (source_root / relative).read_bytes()
            for relative in relative_paths
        }
        display_root = self.base / "substituted-captured-inputs"
        for relative in relative_paths:
            path = display_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"later source substitution\n")

        mip_module = cache_module.HotMainCache._load_identity_module(
            "scripts/materialize_mipstarre.py",
            "_captured_mipstarre_regression",
            captured["scripts/materialize_mipstarre.py"],
            display_root,
        )
        package_module = cache_module.HotMainCache._load_identity_module(
            "scripts/materialize_lake_packages.py",
            "_captured_packages_regression",
            captured["scripts/materialize_lake_packages.py"],
            display_root,
        )
        original_load_json = package_module._load_json
        original_file_sha256 = package_module._file_sha256
        with mock.patch.object(
            cache_module.tempfile,
            "TemporaryDirectory",
            side_effect=AssertionError("temporary pathname boundary opened"),
        ):
            mip_pin = cache_module.HotMainCache._load_captured_pin(
                mip_module,
                "references/mipstarre-upstream.json",
                captured["references/mipstarre-upstream.json"],
            )
            cache_module.HotMainCache._validate_captured_project(
                mip_module, "validate_project_pins", captured, mip_pin
            )
            package_pin = cache_module.HotMainCache._load_captured_pin(
                package_module,
                "references/lake-packages.json",
                captured["references/lake-packages.json"],
            )
            cache_module.HotMainCache._validate_captured_project(
                package_module, "validate_manifests", captured, package_pin
            )

        self.assertIs(original_load_json, package_module._load_json)
        self.assertIs(original_file_sha256, package_module._file_sha256)
        self.assertEqual(
            json.loads(captured["references/mipstarre-upstream.json"])["source"]["commit"],
            mip_pin["source"]["commit"],
        )
        self.assertEqual(
            json.loads(captured["references/lake-packages.json"])["packages"],
            package_pin["packages"],
        )

    def test_captured_project_adapter_rejects_unadmitted_paths(self) -> None:
        module = types.SimpleNamespace(
            validate_project_pins=lambda root, _pin: (root / "unadmitted.json").read_text()
        )
        with self.assertRaisesRegex(cache_module.CacheError, "unauthenticated path"):
            cache_module.HotMainCache._validate_captured_project(
                module,
                "validate_project_pins",
                {"lean-toolchain": b"toolchain\n", "lake-manifest.json": b"{}\n"},
                {},
            )

    def test_prepare_sequences_seed_replace_materialize_verify_and_preserves_authored(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-worktree")
        archive = self.base / "foundation.tar.gz"
        archive.write_bytes(b"authenticated")
        calls: list[object] = []
        authored = cache_module.authored_tree_facts_on_disk(target)
        fake_module = adaptable_materializer(
            load_pin=lambda _path: {"source": {"commit": "1" * 40}},
            validate_project_pins=lambda _root, _pin: calls.append("pins"),
            materialize=lambda _root, _pin_path, _archive, *, replace_existing: (
                calls.append(("materialize", replace_existing)) or {"status": "published"}
            ),
            verify_materialized=lambda _root, _pin: (
                calls.append("verify") or {"status": "verified", **authored}
            ),
        )
        with mock.patch.dict(os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True), \
             mock.patch.object(manager, "_preflight_authenticated_inputs", return_value={"required": True}), \
             mock.patch.object(manager, "_load_identity_module", return_value=fake_module):
            result = manager.prepare(target)
        self.assertEqual(["pins", ("materialize", True), "verify"], calls)
        self.assertEqual("prepared", result["result"])
        self.assertEqual(cache_module.authored_tree_facts_on_disk(target), result["authored_qpbt"])

    def test_prepare_returns_stable_materializer_evidence_after_target_close(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-stable-evidence")
        archive = self.base / "foundation-stable-evidence.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)

        def materialize_with_evidence(
            root: Path, *_args: object, **_kwargs: object
        ) -> dict[str, object]:
            return fake_materializer_evidence(
                root, "MIPStarRE.transaction.retained-test"
            )

        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=materialize_with_evidence,
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )
        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=fake_module
        ):
            result = manager.prepare(target)

        evidence = Path(result["foundation"]["transaction_evidence"])
        self.assertEqual(
            target
            / ".workflow-runtime"
            / "mipstarre-materialization"
            / "MIPStarRE.transaction.retained-test",
            evidence,
        )
        self.assertNotIn("/proc/self/fd/", str(evidence))
        self.assertTrue(evidence.is_dir())

    def test_prepare_evidence_normalization_rejects_descendant_symlink_swap(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-evidence-symlink-swap")
        archive = self.base / "foundation-evidence-symlink-swap.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)
        retained_name = "MIPStarRE.transaction.retained-test"

        def materialize_with_evidence(
            root: Path, *_args: object, **_kwargs: object
        ) -> dict[str, object]:
            return fake_materializer_evidence(root, retained_name)

        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=materialize_with_evidence,
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )
        real_stabilize = manager._stabilize_materializer_evidence
        parked = target / ".workflow-runtime" / "attacker-parked-materialization"
        external = self.base / "external-materializer-evidence"
        (external / retained_name).mkdir(parents=True)

        def swap_before_stabilize(
            materialized: object, bound: object, module_project: Path
        ) -> object:
            runtime = target / ".workflow-runtime" / "mipstarre-materialization"
            runtime.rename(parked)
            runtime.symlink_to(external, target_is_directory=True)
            return real_stabilize(materialized, bound, module_project)

        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=fake_module
        ), mock.patch.object(
            manager,
            "_stabilize_materializer_evidence",
            side_effect=swap_before_stabilize,
        ):
            with self.assertRaisesRegex(
                cache_module.CacheError, "evidence is unavailable|foundation preparation failed"
            ):
                manager.prepare(target)

        self.assertTrue((parked / retained_name).is_dir())
        self.assertTrue((external / retained_name).is_dir())

    def test_prepare_evidence_normalization_rejects_real_directory_replacement(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        target = self.issue_worktree("prepare-evidence-real-replacement")
        bound = manager._eligible_seed_target(target, check_inputs=False)
        retained_name = "MIPStarRE.transaction.retained-test"
        try:
            materialized = fake_materializer_evidence(bound.access_path, retained_name)
            bound.refresh_after_project_mutation()
            evidence = target / ".workflow-runtime" / "mipstarre-materialization" / retained_name
            parked = evidence.with_name("attacker-parked-retained")
            evidence.rename(parked)
            evidence.mkdir()
            with self.assertRaisesRegex(cache_module.CacheError, "evidence identity changed"):
                manager._stabilize_materializer_evidence(
                    materialized, bound, bound.access_path
                )
        finally:
            bound.close()

        self.assertTrue(parked.is_dir())
        self.assertTrue(evidence.is_dir())

    def test_prepare_evidence_rejects_same_inode_staged_descendant_mutation(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        target = self.issue_worktree("prepare-evidence-descendant-mutation")
        bound = manager._eligible_seed_target(target, check_inputs=False)
        retained_name = "MIPStarRE.transaction.retained-test"
        try:
            materialized = fake_materializer_evidence(
                bound.access_path, retained_name, staged_original=b"original"
            )
            bound.refresh_after_project_mutation()
            evidence = (
                target
                / ".workflow-runtime"
                / "mipstarre-materialization"
                / retained_name
            )
            original = evidence / "stage" / "MIPStarRE" / "original"
            inode_before = original.stat(follow_symlinks=False).st_ino
            original.write_bytes(b"modified")
            self.assertEqual(inode_before, original.stat(follow_symlinks=False).st_ino)
            with self.assertRaisesRegex(cache_module.CacheError, "inventory changed"):
                manager._stabilize_materializer_evidence(
                    materialized, bound, bound.access_path
                )
        finally:
            bound.close()
        self.assertEqual(b"modified", original.read_bytes())

    def test_prepare_evidence_rejects_post_inventory_descendant_mutation(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        target = self.issue_worktree("prepare-evidence-post-inventory")
        bound = manager._eligible_seed_target(target, check_inputs=False)
        retained_name = "MIPStarRE.transaction.retained-test"
        real_inventory = manager._materializer_evidence_inventory
        injected = False
        try:
            materialized = fake_materializer_evidence(
                bound.access_path, retained_name, staged_original=b"original"
            )
            bound.refresh_after_project_mutation()
            evidence = (
                target
                / ".workflow-runtime"
                / "mipstarre-materialization"
                / retained_name
            )
            original = evidence / "stage" / "MIPStarRE" / "original"

            def mutate_after_inventory(descriptor: int) -> dict[str, object]:
                nonlocal injected
                result = real_inventory(descriptor)
                if not injected:
                    injected = True
                    original.write_bytes(b"modified")
                return result

            with mock.patch.object(
                cache_module.HotMainCache,
                "_materializer_evidence_inventory",
                side_effect=mutate_after_inventory,
            ):
                with self.assertRaisesRegex(
                    cache_module.CacheError, "inventory changed|changed after normalization"
                ):
                    manager._stabilize_materializer_evidence(
                        materialized, bound, bound.access_path
                    )
        finally:
            bound.close()
        self.assertTrue(injected)
        self.assertEqual(b"modified", original.read_bytes())

    def test_prepare_rejects_authored_drift_before_foundation_verification(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-drift-worktree")
        archive = self.base / "foundation-drift.tar.gz"
        archive.write_bytes(b"authenticated")
        verified = mock.Mock()

        def drift(root: Path, *_args: object, **_kwargs: object) -> dict[str, str]:
            authored = root / "MIPStarRE" / "QPBT"
            authored.mkdir(parents=True)
            (authored / "Drift.lean").write_text("def drift := true\n", encoding="ascii")
            return {"status": "published"}

        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=drift,
            verify_materialized=verified,
        )
        with mock.patch.dict(os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True), \
             mock.patch.object(manager, "_preflight_authenticated_inputs", return_value={"required": True}), \
             mock.patch.object(manager, "_load_identity_module", return_value=fake_module):
            with self.assertRaisesRegex(cache_module.CacheError, "authored QPBT inventory changed"):
                manager.prepare(target)
        verified.assert_not_called()
        self.assertFalse((target / ".lake").exists())

    def test_prepare_authenticates_materializer_before_seed_publication(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        archive = self.base / "foundation-target-input.tar.gz"
        archive.write_bytes(b"authenticated")
        target = self.issue_worktree("prepare-materializer-before-publication")
        publish = mock.Mock(side_effect=AssertionError("seed publication ran"))
        with mock.patch.dict(
            os.environ,
            {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
            clear=True,
        ), mock.patch.object(
            manager,
            "_preflight_authenticated_inputs",
            return_value={"required": True},
        ), mock.patch.object(
            manager, "_publish_seed_locked", publish
        ), mock.patch.object(
            manager,
            "_load_identity_module",
            side_effect=cache_module.CacheError("injected authenticated module failure"),
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "authenticated module failure"):
                manager.prepare(target)
        publish.assert_not_called()
        self.assertFalse((target / ".lake").exists())

    def test_prepare_rejects_verifier_authored_mutation_and_restores_replaced_seed(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-verifier-mutation")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        archive = self.base / "foundation-verifier-mutation.tar.gz"
        archive.write_bytes(b"authenticated")

        def mutate_after_snapshot(_root: Path, _pin: object) -> dict[str, object]:
            evidence = cache_module.authored_tree_facts_on_disk(target)
            authored = target / "MIPStarRE" / "QPBT"
            authored.mkdir(parents=True, exist_ok=True)
            (authored / "VerifierDrift.lean").write_text(
                "def verifierDrift := true\n", encoding="ascii"
            )
            return {"status": "verified", **evidence}

        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=mutate_after_snapshot,
        )
        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=fake_module
        ):
            with self.assertRaisesRegex(
                cache_module.CacheError, "authored QPBT inventory changed|verifier evidence differs"
            ):
                manager.prepare(target, replace_seed=True)

        self.assertEqual(
            "preserve\n",
            (original_lake / "original-marker").read_text(encoding="ascii"),
        )
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertEqual([], list(target.glob(".lake-prepare-rollback-*")))

    def test_prepare_metric_failure_restores_replaced_seed(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-metric-failure")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        archive = self.base / "foundation-metric-failure.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)
        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )

        def fail_metric(_metric: object, *_args: object) -> None:
            staging = next(target.glob(".lake-seed-*"))
            self.assertTrue((staging / ".lake" / "original-marker").is_file())
            raise OSError("injected metric failure")

        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=fake_module
        ), mock.patch.object(manager, "_append_metric", side_effect=fail_metric):
            with self.assertRaisesRegex(cache_module.CacheError, "injected metric failure"):
                manager.prepare(target, replace_seed=True)

        self.assertEqual(
            "preserve\n", (original_lake / "original-marker").read_text(encoding="ascii")
        )
        self.assertEqual([], list(target.glob(".lake.backup-*")))

    def test_seed_failed_atomic_exchange_preserves_original(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-old-rename-failure")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        real_renameat2 = cache_module._linux_renameat2

        def fail_exchange(
            source_parent: int,
            source: str,
            destination_parent: int,
            destination: str,
            flags: int,
        ) -> None:
            if source == destination == ".lake" and flags == cache_module.RENAME_EXCHANGE:
                raise OSError("injected atomic exchange failure")
            real_renameat2(source_parent, source, destination_parent, destination, flags)

        with mock.patch.object(cache_module, "_linux_renameat2", side_effect=fail_exchange):
            with self.assertRaisesRegex(cache_module.CacheError, "atomic exchange failure"):
                manager.seed(target, replace=True)

        self.assertEqual(
            "preserve\n", (original_lake / "original-marker").read_text(encoding="ascii")
        )
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertEqual([], list(target.glob(".lake-seed-*")))

    def test_seed_interruption_immediately_after_publication_restores_original(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-publication-interruption")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")

        with mock.patch.object(
            manager,
            "_validate_seeded_destination",
            side_effect=[None, KeyboardInterrupt("injected post-publication interruption")],
        ):
            with self.assertRaises(KeyboardInterrupt):
                manager.seed(target, replace=True)

        self.assertEqual(
            "preserve\n", (original_lake / "original-marker").read_text(encoding="ascii")
        )
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        failed = next(target.glob(".lake.failed-*"))
        self.assertTrue((failed / ".lake" / "build" / "QPBT.olean").is_file())
        self.assertEqual([], list(target.glob(".lake-seed-*")))

    def test_prepare_publisher_handoff_interruption_restores_original(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-publication-handoff-interruption")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        publish = manager._publish_seed_locked
        archive = self.base / "foundation-handoff.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)
        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )

        def publish_then_interrupt(*args: object, **kwargs: object) -> object:
            publish(*args, **kwargs)
            raise KeyboardInterrupt("injected publisher handoff interruption")

        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=fake_module
        ), mock.patch.object(
            manager,
            "_publish_seed_locked",
            side_effect=publish_then_interrupt,
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "publisher handoff interruption"):
                manager.prepare(target, replace_seed=True)

        self.assertEqual(
            "preserve\n", (original_lake / "original-marker").read_text(encoding="ascii")
        )
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertEqual([], list(target.glob(".lake-seed-*")))
        self.assertEqual([], list(target.glob(".lake-prepare-rollback-*")))

    def test_seed_metric_failure_restores_replaced_seed(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-metric-failure")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")

        def fail_metric(_metric: object, *_args: object) -> None:
            staging = next(target.glob(".lake-seed-*"))
            self.assertTrue((staging / ".lake" / "original-marker").is_file())
            raise OSError("injected seed metric failure")

        with mock.patch.object(manager, "_append_metric", side_effect=fail_metric):
            with self.assertRaisesRegex(OSError, "injected seed metric failure"):
                manager.seed(target, replace=True)

        self.assertEqual(
            "preserve\n", (original_lake / "original-marker").read_text(encoding="ascii")
        )
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))

    def test_seed_metric_fsync_failure_rolls_back_metric_and_replaced_seed(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-metric-fsync-failure")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        real_fsync = cache_module.os.fsync
        calls = 0

        def fail_metric_fsync(descriptor: int) -> None:
            nonlocal calls
            try:
                opened = Path(os.readlink(f"/proc/self/fd/{descriptor}")).resolve()
            except OSError:
                opened = None
            if opened == manager.metrics_path.resolve():
                calls += 1
            if opened == manager.metrics_path.resolve() and calls == 1:
                raise OSError("injected metric fsync failure")
            real_fsync(descriptor)

        with mock.patch.object(cache_module.os, "fsync", side_effect=fail_metric_fsync):
            with self.assertRaisesRegex(OSError, "injected metric fsync failure"):
                manager.seed(target, replace=True)

        self.assertEqual("preserve\n", (original_lake / "original-marker").read_text(encoding="ascii"))
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertEqual([], list(target.glob(".lake-seed-*")))
        metrics = [
            json.loads(line)
            for line in (self.runtime / "metrics" / "hot-main.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual([], [item for item in metrics if item.get("result") == "seeded"])

    def test_seed_metric_short_write_rolls_back_metric_and_replaced_seed(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-metric-short-write")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        real_write = cache_module.os.write
        injected = False

        def short_metric_write(descriptor: int, payload: bytes) -> int:
            nonlocal injected
            try:
                opened = Path(os.readlink(f"/proc/self/fd/{descriptor}")).resolve()
            except OSError:
                opened = None
            if not injected and opened == manager.metrics_path.resolve():
                injected = True
                partial = max(1, len(payload) // 2)
                real_write(descriptor, payload[:partial])
                return partial
            return real_write(descriptor, payload)

        with mock.patch.object(cache_module.os, "write", side_effect=short_metric_write):
            with self.assertRaisesRegex(OSError, "short hot-cache metric write"):
                manager.seed(target, replace=True)

        self.assertEqual("preserve\n", (original_lake / "original-marker").read_text(encoding="ascii"))
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        metrics = [
            json.loads(line)
            for line in (self.runtime / "metrics" / "hot-main.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual([], [item for item in metrics if item.get("result") == "seeded"])
        self.assertEqual([], list(target.glob(".lake-seed-*")))

    def _assert_two_writer_metric_rollback_is_serialized(self, failure_mode: str) -> None:
        manager = self.manager()
        metrics_path = manager.metrics_path
        metrics_path.parent.mkdir(parents=True)
        baseline = b'{"baseline":true}\n'
        metrics_path.write_bytes(baseline)
        context = multiprocessing.get_context("fork")
        rollback_started = context.Event()
        release_rollback = context.Event()
        writer_b_started = context.Event()
        writer_b_completed = context.Event()
        outcome = context.Queue()
        expected_line = context.Queue()
        writer_a = context.Process(
            target=failing_metric_writer,
            args=(
                str(self.repo),
                str(self.runtime),
                failure_mode,
                rollback_started,
                release_rollback,
                outcome,
            ),
        )
        writer_b = context.Process(
            target=successful_metric_writer,
            args=(
                str(self.repo),
                str(self.runtime),
                writer_b_started,
                writer_b_completed,
                expected_line,
            ),
        )
        writer_a.start()
        self.assertTrue(rollback_started.wait(10))
        writer_b.start()
        self.assertTrue(writer_b_started.wait(10))
        expected = expected_line.get(timeout=10)
        self.assertFalse(writer_b_completed.wait(0.25))
        release_rollback.set()
        writer_a.join(10)
        writer_b.join(10)
        self.assertEqual(0, writer_a.exitcode)
        self.assertEqual(0, writer_b.exitcode)
        self.assertEqual("rolled-back", outcome.get(timeout=10))
        self.assertTrue(writer_b_completed.is_set())
        self.assertEqual(baseline + expected, metrics_path.read_bytes())
        for line in metrics_path.read_text(encoding="utf-8").splitlines():
            self.assertIsInstance(json.loads(line), dict)

    def test_two_writer_short_metric_write_preserves_committed_append(self) -> None:
        self._assert_two_writer_metric_rollback_is_serialized("short-write")

    def test_two_writer_metric_fsync_failure_preserves_committed_append(self) -> None:
        self._assert_two_writer_metric_rollback_is_serialized("fsync")

    def _assert_seed_metric_postcommit_cleanup_failure_commits(
        self,
        manager: cache_module.HotMainCache,
        target_name: str,
        cleanup_patch: object,
        message: str,
    ) -> None:
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree(target_name)
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")

        with cleanup_patch:
            result = manager.seed(target, replace=True)

        self.assertEqual("seeded", result["result"], message)
        self.assertTrue((original_lake / "build" / "QPBT.olean").is_file())
        self.assertFalse((original_lake / "original-marker").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertEqual([], list(target.glob(".lake-seed-*")))
        metrics = [
            json.loads(line)
            for line in (self.runtime / "metrics" / "hot-main.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(1, len([item for item in metrics if item.get("result") == "seeded"]))

    def test_seed_metric_descriptor_close_failure_is_postcommit(self) -> None:
        manager = self.manager()
        injected = False
        real_close = cache_module.os.close

        def fail_metric_close(descriptor: int) -> None:
            nonlocal injected
            try:
                opened = Path(os.readlink(f"/proc/self/fd/{descriptor}")).resolve()
            except OSError:
                opened = None
            if not injected and opened == manager.metrics_path.resolve():
                injected = True
                real_close(descriptor)
                raise OSError("injected metric descriptor close failure")
            real_close(descriptor)

        self._assert_seed_metric_postcommit_cleanup_failure_commits(
            manager,
            "seed-metric-descriptor-close-failure",
            mock.patch.object(cache_module.os, "close", side_effect=fail_metric_close),
            "metric descriptor close failure",
        )

    def test_seed_metric_unlock_failure_is_postcommit(self) -> None:
        manager = self.manager()
        injected = False
        real_flock = cache_module.fcntl.flock

        def fail_metric_unlock(descriptor: int, operation: int) -> None:
            nonlocal injected
            try:
                opened = Path(os.readlink(f"/proc/self/fd/{descriptor}")).resolve()
            except OSError:
                opened = None
            if (
                not injected
                and operation == fcntl.LOCK_UN
                and opened == manager.metrics_lock_path.resolve()
            ):
                injected = True
                raise OSError("injected metrics lock unlock failure")
            real_flock(descriptor, operation)

        self._assert_seed_metric_postcommit_cleanup_failure_commits(
            manager,
            "seed-metric-unlock-failure",
            mock.patch.object(cache_module.fcntl, "flock", side_effect=fail_metric_unlock),
            "metrics lock unlock failure",
        )

    def test_seed_metric_stream_close_failure_is_postcommit(self) -> None:
        manager = self.manager()
        injected = False
        real_exit = cache_module.ExclusiveLock.__exit__

        def fail_metric_stream_close(
            lock: cache_module.ExclusiveLock,
            exception_type: object,
            exception: object,
            traceback: object,
        ) -> None:
            nonlocal injected
            if not injected and lock.path == manager.metrics_lock_path:
                injected = True
                original_close = lock.stream.close

                def fail_close() -> None:
                    original_close()
                    raise OSError("injected metrics lock stream close failure")

                lock.stream.close = fail_close
                try:
                    real_exit(lock, exception_type, exception, traceback)
                finally:
                    lock.stream.close = original_close
                return
            real_exit(lock, exception_type, exception, traceback)

        self._assert_seed_metric_postcommit_cleanup_failure_commits(
            manager,
            "seed-metric-stream-close-failure",
            mock.patch.object(
                cache_module.ExclusiveLock, "__exit__", new=fail_metric_stream_close
            ),
            "metrics lock stream close failure",
        )

    def test_prepare_backup_cleanup_interruption_is_nonfatal_after_commit(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-backup-cleanup-interruption")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("old\n", encoding="ascii")
        archive = self.base / "foundation-backup-cleanup.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)
        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )
        real_rmtree = shutil.rmtree

        def interrupt_backup_cleanup(path: object, *args: object, **kwargs: object) -> None:
            if Path(path).name.startswith(".lake.backup-"):
                raise KeyboardInterrupt("injected backup cleanup interruption")
            real_rmtree(path, *args, **kwargs)

        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=fake_module
        ), mock.patch.object(cache_module.shutil, "rmtree", side_effect=interrupt_backup_cleanup):
            result = manager.prepare(target, replace_seed=True)

        self.assertEqual("prepared", result["result"])
        retained = result["seed"]["backup_retained"]
        self.assertIsNotNone(retained)
        self.assertTrue(Path(retained).is_dir())
        self.assertFalse((target / ".lake" / "original-marker").exists())

    def test_prepare_target_lock_excludes_distinct_identity_seed_until_final_checks(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-prepare-interleave",
            recipe=MATERIALIZING_TEST_RECIPE,
        )
        alternate_recipe = cache_module.BuildRecipe.for_testing(
            materialize_command=MATERIALIZING_TEST_RECIPE.materialize_command,
            dependency_command=MATERIALIZING_TEST_RECIPE.dependency_command,
            build_command=MATERIALIZING_TEST_RECIPE.build_command,
            additional_identity_files=MATERIALIZING_TEST_RECIPE.additional_identity_files,
            recipe_id="test-distinct-interleaving-cache",
            version=2,
        )
        alternate = self.manager(
            runtime=self.base / "runtime-prepare-interleave",
            recipe=alternate_recipe,
        )
        for cache in (manager, alternate):
            cache.warm(
                _test_command_callback=fake_success,
                _test_source_verifier=fake_source_verifier,
            )
        self.assertNotEqual(manager.identity.cache_key, alternate.identity.cache_key)
        target = self.issue_worktree("prepare-interleave-target")
        archive = self.base / "foundation-interleave.tar.gz"
        archive.write_bytes(b"authenticated")
        verifier_entered = threading.Event()
        release_verifier = threading.Event()
        seed_finished = threading.Event()
        failures: list[BaseException] = []
        seed_results: list[dict[str, object]] = []

        def blocking_verify(_root: Path, _pin: object) -> dict[str, object]:
            evidence = cache_module.authored_tree_facts_on_disk(target)
            verifier_entered.set()
            if not release_verifier.wait(5):
                raise AssertionError("interleaving regression timed out")
            return {"status": "verified", **evidence}

        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=blocking_verify,
        )

        def run_prepare() -> None:
            try:
                with mock.patch.dict(
                    os.environ,
                    {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                    clear=True,
                ), mock.patch.object(
                    manager,
                    "_preflight_authenticated_inputs",
                    return_value={"required": True},
                ), mock.patch.object(
                    manager, "_load_identity_module", return_value=fake_module
                ):
                    manager.prepare(target)
            except BaseException as error:
                failures.append(error)

        def run_seed() -> None:
            try:
                seed_results.append(alternate.seed(target, replace=True))
            except BaseException as error:
                failures.append(error)
            finally:
                seed_finished.set()

        prepare_thread = threading.Thread(target=run_prepare)
        seed_thread = threading.Thread(target=run_seed)
        prepare_thread.start()
        self.assertTrue(verifier_entered.wait(5), repr(failures))
        seed_thread.start()
        self.assertFalse(seed_finished.wait(0.2))
        release_verifier.set()
        prepare_thread.join(5)
        seed_thread.join(5)

        self.assertFalse(prepare_thread.is_alive())
        self.assertFalse(seed_thread.is_alive())
        self.assertEqual([], failures)
        self.assertTrue(seed_finished.is_set())
        self.assertEqual("seeded", seed_results[0]["result"])

    def test_mathlib_source_rejects_symlinked_git_internals_before_object_reads(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ):
            for name in ("objects", "refs", "HEAD", "config", "index"):
                with self.subTest(name=name):
                    original = source / ".git" / name
                    backup = source / ".git" / f"{name}.real"
                    original.rename(backup)
                    try:
                        if backup.is_dir():
                            original.symlink_to(backup, target_is_directory=True)
                        else:
                            original.symlink_to(backup)
                        with self.assertRaisesRegex(
                            cache_module.CacheError, "Git metadata|standalone|not a git repository"
                        ):
                            cache_module.validate_mathlib_source(source)
                    finally:
                        original.unlink(missing_ok=True)
                        backup.rename(original)

    def test_mathlib_source_rejects_executable_config_without_running_it(self) -> None:
        marker = self.base / "local-git-config-executed"
        command = f"/usr/bin/touch {marker}"
        vectors = (
            ("core.fsmonitor", command),
            ("core.hooksPath", str(self.base / "hostile-hooks")),
            ("filter.attack.clean", command),
            ("diff.attack.textconv", command),
            ("include.path", str(self.base / "hostile-include")),
        )
        for index, (key, value) in enumerate(vectors):
            with self.subTest(key=key):
                source = self.base / f"mathlib-config-{index}"
                commit, tree = initialize_mathlib_source(source)
                run_git(source, "config", key, value)
                with mock.patch.multiple(
                    cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
                ), self.assertRaisesRegex(
                    cache_module.CacheError, "configuration key is not allowed"
                ):
                    cache_module.validate_mathlib_source(source)
                self.assertFalse(marker.exists())

        source = self.base / "mathlib-ambient-config"
        commit, tree = initialize_mathlib_source(source)
        global_config = self.base / "hostile-global-gitconfig"
        global_config.write_text(
            f"[core]\n\tfsmonitor = {command}\n", encoding="utf-8"
        )
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ), mock.patch.dict(
            os.environ,
            {
                "GIT_CONFIG_GLOBAL": str(global_config),
                "GIT_CONFIG_SYSTEM": str(global_config),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.fsmonitor",
                "GIT_CONFIG_VALUE_0": command,
                "GIT_CONFIG_PARAMETERS": f"'core.fsmonitor={command}'",
                "GIT_DIR": str(source / ".git"),
                "GIT_WORK_TREE": str(source),
            },
            clear=False,
        ):
            facts = cache_module.validate_mathlib_source(source)
            trusted = cache_module._trusted_git_environment()
        self.assertEqual(commit, facts["commit"])
        self.assertEqual(os.devnull, trusted["GIT_CONFIG_GLOBAL"])
        self.assertNotIn("GIT_CONFIG_PARAMETERS", trusted)
        self.assertFalse(marker.exists())

    def test_mathlib_source_rejects_nested_special_and_common_git_metadata(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        git_dir = source / ".git"
        nested = git_dir / "objects" / "info" / "external-link"
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.symlink_to(source / "README.md")
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "contains a symlink"):
                cache_module.validate_mathlib_source(source)
            nested.unlink()

            fifo = git_dir / "objects" / "info" / "special-fifo"
            os.mkfifo(fifo)
            try:
                with self.assertRaisesRegex(cache_module.CacheError, "special entry"):
                    cache_module.validate_mathlib_source(source)
            finally:
                fifo.unlink()

            commondir = git_dir / "commondir"
            commondir.write_text("../external\n", encoding="ascii")
            try:
                with self.assertRaisesRegex(cache_module.CacheError, "common directory"):
                    cache_module.validate_mathlib_source(source)
            finally:
                commondir.unlink()

    def test_mathlib_source_rejects_hidden_index_visibility_flags(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        vectors = (
            ("--assume-unchanged", "--no-assume-unchanged"),
            ("--skip-worktree", "--no-skip-worktree"),
        )
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ):
            for enable, disable in vectors:
                with self.subTest(flag=enable):
                    run_git(source, "update-index", enable, "README.md")
                    try:
                        with self.assertRaisesRegex(
                            cache_module.CacheError, "visibility flags"
                        ):
                            cache_module.validate_mathlib_source(source)
                    finally:
                        run_git(source, "update-index", disable, "README.md")

    def test_mathlib_source_recheck_rejects_mid_build_repack(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ):
            facts = cache_module.validate_mathlib_source(source)
            self.assertIsNone(facts["pack_sha256"])
            binding = cache_module.MathlibSourceBinding(
                path=source,
                lake_url=source.as_uri(),
                evidence={"commit": commit, "tree": tree, **facts},
            )
            run_git(source, "gc", "--quiet")
            with self.assertRaisesRegex(cache_module.CacheError, "object pack changed"):
                cache_module.HotMainCache._verify_mathlib_source(binding)

    def test_mathlib_archive_materialization_authenticates_root_and_cleans_failures(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        shallow = self.base / "mathlib-shallow"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-tags", "--depth=1", f"file://{source}", str(shallow)],
            check=True,
            shell=False,
        )
        archive = self.base / "mathlib-fixture.tar.gz"
        facts = pack_mathlib_archive(shallow, archive)
        constants = {
            "MATHLIB_COMMIT": commit,
            "MATHLIB_TREE": tree,
            "MATHLIB_ARCHIVE_SHA256": facts["archive_sha256"],
            "MATHLIB_ARCHIVE_BYTES": facts["archive_bytes"],
            "MATHLIB_ARCHIVE_TAR_SHA256": facts["tar_sha256"],
            "MATHLIB_ARCHIVE_TAR_BYTES": facts["tar_bytes"],
        }
        with mock.patch.multiple(cache_module, **constants):
            destination = self.base / "extracted-mathlib"
            observed = cache_module.materialize_mathlib_archive(archive, destination)
            self.assertEqual(commit, observed["commit"])
            self.assertEqual(tree, observed["tree"])
            self.assertEqual("archive", observed["mode"])
            self.assertEqual(facts["archive_sha256"], observed["archive_sha256"])
            self.assertEqual(commit + "\n", (destination / ".git" / "shallow").read_text())
            cache_module.make_owner_writable(destination)
            shutil.rmtree(destination)

            damaged = self.base / "damaged-mathlib.tar.gz"
            payload = bytearray(archive.read_bytes())
            payload[-1] ^= 1
            damaged.write_bytes(payload)
            with self.assertRaisesRegex(cache_module.CacheError, "checksum|size"):
                cache_module.materialize_mathlib_archive(
                    damaged, self.base / "damaged-extracted"
                )
            self.assertFalse((self.base / "damaged-extracted").exists())

    def test_mathlib_archive_rejects_malformed_records_and_link_chains(self) -> None:
        def record(
            name: str,
            kind: bytes,
            *,
            linkname: str = "",
        ) -> tarfile.TarInfo:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.mode = 0o755 if kind == tarfile.DIRTYPE else 0o644
            member.linkname = linkname
            return member

        cases = (
            (
                "malformed-path",
                [
                    (record("mathlib", tarfile.DIRTYPE), None),
                    (record("mathlib/../escape", tarfile.REGTYPE), b"escape\n"),
                ],
                "unsafe Mathlib archive member path",
            ),
            (
                "duplicate",
                [
                    (record("mathlib", tarfile.DIRTYPE), None),
                    (record("mathlib", tarfile.DIRTYPE), None),
                ],
                "duplicate Mathlib archive member",
            ),
            (
                "hardlink",
                [
                    (record("mathlib", tarfile.DIRTYPE), None),
                    (
                        record(
                            "mathlib/hardlink",
                            tarfile.LNKTYPE,
                            linkname="mathlib/target",
                        ),
                        None,
                    ),
                ],
                "hardlink or special file",
            ),
            (
                "fifo",
                [
                    (record("mathlib", tarfile.DIRTYPE), None),
                    (record("mathlib/fifo", tarfile.FIFOTYPE), None),
                ],
                "hardlink or special file",
            ),
            (
                "transitive-symlink-escape",
                [
                    (record("mathlib", tarfile.DIRTYPE), None),
                    (record("mathlib/D", tarfile.SYMTYPE, linkname="."), None),
                    (record("mathlib/S", tarfile.SYMTYPE, linkname="D/.."), None),
                ],
                "symlink chain escapes",
            ),
            (
                "symlink-cycle",
                [
                    (record("mathlib", tarfile.DIRTYPE), None),
                    (record("mathlib/A", tarfile.SYMTYPE, linkname="B"), None),
                    (record("mathlib/B", tarfile.SYMTYPE, linkname="A"), None),
                ],
                "symlink graph contains a cycle",
            ),
        )
        for name, members, error in cases:
            with self.subTest(case=name):
                archive = self.base / f"{name}.tar.gz"
                facts = pack_mathlib_tar_members(archive, members)
                destination = self.base / f"{name}-extracted"
                with mock.patch.multiple(
                    cache_module,
                    MATHLIB_ARCHIVE_SHA256=facts["archive_sha256"],
                    MATHLIB_ARCHIVE_BYTES=facts["archive_bytes"],
                    MATHLIB_ARCHIVE_TAR_SHA256=facts["tar_sha256"],
                    MATHLIB_ARCHIVE_TAR_BYTES=facts["tar_bytes"],
                ), self.assertRaisesRegex(cache_module.CacheError, error):
                    cache_module.materialize_mathlib_archive(archive, destination)
                self.assertFalse(destination.exists())

    def test_pinned_mathlib_archive_regression(self) -> None:
        archive = Path("/tmp/mathlib-81a5d257-shallow-repo.tar.gz")
        if not archive.is_file():
            self.skipTest(f"pinned audit archive is unavailable: {archive}")
        destination = self.base / "pinned-mathlib"
        started = time.monotonic()
        facts = cache_module.materialize_mathlib_archive(archive, destination)
        self.assertEqual(cache_module.MATHLIB_COMMIT, facts["commit"])
        self.assertEqual(cache_module.MATHLIB_TREE, facts["tree"])
        self.assertEqual(
            "4659f2a0cabfec474474f5e83ea3d495e711b735418742dd3d642328adcada02",
            facts["pack_sha256"],
        )
        self.assertEqual(27_574_578, facts["pack_bytes"])
        self.assertLess(time.monotonic() - started, 60)
        cache_module.make_owner_writable(destination)
        shutil.rmtree(destination)

    def test_warm_constructs_local_lake_map_and_preserves_key(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        alternate = self.base / "mathlib-source-alternate"
        shutil.copytree(source, alternate, symlinks=True)
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ), mock.patch.object(
            cache_module, "CANONICAL_BUILD_RECIPE", PRODUCTION_SETUP_PROBE_RECIPE
        ):
            manager = cache_module.HotMainCache(self.repo, self.repo, self.runtime)
            original_run = manager._run_logged
            lake_environments: list[dict[str, str]] = []
            setup_environments: list[dict[str, str] | None] = []

            def fake_run(
                root: Path,
                command: list[str] | tuple[str, ...],
                log_path: Path,
                *,
                environment: dict[str, str] | None = None,
            ) -> int:
                if command[0] == "git":
                    return original_run(root, command, log_path, environment=environment)
                if command[0] == "python3":
                    setup_environments.append(environment)
                    return 0
                if command[0] == "lake":
                    self.assertIsNotNone(environment)
                    lake_environments.append(dict(environment or {}))
                    if command[-1] == "build":
                        build = root / ".lake" / "build"
                        build.mkdir(parents=True, exist_ok=True)
                        (build / "QPBT.olean").write_text("probe\n", encoding="ascii")
                    return 0
                raise AssertionError(f"unexpected command: {command}")

            with mock.patch.dict(
                os.environ,
                {
                    cache_module.MATHLIB_SOURCE_ENV: str(source),
                    "LAKE_PKG_URL_MAP": "",
                },
                clear=False,
            ), mock.patch.object(manager, "_run_logged", side_effect=fake_run), \
                 mock.patch.object(manager, "_preflight_authenticated_inputs", side_effect=lambda: manager._preflight_mathlib_input()):
                os.environ.pop(cache_module.MATHLIB_ARCHIVE_ENV, None)
                built = manager.warm()
                self.assertEqual("built", built["result"])
                self.assertTrue(manager.is_ready(deep=True))
                manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
                self.assertEqual("source", manifest["mathlib_source"]["mode"])
                self.assertNotIn(str(source), json.dumps(manifest["mathlib_source"]))
                self.assertEqual(2, len(lake_environments))
                self.assertEqual([None, None, None], setup_environments)
                for environment in lake_environments:
                    self.assertEqual(
                        '{"mathlib":"%s"}' % source.as_uri(),
                        environment["LAKE_PKG_URL_MAP"],
                    )

                alternate_manager = cache_module.HotMainCache(
                    self.repo, self.repo, self.runtime
                )
                with mock.patch.dict(
                    os.environ,
                    {cache_module.MATHLIB_SOURCE_ENV: str(alternate)},
                    clear=False,
                ), mock.patch.object(
                    alternate_manager, "_preflight_authenticated_inputs",
                    side_effect=lambda: alternate_manager._preflight_mathlib_input(),
                ):
                    hit = alternate_manager.warm()
                self.assertEqual("hit", hit["result"])
                self.assertEqual(manager.identity.cache_key, alternate_manager.identity.cache_key)

    def test_warm_archive_input_is_staged_and_not_published(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        shallow = self.base / "mathlib-shallow-warm"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-tags", "--depth=1", f"file://{source}", str(shallow)],
            check=True,
            shell=False,
        )
        archive = self.base / "mathlib-warm.tar.gz"
        facts = pack_mathlib_archive(shallow, archive)
        constants = {
            "MATHLIB_COMMIT": commit,
            "MATHLIB_TREE": tree,
            "MATHLIB_ARCHIVE_SHA256": facts["archive_sha256"],
            "MATHLIB_ARCHIVE_BYTES": facts["archive_bytes"],
            "MATHLIB_ARCHIVE_TAR_SHA256": facts["tar_sha256"],
            "MATHLIB_ARCHIVE_TAR_BYTES": facts["tar_bytes"],
        }
        with mock.patch.multiple(cache_module, **constants), mock.patch.object(
            cache_module, "CANONICAL_BUILD_RECIPE", PRODUCTION_PROBE_RECIPE
        ):
            manager = cache_module.HotMainCache(
                self.repo, self.repo, self.base / "archive-warm-runtime"
            )
            original_run = manager._run_logged
            lake_urls: list[str] = []

            def fake_run(
                root: Path,
                command: list[str] | tuple[str, ...],
                log_path: Path,
                *,
                environment: dict[str, str] | None = None,
            ) -> int:
                if command[0] == "git":
                    return original_run(root, command, log_path, environment=environment)
                if command[0] == "lake":
                    lake_urls.append((environment or {})["LAKE_PKG_URL_MAP"])
                    if command[-1] == "build":
                        build = root / ".lake" / "build"
                        build.mkdir(parents=True, exist_ok=True)
                        (build / "QPBT.olean").write_text("archive\n", encoding="ascii")
                    return 0
                raise AssertionError(f"unexpected command: {command}")

            with mock.patch.dict(
                os.environ,
                {
                    cache_module.MATHLIB_ARCHIVE_ENV: str(archive),
                    "LAKE_PKG_URL_MAP": "",
                },
                clear=False,
            ), mock.patch.object(manager, "_run_logged", side_effect=fake_run), \
                 mock.patch.object(manager, "_preflight_authenticated_inputs", side_effect=lambda: manager._preflight_mathlib_input()):
                os.environ.pop(cache_module.MATHLIB_SOURCE_ENV, None)
                built = manager.warm()
            self.assertEqual("built", built["result"])
            self.assertTrue(manager.is_ready(deep=True))
            manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("archive", manifest["mathlib_source"]["mode"])
            self.assertEqual(facts["archive_sha256"], manifest["mathlib_source"]["archive_sha256"])
            self.assertFalse((manager.snapshot_dir / "mathlib-source").exists())
            self.assertEqual(2, len(lake_urls))
            self.assertTrue(all('"mathlib":"file://' in value for value in lake_urls))

    def test_warm_surfaces_reservoir_cache_failure_without_ready(self) -> None:
        source, commit, tree = self.mathlib_fixture()
        failure_runtime = self.base / "reservoir-runtime"
        with mock.patch.multiple(
            cache_module, MATHLIB_COMMIT=commit, MATHLIB_TREE=tree
        ), mock.patch.object(
            cache_module, "CANONICAL_BUILD_RECIPE", PRODUCTION_PROBE_RECIPE
        ):
            manager = cache_module.HotMainCache(self.repo, self.repo, failure_runtime)
            original_run = manager._run_logged

            def fail_reservoir(
                root: Path,
                command: list[str] | tuple[str, ...],
                log_path: Path,
                *,
                environment: dict[str, str] | None = None,
            ) -> int:
                if command[0] == "git":
                    return original_run(root, command, log_path, environment=environment)
                if command[-3:] == ("exe", "cache", "get"):
                    self.assertEqual(
                        '{"mathlib":"%s"}' % source.as_uri(),
                        (environment or {})["LAKE_PKG_URL_MAP"],
                    )
                    return 17
                raise AssertionError(f"unexpected command: {command}")

            with mock.patch.dict(
                os.environ,
                {
                    cache_module.MATHLIB_SOURCE_ENV: str(source),
                    "LAKE_PKG_URL_MAP": "",
                },
                clear=False,
            ), mock.patch.object(manager, "_run_logged", side_effect=fail_reservoir), \
                 mock.patch.object(manager, "_preflight_authenticated_inputs", side_effect=lambda: manager._preflight_mathlib_input()):
                os.environ.pop(cache_module.MATHLIB_ARCHIVE_ENV, None)
                with self.assertRaisesRegex(
                    cache_module.CacheError, "dependency cache command failed"
                ):
                    manager.warm()
            self.assertFalse(manager.is_ready())
            self.assertEqual([], list(failure_runtime.rglob("READY")))
            failures = list((failure_runtime / "cache" / "failures").iterdir())
            self.assertEqual(1, len(failures))
            failure = json.loads((failures[0] / "failure.json").read_text(encoding="utf-8"))
            self.assertEqual("source", failure["mathlib_source"]["mode"])
            self.assertIn("dependency cache command failed", failure["error"])

    def test_warm_rejects_post_build_materialized_source_drift(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-materialized-drift",
            recipe=MATERIALIZING_TEST_RECIPE,
        )

        def mutate_source(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                with log_path.open("ab") as log:
                    log.write(b"build completed before source verification\n")
                (project / "MIPStarRE" / "materialized-marker").write_text(
                    "tampered\n", encoding="utf-8"
                )
            return result

        with self.assertRaisesRegex(cache_module.CacheError, "source verification failed"):
            manager.warm(
                _test_command_callback=mutate_source,
                _test_source_verifier=fake_source_verifier,
            )
        self.assertFalse(manager.is_ready())
        failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        self.assertTrue((failures[0] / "build.log").is_file())
        failure = json.loads((failures[0] / "failure.json").read_text(encoding="utf-8"))
        self.assertIn("source verification failed", failure["error"])

    def test_warm_rejects_build_created_untracked_qpbt_source(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-untracked-qpbt",
            recipe=MATERIALIZING_TEST_RECIPE,
        )

        def generate_source(
            project: Path, command: list[str] | tuple[str, ...], log_path: Path
        ) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                authored = project / "MIPStarRE" / "QPBT"
                authored.mkdir()
                (authored / "Generated.lean").write_text(
                    "def generated := true\n", encoding="utf-8"
                )
            return result

        with self.assertRaisesRegex(cache_module.CacheError, "after_build"):
            manager.warm(
                _test_command_callback=generate_source,
                _test_source_verifier=fake_source_verifier,
            )
        self.assertFalse(manager.is_ready())

    def test_committed_authored_qpbt_tree_is_bound_into_cache_identity(self) -> None:
        before = self.manager(recipe=MATERIALIZING_TEST_RECIPE).identity
        authored = self.repo / "MIPStarRE" / "QPBT"
        authored.mkdir()
        payload = b"def committed := true\n"
        (authored / "Committed.lean").write_bytes(payload)
        run_git(self.repo, "add", "MIPStarRE/QPBT/Committed.lean")
        run_git(self.repo, "commit", "-m", "add committed QPBT source")
        after = self.manager(recipe=MATERIALIZING_TEST_RECIPE).identity
        self.assertNotEqual(before.cache_key, after.cache_key)
        self.assertEqual(1, after.source_contract["authored_qpbt_files"])
        self.assertEqual(len(payload), after.source_contract["authored_qpbt_bytes"])

    def test_ready_and_seed_require_valid_source_evidence(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-source-evidence",
            recipe=MATERIALIZING_TEST_RECIPE,
        )
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("source-evidence-target")
        cache_module.make_owner_writable(manager.snapshot_dir)
        manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        manifest["source_evidence"]["inventory_sha256"] = "invalid"
        manager.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        manager.ready_path.write_text(
            cache_module.sha256_file(manager.manifest_path) + "\n", encoding="ascii"
        )
        self.assertFalse(manager.is_ready())
        with self.assertRaisesRegex(cache_module.CacheError, "deep artifact verification"):
            manager.seed(target)

    def test_ready_rejects_valid_shaped_semantic_source_evidence_tampering(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-semantic-source-evidence",
            recipe=MATERIALIZING_TEST_RECIPE,
        )
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        cache_module.make_owner_writable(manager.snapshot_dir)
        original = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        mutations = {
            "source_commit": "2" * 40,
            "inventory_sha256": "2" * 64,
            "files": original["source_evidence"]["files"] + 1,
            "bytes": original["source_evidence"]["bytes"] + 1,
            "authored_qpbt_files": 1,
            "authored_qpbt_bytes": 1,
            "authored_qpbt_sha256": "2" * 64,
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                manifest = json.loads(json.dumps(original))
                manifest["source_evidence"][field] = replacement
                manager.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                manager.ready_path.write_text(
                    cache_module.sha256_file(manager.manifest_path) + "\n", encoding="ascii"
                )
                self.assertFalse(manager.is_ready(deep=True))

    def test_seed_rechecks_source_evidence_after_copy(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-seed-source-race",
            recipe=MATERIALIZING_TEST_RECIPE,
        )
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("seed-source-race-target")
        original_copy = cache_module.reflink_copytree

        def copy_then_tamper(
            source: Path, destination: Path, **options: object
        ) -> cache_module.CopyStats:
            copied = original_copy(source, destination, **options)
            cache_module.make_owner_writable(manager.snapshot_dir)
            manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
            manifest["source_evidence"]["pin_sha256"] = "0" * 64
            manager.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            manager.ready_path.write_text(
                cache_module.sha256_file(manager.manifest_path) + "\n", encoding="ascii"
            )
            return copied

        with mock.patch.object(cache_module, "reflink_copytree", side_effect=copy_then_tamper):
            with self.assertRaisesRegex(cache_module.CacheError, "lost source evidence"):
                manager.seed(target)
        self.assertFalse((target / ".lake").exists())

    def test_failed_build_is_retained_but_never_published(self) -> None:
        manager = self.manager()

        def fail(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            if list(command) == ["fake", "build"]:
                return 7
            return fake_success(project, command, log_path)

        with self.assertRaises(cache_module.CacheError):
            manager.warm(_test_command_callback=fail)
        self.assertFalse(manager.is_ready())
        failures = list((self.runtime / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        self.assertFalse((failures[0] / "READY").exists())

    def test_seed_refuses_existing_or_missing_target(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("issue")
        (target / ".lake").mkdir()
        with self.assertRaises(cache_module.CacheError):
            manager.seed(target)
        with self.assertRaises(cache_module.CacheError):
            manager.seed(self.base / "typo")

    def test_recipe_is_bound_to_identity_and_readiness(self) -> None:
        test_manager = self.manager()
        canonical = cache_module.HotMainCache(self.repo, self.repo, self.runtime)
        self.assertNotEqual(test_manager.identity.cache_key, canonical.identity.cache_key)
        self.assertTrue(test_manager.identity.recipe["test_only"])
        self.assertFalse(canonical.identity.recipe["test_only"])

        with self.assertRaisesRegex(cache_module.CacheError, "test recipe"):
            canonical.warm(_test_command_callback=fake_success)
        self.assertFalse(canonical.is_ready())

        test_manager.warm(_test_command_callback=fake_success)
        manifest = json.loads(test_manager.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(test_manager.identity.recipe, manifest["recipe"])
        cache_module.make_owner_writable(test_manager.snapshot_dir)
        manifest["recipe"]["version"] += 1
        test_manager.manifest_path.write_text(
            __import__("json").dumps(manifest),
            encoding="utf-8",
        )
        self.assertFalse(test_manager.is_ready())

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cache_module.build_parser().parse_args(["warm", "--build-command", "true"])

    def test_seed_deeply_rejects_corrupted_published_artifact(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-corrupt")
        manager.warm(_test_command_callback=fake_success)
        self.assertTrue(manager.is_ready())
        cache_module.make_owner_writable(manager.lake_dir)
        artifact = manager.build_dir / "QPBT.olean"
        artifact.write_text("corrupted\n", encoding="utf-8")
        self.assertTrue(manager.is_ready())
        self.assertFalse(manager.is_ready(deep=True))
        target = self.issue_worktree("corrupt-target")
        with self.assertRaisesRegex(cache_module.CacheError, "deep artifact verification"):
            manager.seed(target)

    def test_ready_marker_binds_manifest_bytes(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-ready")
        manager.warm(_test_command_callback=fake_success)
        manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        cache_module.make_owner_writable(manager.snapshot_dir)
        manifest["created_at"] = "tampered"
        manager.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertFalse(manager.is_ready())

    def test_warm_rechecks_key_inputs_after_build(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-pins")

        def mutate_pin(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                (project / "lakefile.toml").write_text("changed during build\n", encoding="utf-8")
            return result

        with self.assertRaisesRegex(cache_module.CacheError, "cache-key inputs changed"):
            manager.warm(_test_command_callback=mutate_pin)
        self.assertFalse(manager.is_ready())

    def test_warm_rejects_post_build_tracked_source_changes(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-source")

        def mutate_source(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                (project / "MIPStarRE" / "Basic.lean").write_text(
                    "def answer := 99\n",
                    encoding="utf-8",
                )
            return result

        with self.assertRaisesRegex(cache_module.CacheError, "project source changed"):
            manager.warm(_test_command_callback=mutate_source)
        self.assertFalse(manager.is_ready())

    def test_seed_rejects_wrong_or_incompatible_worktrees(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)

        unregistered = self.base / "unregistered"
        unregistered.mkdir()
        for source in ("lean-toolchain", "lakefile.toml", "lake-manifest.json"):
            shutil.copy2(self.repo / source, unregistered / source)
        with self.assertRaisesRegex(cache_module.CacheError, "registered Git worktree"):
            manager.seed(unregistered)
        with self.assertRaisesRegex(cache_module.CacheError, "main worktree"):
            manager.seed(self.repo)

        incompatible = self.issue_worktree("incompatible")
        (incompatible / "lean-toolchain").write_text("different toolchain\n", encoding="utf-8")
        with self.assertRaisesRegex(cache_module.CacheError, "incompatible"):
            manager.seed(incompatible)

        stale = self.issue_worktree("stale")
        stale.rename(self.base / "stale-original")
        stale.mkdir()
        for source in ("lean-toolchain", "lakefile.toml", "lake-manifest.json"):
            shutil.copy2(self.repo / source, stale / source)
        with self.assertRaisesRegex(cache_module.CacheError, "live Git worktree"):
            manager.seed(stale)

    def test_seed_admission_ignores_ambient_git_worktree_and_config(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("ambient-git-target")
        hostile = {
            "GIT_WORK_TREE": str(self.base / "unrelated-worktree"),
            "GIT_DIR": str(self.base / "unrelated-git-dir"),
            "GIT_CONFIG_GLOBAL": str(self.base / "hostile-global-config"),
            "GIT_CONFIG_SYSTEM": str(self.base / "hostile-system-config"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.fsmonitor",
            "GIT_CONFIG_VALUE_0": "touch hostile-marker",
            "GIT_CONFIG_PARAMETERS": "'core.fsmonitor=touch hostile-marker'",
        }
        with mock.patch.dict(os.environ, hostile, clear=False):
            result = manager.seed(target)
        self.assertEqual("seeded", result["result"])

    def test_seed_rejects_symlink_component_before_resolution(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        real_parent = self.base / "real-parent"
        target = real_parent / "issue"
        run_git(self.repo, "worktree", "add", "--detach", str(target), self.commit)
        alias_parent = self.base / "alias-parent"
        alias_parent.symlink_to(real_parent, target_is_directory=True)

        with self.assertRaisesRegex(cache_module.CacheError, "symlink component"):
            manager.seed(alias_parent / "issue")

    def test_seed_replace_rolls_back_original_on_post_publish_failure(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("rollback")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_text("keep me\n", encoding="utf-8")

        with mock.patch.object(
            manager,
            "_validate_seeded_destination",
            side_effect=cache_module.CacheError("injected validation failure"),
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "injected validation failure"):
                manager.seed(target, replace=True)

        self.assertEqual("keep me\n", (original / "original-marker").read_text(encoding="utf-8"))
        self.assertFalse((original / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertEqual([], list(target.glob(".lake-seed-*")))

    def _crash_seed_after_atomic_publication(
        self,
        manager: cache_module.HotMainCache,
        target: Path,
    ) -> None:
        real_renameat2 = cache_module._linux_renameat2
        context = multiprocessing.get_context("fork")

        def interrupted_seed() -> None:
            def kill_at_boundary(
                source_parent: int,
                source: str,
                destination_parent: int,
                destination: str,
                flags: int,
            ) -> None:
                real_renameat2(source_parent, source, destination_parent, destination, flags)
                if source == destination == ".lake":
                    os.kill(os.getpid(), signal.SIGKILL)

            cache_module._linux_renameat2 = kill_at_boundary
            manager.seed(target, replace=True)

        process = context.Process(target=interrupted_seed)
        process.start()
        process.join(10)
        self.assertEqual(-signal.SIGKILL, process.exitcode)

    def test_seed_rejects_unowned_backup_decoys_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        for destination_present in (False, True):
            with self.subTest(destination_present=destination_present):
                target = self.issue_worktree(f"unowned-backup-{destination_present}")
                destination = target / ".lake"
                if destination_present:
                    destination.mkdir()
                    (destination / "current-user-bytes").write_bytes(b"current")
                backup = target / ".lake.backup-manual"
                backup.mkdir()
                (backup / "decoy-bytes").write_bytes(b"decoy")
                with self.assertRaisesRegex(
                    cache_module.CacheError, "no independent ownership proof"
                ):
                    manager.seed(target)
                self.assertEqual(b"decoy", (backup / "decoy-bytes").read_bytes())
                if destination_present:
                    self.assertEqual(
                        b"current", (destination / "current-user-bytes").read_bytes()
                    )
                else:
                    self.assertFalse(destination.exists())

    def test_seed_rejects_self_consistent_unowned_committed_journal_byte_exact(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("unowned-self-consistent-journal")
        destination = target / ".lake"
        destination.mkdir()
        (destination / "current").write_bytes(b"current bytes\n")
        transaction_id = "a" * 32
        backup = target / f".lake.backup-{transaction_id}"
        backup.mkdir()
        (backup / "claimed-original").write_bytes(b"claimed original bytes\n")
        journal_dir = manager._seed_transaction_dir(target)
        journal_dir.mkdir(parents=True)
        value = {
            "schema_version": 1,
            "transaction_version": 1,
            "transaction_id": transaction_id,
            "target_project": str(target),
            "destination": str(destination),
            "target_lock_digest": manager._seed_target_digest(target),
            "replace": True,
            "backup_basename": backup.name,
            "staging_basename": f".lake-seed-{transaction_id}",
            "retained_basename": f".lake.retained-{transaction_id}",
            "original": manager._lake_tree_identity(backup),
            "replacement": manager._lake_tree_identity(destination),
            "cache_key": manager.identity.cache_key,
            "main_commit": manager.identity.main_commit,
            "cache_manifest_sha256": cache_module.sha256_file(manager.manifest_path),
        }
        payload = manager._journal_bytes(value)
        digest = hashlib.sha256(payload).hexdigest()
        (journal_dir / "journal.json").write_bytes(payload)
        (journal_dir / "journal.sha256").write_text(digest + "\n", encoding="ascii")
        (journal_dir / "COMMITTED").write_text(digest + "\n", encoding="ascii")
        target_before = byte_snapshot(target)
        journal_before = byte_snapshot(journal_dir)

        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target, replace=True)

        target_after = byte_snapshot(target)
        for relative, facts in target_before.items():
            if relative != ".":
                self.assertEqual(facts, target_after[relative])
        self.assertEqual(journal_before, byte_snapshot(journal_dir))

    def _swap_worktree_aba(self, target: Path, substitute: Path) -> None:
        parked = target.with_name(target.name + "-parked")
        os.replace(target, parked)
        os.replace(substitute, target)
        os.replace(target, substitute)
        os.replace(parked, target)

    def test_seed_rejects_target_swap_restore_during_copy_without_changing_either(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-target-aba")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original").write_bytes(b"original\n")
        substitute = self.base / "seed-target-aba-substitute"
        substitute.mkdir()
        (substitute / ".lake").mkdir()
        (substitute / ".lake" / "substitute").write_bytes(b"substitute\n")
        target_before = byte_snapshot(target)
        substitute_before = byte_snapshot(substitute)
        real_copy = cache_module.reflink_copytree

        def copy_after_aba(source: Path, destination: Path, **options: object) -> object:
            self._swap_worktree_aba(target, substitute)
            return real_copy(source, destination, **options)

        with mock.patch.object(cache_module, "reflink_copytree", side_effect=copy_after_aba):
            with self.assertRaisesRegex(cache_module.CacheError, "identity changed|namespace changed"):
                manager.seed(target, replace=True)

        target_after = byte_snapshot(target)
        for relative, facts in target_before.items():
            if relative != ".":
                self.assertEqual(facts, target_after[relative])
        self.assertEqual(substitute_before, byte_snapshot(substitute))

    def test_seed_rejects_target_swap_restore_during_recovery_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-recovery-target-aba")
        substitute = self.base / "seed-recovery-target-aba-substitute"
        substitute.mkdir()
        (substitute / "substitute").write_bytes(b"substitute\n")
        target_before = byte_snapshot(target)
        substitute_before = byte_snapshot(substitute)
        real_recover = manager._recover_interrupted_seed

        def recover_after_aba(bound: object) -> None:
            self._swap_worktree_aba(target, substitute)
            real_recover(bound)

        with mock.patch.object(
            manager, "_recover_interrupted_seed", side_effect=recover_after_aba
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "identity changed|namespace changed"):
                manager.seed(target)

        self.assertEqual(target_before, byte_snapshot(target))
        self.assertEqual(substitute_before, byte_snapshot(substitute))

    def test_seed_rejects_target_swap_restore_during_validation_byte_exact(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-validation-target-aba")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original").write_bytes(b"original\n")
        substitute = self.base / "seed-validation-target-aba-substitute"
        substitute.mkdir()
        (substitute / ".lake").mkdir()
        (substitute / ".lake" / "substitute").write_bytes(b"substitute\n")
        target_before = byte_snapshot(target)
        substitute_before = byte_snapshot(substitute)
        real_validate = manager._validate_seeded_destination
        calls = 0

        def validate_then_aba(destination: Path) -> None:
            nonlocal calls
            real_validate(destination)
            calls += 1
            if calls == 1:
                self._swap_worktree_aba(target, substitute)

        with mock.patch.object(
            manager, "_validate_seeded_destination", side_effect=validate_then_aba
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "identity changed|namespace changed"):
                manager.seed(target, replace=True)

        target_after = byte_snapshot(target)
        for relative, facts in target_before.items():
            if relative != ".":
                self.assertEqual(facts, target_after[relative])
        self.assertEqual(substitute_before, byte_snapshot(substitute))

    def test_seed_rejects_target_swap_restore_at_metric_commit_byte_exact(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-metric-target-aba")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original").write_bytes(b"original\n")
        substitute = self.base / "seed-metric-target-aba-substitute"
        substitute.mkdir()
        (substitute / ".lake").mkdir()
        (substitute / ".lake" / "substitute").write_bytes(b"substitute\n")
        target_before = byte_snapshot(target)
        substitute_before = byte_snapshot(substitute)
        real_append = manager._append_metric

        def append_after_aba(metric: object, guard: object) -> None:
            self._swap_worktree_aba(target, substitute)
            real_append(metric, guard)

        with mock.patch.object(manager, "_append_metric", side_effect=append_after_aba):
            with self.assertRaisesRegex(cache_module.CacheError, "identity changed|namespace changed"):
                manager.seed(target, replace=True)

        staging = next(target.glob(".lake-seed-*")) / ".lake"
        self.assertEqual(snapshot_subtree(target_before, ".lake"), byte_snapshot(staging))
        target_after = byte_snapshot(target)
        for relative, facts in target_before.items():
            if relative != "." and not relative.startswith(".lake"):
                self.assertEqual(facts, target_after[relative])
        self.assertEqual(substitute_before, byte_snapshot(substitute))

    def test_seed_atomic_exchange_crash_requires_manual_recovery_unchanged(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-replace-false")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target)
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"keep", (backup / "original-marker").read_bytes())

    def test_seed_recovers_before_invalid_cache_admission(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-invalid-cache")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        cache_module.make_owner_writable(manager.snapshot_dir)
        manager.ready_path.write_text("0" * 64 + "\n", encoding="ascii")
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target, replace=True)
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"keep", (backup / "original-marker").read_bytes())

    def test_prepare_recovers_before_input_admission(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-invalid-input")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        with mock.patch.object(
            manager,
            "_preflight_authenticated_inputs",
            side_effect=cache_module.CacheError("injected input admission failure"),
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
                manager.prepare(target, replace_seed=True)
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"keep", (backup / "original-marker").read_bytes())

    def test_seed_rejects_tampered_journal_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-tampered")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        journal = manager._seed_transaction_dir(target) / "journal.json"
        journal.write_bytes(journal.read_bytes().replace(b'"replace":true', b'"replace":false'))
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target, replace=True)
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"keep", (backup / "original-marker").read_bytes())

    def test_seed_rejects_wrong_backup_identity_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-wrong-backup")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        (backup / "unrecorded").write_bytes(b"changed")
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target, replace=True)
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"changed", (backup / "unrecorded").read_bytes())

    def test_seed_rejects_extra_backup_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-extra-backup")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        owned = next(target.glob(".lake-seed-*")) / ".lake"
        extra = target / ".lake.backup-extra"
        extra.mkdir()
        (extra / "decoy").write_bytes(b"decoy")
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target, replace=True)
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"keep", (owned / "original-marker").read_bytes())
        self.assertEqual(b"decoy", (extra / "decoy").read_bytes())

    def test_seed_atomic_exchange_never_has_absent_destination(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-second-rename")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_atomic_publication(manager, target)
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target)
        self.assertTrue((original / "build" / "QPBT.olean").is_file())
        self.assertEqual(b"keep", (backup / "original-marker").read_bytes())
        self.assertEqual([], list(target.glob(".lake.retained-*")))

    def test_seed_metric_commit_recovers_before_commit_marker(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-metric-commit")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"old")
        context = multiprocessing.get_context("fork")

        def interrupted_seed() -> None:
            with mock.patch.object(
                manager,
                "_mark_seed_committed",
                side_effect=lambda _replacement: os.kill(os.getpid(), signal.SIGKILL),
            ):
                manager.seed(target, replace=True)

        process = context.Process(target=interrupted_seed)
        process.start()
        process.join(10)
        self.assertEqual(-signal.SIGKILL, process.exitcode)
        self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())
        backup = next(target.glob(".lake-seed-*")) / ".lake"
        with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
            manager.seed(target)
        self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())
        self.assertFalse((target / ".lake" / "original-marker").exists())
        self.assertEqual(b"old", (backup / "original-marker").read_bytes())
        self.assertTrue(manager._seed_transaction_dir(target).exists())

    def test_prepare_rejects_target_swap_restore_during_materialization_byte_exact(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-target-aba")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original").write_bytes(b"original\n")
        substitute = self.base / "prepare-target-aba-substitute"
        substitute.mkdir()
        (substitute / ".lake").mkdir()
        (substitute / ".lake" / "substitute").write_bytes(b"substitute\n")
        target_before = byte_snapshot(target)
        substitute_before = byte_snapshot(substitute)
        archive = self.base / "prepare-target-aba.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)

        def materialize_with_aba(*_args: object, **_kwargs: object) -> dict[str, str]:
            self._swap_worktree_aba(target, substitute)
            return {"status": "published"}

        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=materialize_with_aba,
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )
        with mock.patch.dict(
            os.environ, {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)}, clear=True
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(manager, "_load_identity_module", return_value=fake_module):
            with self.assertRaisesRegex(cache_module.CacheError, "identity changed|namespace changed"):
                manager.prepare(target, replace_seed=True)

        staging = next(target.glob(".lake-seed-*")) / ".lake"
        self.assertEqual(snapshot_subtree(target_before, ".lake"), byte_snapshot(staging))
        target_after = byte_snapshot(target)
        for relative, facts in target_before.items():
            if relative != "." and not relative.startswith(".lake"):
                self.assertEqual(facts, target_after[relative])
        self.assertEqual(substitute_before, byte_snapshot(substitute))

    def test_committed_backup_substitution_is_retained_unchanged_for_manual_recovery(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("backup-substitution")
        original = target / ".lake"
        original.mkdir()
        (original / "original").write_bytes(b"original\n")
        genuine_saved = target / ".genuine-saved"
        substitute_bytes = b"substitute\n"
        real_retain = manager._retain_seed_backup

        def substitute_before_retention(
            bound: object, replacement: object
        ) -> object:
            staging = target / replacement.staging_root.name
            backup = staging / ".lake"
            os.replace(backup, genuine_saved)
            backup.mkdir()
            (backup / "substitute").write_bytes(substitute_bytes)
            return real_retain(bound, replacement)

        with mock.patch.object(
            manager, "_retain_seed_backup", side_effect=substitute_before_retention
        ):
            with self.assertRaisesRegex(
                cache_module.CacheError, "identity changed|object name changed|finalization failed"
            ):
                manager.seed(target, replace=True)

        backup = next(target.glob(".lake-seed-*")) / ".lake"
        self.assertEqual(substitute_bytes, (backup / "substitute").read_bytes())
        self.assertEqual(b"original\n", (genuine_saved / "original").read_bytes())
        self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())
        self.assertTrue(manager._seed_transaction_dir(target).is_dir())

    def test_committed_backup_swap_restore_aba_fails_before_retention(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("backup-aba")
        original = target / ".lake"
        original.mkdir()
        (original / "original").write_bytes(b"original\n")
        substitute = target / ".backup-substitute"
        substitute.mkdir()
        (substitute / "substitute").write_bytes(b"substitute\n")
        real_retain = manager._retain_seed_backup

        def aba_before_retention(bound: object, replacement: object) -> object:
            staging = target / replacement.staging_root.name
            backup = staging / ".lake"
            parked = target / ".backup-parked"
            os.replace(backup, parked)
            os.replace(substitute, backup)
            os.replace(backup, substitute)
            os.replace(parked, backup)
            return real_retain(bound, replacement)

        with mock.patch.object(
            manager, "_retain_seed_backup", side_effect=aba_before_retention
        ):
            with self.assertRaisesRegex(
                cache_module.CacheError, "identity changed|object name changed|finalization failed"
            ):
                manager.seed(target, replace=True)

        backup = next(target.glob(".lake-seed-*")) / ".lake"
        self.assertEqual(b"original\n", (backup / "original").read_bytes())
        self.assertEqual(b"substitute\n", (substitute / "substitute").read_bytes())
        self.assertTrue(manager._seed_transaction_dir(target).is_dir())

    def test_seed_and_prepare_reject_in_place_displaced_tree_mutation(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-displaced-mutation-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"displaced-mutation-{action}")
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"original")
                archive = self.base / f"displaced-mutation-{action}.tar.gz"
                archive.write_bytes(b"authenticated")
                authored = cache_module.authored_tree_facts_on_disk(target)
                fake_module = adaptable_materializer(
                    load_pin=lambda _path: {},
                    validate_project_pins=lambda _root, _pin: None,
                    materialize=lambda *_args, **_kwargs: {"status": "published"},
                    verify_materialized=lambda *_args: {"status": "verified", **authored},
                )
                real_retain = manager._retain_seed_backup
                injected = False

                def mutate_before_retention(bound: object, replacement: object) -> object:
                    nonlocal injected
                    if not injected:
                        injected = True
                        descriptor = os.open(
                            "original",
                            os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW,
                            dir_fd=replacement.original_descriptor,
                        )
                        try:
                            os.write(descriptor, b"modified")
                        finally:
                            os.close(descriptor)
                    return real_retain(bound, replacement)

                with mock.patch.object(
                    manager, "_retain_seed_backup", side_effect=mutate_before_retention
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError, "recursive inventory changed|finalization failed"
                    ):
                        if action == "prepare":
                            with mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ), mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ), mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ):
                                manager.prepare(target, replace_seed=True)
                        else:
                            manager.seed(target, replace=True)
                self.assertTrue(injected)
                displaced = next(target.glob(".lake-seed-*")) / ".lake"
                self.assertEqual(b"modified", (displaced / "original").read_bytes())
                self.assertTrue(manager._seed_transaction_dir(target).is_dir())

    def test_seed_and_prepare_reject_unexpected_final_staging_entry(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-final-stage-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"final-stage-{action}")
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"original")
                archive = self.base / f"final-stage-{action}.tar.gz"
                archive.write_bytes(b"authenticated")
                authored = cache_module.authored_tree_facts_on_disk(target)
                fake_module = adaptable_materializer(
                    load_pin=lambda _path: {},
                    validate_project_pins=lambda _root, _pin: None,
                    materialize=lambda *_args, **_kwargs: {"status": "published"},
                    verify_materialized=lambda *_args: {"status": "verified", **authored},
                )
                real_discard = manager._discard_seed_rollback_root
                injected = False

                def contaminate_final_stage(bound: object, replacement: object) -> None:
                    nonlocal injected
                    if not injected:
                        injected = True
                        descriptor = os.open(
                            "unexpected",
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                            0o600,
                            dir_fd=replacement.staging_descriptor,
                        )
                        try:
                            os.write(descriptor, b"preserve")
                        finally:
                            os.close(descriptor)
                    real_discard(bound, replacement)

                with mock.patch.object(
                    manager, "_discard_seed_rollback_root", side_effect=contaminate_final_stage
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError, "transaction object name changed|finalization failed"
                    ):
                        if action == "prepare":
                            with mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ), mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ), mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ):
                                manager.prepare(target, replace_seed=True)
                        else:
                            manager.seed(target, replace=True)
                staging = next(target.glob(".lake-seed-*"))
                retained = next(target.glob(".lake.retained-*"))
                self.assertTrue(injected)
                self.assertEqual(b"preserve", (staging / "unexpected").read_bytes())
                self.assertEqual(
                    b"original", (retained / "original").read_bytes()
                )
                journal_parent = manager._seed_transaction_dir(target).parent
                self.assertEqual(1, len(list(journal_parent.glob("*.retained-*"))))

    def test_cache_copy_post_handoff_relocation_receives_no_bytes(self) -> None:
        for object_kind in ("directory", "file"):
            with self.subTest(object_kind=object_kind):
                source_root = self.base / f"copy-source-{object_kind}"
                destination = self.base / f"copy-destination-{object_kind}"
                external = self.base / f"copy-external-{object_kind}"
                source_root.mkdir()
                external.mkdir()
                if object_kind == "directory":
                    (source_root / "child").mkdir()
                    (source_root / "child" / "payload").write_bytes(b"foundation")
                    selected_name = "child"
                else:
                    (source_root / "payload").write_bytes(b"foundation")
                    selected_name = "payload"
                external_descriptor = os.open(external, cache_module._authored_directory_flags())
                real_create = cache_module._create_copy_output
                real_link = cache_module._linux_link_unnamed_file
                real_write = cache_module.os.write
                injected = False
                payload_was_unnamed = False

                def relocate_after_handoff(
                    parent_descriptor: int,
                    name: str,
                    parent_monitor: object,
                    label: str,
                ) -> object:
                    nonlocal injected
                    binding = real_create(
                        parent_descriptor,
                        name,
                        parent_monitor,  # type: ignore[arg-type]
                        label,
                    )
                    if name == selected_name and not injected:
                        injected = True
                        os.rename(
                            name,
                            f"relocated-{name}",
                            src_dir_fd=parent_descriptor,
                            dst_dir_fd=external_descriptor,
                        )
                    return binding

                def relocate_file_after_link(
                    descriptor: int, parent_descriptor: int, name: str
                ) -> None:
                    nonlocal injected
                    real_link(descriptor, parent_descriptor, name)
                    if object_kind == "file" and name == selected_name and not injected:
                        injected = True
                        os.rename(
                            name,
                            f"relocated-{name}",
                            src_dir_fd=parent_descriptor,
                            dst_dir_fd=external_descriptor,
                        )

                def assert_unnamed_write(descriptor: int, payload: object) -> int:
                    nonlocal payload_was_unnamed
                    if bytes(payload) == b"foundation":  # type: ignore[arg-type]
                        payload_was_unnamed = True
                        self.assertEqual(0, os.fstat(descriptor).st_nlink)
                    return real_write(descriptor, payload)  # type: ignore[arg-type]

                try:
                    with mock.patch.object(
                        cache_module, "_create_copy_output", side_effect=relocate_after_handoff
                    ), mock.patch.object(
                        cache_module,
                        "_linux_link_unnamed_file",
                        side_effect=relocate_file_after_link,
                    ), mock.patch.object(
                        cache_module.os, "write", side_effect=assert_unnamed_write
                    ):
                        with self.assertRaises(cache_module.CacheError):
                            cache_module.reflink_copytree(source_root, destination)
                finally:
                    os.close(external_descriptor)
                self.assertTrue(injected)
                relocated = external / f"relocated-{selected_name}"
                if object_kind == "directory":
                    self.assertTrue(relocated.is_dir())
                    self.assertEqual([], list(relocated.iterdir()))
                else:
                    self.assertTrue(payload_was_unnamed)
                    self.assertEqual(b"foundation", relocated.read_bytes())

    def test_late_cache_output_hard_link_prevents_seed_publication(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-late-cache-link")
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("late-cache-link")
        external = self.base / "late-cache-output.olean"
        real_copy = cache_module.reflink_copytree
        injected = False

        def link_after_copy(source: Path, destination: Path, **options: object) -> object:
            nonlocal injected
            result = real_copy(source, destination, **options)  # type: ignore[arg-type]
            descriptor = int(options["destination_descriptor"])
            build = os.open(
                "build", cache_module._authored_directory_flags(), dir_fd=descriptor
            )
            try:
                os.link(
                    "QPBT.olean",
                    external,
                    src_dir_fd=build,
                    follow_symlinks=False,
                )
            finally:
                os.close(build)
            injected = True
            return result

        with mock.patch.object(
            cache_module, "reflink_copytree", side_effect=link_after_copy
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "single-link"):
                manager.seed(target)
        self.assertTrue(injected)
        self.assertEqual(b"compiled-main\n", external.read_bytes())
        self.assertFalse((target / ".lake").exists())

    def test_cache_reflink_payload_is_unnamed_until_complete(self) -> None:
        source_root = self.base / "reflink-unnamed-source"
        destination = self.base / "reflink-unnamed-destination"
        source_root.mkdir()
        (source_root / "payload").write_bytes(b"foundation")
        observed = False
        real_write = cache_module.os.write

        def emulate_reflink(destination_descriptor: int, operation: int, source_descriptor: int) -> int:
            nonlocal observed
            self.assertEqual(cache_module.FICLONE, operation)
            observed = True
            self.assertEqual(0, os.fstat(destination_descriptor).st_nlink)
            self.assertFalse((destination / "payload").exists())
            payload = os.pread(source_descriptor, 1024, 0)
            self.assertEqual(len(payload), real_write(destination_descriptor, payload))
            return 0

        with mock.patch.object(cache_module.fcntl, "ioctl", side_effect=emulate_reflink):
            stats = cache_module.reflink_copytree(source_root, destination)
        self.assertTrue(observed)
        self.assertEqual(1, stats.reflinked)
        self.assertEqual(b"foundation", (destination / "payload").read_bytes())

    def test_final_staging_mutation_after_old_last_drain_prevents_success(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-post-drain")
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("post-drain")
        (target / ".lake").mkdir()
        (target / ".lake" / "original").write_bytes(b"original")
        real_refresh = cache_module._BoundSeedTarget.refresh_after_project_mutation
        injected = False

        def inject_after_retention(bound: object) -> None:
            nonlocal injected
            retained = list(target.glob(".lake.transaction-evidence-*"))
            if retained and not injected:
                injected = True
                (retained[0] / "late").write_bytes(b"preserve")
            real_refresh(bound)  # type: ignore[arg-type]

        with mock.patch.object(
            cache_module._BoundSeedTarget,
            "refresh_after_project_mutation",
            side_effect=inject_after_retention,
            autospec=True,
        ):
            with self.assertRaisesRegex(
                cache_module.CacheError, "object name changed|finalization failed"
            ):
                manager.seed(target, replace=True)
        retained = next(target.glob(".lake.transaction-evidence-*"))
        self.assertTrue(injected)
        self.assertEqual(b"preserve", (retained / "late").read_bytes())

    def test_retained_backup_mutation_after_old_inventory_prevents_success(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-post-backup-scan")
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("post-backup-scan")
        (target / ".lake").mkdir()
        (target / ".lake" / "original").write_bytes(b"original")
        real_refresh = cache_module._BoundSeedTarget.refresh_after_project_mutation
        injected = False

        def inject_before_final_inventory(bound: object) -> None:
            nonlocal injected
            retained = list(target.glob(".lake.retained-*"))
            if retained and not injected:
                injected = True
                (retained[0] / "original").write_bytes(b"modified")
            real_refresh(bound)  # type: ignore[arg-type]

        with mock.patch.object(
            cache_module._BoundSeedTarget,
            "refresh_after_project_mutation",
            side_effect=inject_before_final_inventory,
            autospec=True,
        ):
            with self.assertRaisesRegex(
                cache_module.CacheError, "recursive inventory changed|finalization failed"
            ):
                manager.seed(target, replace=True)
        retained = next(target.glob(".lake.retained-*"))
        self.assertTrue(injected)
        self.assertEqual(b"modified", (retained / "original").read_bytes())

    def test_dry_seed_holds_target_lock_through_admission(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-dry-lock")
        target = self.issue_worktree("dry-lock")
        _lexical, lock_path = manager._target_lock_path(target)
        entered = threading.Event()
        release = threading.Event()
        competitor_acquired = threading.Event()
        failures: list[BaseException] = []

        def paused_admission(*_args: object, **_kwargs: object) -> dict[str, object]:
            entered.set()
            if not release.wait(5):
                raise AssertionError("dry admission release timed out")
            return {"action": "seed", "dry_run": True}

        def run_dry() -> None:
            try:
                manager.seed(target, dry_run=True)
            except BaseException as error:
                failures.append(error)

        def compete() -> None:
            try:
                with cache_module.ExclusiveLock(lock_path):
                    competitor_acquired.set()
            except BaseException as error:
                failures.append(error)

        with mock.patch.object(
            manager, "_dry_seed_locked", side_effect=paused_admission
        ):
            dry_thread = threading.Thread(target=run_dry)
            competitor = threading.Thread(target=compete)
            dry_thread.start()
            self.assertTrue(entered.wait(5))
            competitor.start()
            self.assertFalse(competitor_acquired.wait(0.1))
            release.set()
            dry_thread.join(5)
            competitor.join(5)
        self.assertFalse(dry_thread.is_alive())
        self.assertFalse(competitor.is_alive())
        self.assertTrue(competitor_acquired.is_set())
        self.assertEqual([], failures)

    def test_seed_and_prepare_journal_bootstrap_reject_ancestor_substitution(self) -> None:
        for action in ("seed", "prepare"):
            for schedule in ("symlink", "pre_open", "post_handoff"):
                with self.subTest(action=action, schedule=schedule):
                    recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                    manager = self.manager(
                        runtime=self.base / f"runtime-journal-{action}-{schedule}", recipe=recipe
                    )
                    manager.warm(
                        _test_command_callback=fake_success,
                        _test_source_verifier=(
                            fake_source_verifier if action == "prepare" else None
                        ),
                    )
                    target = self.issue_worktree(f"journal-{action}-{schedule}")
                    (target / ".lake").mkdir()
                    (target / ".lake" / "original").write_bytes(b"original")
                    external = self.base / f"external-journal-{action}-{schedule}"
                    external.mkdir()
                    transactions = manager.runtime_dir / "transactions"
                    if schedule == "symlink":
                        transactions.symlink_to(external, target_is_directory=True)
                    elif schedule == "pre_open":
                        transactions.mkdir()
                    real_open_parent = manager._open_seed_journal_parent
                    real_os_open = cache_module.os.open
                    external_descriptor: int | None = None
                    ancestor_substituted = False

                    def substitute_before_ancestor_open(
                        path: object,
                        flags: int,
                        mode: int = 0o777,
                        *,
                        dir_fd: int | None = None,
                    ) -> int:
                        nonlocal ancestor_substituted
                        if (
                            schedule == "pre_open"
                            and str(path) == "transactions"
                            and dir_fd is not None
                            and not ancestor_substituted
                            and Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                            == manager.runtime_dir
                        ):
                            ancestor_substituted = True
                            transactions.rename(manager.runtime_dir / "transactions-parked")
                            transactions.symlink_to(external, target_is_directory=True)
                        return real_os_open(path, flags, mode, dir_fd=dir_fd)

                    def relocate_parent_after_handoff(replacement: object) -> int:
                        nonlocal external_descriptor
                        descriptor = real_open_parent(replacement)
                        bindings = replacement.journal_ancestor_bindings
                        assert bindings is not None
                        transactions_descriptor = bindings[-1][0]
                        external_descriptor = os.open(
                            external, cache_module._authored_directory_flags()
                        )
                        os.rename(
                            "seed",
                            "relocated-seed",
                            src_dir_fd=transactions_descriptor,
                            dst_dir_fd=external_descriptor,
                        )
                        return descriptor

                    archive = self.base / f"journal-{action}-{schedule}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    parent_patch = (
                        mock.patch.object(
                            manager,
                            "_open_seed_journal_parent",
                            side_effect=relocate_parent_after_handoff,
                        )
                        if schedule == "post_handoff"
                        else mock.patch.object(
                            manager,
                            "_open_seed_journal_parent",
                            wraps=manager._open_seed_journal_parent,
                        )
                    )
                    open_patch = (
                        mock.patch.object(
                            cache_module.os,
                            "open",
                            side_effect=substitute_before_ancestor_open,
                        )
                        if schedule == "pre_open"
                        else mock.patch.object(cache_module.os, "open", wraps=real_os_open)
                    )
                    try:
                        with parent_patch, open_patch, mock.patch.object(
                            manager, "_require_seed_capabilities"
                        ):
                            with self.assertRaises(cache_module.CacheError):
                                if action == "prepare":
                                    with mock.patch.dict(
                                        os.environ,
                                        {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                        clear=True,
                                    ), mock.patch.object(
                                        manager,
                                        "_preflight_authenticated_inputs",
                                        return_value={"required": True},
                                    ), mock.patch.object(
                                        manager,
                                        "_load_identity_module",
                                        return_value=fake_module,
                                    ):
                                        manager.prepare(target, replace_seed=True)
                                else:
                                    manager.seed(target, replace=True)
                    finally:
                        if external_descriptor is not None:
                            os.close(external_descriptor)
                    self.assertEqual(
                        b"original", (target / ".lake" / "original").read_bytes()
                    )
                    if schedule == "symlink":
                        self.assertEqual([], list(external.iterdir()))
                    elif schedule == "pre_open":
                        self.assertTrue(ancestor_substituted)
                        self.assertEqual([], list(external.iterdir()))
                        self.assertTrue(
                            (manager.runtime_dir / "transactions-parked").is_dir()
                        )
                    else:
                        relocated = external / "relocated-seed"
                        self.assertTrue(relocated.is_dir())
                        self.assertEqual([], list(relocated.iterdir()))

    def test_dry_and_live_seed_prepare_refuse_interrupted_state_before_admission(self) -> None:
        for action in ("seed", "prepare"):
            for dry_run in (False, True):
                for state_kind in ("journal", "staging"):
                    with self.subTest(
                        action=action, dry_run=dry_run, state_kind=state_kind
                    ):
                        recipe = (
                            MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                        )
                        manager = self.manager(
                            runtime=self.base / f"runtime-state-{action}-{dry_run}-{state_kind}",
                            recipe=recipe,
                        )
                        target = self.issue_worktree(
                            f"state-{action}-{dry_run}-{state_kind}"
                        )
                        if state_kind == "journal":
                            state = manager._seed_transaction_dir(target)
                            state.mkdir(parents=True)
                            (state / "evidence").write_bytes(b"preserve")
                        else:
                            state = target / ".lake-seed-interrupted"
                            state.mkdir()
                            (state / "evidence").write_bytes(b"preserve")
                        before = byte_snapshot(state)
                        capability = mock.Mock(
                            side_effect=AssertionError("capability admission ran")
                        )
                        inputs = mock.Mock(side_effect=AssertionError("input admission ran"))
                        with mock.patch.object(
                            manager, "_require_seed_capabilities", capability
                        ), mock.patch.object(
                            manager, "_preflight_authenticated_inputs", inputs
                        ):
                            with self.assertRaisesRegex(
                                cache_module.CacheError, "interrupted seed state"
                            ):
                                if action == "prepare":
                                    manager.prepare(target, dry_run=dry_run)
                                else:
                                    manager.seed(target, dry_run=dry_run)
                        capability.assert_not_called()
                        inputs.assert_not_called()
                        self.assertEqual(before, byte_snapshot(state))

    def test_seed_and_prepare_refuse_missing_atomic_capability_before_mutation(self) -> None:
        for action in ("seed", "prepare"):
            for dry_run in (False, True):
                with self.subTest(action=action, dry_run=dry_run):
                    recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                    manager = self.manager(
                        runtime=self.base / f"runtime-capability-{action}-{dry_run}",
                        recipe=recipe,
                    )
                    manager.warm(
                        _test_command_callback=fake_success,
                        _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                    )
                    target = self.issue_worktree(f"capability-{action}-{dry_run}")
                    before = byte_snapshot(target)
                    identity_admission = mock.Mock(
                        side_effect=AssertionError("identity input admission ran")
                    )
                    archive_admission = mock.Mock(
                        side_effect=AssertionError("archive input admission ran")
                    )
                    status_admission = mock.Mock(
                        side_effect=AssertionError("cache status admission ran")
                    )
                    readiness_admission = mock.Mock(
                        side_effect=AssertionError("cache readiness admission ran")
                    )
                    with mock.patch.object(
                        cache_module,
                        "_probe_renameat2_semantics",
                        side_effect=cache_module.CacheError("atomic capability unavailable"),
                    ), mock.patch.object(
                        manager, "_capture_identity_inputs", identity_admission
                    ), mock.patch.object(
                        manager, "_preflight_authenticated_inputs", archive_admission
                    ), mock.patch.object(
                        manager, "status", status_admission
                    ), mock.patch.object(manager, "is_ready", readiness_admission):
                        with self.assertRaisesRegex(
                            cache_module.CacheError, "capability unavailable"
                        ):
                            if action == "seed":
                                manager.seed(target, dry_run=dry_run)
                            else:
                                manager.prepare(target, dry_run=dry_run)
                    identity_admission.assert_not_called()
                    archive_admission.assert_not_called()
                    status_admission.assert_not_called()
                    readiness_admission.assert_not_called()
                    self.assertEqual(before, byte_snapshot(target))
                    self.assertFalse(manager._seed_transaction_dir(target).exists())

    def test_dry_prepare_runs_materializer_admission_before_delegated_seed(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        target = self.issue_worktree("dry-prepare-admission-order")
        events: list[str] = []
        module = types.SimpleNamespace()
        delegated = mock.Mock(
            side_effect=lambda *_args, **_kwargs: (
                events.append("seed")
                or {"action": "seed", "dry_run": True, "target": str(target / ".lake")}
            )
        )

        with mock.patch.object(
            manager,
            "_assert_no_materializer_recovery_state",
            side_effect=lambda _target: events.append("state"),
        ), mock.patch.object(
            manager, "_require_seed_capabilities"
        ), mock.patch.object(
            manager,
            "_preflight_authenticated_inputs",
            side_effect=lambda: events.append("archive") or {"required": True},
        ), mock.patch.object(
            manager,
            "_load_identity_module",
            side_effect=lambda *_args: events.append("module") or module,
        ), mock.patch.object(
            manager,
            "_adapt_materializer_to_bound_target",
            side_effect=lambda *_args: events.append("interface"),
        ), mock.patch.object(
            manager,
            "_load_captured_pin",
            side_effect=lambda *_args: events.append("pin") or {},
        ), mock.patch.object(
            manager,
            "_validate_captured_project",
            side_effect=lambda *_args: events.append("validate"),
        ), mock.patch.object(manager, "_dry_seed_locked", delegated):
            result = manager.prepare(target, dry_run=True)

        self.assertEqual(
            ["state", "archive", "module", "interface", "pin", "validate", "state", "seed"],
            events,
        )
        self.assertEqual("prepare", result["action"])
        delegated.assert_called_once()
        self.assertEqual(target, delegated.call_args.args[0])
        self.assertFalse(delegated.call_args.kwargs["replace"])
        self.assertIsInstance(
            delegated.call_args.kwargs["target_lock"], cache_module.ExclusiveLock
        )

    def test_dry_prepare_refuses_materializer_state_and_interface_before_seed(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        target = self.issue_worktree("dry-prepare-materializer-refusal")
        transaction = (
            target
            / ".workflow-runtime"
            / "mipstarre-materialization"
            / "MIPStarRE.transaction"
        )
        transaction.mkdir(parents=True)
        archive = mock.Mock(side_effect=AssertionError("archive admission ran"))
        delegated = mock.Mock(side_effect=AssertionError("delegated seed ran"))
        with mock.patch.object(
            manager, "_require_seed_capabilities"
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", archive
        ), mock.patch.object(manager, "seed", delegated):
            with self.assertRaisesRegex(cache_module.CacheError, "persisted materializer state"):
                manager.prepare(target, dry_run=True)
        archive.assert_not_called()
        delegated.assert_not_called()

        interface_target = self.issue_worktree("dry-prepare-interface-refusal")
        with mock.patch.object(
            manager, "_require_seed_capabilities"
        ), mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
        ), mock.patch.object(
            manager, "_load_identity_module", return_value=types.SimpleNamespace()
        ), mock.patch.object(manager, "seed", delegated):
            with self.assertRaisesRegex(cache_module.CacheError, "lacks the bound fail-closed interface"):
                manager.prepare(interface_target, dry_run=True)
        delegated.assert_not_called()

    def test_seed_and_prepare_reject_created_staging_and_journal_substitution(self) -> None:
        for action in ("seed", "prepare"):
            for object_kind in ("staging", "journal"):
                with self.subTest(action=action, object_kind=object_kind):
                    recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                    manager = self.manager(
                        runtime=self.base / f"runtime-handoff-{action}-{object_kind}",
                        recipe=recipe,
                    )
                    manager.warm(
                        _test_command_callback=fake_success,
                        _test_source_verifier=(
                            fake_source_verifier if action == "prepare" else None
                        ),
                    )
                    target = self.issue_worktree(f"handoff-{action}-{object_kind}")
                    if object_kind == "journal":
                        (target / ".lake").mkdir()
                        (target / ".lake" / "original").write_bytes(b"preserve")
                    archive_path = self.base / f"handoff-{action}-{object_kind}.tar.gz"
                    archive_path.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {
                            "status": "verified",
                            **authored,
                        },
                    )
                    journal_name = manager._seed_transaction_dir(target).name
                    real_mkdir = cache_module.os.mkdir
                    injected: list[tuple[Path, str, str]] = []

                    def substitute_after_mkdir(
                        path: object,
                        mode: int = 0o777,
                        *,
                        dir_fd: int | None = None,
                    ) -> None:
                        real_mkdir(path, mode, dir_fd=dir_fd)
                        name = str(path)
                        selected = (
                            object_kind == "staging" and name.startswith(".lake-seed-")
                        ) or (object_kind == "journal" and name == journal_name)
                        if selected and dir_fd is not None and not injected:
                            parked = f"attacker-created-{name}"
                            os.rename(
                                name,
                                parked,
                                src_dir_fd=dir_fd,
                                dst_dir_fd=dir_fd,
                            )
                            real_mkdir(name, mode, dir_fd=dir_fd)
                            parent = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                            (parent / name / "substitute").write_bytes(b"preserve")
                            injected.append((parent, parked, name))

                    with mock.patch.dict(
                        os.environ,
                        {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive_path)},
                        clear=True,
                    ), mock.patch.object(
                        manager, "_preflight_authenticated_inputs", return_value={"required": True}
                    ), mock.patch.object(
                        manager, "_load_identity_module", return_value=fake_module
                    ), mock.patch.object(
                        manager, "_require_seed_capabilities"
                    ), mock.patch.object(
                        cache_module.os, "mkdir", side_effect=substitute_after_mkdir
                    ):
                        with self.assertRaisesRegex(cache_module.CacheError, "exact monitor events"):
                            if action == "prepare":
                                manager.prepare(
                                    target, replace_seed=object_kind == "journal"
                                )
                            else:
                                manager.seed(target, replace=object_kind == "journal")

                    self.assertEqual(1, len(injected))
                    parent, parked, substitute = injected[0]
                    self.assertTrue((parent / parked).is_dir())
                    self.assertEqual(
                        b"preserve", (parent / substitute / "substitute").read_bytes()
                    )
                    if object_kind == "journal":
                        self.assertFalse((parent / substitute / "journal.json").exists())
                        self.assertEqual(
                            b"preserve", (target / ".lake" / "original").read_bytes()
                        )
                        self.assertFalse((target / ".lake" / "build").exists())
                    else:
                        self.assertFalse((parent / substitute / ".lake").exists())

    def test_seed_and_prepare_reject_inner_staging_and_journal_file_handoffs(self) -> None:
        for action in ("seed", "prepare"):
            for child_kind in ("staged_lake", "journal_file"):
                with self.subTest(action=action, child_kind=child_kind):
                    recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                    manager = self.manager(
                        runtime=self.base / f"runtime-inner-handoff-{action}-{child_kind}",
                        recipe=recipe,
                    )
                    manager.warm(
                        _test_command_callback=fake_success,
                        _test_source_verifier=(
                            fake_source_verifier if action == "prepare" else None
                        ),
                    )
                    target = self.issue_worktree(f"inner-handoff-{action}-{child_kind}")
                    if child_kind == "journal_file":
                        (target / ".lake").mkdir()
                        (target / ".lake" / "original").write_bytes(b"preserve")
                    archive_path = self.base / f"inner-handoff-{action}-{child_kind}.tar.gz"
                    archive_path.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {
                            "status": "verified",
                            **authored,
                        },
                    )
                    real_mkdir = cache_module.os.mkdir
                    real_open = cache_module.os.open
                    injected: list[tuple[Path, str, str]] = []

                    def substitute_staged_lake(
                        path: object,
                        mode: int = 0o777,
                        *,
                        dir_fd: int | None = None,
                    ) -> None:
                        real_mkdir(path, mode, dir_fd=dir_fd)
                        if path == ".lake" and dir_fd is not None and not injected:
                            parent = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                            if parent.name.startswith(".lake-seed-"):
                                os.rename(
                                    ".lake",
                                    "attacker-created-.lake",
                                    src_dir_fd=dir_fd,
                                    dst_dir_fd=dir_fd,
                                )
                                real_mkdir(".lake", mode, dir_fd=dir_fd)
                                injected.append((parent, "attacker-created-.lake", ".lake"))

                    def substitute_journal_file(
                        path: object,
                        flags: int,
                        mode: int = 0o777,
                        *,
                        dir_fd: int | None = None,
                    ) -> int:
                        descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
                        if path == "journal.json" and dir_fd is not None and not injected:
                            parent = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                            os.rename(
                                "journal.json",
                                "attacker-created-journal.json",
                                src_dir_fd=dir_fd,
                                dst_dir_fd=dir_fd,
                            )
                            substitute = real_open(
                                "journal.json",
                                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                0o600,
                                dir_fd=dir_fd,
                            )
                            os.write(substitute, b"preserve")
                            os.close(substitute)
                            injected.append(
                                (parent, "attacker-created-journal.json", "journal.json")
                            )
                        return descriptor

                    mkdir_effect = (
                        substitute_staged_lake if child_kind == "staged_lake" else real_mkdir
                    )
                    open_effect = (
                        substitute_journal_file if child_kind == "journal_file" else real_open
                    )
                    with mock.patch.dict(
                        os.environ,
                        {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive_path)},
                        clear=True,
                    ), mock.patch.object(
                        manager, "_preflight_authenticated_inputs", return_value={"required": True}
                    ), mock.patch.object(
                        manager, "_load_identity_module", return_value=fake_module
                    ), mock.patch.object(
                        manager, "_require_seed_capabilities"
                    ), mock.patch.object(
                        cache_module.os, "mkdir", side_effect=mkdir_effect
                    ), mock.patch.object(
                        cache_module.os, "open", side_effect=open_effect
                    ):
                        with self.assertRaisesRegex(cache_module.CacheError, "exact monitor events"):
                            if action == "prepare":
                                manager.prepare(
                                    target, replace_seed=child_kind == "journal_file"
                                )
                            else:
                                manager.seed(target, replace=child_kind == "journal_file")

                    self.assertEqual(1, len(injected))
                    parent, parked, substitute = injected[0]
                    self.assertTrue((parent / parked).exists())
                    if child_kind == "journal_file":
                        self.assertEqual(b"preserve", (parent / substitute).read_bytes())
                        self.assertEqual(
                            b"preserve", (target / ".lake" / "original").read_bytes()
                        )
                    else:
                        self.assertTrue((parent / substitute).is_dir())
                        self.assertFalse((parent / substitute / "build").exists())

    def test_seed_copy_rejects_descendant_symlink_before_external_write(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-descendant-symlink")
        external = self.base / "external-cache-copy-target"
        external.mkdir()
        real_mkdir = cache_module.os.mkdir
        injected: list[Path] = []

        def substitute_after_mkdir(
            path: object,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            real_mkdir(path, mode, dir_fd=dir_fd)
            if path == "build" and dir_fd is not None and not injected:
                parent = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                os.rename(
                    "build",
                    "attacker-created-build",
                    src_dir_fd=dir_fd,
                    dst_dir_fd=dir_fd,
                )
                os.symlink(str(external), "build", target_is_directory=True, dir_fd=dir_fd)
                injected.append(parent)

        with mock.patch.object(
            cache_module.os, "mkdir", side_effect=substitute_after_mkdir
        ), mock.patch.object(manager, "_require_seed_capabilities"):
            with self.assertRaisesRegex(cache_module.CacheError, "exact monitor events"):
                manager.seed(target)

        self.assertEqual([], list(external.iterdir()))
        self.assertEqual(1, len(injected))
        parked = list(target.rglob("attacker-created-build"))
        self.assertEqual(1, len(parked))
        self.assertTrue(parked[0].is_dir())
        self.assertTrue((parked[0].parent / "build").is_symlink())

    def test_retained_journal_modification_prevents_success(self) -> None:
        for filename in ("journal.json", "COMMITTED"):
            with self.subTest(filename=filename):
                manager = self.manager(runtime=self.base / f"runtime-journal-modify-{filename}")
                manager.warm(_test_command_callback=fake_success)
                target = self.issue_worktree(f"journal-modify-{filename}")
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"original")
                real_move = cache_module.HotMainCache._atomic_move_bound
                retained_paths: list[Path] = []

                def move_then_modify(
                    source_parent: int,
                    source_name: str,
                    source_descriptor: int,
                    destination_parent: int,
                    destination_name: str,
                    label: str,
                ) -> None:
                    real_move(
                        source_parent,
                        source_name,
                        source_descriptor,
                        destination_parent,
                        destination_name,
                        label,
                    )
                    if label == "seed transaction journal retention":
                        retained = Path("/proc/self/fd") / str(destination_parent) / destination_name
                        (retained / filename).write_bytes(b"corrupt\n")
                        retained_paths.append(
                            Path(os.readlink(f"/proc/self/fd/{destination_parent}"))
                            / destination_name
                        )

                with mock.patch.object(
                    cache_module.HotMainCache,
                    "_atomic_move_bound",
                    side_effect=move_then_modify,
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError,
                        "exact monitor events|journal file .* changed",
                    ):
                        manager.seed(target, replace=True)

                self.assertEqual(1, len(retained_paths))
                self.assertEqual(b"corrupt\n", (retained_paths[0] / filename).read_bytes())
                self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())

    def test_seed_and_prepare_atomic_no_replace_preserve_concurrent_destination(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-no-replace-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"no-replace-{action}")
                real_renameat2 = cache_module._linux_renameat2
                injected = False

                def collide(
                    source_parent: int,
                    source: str,
                    destination_parent: int,
                    destination: str,
                    flags: int,
                ) -> None:
                    nonlocal injected
                    if (
                        not injected
                        and source == destination == ".lake"
                        and flags == cache_module.RENAME_NOREPLACE
                    ):
                        injected = True
                        (target / ".lake").mkdir()
                        (target / ".lake" / "concurrent").write_bytes(b"preserve")
                    real_renameat2(
                        source_parent, source, destination_parent, destination, flags
                    )

                contexts: list[object] = [
                    mock.patch.object(cache_module, "_linux_renameat2", side_effect=collide)
                ]
                if action == "prepare":
                    archive = self.base / f"no-replace-{action}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    materialize = mock.Mock(return_value={"status": "published"})
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=materialize,
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    contexts.extend(
                        [
                            mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ),
                            mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ),
                            mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ),
                        ]
                    )
                with contexts[0]:
                    if action == "prepare":
                        with contexts[1], contexts[2], contexts[3]:
                            with self.assertRaisesRegex(cache_module.CacheError, "destination appeared"):
                                manager.prepare(target)
                    else:
                        with self.assertRaisesRegex(cache_module.CacheError, "destination appeared"):
                            manager.seed(target)
                self.assertTrue(injected)
                self.assertEqual(b"preserve", (target / ".lake" / "concurrent").read_bytes())
                self.assertEqual(
                    [],
                    [
                        record
                        for record in self.metric_records(manager)
                        if record.get("result") == "seeded"
                    ],
                )
                if action == "prepare":
                    materialize.assert_not_called()

    def test_prepare_rejects_persisted_materializer_state_before_input_admission(self) -> None:
        for suffix in ("MIPStarRE.transaction", "MIPStarRE.transaction.cleanup"):
            with self.subTest(suffix=suffix):
                manager = self.manager(
                    runtime=self.base / f"runtime-materializer-state-{suffix}",
                    recipe=MATERIALIZING_TEST_RECIPE,
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier,
                )
                target = self.issue_worktree(f"materializer-state-{suffix}")
                state = target / ".workflow-runtime" / "mipstarre-materialization" / suffix
                state.mkdir(parents=True)
                (state / "untrusted").write_bytes(b"preserve")
                before = byte_snapshot(target)
                admission = mock.Mock(side_effect=AssertionError("input admission ran"))
                with mock.patch.object(
                    manager, "_preflight_authenticated_inputs", admission
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError, "no independent ownership proof"
                    ):
                        manager.prepare(target)
                admission.assert_not_called()
                self.assertEqual(before, byte_snapshot(target))

    def test_prepare_refuses_unadaptable_materializer_before_seed_for_both_modes(self) -> None:
        for replace in (False, True):
            with self.subTest(replace=replace):
                manager = self.manager(
                    runtime=self.base / f"runtime-unadaptable-{replace}",
                    recipe=MATERIALIZING_TEST_RECIPE,
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier,
                )
                target = self.issue_worktree(f"unadaptable-{replace}")
                archive = self.base / f"unadaptable-{replace}.tar.gz"
                archive.write_bytes(b"authenticated")
                materialize = mock.Mock(side_effect=AssertionError("materializer ran"))
                module = types.SimpleNamespace(
                    load_pin=lambda _path: {},
                    validate_project_pins=lambda _root, _pin: None,
                    materialize=materialize,
                    verify_materialized=lambda *_args: {},
                )
                with mock.patch.dict(
                    os.environ,
                    {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                    clear=True,
                ), mock.patch.object(
                    manager,
                    "_preflight_authenticated_inputs",
                    return_value={"required": True},
                ), mock.patch.object(
                    manager, "_load_identity_module", return_value=module
                ):
                    with self.assertRaisesRegex(cache_module.CacheError, "bound fail-closed interface"):
                        manager.prepare(target, replace_seed=replace)
                materialize.assert_not_called()
                self.assertFalse((target / ".lake").exists())
                self.assertEqual([], list(target.glob(".lake-seed-*")))

    def test_materializer_adapter_never_delegates_persisted_recovery(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        target_path = self.issue_worktree("materializer-no-recovery-delegation")
        target = manager._eligible_seed_target(target_path, check_inputs=False)
        try:
            delegated_recovery = mock.Mock(
                side_effect=AssertionError("legacy persisted recovery ran")
            )
            module = adaptable_materializer(_recover=delegated_recovery)
            manager._adapt_materializer_to_bound_target(module, target)
            transaction = (
                target.access_path
                / ".workflow-runtime"
                / "mipstarre-materialization"
                / "MIPStarRE.transaction"
            )
            module._recover(transaction, target.access_path / "MIPStarRE", {})
            delegated_recovery.assert_not_called()
            transaction.mkdir(parents=True)
            with self.assertRaisesRegex(
                module.MaterializationError, "no independent ownership proof"
            ):
                module._recover(transaction, target.access_path / "MIPStarRE", {})
            delegated_recovery.assert_not_called()
        finally:
            target.close()

    def test_seed_and_prepare_reject_ancestor_swap_restore(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-ancestor-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                ancestor = self.base / f"registered-{action}"
                target_parent = ancestor / "nested"
                target_parent.mkdir(parents=True)
                target = target_parent / "issue"
                run_git(self.repo, "worktree", "add", "--detach", str(target), self.commit)
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"preserve")
                substitute = self.base / f"ancestor-substitute-{action}"
                substitute.mkdir()
                parked = self.base / f"ancestor-parked-{action}"
                real_copy = cache_module.reflink_copytree

                def copy_after_ancestor_aba(
                    source: Path, destination: Path, **options: object
                ) -> object:
                    os.replace(ancestor, parked)
                    os.replace(substitute, ancestor)
                    os.replace(ancestor, substitute)
                    os.replace(parked, ancestor)
                    return real_copy(source, destination, **options)

                patches: list[object] = [
                    mock.patch.object(
                        cache_module, "reflink_copytree", side_effect=copy_after_ancestor_aba
                    )
                ]
                if action == "prepare":
                    archive = self.base / f"ancestor-{action}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    patches.extend(
                        [
                            mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ),
                            mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ),
                            mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ),
                        ]
                    )
                with patches[0]:
                    if action == "prepare":
                        with patches[1], patches[2], patches[3]:
                            with self.assertRaisesRegex(cache_module.CacheError, "ancestor namespace"):
                                manager.prepare(target, replace_seed=True)
                    else:
                        with self.assertRaisesRegex(cache_module.CacheError, "ancestor namespace"):
                            manager.seed(target, replace=True)
                self.assertEqual(b"preserve", (target / ".lake" / "original").read_bytes())
                self.assertTrue(substitute.is_dir())

    def test_seed_and_prepare_recheck_live_git_registration_before_publication(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-registration-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"registration-{action}")
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"preserve")
                records = cache_module.git_worktrees(self.repo)
                calls = 0

                def disappear(_repo: Path) -> list[cache_module.WorktreeRecord]:
                    nonlocal calls
                    calls += 1
                    return records if calls <= 2 else []

                contexts: list[object] = [
                    mock.patch.object(cache_module, "git_worktrees", side_effect=disappear)
                ]
                if action == "prepare":
                    archive = self.base / f"registration-{action}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    contexts.extend(
                        [
                            mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ),
                            mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ),
                            mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ),
                        ]
                    )
                with contexts[0]:
                    if action == "prepare":
                        with contexts[1], contexts[2], contexts[3]:
                            with self.assertRaisesRegex(cache_module.CacheError, "not the project root"):
                                manager.prepare(target, replace_seed=True)
                    else:
                        with self.assertRaisesRegex(cache_module.CacheError, "not the project root"):
                            manager.seed(target, replace=True)
                self.assertGreaterEqual(calls, 3)
                self.assertEqual(b"preserve", (target / ".lake" / "original").read_bytes())

    def test_seed_and_prepare_preserve_substituted_live_journal(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-journal-substitute-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"journal-substitute-{action}")
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"original")
                saved = manager._seed_transaction_dir(target).with_name(
                    f"saved-journal-{action}"
                )
                real_clear = manager._clear_seed_journal

                def substitute_journal(replacement: object) -> None:
                    os.replace(replacement.journal_dir, saved)
                    replacement.journal_dir.mkdir()
                    (replacement.journal_dir / "unknown").write_bytes(b"preserve")
                    real_clear(replacement)

                contexts: list[object] = [
                    mock.patch.object(
                        manager, "_clear_seed_journal", side_effect=substitute_journal
                    )
                ]
                if action == "prepare":
                    archive = self.base / f"journal-substitute-{action}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    contexts.extend(
                        [
                            mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ),
                            mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ),
                            mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ),
                        ]
                    )
                with contexts[0]:
                    if action == "prepare":
                        with contexts[1], contexts[2], contexts[3]:
                            with self.assertRaisesRegex(cache_module.CacheError, "journal|finalization"):
                                manager.prepare(target, replace_seed=True)
                    else:
                        with self.assertRaisesRegex(cache_module.CacheError, "journal|object name"):
                            manager.seed(target, replace=True)
                self.assertEqual(
                    b"preserve",
                    (manager._seed_transaction_dir(target) / "unknown").read_bytes(),
                )
                self.assertTrue((saved / "journal.json").is_file())
                self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())

    def test_prepare_rejects_self_consistent_unowned_seed_journal_before_inputs(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-unowned-seed-journal")
        journal = manager._seed_transaction_dir(target)
        journal.mkdir(parents=True)
        payload = b'{"self_asserted":true}\n'
        digest = hashlib.sha256(payload).hexdigest()
        (journal / "journal.json").write_bytes(payload)
        (journal / "journal.sha256").write_text(digest + "\n", encoding="ascii")
        (journal / "COMMITTED").write_text(digest + "\n", encoding="ascii")
        before = byte_snapshot(journal)
        admission = mock.Mock(side_effect=AssertionError("input admission ran"))
        with mock.patch.object(manager, "_preflight_authenticated_inputs", admission):
            with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
                manager.prepare(target)
        admission.assert_not_called()
        self.assertEqual(before, byte_snapshot(journal))

    def test_prepare_atomic_exchange_crash_never_removes_destination(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        target = self.issue_worktree("prepare-atomic-crash")
        original = target / ".lake"
        original.mkdir()
        (original / "original").write_bytes(b"preserve")
        archive = self.base / "prepare-atomic-crash.tar.gz"
        archive.write_bytes(b"authenticated")
        authored = cache_module.authored_tree_facts_on_disk(target)
        fake_module = adaptable_materializer(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )
        real_renameat2 = cache_module._linux_renameat2
        context = multiprocessing.get_context("fork")

        def interrupted_prepare() -> None:
            def kill_after_exchange(
                source_parent: int,
                source: str,
                destination_parent: int,
                destination: str,
                flags: int,
            ) -> None:
                real_renameat2(source_parent, source, destination_parent, destination, flags)
                if source == destination == ".lake":
                    os.kill(os.getpid(), signal.SIGKILL)

            with mock.patch.dict(
                os.environ,
                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                clear=True,
            ), mock.patch.object(
                manager,
                "_preflight_authenticated_inputs",
                return_value={"required": True},
            ), mock.patch.object(
                manager, "_load_identity_module", return_value=fake_module
            ), mock.patch.object(
                cache_module, "_linux_renameat2", side_effect=kill_after_exchange
            ):
                manager.prepare(target, replace_seed=True)

        process = context.Process(target=interrupted_prepare)
        process.start()
        process.join(10)
        self.assertEqual(-signal.SIGKILL, process.exitcode)
        self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())
        displaced = next(target.glob(".lake-seed-*")) / ".lake"
        self.assertEqual(b"preserve", (displaced / "original").read_bytes())
        with mock.patch.object(
            manager,
            "_preflight_authenticated_inputs",
            side_effect=AssertionError("input admission ran"),
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "no independent ownership proof"):
                manager.prepare(target, replace_seed=True)

    def test_seed_and_prepare_do_not_replace_retention_collision(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-retention-collision-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"retention-collision-{action}")
                (target / ".lake").mkdir()
                (target / ".lake" / "original").write_bytes(b"original")
                real_retain = manager._retain_seed_backup

                def collide_retention(bound: object, replacement: object) -> object:
                    retained = target / f".lake.retained-{replacement.transaction_id}"
                    retained.mkdir()
                    (retained / "decoy").write_bytes(b"preserve")
                    return real_retain(bound, replacement)

                contexts: list[object] = [
                    mock.patch.object(
                        manager, "_retain_seed_backup", side_effect=collide_retention
                    )
                ]
                if action == "prepare":
                    archive = self.base / f"retention-collision-{action}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    contexts.extend(
                        [
                            mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ),
                            mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ),
                            mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ),
                        ]
                    )
                with contexts[0]:
                    if action == "prepare":
                        with contexts[1], contexts[2], contexts[3]:
                            with self.assertRaisesRegex(cache_module.CacheError, "identity|finalization"):
                                manager.prepare(target, replace_seed=True)
                    else:
                        with self.assertRaisesRegex(cache_module.CacheError, "identity"):
                            manager.seed(target, replace=True)
                retained = next(target.glob(".lake.retained-*"))
                self.assertEqual(b"preserve", (retained / "decoy").read_bytes())
                displaced = next(target.glob(".lake-seed-*")) / ".lake"
                self.assertEqual(b"original", (displaced / "original").read_bytes())

    def test_seed_and_prepare_preserve_substituted_empty_staging_root(self) -> None:
        for action in ("seed", "prepare"):
            with self.subTest(action=action):
                recipe = MATERIALIZING_TEST_RECIPE if action == "prepare" else TEST_RECIPE
                manager = self.manager(
                    runtime=self.base / f"runtime-staging-substitute-{action}", recipe=recipe
                )
                manager.warm(
                    _test_command_callback=fake_success,
                    _test_source_verifier=fake_source_verifier if action == "prepare" else None,
                )
                target = self.issue_worktree(f"staging-substitute-{action}")
                real_discard = manager._discard_seed_rollback_root
                saved = target / f"saved-staging-{action}"
                injected = False

                def substitute_staging(bound: object, replacement: object) -> None:
                    nonlocal injected
                    if not injected:
                        injected = True
                        staging = target / replacement.staging_root.name
                        os.replace(staging, saved)
                        staging.mkdir()
                        (staging / "unknown").write_bytes(b"preserve")
                    real_discard(bound, replacement)

                contexts: list[object] = [
                    mock.patch.object(
                        manager,
                        "_discard_seed_rollback_root",
                        side_effect=substitute_staging,
                    )
                ]
                if action == "prepare":
                    archive = self.base / f"staging-substitute-{action}.tar.gz"
                    archive.write_bytes(b"authenticated")
                    authored = cache_module.authored_tree_facts_on_disk(target)
                    fake_module = adaptable_materializer(
                        load_pin=lambda _path: {},
                        validate_project_pins=lambda _root, _pin: None,
                        materialize=lambda *_args, **_kwargs: {"status": "published"},
                        verify_materialized=lambda *_args: {"status": "verified", **authored},
                    )
                    contexts.extend(
                        [
                            mock.patch.dict(
                                os.environ,
                                {cache_module.MIPSTARRE_ARCHIVE_ENV: str(archive)},
                                clear=True,
                            ),
                            mock.patch.object(
                                manager,
                                "_preflight_authenticated_inputs",
                                return_value={"required": True},
                            ),
                            mock.patch.object(
                                manager, "_load_identity_module", return_value=fake_module
                            ),
                        ]
                    )
                with contexts[0]:
                    if action == "prepare":
                        with contexts[1], contexts[2], contexts[3]:
                            with self.assertRaisesRegex(cache_module.CacheError, "identity|namespace"):
                                manager.prepare(target)
                    else:
                        with self.assertRaisesRegex(cache_module.CacheError, "identity|namespace"):
                            manager.seed(target)
                staging = next(target.glob(".lake-seed-*"))
                self.assertEqual(b"preserve", (staging / "unknown").read_bytes())
                self.assertTrue(saved.is_dir())

    def _warm_with_external_link(self, manager: cache_module.HotMainCache, external: Path) -> None:
        def build_with_link(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                link = project / ".lake" / "packages" / "external"
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(external, target_is_directory=True)
            return result

        manager.warm(_test_command_callback=build_with_link)

    def test_seed_rejects_writable_and_read_only_external_links(self) -> None:
        for read_only in (False, True):
            with self.subTest(read_only=read_only):
                manager = self.manager(runtime=self.base / f"runtime-external-{read_only}")
                external = self.base / f"external-package-{read_only}"
                external.mkdir()
                marker = external / "marker"
                marker.write_bytes(b"external")
                if read_only:
                    marker.chmod(0o444)
                    external.chmod(0o555)
                self._warm_with_external_link(manager, external)
                target = self.issue_worktree(f"external-target-{read_only}")
                with self.assertRaisesRegex(
                    cache_module.CacheError, "escapes private Lake tree"
                ):
                    manager.seed(target)
                self.assertEqual(b"external", marker.read_bytes())
                self.assertFalse((target / ".lake").exists())
                self.assertEqual([], list(target.glob(".lake.backup-*")))

    def test_seed_accepts_relative_link_contained_in_private_tree(self) -> None:
        manager = self.manager(runtime=self.base / "runtime-contained-link")

        def build_with_link(
            project: Path,
            command: list[str] | tuple[str, ...],
            log_path: Path,
        ) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                package = project / ".lake" / "packages" / "fixture"
                package.mkdir(parents=True, exist_ok=True)
                (package / "marker").write_bytes(b"inside")
                (package.parent / "alias").symlink_to("fixture", target_is_directory=True)
            return result

        manager.warm(_test_command_callback=build_with_link)
        target = self.issue_worktree("contained-link-target")
        self.assertEqual("seeded", manager.seed(target)["result"])
        self.assertEqual(
            b"inside", (target / ".lake" / "packages" / "alias" / "marker").read_bytes()
        )

    def test_seed_rejects_broken_and_cyclic_private_links(self) -> None:
        for case in ("broken", "cycle"):
            with self.subTest(case=case):
                manager = self.manager(runtime=self.base / f"runtime-link-{case}")

                def build_with_invalid_link(
                    project: Path,
                    command: list[str] | tuple[str, ...],
                    log_path: Path,
                ) -> int:
                    result = fake_success(project, command, log_path)
                    if list(command) == ["fake", "build"]:
                        packages = project / ".lake" / "packages"
                        packages.mkdir(parents=True, exist_ok=True)
                        first = packages / "first"
                        if case == "broken":
                            first.symlink_to("missing")
                        else:
                            first.symlink_to("second")
                            (packages / "second").symlink_to("first")
                    return result

                manager.warm(_test_command_callback=build_with_invalid_link)
                target = self.issue_worktree(f"invalid-link-target-{case}")
                with self.assertRaisesRegex(
                    cache_module.CacheError, "symlink target cannot be resolved"
                ):
                    manager.seed(target)
                self.assertFalse((target / ".lake").exists())

    def test_two_processes_elect_exactly_one_builder(self) -> None:
        counter = self.base / "build-count.txt"
        context = multiprocessing.get_context("fork")
        first = context.Process(target=contention_worker, args=(str(self.repo), str(self.runtime), str(counter)))
        second = context.Process(target=contention_worker, args=(str(self.repo), str(self.runtime), str(counter)))
        first.start()
        second.start()
        first.join(10)
        second.join(10)
        self.assertEqual(0, first.exitcode)
        self.assertEqual(0, second.exitcode)
        self.assertEqual(
            ["materialize", "build"],
            counter.read_text(encoding="utf-8").splitlines(),
        )
        metrics = [
            json.loads(line)
            for line in (self.runtime / "metrics" / "hot-main.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(1, sum(item["builds"] for item in metrics))
        self.assertEqual(1, sum(item["lock_waited"] for item in metrics))

    def test_linked_worktrees_share_omitted_runtime_and_builder_lock(self) -> None:
        first = self.issue_worktree("linked-first")
        second = self.issue_worktree("linked-second")
        first_runtime = cache_module.default_runtime_dir(first)
        second_runtime = cache_module.default_runtime_dir(second)
        self.assertEqual(first_runtime, second_runtime)
        self.assertEqual(self.repo.resolve() / ".workflow-runtime", first_runtime)

        counter = self.base / "linked-build-count.txt"
        context = multiprocessing.get_context("fork")
        first_process = context.Process(
            target=linked_worktree_contention_worker,
            args=(str(first), str(counter)),
        )
        second_process = context.Process(
            target=linked_worktree_contention_worker,
            args=(str(second), str(counter)),
        )
        first_process.start()
        second_process.start()
        first_process.join(10)
        second_process.join(10)
        self.assertEqual(0, first_process.exitcode)
        self.assertEqual(0, second_process.exitcode)
        self.assertEqual(["build"], counter.read_text(encoding="utf-8").splitlines())
        metrics = [
            json.loads(line)
            for line in (first_runtime / "metrics" / "hot-main.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(1, sum(item["builds"] for item in metrics))
        self.assertEqual(1, sum(item["lock_waited"] for item in metrics))

    def test_default_runtime_skips_prunable_unresolvable_worktree(self) -> None:
        stale = self.issue_worktree("stale-loop")
        shutil.rmtree(stale)
        stale.symlink_to(stale)

        records = cache_module.git_worktrees(self.repo)
        self.assertTrue(next(record for record in records if record.path == stale).prunable)
        self.assertEqual(
            self.repo.resolve() / ".workflow-runtime",
            cache_module.default_runtime_dir(self.repo),
        )

    def test_default_runtime_resolution_errors_fail_closed(self) -> None:
        class BrokenPath:
            def __init__(self, error: BaseException):
                self.error = error

            def resolve(self, *, strict: bool = False) -> Path:
                raise self.error

        for error in (RuntimeError("symlink loop"), PermissionError("denied")):
            with self.subTest(error=type(error).__name__):
                records = [
                    cache_module.WorktreeRecord(
                        path=BrokenPath(error),
                        head=self.commit,
                        bare=False,
                        prunable=False,
                    )
                ]
                with mock.patch.object(cache_module, "git_worktrees", return_value=records):
                    with self.assertRaisesRegex(cache_module.CacheError, "pass --runtime-dir"):
                        cache_module.default_runtime_dir(self.repo)

    def test_cli_default_runtime_resolution_failures_are_concise(self) -> None:
        missing = self.base / "missing-repository"
        loop = self.base / "repository-loop"
        loop.symlink_to(loop)
        for repo_root in (missing, loop):
            with self.subTest(repo_root=repo_root.name):
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    result = cache_module.main(
                        ["--repo-root", str(repo_root), "status"]
                    )
                self.assertEqual(2, result)
                self.assertTrue(stderr.getvalue().startswith("error: "))
                self.assertIn("pass --runtime-dir explicitly", stderr.getvalue())

    def test_cli_runtime_default_and_explicit_override(self) -> None:
        parser = cache_module.build_parser()
        with mock.patch.object(cache_module, "HotMainCache") as constructor:
            constructor.return_value.status.return_value = {}

            cache_module.run_cli(
                parser.parse_args(["--repo-root", str(self.repo), "status"])
            )
            self.assertEqual(
                self.repo.resolve() / ".workflow-runtime",
                constructor.call_args.args[2],
            )

            constructor.reset_mock()
            cache_module.run_cli(
                parser.parse_args(
                    [
                        "--repo-root",
                        str(self.repo),
                        "--runtime-dir",
                        "custom-runtime",
                        "status",
                    ]
                )
            )
            self.assertEqual(self.repo.resolve() / "custom-runtime", constructor.call_args.args[2])

            constructor.reset_mock()
            absolute_runtime = self.base / "absolute-runtime"
            cache_module.run_cli(
                parser.parse_args(
                    [
                        "--repo-root",
                        str(self.repo),
                        "--runtime-dir",
                        str(absolute_runtime),
                        "status",
                    ]
                )
            )
            self.assertEqual(absolute_runtime, constructor.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
