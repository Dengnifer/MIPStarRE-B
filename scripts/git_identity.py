#!/usr/bin/env python3
"""Resolve and authenticate immutable Git commit/tree identities."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Sequence


FULL_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class GitIdentityError(Exception):
    """Git could not authenticate the requested commit and tree."""


@dataclass(frozen=True)
class GitIdentity:
    """A Git-resolved commit, root tree, and bound worktree incarnation."""

    commit: str
    tree: str
    worktree: Path
    worktree_device: int
    worktree_inode: int


def _git_environment() -> dict[str, str]:
    """Return a minimal environment for non-interactive Git plumbing."""

    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
    }


def _worktree_identity(path: Path) -> tuple[int, int]:
    """Return the directory identity after rejecting every symlink component."""

    current = Path(path.anchor)
    try:
        for component in path.parts[1:]:
            current /= component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise GitIdentityError(
                    f"Git worktree path contains a symlink component: {current}"
                )
        metadata = path.lstat()
    except OSError as error:
        raise GitIdentityError(f"could not inspect Git worktree {path}: {error}") from error
    if not stat.S_ISDIR(metadata.st_mode):
        raise GitIdentityError(f"Git worktree is not a directory: {path}")
    return metadata.st_dev, metadata.st_ino


def _assert_worktree_identity(
    cwd: Path,
    expected_identity: tuple[int, int],
) -> None:
    actual_identity = _worktree_identity(cwd)
    if actual_identity != expected_identity:
        raise GitIdentityError(
            f"Git worktree changed during authentication: {cwd}"
        )


def recheck_git_identity_worktree(identity: GitIdentity) -> None:
    """Fail unless ``identity.worktree`` still names the authenticated directory."""

    _assert_worktree_identity(
        identity.worktree,
        (identity.worktree_device, identity.worktree_inode),
    )


def _git(
    cwd: Path,
    arguments: Sequence[str],
    *,
    worktree_identity: tuple[int, int],
) -> str:
    _assert_worktree_identity(cwd, worktree_identity)
    command = [
        "git",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.fsmonitor=false",
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=_git_environment(),
        )
    except OSError as error:
        raise GitIdentityError(f"could not run git: {error}") from error
    _assert_worktree_identity(cwd, worktree_identity)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        if not detail:
            detail = f"exit code {completed.returncode}"
        raise GitIdentityError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.strip()


def _full_oid(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if not FULL_GIT_OID_RE.fullmatch(normalized):
        raise GitIdentityError(f"Git resolved an invalid {label} object id {value!r}")
    return normalized


def _prove_object(
    cwd: Path,
    worktree_identity: tuple[int, int],
    object_id: str,
    expected_type: str,
) -> None:
    _git(cwd, ["cat-file", "-e", object_id], worktree_identity=worktree_identity)
    actual_type = _git(
        cwd,
        ["cat-file", "-t", object_id],
        worktree_identity=worktree_identity,
    )
    if actual_type != expected_type:
        raise GitIdentityError(
            f"Git object {object_id} has type {actual_type!r}, expected {expected_type!r}"
        )


def _canonical_ref(
    cwd: Path,
    worktree_identity: tuple[int, int],
    raw_ref: str,
) -> str:
    """Return one canonical ref name, rejecting Git's ambiguous DWIM cases."""

    if raw_ref == "HEAD":
        return raw_ref
    if raw_ref.startswith("refs/"):
        _git(
            cwd,
            ["check-ref-format", raw_ref],
            worktree_identity=worktree_identity,
        )
        return raw_ref
    _git(
        cwd,
        ["check-ref-format", "--allow-onelevel", raw_ref],
        worktree_identity=worktree_identity,
    )
    ref_names = set(
        _git(
            cwd,
            ["for-each-ref", "--format=%(refname)"],
            worktree_identity=worktree_identity,
        ).splitlines()
    )
    possible_names = {
        f"refs/{raw_ref}",
        f"refs/tags/{raw_ref}",
        f"refs/heads/{raw_ref}",
        f"refs/remotes/{raw_ref}",
        f"refs/remotes/{raw_ref}/HEAD",
    }
    matches = sorted(ref_names & possible_names)
    if len(matches) > 1:
        raise GitIdentityError(
            f"Git ref {raw_ref!r} is ambiguous; use one of: {', '.join(matches)}"
        )
    if not matches:
        raise GitIdentityError(
            f"Git ref {raw_ref!r} does not name a canonical symbolic ref"
        )
    return matches[0]


