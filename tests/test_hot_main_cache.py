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

    def mathlib_fixture(self) -> tuple[Path, str, str]:
        source = self.base / "mathlib-source"
        commit, tree = initialize_mathlib_source(source)
        write_mathlib_pin(self.repo, commit)
        run_git(self.repo, "add", "lake-manifest.json")
        run_git(self.repo, "commit", "-m", "pin mathlib fixture")
        return source, commit, tree

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
        fake_module = types.SimpleNamespace(
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

        fake_module = types.SimpleNamespace(
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

    def test_prepare_rejects_target_module_and_pin_substitution_before_load(self) -> None:
        manager = self.manager(recipe=MATERIALIZING_TEST_RECIPE)
        manager.warm(
            _test_command_callback=fake_success,
            _test_source_verifier=fake_source_verifier,
        )
        archive = self.base / "foundation-target-input.tar.gz"
        archive.write_bytes(b"authenticated")
        original_publish = manager._publish_seed_locked
        for index, relative in enumerate(
            ("scripts/materialize_mipstarre.py", "references/mipstarre-upstream.json")
        ):
            with self.subTest(relative=relative):
                target = self.issue_worktree(f"prepare-target-input-substitution-{index}")

                def publish_then_substitute(*args: object, **kwargs: object) -> object:
                    result = original_publish(*args, **kwargs)
                    path = target / relative
                    substitute = path.with_name(path.name + ".substitute")
                    substitute.write_bytes(b"substituted target input\n")
                    os.replace(substitute, path)
                    return result

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
                    "_publish_seed_locked",
                    side_effect=publish_then_substitute,
                ), mock.patch.object(
                    manager,
                    "_load_identity_module",
                    side_effect=AssertionError("substituted target module was loaded"),
                ):
                    with self.assertRaisesRegex(
                        cache_module.CacheError, "exact main cache identity"
                    ):
                        manager.prepare(target)
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

        def mutate_after_snapshot(root: Path, _pin: object) -> dict[str, object]:
            evidence = cache_module.authored_tree_facts_on_disk(root)
            authored = root / "MIPStarRE" / "QPBT"
            authored.mkdir(parents=True, exist_ok=True)
            (authored / "VerifierDrift.lean").write_text(
                "def verifierDrift := true\n", encoding="ascii"
            )
            return {"status": "verified", **evidence}

        fake_module = types.SimpleNamespace(
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
        fake_module = types.SimpleNamespace(
            load_pin=lambda _path: {},
            validate_project_pins=lambda _root, _pin: None,
            materialize=lambda *_args, **_kwargs: {"status": "published"},
            verify_materialized=lambda *_args: {"status": "verified", **authored},
        )

        def fail_metric(_metric: object) -> None:
            self.assertEqual(1, len(list(target.glob(".lake.backup-*"))))
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

    def test_seed_failed_old_to_backup_rename_preserves_original(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("seed-old-rename-failure")
        original_lake = target / ".lake"
        original_lake.mkdir()
        (original_lake / "original-marker").write_text("preserve\n", encoding="ascii")
        real_replace = os.replace

        def fail_old_move(source: object, destination: object) -> None:
            if Path(source) == original_lake and Path(destination).name.startswith(".lake.backup-"):
                raise OSError("injected old-to-backup rename failure")
            real_replace(source, destination)

        with mock.patch.object(cache_module.os, "replace", side_effect=fail_old_move):
            with self.assertRaisesRegex(OSError, "old-to-backup rename failure"):
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
            side_effect=KeyboardInterrupt("injected post-publication interruption"),
        ):
            with self.assertRaises(KeyboardInterrupt):
                manager.seed(target, replace=True)

        self.assertEqual(
            "preserve\n", (original_lake / "original-marker").read_text(encoding="ascii")
        )
        self.assertFalse((original_lake / "build" / "QPBT.olean").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
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

        def publish_then_interrupt(*args: object, **kwargs: object) -> object:
            publish(*args, **kwargs)
            raise KeyboardInterrupt("injected publisher handoff interruption")

        with mock.patch.object(
            manager, "_preflight_authenticated_inputs", return_value={"required": True}
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

        def fail_metric(_metric: object) -> None:
            self.assertEqual(1, len(list(target.glob(".lake.backup-*"))))
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
            if not injected:
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
        fake_module = types.SimpleNamespace(
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

        def blocking_verify(root: Path, _pin: object) -> dict[str, object]:
            evidence = cache_module.authored_tree_facts_on_disk(root)
            verifier_entered.set()
            if not release_verifier.wait(5):
                raise AssertionError("interleaving regression timed out")
            return {"status": "verified", **evidence}

        fake_module = types.SimpleNamespace(
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
        self.assertTrue(verifier_entered.wait(5))
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

        def copy_then_tamper(source: Path, destination: Path) -> cache_module.CopyStats:
            copied = original_copy(source, destination)
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

    def _crash_seed_after_rename(
        self,
        manager: cache_module.HotMainCache,
        target: Path,
        rename_number: int,
    ) -> None:
        real_replace = cache_module.os.replace
        context = multiprocessing.get_context("fork")

        def interrupted_seed() -> None:
            renames = 0

            def kill_at_boundary(source: object, destination: object) -> None:
                nonlocal renames
                real_replace(source, destination)
                destination_path = Path(destination)
                if (
                    destination_path.name.startswith(".lake.backup-")
                    or destination_path == target / ".lake"
                ):
                    renames += 1
                    if renames == rename_number:
                        os.kill(os.getpid(), signal.SIGKILL)

            cache_module.os.replace = kill_at_boundary
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
                    cache_module.CacheError, "unowned interrupted seed backup"
                ):
                    manager.seed(target)
                self.assertEqual(b"decoy", (backup / "decoy-bytes").read_bytes())
                if destination_present:
                    self.assertEqual(
                        b"current", (destination / "current-user-bytes").read_bytes()
                    )
                else:
                    self.assertFalse(destination.exists())

    def test_seed_first_rename_recovery_preserves_replace_false(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-replace-false")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 1)
        with self.assertRaisesRegex(cache_module.CacheError, "target .lake already exists"):
            manager.seed(target)
        self.assertEqual(b"keep", (original / "original-marker").read_bytes())
        self.assertEqual([], list(target.glob(".lake.backup-*")))

    def test_seed_recovers_before_invalid_cache_admission(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-invalid-cache")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 1)
        cache_module.make_owner_writable(manager.snapshot_dir)
        manager.ready_path.write_text("0" * 64 + "\n", encoding="ascii")
        with self.assertRaisesRegex(cache_module.CacheError, "deep artifact verification"):
            manager.seed(target, replace=True)
        self.assertEqual(b"keep", (original / "original-marker").read_bytes())
        self.assertEqual([], list(target.glob(".lake.backup-*")))

    def test_prepare_recovers_before_input_admission(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-invalid-input")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 1)
        with mock.patch.object(
            manager,
            "_preflight_authenticated_inputs",
            side_effect=cache_module.CacheError("injected input admission failure"),
        ):
            with self.assertRaisesRegex(cache_module.CacheError, "input admission failure"):
                manager.prepare(target, replace_seed=True)
        self.assertEqual(b"keep", (original / "original-marker").read_bytes())
        self.assertEqual([], list(target.glob(".lake.backup-*")))

    def test_seed_rejects_tampered_journal_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-tampered")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 1)
        backup = next(target.glob(".lake.backup-*"))
        journal = manager._seed_transaction_dir(target) / "journal.json"
        journal.write_bytes(journal.read_bytes().replace(b'"replace":true', b'"replace":false'))
        with self.assertRaisesRegex(cache_module.CacheError, "authentication failed"):
            manager.seed(target, replace=True)
        self.assertFalse(original.exists())
        self.assertEqual(b"keep", (backup / "original-marker").read_bytes())

    def test_seed_rejects_wrong_backup_identity_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-wrong-backup")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 1)
        backup = next(target.glob(".lake.backup-*"))
        (backup / "unrecorded").write_bytes(b"changed")
        with self.assertRaisesRegex(cache_module.CacheError, "does not match"):
            manager.seed(target, replace=True)
        self.assertFalse(original.exists())
        self.assertEqual(b"changed", (backup / "unrecorded").read_bytes())

    def test_seed_rejects_extra_backup_without_mutation(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-extra-backup")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 1)
        owned = next(target.glob(".lake.backup-*"))
        extra = target / ".lake.backup-extra"
        extra.mkdir()
        (extra / "decoy").write_bytes(b"decoy")
        with self.assertRaisesRegex(cache_module.CacheError, "ambiguous interrupted"):
            manager.seed(target, replace=True)
        self.assertFalse(original.exists())
        self.assertEqual(b"keep", (owned / "original-marker").read_bytes())
        self.assertEqual(b"decoy", (extra / "decoy").read_bytes())

    def test_seed_second_rename_recovery_restores_and_retains_replacement(self) -> None:
        manager = self.manager()
        manager.warm(_test_command_callback=fake_success)
        target = self.issue_worktree("journal-second-rename")
        original = target / ".lake"
        original.mkdir()
        (original / "original-marker").write_bytes(b"keep")
        self._crash_seed_after_rename(manager, target, 2)
        with self.assertRaisesRegex(cache_module.CacheError, "target .lake already exists"):
            manager.seed(target)
        self.assertEqual(b"keep", (original / "original-marker").read_bytes())
        retained = list(target.glob(".lake.retained-*"))
        self.assertEqual(1, len(retained))
        self.assertTrue((retained[0] / "build" / "QPBT.olean").is_file())
        self.assertEqual([], list(target.glob(".lake.backup-*")))

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
        self.assertEqual(1, len(list(target.glob(".lake.backup-*"))))
        with self.assertRaisesRegex(cache_module.CacheError, "target .lake already exists"):
            manager.seed(target)
        self.assertTrue((target / ".lake" / "build" / "QPBT.olean").is_file())
        self.assertFalse((target / ".lake" / "original-marker").exists())
        self.assertEqual([], list(target.glob(".lake.backup-*")))
        self.assertFalse(manager._seed_transaction_dir(target).exists())

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
