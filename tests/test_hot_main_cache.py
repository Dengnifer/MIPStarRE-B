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
import stat
import subprocess
import sys
import tarfile
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

PACKAGE_MATERIALIZING_TEST_RECIPE = cache_module.BuildRecipe.for_testing(
    package_materialize_command=("fake", "package-materialize"),
    package_verify_command=("fake", "package-verify"),
    dependency_command=("fake", "deps"),
    build_command=("fake", "build"),
    additional_identity_files=(
        "references/lake-packages.json",
        "references/mathlib-lake-manifest.json",
        "scripts/materialize_lake_packages.py",
    ),
    recipe_id="test-fake-package-materializing-build",
)


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
        (project / ".lake" / "package-overrides.json").write_text("{}\n", encoding="ascii")
    elif list(command) == ["fake", "package-verify"]:
        marker = project / ".lake" / "packages" / "fixture" / "marker"
        if not marker.is_file() or marker.read_text(encoding="ascii") != "package\n":
            return 9
    elif list(command) == ["fake", "deps"]:
        package = project / ".lake" / "packages" / "mathlib"
        package.mkdir(parents=True, exist_ok=True)
        (package / "marker").write_text("dependency\n", encoding="utf-8")
    elif list(command) == ["fake", "build"]:
        build = project / ".lake" / "build"
        build.mkdir(parents=True, exist_ok=True)
        (build / "QPBT.olean").write_text("compiled-main\n", encoding="utf-8")
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
        "authored_qpbt_files": 0,
        "authored_qpbt_bytes": 0,
        "authored_qpbt_sha256": hashlib.sha256().hexdigest(),
    }


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

    def test_packages_are_identity_bound_materialized_and_verified_before_lake_steps(self) -> None:
        manager = self.manager(recipe=PACKAGE_MATERIALIZING_TEST_RECIPE)
        calls: list[list[str]] = []

        def callback(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            calls.append(list(command))
            return fake_success(project, command, log_path)

        self.assertEqual("built", manager.warm(_test_command_callback=callback)["result"])
        self.assertEqual(
            [
                ["fake", "package-materialize"],
                ["fake", "package-verify"],
                ["fake", "deps"],
                ["fake", "build"],
                ["fake", "package-verify"],
            ],
            calls,
        )
        self.assertIn("references/lake-packages.json", manager.identity.inputs)
        self.assertIn("references/mathlib-lake-manifest.json", manager.identity.inputs)
        self.assertIn("scripts/materialize_lake_packages.py", manager.identity.inputs)
        manifest = json.loads(manager.manifest_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(manifest["package_materialize_seconds"], 0)
        self.assertGreaterEqual(manifest["package_verify_seconds"], 0)

    def test_warm_rejects_post_build_package_drift(self) -> None:
        manager = self.manager(
            runtime=self.base / "runtime-package-drift",
            recipe=PACKAGE_MATERIALIZING_TEST_RECIPE,
        )

        def mutate_package(project: Path, command: list[str] | tuple[str, ...], log_path: Path) -> int:
            result = fake_success(project, command, log_path)
            if list(command) == ["fake", "build"]:
                (project / ".lake" / "packages" / "fixture" / "marker").write_text(
                    "tampered\n", encoding="ascii"
                )
            return result

        with self.assertRaisesRegex(
            cache_module.CacheError, "Lake package verification command failed"
        ):
            manager.warm(_test_command_callback=mutate_package)
        self.assertFalse(manager.is_ready())
        failures = list((manager.runtime_dir / "cache" / "failures").iterdir())
        self.assertEqual(1, len(failures))
        failure = json.loads((failures[0] / "failure.json").read_text(encoding="utf-8"))
        self.assertIn("Lake package verification command failed", failure["error"])

    def test_canonical_lake_commands_require_override_and_reject_updates(self) -> None:
        canonical = cache_module.CANONICAL_BUILD_RECIPE
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
            ), mock.patch.object(manager, "_run_logged", side_effect=fake_run):
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
            ), mock.patch.object(manager, "_run_logged", side_effect=fake_run):
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
            ), mock.patch.object(manager, "_run_logged", side_effect=fail_reservoir):
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

        with self.assertRaisesRegex(cache_module.CacheError, "project source changed"):
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
