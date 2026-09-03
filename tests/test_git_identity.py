from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import git_identity  # noqa: E402
import hot_main_cache  # noqa: E402


def git(cwd: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
        env={
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.defpath,
        },
    )
    return completed.stdout.strip()


class GitIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Git Identity Test")
        git(self.repo, "config", "user.email", "git-identity@example.invalid")
        (self.repo / "tracked.txt").write_text("base\n", encoding="ascii")
        git(self.repo, "add", "tracked.txt")
        git(self.repo, "commit", "-m", "base")
        self.base_commit = git(self.repo, "rev-parse", "HEAD")
        self.base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        (self.repo / "tracked.txt").write_text("head\n", encoding="ascii")
        git(self.repo, "commit", "-am", "head")
        self.head_commit = git(self.repo, "rev-parse", "HEAD")
        self.head_tree = git(self.repo, "rev-parse", "HEAD^{tree}")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_symbolic_and_exact_refs_resolve_to_proven_commit_and_tree(self) -> None:
        with (
            git_identity.resolve_git_identity(self.repo, "main") as symbolic,
            git_identity.resolve_git_identity(self.repo, self.head_commit) as exact,
        ):
            self.assertEqual(self.head_commit, symbolic.commit)
            self.assertEqual(self.head_tree, symbolic.tree)
            self.assertEqual(self.repo, symbolic.worktree)
            self.assertEqual(symbolic, exact)

    def test_ambiguous_shorthand_ref_requires_a_fully_qualified_name(self) -> None:
        git(self.repo, "tag", "main", self.base_commit)
        with self.assertRaisesRegex(git_identity.GitIdentityError, "ambiguous"):
            git_identity.resolve_git_identity(self.repo, "main")
        with (
            git_identity.resolve_git_identity(self.repo, "refs/heads/main") as branch,
            git_identity.resolve_git_identity(self.repo, "refs/tags/main") as tag,
        ):
            self.assertEqual(self.head_commit, branch.commit)
            self.assertEqual(self.base_commit, tag.commit)

    def test_cli_returns_the_same_exact_identity(self) -> None:
        arguments = git_identity.build_parser().parse_args(
            ["--worktree", str(self.repo), "main"]
        )
        self.assertEqual(
            {"commit": self.head_commit, "tree": self.head_tree},
            git_identity.run_cli(arguments),
        )

    def test_nonexistent_full_looking_sha_is_rejected(self) -> None:
        guessed = self.head_commit[:7] + ("0" * 33)
        self.assertNotEqual(self.head_commit, guessed)
        with self.assertRaisesRegex(git_identity.GitIdentityError, "rev-parse"):
            git_identity.resolve_git_identity(self.repo, guessed)

    def test_sha256_repository_rejects_sha1_length_prefix_and_accepts_full_id(self) -> None:
        repository = self.root / "sha256-repo"
        repository.mkdir()
        git(repository, "init", "--object-format=sha256", "-b", "main")
        git(repository, "config", "user.name", "Git Identity Test")
        git(repository, "config", "user.email", "git-identity@example.invalid")
        (repository / "tracked.txt").write_text("sha256\n", encoding="ascii")
        git(repository, "add", "tracked.txt")
        git(repository, "commit", "-m", "sha256 base")
        commit = git(repository, "rev-parse", "HEAD")
        tree = git(repository, "rev-parse", "HEAD^{tree}")
        self.assertEqual(64, len(commit))

        with self.assertRaisesRegex(git_identity.GitIdentityError, "object format length"):
            git_identity.resolve_git_identity(repository, commit[:40])
        with git_identity.resolve_git_identity(repository, commit) as identity:
            self.assertEqual(commit, identity.commit)
            self.assertEqual(tree, identity.tree)

    def test_object_format_and_resolution_share_one_repository_binding(self) -> None:
        repository = self.root / "sha256-bound-repo"
        repository.mkdir()
        git(repository, "init", "--object-format=sha256", "-b", "main")
        git(repository, "config", "user.name", "Git Identity Test")
        git(repository, "config", "user.email", "git-identity@example.invalid")
        (repository / "tracked.txt").write_text("sha256\n", encoding="ascii")
        git(repository, "add", "tracked.txt")
        git(repository, "commit", "-m", "sha256 base")
        commit = git(repository, "rev-parse", "HEAD")
        tree = git(repository, "rev-parse", "HEAD^{tree}")

        substitute = self.root / "sha1-substitute"
        substitute.mkdir()
        git(substitute, "init", "-b", "main")
        authentic_git = self.root / "sha256-authentic.git"
        original_run = subprocess.run
        format_swaps = 0

        def swap_format_repository(
            *arguments: object,
            **keywords: object,
        ) -> subprocess.CompletedProcess[str]:
            nonlocal format_swaps
            command = arguments[0]
            if not (
                isinstance(command, list)
                and command[-2:] == ["rev-parse", "--show-object-format=input"]
            ):
                return original_run(*arguments, **keywords)
            (repository / ".git").rename(authentic_git)
            (substitute / ".git").rename(repository / ".git")
            try:
                format_swaps += 1
                return original_run(*arguments, **keywords)
            finally:
                (repository / ".git").rename(substitute / ".git")
                authentic_git.rename(repository / ".git")

        with mock.patch.object(
            git_identity.subprocess,
            "run",
            side_effect=swap_format_repository,
        ):
            with self.assertRaisesRegex(git_identity.GitIdentityError, "object format length"):
                git_identity.resolve_git_identity(
                    repository,
                    commit[:40],
                    expected_tree=tree,
                )
            with git_identity.resolve_git_identity(
                repository,
                commit,
                expected_tree=tree,
            ) as identity:
                self.assertEqual(commit, identity.commit)
                self.assertEqual(tree, identity.tree)
        self.assertEqual(2, format_swaps)

    def test_tree_mismatch_is_rejected_after_object_resolution(self) -> None:
        with self.assertRaisesRegex(git_identity.GitIdentityError, "tree mismatch"):
            git_identity.resolve_git_identity(
                self.repo,
                self.base_commit,
                expected_tree=self.head_tree,
            )

    def test_detached_head_does_not_replace_the_declared_review_base(self) -> None:
        git(self.repo, "checkout", "--detach", self.head_commit)
        with git_identity.resolve_git_identity(self.repo, self.base_commit) as identity:
            self.assertEqual(self.base_commit, identity.commit)
            self.assertEqual(self.base_tree, identity.tree)
            self.assertEqual(self.head_commit, git(self.repo, "rev-parse", "HEAD"))

    def test_bound_descriptor_is_retained_until_explicit_close(self) -> None:
        identity = git_identity.resolve_git_identity(self.repo, "main")
        descriptor = identity._worktree_fd
        assert identity._repository_binding is not None
        repository_descriptors = identity._repository_binding.descriptors()
        opened = os.fstat(descriptor)
        self.assertEqual(
            (identity.worktree_device, identity.worktree_inode),
            (opened.st_dev, opened.st_ino),
        )
        identity.close()
        self.assertEqual(-1, identity._worktree_fd)
        with self.assertRaises(OSError):
            os.fstat(descriptor)
        for repository_descriptor in repository_descriptors:
            with self.assertRaises(OSError):
                os.fstat(repository_descriptor)
        identity.close()

    def test_repository_subdirectory_is_not_accepted_as_the_worktree(self) -> None:
        child = self.repo / "child"
        child.mkdir()
        with self.assertRaisesRegex(git_identity.GitIdentityError, "repository root"):
            git_identity.resolve_git_identity(child, "main")

    def test_bare_repository_is_not_accepted_as_a_worktree(self) -> None:
        bare = self.root / "bare.git"
        git(self.root, "init", "--bare", str(bare))
        with self.assertRaisesRegex(git_identity.GitIdentityError, "not a Git worktree"):
            git_identity.resolve_git_identity(bare, "HEAD")

    def test_symlink_alias_is_rejected_before_and_after_retarget(self) -> None:
        alias = self.root / "worktree-alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(git_identity.GitIdentityError, "symlink component"):
            git_identity.resolve_git_identity(alias, "main")
        alias.unlink()
        alternate = self.root / "alternate"
        alternate.mkdir()
        alias.symlink_to(alternate, target_is_directory=True)
        with self.assertRaisesRegex(git_identity.GitIdentityError, "symlink component"):
            git_identity.resolve_git_identity(alias, "main")

    def test_symlink_before_parent_component_is_rejected_before_normalization(self) -> None:
        alias = self.root / "lexical-alias"
        alias.symlink_to("/", target_is_directory=True)
        lexical_path = alias / ".." / self.repo.name
        self.assertEqual(self.repo, Path(os.path.abspath(lexical_path)))

        with (
            mock.patch.object(git_identity.subprocess, "run") as run,
            self.assertRaisesRegex(git_identity.GitIdentityError, "unsafe parent component"),
        ):
            git_identity.resolve_git_identity(lexical_path, "main")
        run.assert_not_called()

    def test_linked_worktree_gitfile_and_common_directory_are_supported(self) -> None:
        linked = self.root / "linked"
        git(self.repo, "worktree", "add", "--detach", str(linked), self.base_commit)
        self.assertTrue((linked / ".git").is_file())

        with git_identity.resolve_git_identity(
            linked,
            self.base_commit,
            expected_tree=self.base_tree,
        ) as identity:
            self.assertEqual(self.base_commit, identity.commit)
            self.assertEqual(self.base_tree, identity.tree)
            self.assertIsNotNone(identity._repository_binding)
            assert identity._repository_binding is not None
            self.assertIsNotNone(identity._repository_binding.git_entry_file)
            self.assertIsNotNone(identity._repository_binding.common_dir_file)

    def test_root_replacement_during_git_call_is_rejected(self) -> None:
        original_run = subprocess.run
        moved = self.root / "moved-repo"

        def replace_root(*arguments: object, **keywords: object) -> subprocess.CompletedProcess[str]:
            completed = original_run(*arguments, **keywords)
            command = arguments[0]
            if isinstance(command, list) and command[-2:] == ["rev-parse", "--show-prefix"]:
                self.repo.rename(moved)
                self.repo.mkdir()
            return completed

        with (
            mock.patch.object(git_identity.subprocess, "run", side_effect=replace_root),
            self.assertRaisesRegex(git_identity.GitIdentityError, "changed during authentication"),
        ):
            git_identity.resolve_git_identity(self.repo, "main")

    def test_transient_aba_swap_cannot_substitute_git_execution(self) -> None:
        substitute = self.root / "substitute-repo"
        substitute.mkdir()
        git(substitute, "init", "-b", "main")
        git(substitute, "config", "user.name", "Git Identity Test")
        git(substitute, "config", "user.email", "git-identity@example.invalid")
        (substitute / "tracked.txt").write_text("substitute\n", encoding="ascii")
        git(substitute, "add", "tracked.txt")
        git(substitute, "commit", "-m", "substitute")
        substitute_tree = git(substitute, "rev-parse", "HEAD^{tree}")
        moved = self.root / "original-repo-moved"
        original_run = subprocess.run
        bound_calls = 0

        def swap_run_restore(
            *arguments: object,
            **keywords: object,
        ) -> subprocess.CompletedProcess[str]:
            nonlocal bound_calls
            cwd = keywords.get("cwd")
            pass_fds = keywords.get("pass_fds")
            self.assertIsInstance(cwd, str)
            self.assertRegex(str(cwd), r"^/proc/self/fd/[0-9]+$")
            self.assertIsInstance(pass_fds, tuple)
            self.assertGreaterEqual(len(pass_fds), 3)
            self.assertIn(int(str(cwd).rsplit("/", 1)[-1]), pass_fds)
            self.repo.rename(moved)
            substitute.rename(self.repo)
            try:
                completed = original_run(*arguments, **keywords)
                bound_calls += 1
                return completed
            finally:
                self.repo.rename(substitute)
                moved.rename(self.repo)

        with mock.patch.object(
            git_identity.subprocess,
            "run",
            side_effect=swap_run_restore,
        ):
            with git_identity.resolve_git_identity(self.repo, "main") as identity:
                self.assertEqual(self.head_commit, identity.commit)
                self.assertEqual(self.head_tree, identity.tree)
            with self.assertRaisesRegex(git_identity.GitIdentityError, "tree mismatch"):
                git_identity.resolve_git_identity(
                    self.repo,
                    "main",
                    expected_tree=substitute_tree,
                )
        self.assertGreater(bound_calls, 0)

    def test_missing_promisor_object_never_invokes_lazy_fetch_transport(self) -> None:
        sentinel = self.root / "transport-invoked"
        remote = self.root / "sentinel-remote"
        remote.write_text(
            f"#!/bin/sh\nprintf invoked > {sentinel}\nexit 1\n",
            encoding="ascii",
        )
        remote.chmod(0o755)
        git(self.repo, "config", "remote.origin.url", f"ext::{remote}")
        git(self.repo, "config", "remote.origin.promisor", "true")
        git(self.repo, "config", "remote.origin.partialclonefilter", "blob:none")
        git(self.repo, "config", "protocol.ext.allow", "always")
        object_path = self.repo / ".git" / "objects" / self.base_commit[:2] / self.base_commit[2:]
        self.assertTrue(object_path.is_file())
        object_path.unlink()

        probe = subprocess.run(
            ["git", "cat-file", "-e", self.base_commit],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
            env={
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": os.defpath,
            },
        )
        self.assertNotEqual(0, probe.returncode)
        self.assertTrue(sentinel.is_file())
        sentinel.unlink()

        with self.assertRaises(git_identity.GitIdentityError):
            git_identity.resolve_git_identity(self.repo, self.base_commit)
        self.assertFalse(sentinel.exists())

    def test_invalid_cache_main_has_zero_build_publication_or_metric_effects(self) -> None:
        runtime = self.root / "runtime"
        guessed = self.head_commit[:7] + ("f" * 33)
        self.assertNotEqual(self.head_commit, guessed)
        arguments = hot_main_cache.build_parser().parse_args(
            [
                "--repo-root",
                str(self.repo),
                "--runtime-dir",
                str(runtime),
                "--main-commit",
                guessed,
                "warm",
            ]
        )
        with (
            mock.patch.object(hot_main_cache.HotMainCache, "warm") as build,
            mock.patch.object(hot_main_cache.HotMainCache, "_append_metric") as metric,
            self.assertRaises(hot_main_cache.CacheError),
        ):
            hot_main_cache.run_cli(arguments)
        build.assert_not_called()
        metric.assert_not_called()
        self.assertFalse(runtime.exists())


if __name__ == "__main__":
    unittest.main()