def resolve_git_identity(
    worktree: Path,
    ref: str,
    *,
    expected_tree: str | None = None,
) -> GitIdentity:
    """Resolve ``ref`` and prove its commit and root-tree objects exist.

    ``ref`` may be a symbolic ref or an exact object ID.  A supplied expected
    tree is treated as admission authority and must match Git's result exactly.
    The current worktree ``HEAD`` is deliberately not compared with ``ref``:
    reviewers bind the PR base while inspecting a detached candidate head.
    """

    if not isinstance(ref, str) or not ref.strip():
        raise GitIdentityError("Git commit ref must be a non-empty string")
    if "\x00" in ref or "\n" in ref or "\r" in ref:
        raise GitIdentityError("Git commit ref contains a forbidden control character")
    try:
        cwd = Path(os.path.abspath(os.fspath(worktree)))
    except (OSError, TypeError, ValueError) as error:
        raise GitIdentityError(f"could not normalize Git worktree {worktree}: {error}") from error
    worktree_identity = _worktree_identity(cwd)

    repository_root = _git(
        cwd,
        ["rev-parse", "--show-toplevel"],
        worktree_identity=worktree_identity,
    )
    try:
        reported_root = Path(os.path.abspath(repository_root))
    except (OSError, TypeError, ValueError) as error:
        raise GitIdentityError(f"Git reported an invalid worktree root: {error}") from error
    if reported_root != cwd:
        raise GitIdentityError(
            f"session worktree must be the Git repository root: expected {cwd}, got {reported_root}"
        )

    raw_ref = ref.strip()
    resolved_ref = (
        raw_ref
        if FULL_GIT_OID_RE.fullmatch(raw_ref)
        else _canonical_ref(cwd, worktree_identity, raw_ref)
    )
    commit = _full_oid(
        _git(
            cwd,
            ["rev-parse", "--verify", "--end-of-options", f"{resolved_ref}^{{commit}}"],
            worktree_identity=worktree_identity,
        ),
        "commit",
    )
    _prove_object(cwd, worktree_identity, commit, "commit")
    tree = _full_oid(
        _git(
            cwd,
            ["rev-parse", "--verify", "--end-of-options", f"{commit}^{{tree}}"],
            worktree_identity=worktree_identity,
        ),
        "tree",
    )
    _prove_object(cwd, worktree_identity, tree, "tree")

    if expected_tree is not None:
        if not isinstance(expected_tree, str):
            raise GitIdentityError("expected Git tree must be a full object ID string")
        expected = expected_tree.strip().lower()
        if not FULL_GIT_OID_RE.fullmatch(expected):
            raise GitIdentityError(
                f"expected Git tree must be a full object ID, got {expected_tree!r}"
            )
        if expected != tree:
            raise GitIdentityError(
                f"Git tree mismatch for {raw_ref!r}: expected {expected}, resolved {tree}"
            )
    _assert_worktree_identity(cwd, worktree_identity)
    return GitIdentity(
        commit=commit,
        tree=tree,
        worktree=cwd,
        worktree_device=worktree_identity[0],
        worktree_inode=worktree_identity[1],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ref", help="symbolic ref or exact commit object ID")
    parser.add_argument(
        "--worktree",
        default=".",
        help="Git worktree root (default: current directory)",
    )
    parser.add_argument("--expected-tree", help="optional exact expected root-tree ID")
    return parser


def run_cli(arguments: argparse.Namespace) -> dict[str, str]:
    identity = resolve_git_identity(
        Path(arguments.worktree),
        arguments.ref,
        expected_tree=arguments.expected_tree,
    )
    return {"commit": identity.commit, "tree": identity.tree}


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        result = run_cli(arguments)
    except GitIdentityError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
