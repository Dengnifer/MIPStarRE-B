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
        symbolic = git_identity.resolve_git_identity(self.repo, "main")
        exact = git_identity.resolve_git_identity(self.repo, self.head_commit)
        self.assertEqual(
            git_identity.GitIdentity(self.head_commit, self.head_tree),
            symbolic,
        )
        self.assertEqual(symbolic, exact)

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

    def test_tree_mismatch_is_rejected_after_object_resolution(self) -> None:
        with self.assertRaisesRegex(git_identity.GitIdentityError, "tree mismatch"):
            git_identity.resolve_git_identity(
                self.repo,
                self.base_commit,
                expected_tree=self.head_tree,
            )

    def test_detached_head_does_not_replace_the_declared_review_base(self) -> None:
        git(self.repo, "checkout", "--detach", self.head_commit)
        identity = git_identity.resolve_git_identity(self.repo, self.base_commit)
        self.assertEqual(self.base_commit, identity.commit)
        self.assertEqual(self.base_tree, identity.tree)
        self.assertEqual(self.head_commit, git(self.repo, "rev-parse", "HEAD"))

    def test_repository_subdirectory_is_not_accepted_as_the_worktree(self) -> None:
        child = self.repo / "child"
        child.mkdir()
        with self.assertRaisesRegex(git_identity.GitIdentityError, "repository root"):
            git_identity.resolve_git_identity(child, "main")

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
