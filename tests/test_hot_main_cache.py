from __future__ import annotations

from contextlib import redirect_stderr
import fcntl
import io
import json
import multiprocessing
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import hot_main_cache as cache_module  # noqa: E402


TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
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
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "initial")
    return run_git(root, "rev-parse", "HEAD")


def fake_success(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
    if list(command) == ["fake", "deps"]:
        package = project / ".lake" / "packages" / "mathlib"
        package.mkdir(parents=True, exist_ok=True)
        (package / "marker").write_text("dependency\n", encoding="utf-8")
    elif list(command) == ["fake", "build"]:
        build = project / ".lake" / "build"
        build.mkdir(parents=True, exist_ok=True)
        (build / "QPBT.olean").write_text("compiled-main\n", encoding="utf-8")
    return 0


def contention_worker(repo: str, runtime: str, counter: str) -> None:
    manager = cache_module.HotMainCache(
        Path(repo),
        Path(repo),
        Path(runtime),
        _test_recipe=TEST_RECIPE,
    )

    def callback(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
        if list(command) == ["fake", "build"]:
            with Path(counter).open("a+", encoding="utf-8") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                stream.write("build\n")
                stream.flush()
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            time.sleep(0.25)
        return fake_success(project, command, log_path)

    manager.warm(_test_command_callback=callback)


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

    def test_identity_comes_from_exact_main_not_dirty_worktree(self) -> None:
        first = self.manager().identity
        (self.repo / "lakefile.toml").write_text("dirty feature content\n", encoding="utf-8")
        second = self.manager().identity
        self.assertEqual(first.cache_key, second.cache_key)
        self.assertEqual(self.commit, second.main_commit)

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

        with self.assertRaisesRegex(cache_module.CacheError, "tracked source changed"):
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
        self.assertEqual(["build"], counter.read_text(encoding="utf-8").splitlines())
        metrics = [
            json.loads(line)
            for line in (self.runtime / "metrics" / "hot-main.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(1, sum(item["builds"] for item in metrics))
        self.assertEqual(1, sum(item["lock_waited"] for item in metrics))


if __name__ == "__main__":
    unittest.main()
