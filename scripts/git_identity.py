#!/usr/bin/env python3
"""Resolve and authenticate immutable Git commit/tree identities."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Sequence


FULL_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
GIT_OBJECT_FORMAT_LENGTHS = {"sha1": 40, "sha256": 64}


class GitIdentityError(Exception):
    """Git could not authenticate the requested commit and tree."""


@dataclass
class _DirectoryProof:
    """A retained directory and the lexical path used to reach it."""

    path: str
    descriptor: int
    device: int
    inode: int


@dataclass
class _FileProof:
    """A retained single-link metadata file with immutable admitted bytes."""

    name: str
    descriptor: int
    signature: tuple[int, int, int, int, int, int, int]
    content: bytes


@dataclass
class _RepositoryBinding:
    """Git directory authorities retained across resolution and publication."""

    git_entry_file: _FileProof | None
    git_dir: _DirectoryProof
    common_dir_file: _FileProof | None
    common_dir: _DirectoryProof

    def descriptors(self) -> tuple[int, ...]:
        descriptors = [self.git_dir.descriptor, self.common_dir.descriptor]
        if self.git_entry_file is not None:
            descriptors.append(self.git_entry_file.descriptor)
        if self.common_dir_file is not None:
            descriptors.append(self.common_dir_file.descriptor)
        return tuple(descriptors)

    def close(self) -> None:
        first_error: BaseException | None = None
        for descriptor in self.descriptors():
            if descriptor < 0:
                continue
            try:
                os.close(descriptor)
            except BaseException as error:
                if first_error is None:
                    first_error = error
        self.git_dir.descriptor = -1
        self.common_dir.descriptor = -1
        if self.git_entry_file is not None:
            self.git_entry_file.descriptor = -1
        if self.common_dir_file is not None:
            self.common_dir_file.descriptor = -1
        if first_error is not None:
            raise first_error


@dataclass(frozen=True)
class GitIdentity:
    """A Git-resolved commit, root tree, and live repository proof."""

    commit: str
    tree: str
    worktree: Path
    worktree_device: int
    worktree_inode: int
    _worktree_fd: int = field(repr=False, compare=False)
    _repository_binding: _RepositoryBinding | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def close(self) -> None:
        """Release the retained worktree descriptor, idempotently."""

        descriptor = self._worktree_fd
        repository_binding = self._repository_binding
        if descriptor < 0 and repository_binding is None:
            return
        object.__setattr__(self, "_worktree_fd", -1)
        object.__setattr__(self, "_repository_binding", None)
        first_error: BaseException | None = None
        if repository_binding is not None:
            try:
                repository_binding.close()
            except BaseException as error:
                first_error = error
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except BaseException as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    def __enter__(self) -> GitIdentity:
        return self

    def __exit__(self, *_exception: object) -> None:
        self.close()


class GitIdentityProofs(dict[str, GitIdentity]):
    """Dispatch-scoped identities whose descriptors close on every exit path."""

    def __enter__(self) -> GitIdentityProofs:
        return self

    def __setitem__(self, key: str, identity: GitIdentity) -> None:
        previous = self.get(key)
        if previous is not None and previous is not identity:
            previous.close()
        super().__setitem__(key, identity)

    def close(self) -> None:
        """Attempt every retained close, then propagate the first failure."""

        identities = list(self.values())
        self.clear()
        first_error: BaseException | None = None
        for identity in identities:
            try:
                identity.close()
            except BaseException as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error

    def __exit__(self, *_exception: object) -> None:
        self.close()


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


def _directory_flags() -> int:
    """Return the Linux flags required for a retained directory descriptor."""

    required = ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
    missing = [name for name in required if not hasattr(os, name)]
    dir_fd_missing = os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd
    nofollow_missing = os.stat not in os.supports_follow_symlinks
    if missing or dir_fd_missing or nofollow_missing:
        unavailable = [*missing]
        if dir_fd_missing:
            unavailable.append("openat(dir_fd=...) support")
        if nofollow_missing:
            unavailable.append("stat(follow_symlinks=False) support")
        detail = ", ".join(unavailable)
        raise GitIdentityError(f"secure Git worktree opening is unavailable: {detail}")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _open_worktree(path: Path) -> int:
    """Open an absolute directory path component-wise without following links."""

    if not path.is_absolute() or not path.anchor:
        raise GitIdentityError(f"Git worktree path is not absolute: {path}")
    flags = _directory_flags()
    descriptor = -1
    try:
        descriptor = os.open(path.anchor, flags)
        for component in path.parts[1:]:
            metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                raise GitIdentityError(
                    f"Git worktree path contains a symlink component: {path}"
                )
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            try:
                opened = os.fstat(next_descriptor)
                if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                    raise GitIdentityError(
                        f"Git worktree changed during authentication: {path}"
                    )
            except BaseException:
                os.close(next_descriptor)
                raise
            previous_descriptor = descriptor
            descriptor = next_descriptor
            os.close(previous_descriptor)
        return descriptor
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        raise GitIdentityError(f"could not securely open Git worktree {path}: {error}") from error
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        raise


def _open_directory_path(path: str, *, base_fd: int | None, label: str) -> int:
    """Open a metadata directory path without following any symlink component."""

    parsed = Path(path)
    flags = _directory_flags()
    descriptor = -1
    try:
        if parsed.is_absolute():
            descriptor = os.open(parsed.anchor, flags)
            components = parsed.parts[1:]
        else:
            if base_fd is None:
                raise GitIdentityError(f"relative {label} path has no authenticated base: {path}")
            descriptor = os.dup(base_fd)
            components = parsed.parts
        for component in components:
            metadata = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                raise GitIdentityError(f"{label} path contains a symlink component: {path}")
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            try:
                opened = os.fstat(next_descriptor)
                if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                    raise GitIdentityError(f"{label} changed during authentication: {path}")
            except BaseException:
                os.close(next_descriptor)
                raise
            previous_descriptor = descriptor
            descriptor = next_descriptor
            os.close(previous_descriptor)
        return descriptor
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        raise GitIdentityError(f"could not securely open {label} {path}: {error}") from error
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        raise


def _open_directory_proof(path: str, *, base_fd: int | None, label: str) -> _DirectoryProof:
    descriptor = _open_directory_path(path, base_fd=base_fd, label=label)
    metadata = os.fstat(descriptor)
    return _DirectoryProof(path, descriptor, metadata.st_dev, metadata.st_ino)


def _file_signature(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_metadata_file(descriptor: int, *, label: str) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    content = os.read(descriptor, 4097)
    if len(content) > 4096:
        raise GitIdentityError(f"{label} is unexpectedly large")
    return content


def _open_file_proof(parent_fd: int, name: str, *, label: str) -> _FileProof:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptor = -1
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise GitIdentityError(f"{label} must be a single-link regular file")
        descriptor = os.open(name, flags, dir_fd=parent_fd)
        opened_before = os.fstat(descriptor)
        if _file_signature(opened_before) != _file_signature(metadata):
            raise GitIdentityError(f"{label} changed during authentication")
        content = _read_metadata_file(descriptor, label=label)
        opened_after = os.fstat(descriptor)
        if _file_signature(opened_after) != _file_signature(opened_before):
            raise GitIdentityError(f"{label} changed during authentication")
        return _FileProof(name, descriptor, _file_signature(opened_after), content)
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        raise GitIdentityError(f"could not securely open {label}: {error}") from error
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        raise


def _metadata_path(content: bytes, *, label: str, prefix: bytes = b"") -> str:
    line = content
    if line.endswith(b"\n"):
        line = line[:-1]
        if line.endswith(b"\r"):
            line = line[:-1]
    if b"\n" in line or b"\r" in line or b"\x00" in line:
        raise GitIdentityError(f"{label} must contain exactly one path line")
    if prefix and not line.startswith(prefix):
        raise GitIdentityError(f"{label} does not contain a Git directory path")
    raw_path = line[len(prefix) :]
    if not raw_path:
        raise GitIdentityError(f"{label} contains an empty path")
    return os.fsdecode(raw_path)


def _open_repository_binding(worktree_fd: int) -> _RepositoryBinding:
    """Authenticate ordinary or linked-worktree Git metadata once."""

    retained: list[int] = []
    try:
        try:
            git_entry = os.stat(".git", dir_fd=worktree_fd, follow_symlinks=False)
        except FileNotFoundError as error:
            raise GitIdentityError(
                "session worktree is not a Git worktree or is not the repository root"
            ) from error
        if stat.S_ISDIR(git_entry.st_mode):
            git_entry_file = None
            git_dir = _open_directory_proof(
                ".git",
                base_fd=worktree_fd,
                label="Git directory",
            )
            retained.append(git_dir.descriptor)
        elif stat.S_ISREG(git_entry.st_mode):
            git_entry_file = _open_file_proof(worktree_fd, ".git", label="Git gitfile")
            retained.append(git_entry_file.descriptor)
            git_dir_path = _metadata_path(
                git_entry_file.content,
                label="Git gitfile",
                prefix=b"gitdir: ",
            )
            git_dir = _open_directory_proof(
                git_dir_path,
                base_fd=worktree_fd,
                label="Git directory",
            )
            retained.append(git_dir.descriptor)
        else:
            raise GitIdentityError("worktree .git entry must be a directory or regular gitfile")

        try:
            os.stat("commondir", dir_fd=git_dir.descriptor, follow_symlinks=False)
        except FileNotFoundError:
            common_dir_file = None
            common_dir = _open_directory_proof(
                ".",
                base_fd=git_dir.descriptor,
                label="Git common directory",
            )
        else:
            common_dir_file = _open_file_proof(
                git_dir.descriptor,
                "commondir",
                label="Git commondir file",
            )
            retained.append(common_dir_file.descriptor)
            common_dir_path = _metadata_path(
                common_dir_file.content,
                label="Git commondir file",
            )
            common_dir = _open_directory_proof(
                common_dir_path,
                base_fd=git_dir.descriptor,
                label="Git common directory",
            )
        retained.append(common_dir.descriptor)
        return _RepositoryBinding(git_entry_file, git_dir, common_dir_file, common_dir)
    except OSError as error:
        for descriptor in reversed(retained):
            os.close(descriptor)
        raise GitIdentityError(
            f"could not authenticate Git repository metadata: {error}"
        ) from error
    except BaseException:
        for descriptor in reversed(retained):
            os.close(descriptor)
        raise


def _assert_directory_proof(
    proof: _DirectoryProof,
    *,
    base_fd: int | None,
    label: str,
) -> None:
    if proof.descriptor < 0:
        raise GitIdentityError(f"{label} proof is already closed")
    try:
        retained = os.fstat(proof.descriptor)
    except OSError as error:
        raise GitIdentityError(f"could not inspect bound {label}: {error}") from error
    expected = proof.device, proof.inode
    if (retained.st_dev, retained.st_ino) != expected:
        raise GitIdentityError(f"bound {label} identity changed: {proof.path}")
    reopened = _open_directory_path(proof.path, base_fd=base_fd, label=label)
    try:
        current = os.fstat(reopened)
        if (current.st_dev, current.st_ino) != expected:
            raise GitIdentityError(f"{label} changed during authentication: {proof.path}")
    finally:
        os.close(reopened)


def _assert_file_proof(proof: _FileProof, *, parent_fd: int, label: str) -> None:
    if proof.descriptor < 0:
        raise GitIdentityError(f"{label} proof is already closed")
    try:
        named = os.stat(proof.name, dir_fd=parent_fd, follow_symlinks=False)
        before = os.fstat(proof.descriptor)
        if _file_signature(named) != proof.signature or _file_signature(before) != proof.signature:
            raise GitIdentityError(f"{label} changed during authentication")
        content = _read_metadata_file(proof.descriptor, label=label)
        after = os.fstat(proof.descriptor)
    except OSError as error:
        raise GitIdentityError(f"could not recheck {label}: {error}") from error
    if content != proof.content or _file_signature(after) != proof.signature:
        raise GitIdentityError(f"{label} changed during authentication")


def _assert_repository_binding(binding: _RepositoryBinding, worktree_fd: int) -> None:
    if binding.git_entry_file is None:
        _assert_directory_proof(
            binding.git_dir,
            base_fd=worktree_fd,
            label="Git directory",
        )
    else:
        _assert_file_proof(binding.git_entry_file, parent_fd=worktree_fd, label="Git gitfile")
        _assert_directory_proof(
            binding.git_dir,
            base_fd=worktree_fd,
            label="Git directory",
        )
    if binding.common_dir_file is not None:
        _assert_file_proof(
            binding.common_dir_file,
            parent_fd=binding.git_dir.descriptor,
            label="Git commondir file",
        )
    _assert_directory_proof(
        binding.common_dir,
        base_fd=binding.git_dir.descriptor,
        label="Git common directory",
    )


def _assert_worktree_identity(
    cwd: Path,
    expected_identity: tuple[int, int],
) -> None:
    descriptor = _open_worktree(cwd)
    try:
        metadata = os.fstat(descriptor)
        actual_identity = metadata.st_dev, metadata.st_ino
        if actual_identity != expected_identity:
            raise GitIdentityError(
                f"Git worktree changed during authentication: {cwd}"
            )
    finally:
        os.close(descriptor)


def _assert_worktree_binding(
    cwd: Path,
    descriptor: int,
    expected_identity: tuple[int, int],
) -> None:
    """Check both the retained directory object and its current canonical name."""

    if descriptor < 0:
        raise GitIdentityError(f"Git worktree proof is already closed: {cwd}")
    try:
        metadata = os.fstat(descriptor)
    except OSError as error:
        raise GitIdentityError(f"could not inspect bound Git worktree {cwd}: {error}") from error
    if (metadata.st_dev, metadata.st_ino) != expected_identity:
        raise GitIdentityError(f"bound Git worktree identity changed: {cwd}")
    _assert_worktree_identity(cwd, expected_identity)


def recheck_git_identity_worktree(identity: GitIdentity) -> None:
    """Fail unless the live worktree and repository proofs remain bound."""

    _assert_worktree_binding(
        identity.worktree,
        identity._worktree_fd,
        (identity.worktree_device, identity.worktree_inode),
    )
    if identity._repository_binding is not None:
        _assert_repository_binding(identity._repository_binding, identity._worktree_fd)


def _git(
    cwd: Path,
    arguments: Sequence[str],
    *,
    worktree_fd: int,
    worktree_identity: tuple[int, int],
    repository_binding: _RepositoryBinding,
) -> str:
    _assert_worktree_binding(cwd, worktree_fd, worktree_identity)
    _assert_repository_binding(repository_binding, worktree_fd)
    command = [
        "git",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.fsmonitor=false",
        *arguments,
    ]
    try:
        environment = _git_environment()
        environment.update(
            {
                "GIT_DIR": f"/proc/self/fd/{repository_binding.git_dir.descriptor}",
                "GIT_COMMON_DIR": (
                    f"/proc/self/fd/{repository_binding.common_dir.descriptor}"
                ),
                "GIT_WORK_TREE": f"/proc/self/fd/{worktree_fd}",
            }
        )
        inherited_fds = tuple(
            sorted({worktree_fd, *repository_binding.descriptors()})
        )
        completed = subprocess.run(
            command,
            cwd=f"/proc/self/fd/{worktree_fd}",
            pass_fds=inherited_fds,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=environment,
        )
    except OSError as error:
        raise GitIdentityError(f"could not run git: {error}") from error
    _assert_worktree_binding(cwd, worktree_fd, worktree_identity)
    _assert_repository_binding(repository_binding, worktree_fd)
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


def _repository_input_oid_lengths(
    cwd: Path,
    worktree_fd: int,
    worktree_identity: tuple[int, int],
    repository_binding: _RepositoryBinding,
) -> set[int]:
    """Return full object-ID lengths accepted by the bound repository."""

    advertised = _git(
        cwd,
        ["rev-parse", "--show-object-format=input"],
        worktree_fd=worktree_fd,
        worktree_identity=worktree_identity,
        repository_binding=repository_binding,
    ).split()
    if not advertised or any(name not in GIT_OBJECT_FORMAT_LENGTHS for name in advertised):
        detail = " ".join(advertised) or "<empty>"
        raise GitIdentityError(
            f"Git advertised unsupported input object format(s): {detail}"
        )
    return {GIT_OBJECT_FORMAT_LENGTHS[name] for name in advertised}


def _prove_object(
    cwd: Path,
    worktree_fd: int,
    worktree_identity: tuple[int, int],
    repository_binding: _RepositoryBinding,
    object_id: str,
    expected_type: str,
) -> None:
    _git(
        cwd,
        ["cat-file", "-e", object_id],
        worktree_fd=worktree_fd,
        worktree_identity=worktree_identity,
        repository_binding=repository_binding,
    )
    actual_type = _git(
        cwd,
        ["cat-file", "-t", object_id],
        worktree_fd=worktree_fd,
        worktree_identity=worktree_identity,
        repository_binding=repository_binding,
    )
    if actual_type != expected_type:
        raise GitIdentityError(
            f"Git object {object_id} has type {actual_type!r}, expected {expected_type!r}"
        )


def _canonical_ref(
    cwd: Path,
    worktree_fd: int,
    worktree_identity: tuple[int, int],
    repository_binding: _RepositoryBinding,
    raw_ref: str,
) -> str:
    """Return one canonical ref name, rejecting Git's ambiguous DWIM cases."""

    if raw_ref == "HEAD":
        return raw_ref
    if raw_ref.startswith("refs/"):
        _git(
            cwd,
            ["check-ref-format", raw_ref],
            worktree_fd=worktree_fd,
            worktree_identity=worktree_identity,
            repository_binding=repository_binding,
        )
        return raw_ref
    _git(
        cwd,
        ["check-ref-format", "--allow-onelevel", raw_ref],
        worktree_fd=worktree_fd,
        worktree_identity=worktree_identity,
        repository_binding=repository_binding,
    )
    ref_names = set(
        _git(
            cwd,
            ["for-each-ref", "--format=%(refname)"],
            worktree_fd=worktree_fd,
            worktree_identity=worktree_identity,
            repository_binding=repository_binding,
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
        lexical_worktree = Path(worktree)
        if ".." in lexical_worktree.parts:
            raise GitIdentityError(
                f"Git worktree path contains an unsafe parent component: {worktree}"
            )
        cwd = lexical_worktree if lexical_worktree.is_absolute() else Path.cwd() / lexical_worktree
    except (OSError, TypeError, ValueError) as error:
        raise GitIdentityError(f"could not normalize Git worktree {worktree}: {error}") from error
    worktree_fd = -1
    repository_binding: _RepositoryBinding | None = None
    try:
        worktree_fd = _open_worktree(cwd)
        metadata = os.fstat(worktree_fd)
        worktree_identity = metadata.st_dev, metadata.st_ino
        repository_binding = _open_repository_binding(worktree_fd)

        inside_worktree = _git(
            cwd,
            ["rev-parse", "--is-inside-work-tree"],
            worktree_fd=worktree_fd,
            worktree_identity=worktree_identity,
            repository_binding=repository_binding,
        )
        if inside_worktree != "true":
            raise GitIdentityError(f"session worktree is not a Git worktree: {cwd}")
        repository_prefix = _git(
            cwd,
            ["rev-parse", "--show-prefix"],
            worktree_fd=worktree_fd,
            worktree_identity=worktree_identity,
            repository_binding=repository_binding,
        )
        if repository_prefix:
            raise GitIdentityError(
                f"session worktree must be the Git repository root: {cwd}"
            )

        raw_ref = ref.strip()
        direct_object_id = FULL_GIT_OID_RE.fullmatch(raw_ref) is not None
        if direct_object_id:
            accepted_lengths = _repository_input_oid_lengths(
                cwd,
                worktree_fd,
                worktree_identity,
                repository_binding,
            )
            if len(raw_ref) not in accepted_lengths:
                lengths = ", ".join(str(length) for length in sorted(accepted_lengths))
                raise GitIdentityError(
                    f"Git object ID length {len(raw_ref)} does not match repository "
                    f"input object format length(s): {lengths}"
                )
            resolved_ref = raw_ref
        else:
            resolved_ref = _canonical_ref(
                cwd,
                worktree_fd,
                worktree_identity,
                repository_binding,
                raw_ref,
            )
        commit = _full_oid(
            _git(
                cwd,
                ["rev-parse", "--verify", "--end-of-options", f"{resolved_ref}^{{commit}}"],
                worktree_fd=worktree_fd,
                worktree_identity=worktree_identity,
                repository_binding=repository_binding,
            ),
            "commit",
        )
        if direct_object_id and commit != raw_ref:
            raise GitIdentityError(
                f"Git object ID {raw_ref!r} is not the exact resolved commit {commit}"
            )
        _prove_object(
            cwd,
            worktree_fd,
            worktree_identity,
            repository_binding,
            commit,
            "commit",
        )
        tree = _full_oid(
            _git(
                cwd,
                ["rev-parse", "--verify", "--end-of-options", f"{commit}^{{tree}}"],
                worktree_fd=worktree_fd,
                worktree_identity=worktree_identity,
                repository_binding=repository_binding,
            ),
            "tree",
        )
        _prove_object(
            cwd,
            worktree_fd,
            worktree_identity,
            repository_binding,
            tree,
            "tree",
        )

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
        _assert_worktree_binding(cwd, worktree_fd, worktree_identity)
        _assert_repository_binding(repository_binding, worktree_fd)
        return GitIdentity(
            commit=commit,
            tree=tree,
            worktree=cwd,
            worktree_device=worktree_identity[0],
            worktree_inode=worktree_identity[1],
            _worktree_fd=worktree_fd,
            _repository_binding=repository_binding,
        )
    except BaseException:
        if repository_binding is not None:
            try:
                repository_binding.close()
            except BaseException:
                pass
        if worktree_fd >= 0:
            try:
                os.close(worktree_fd)
            except BaseException:
                pass
        raise


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
    with resolve_git_identity(
        Path(arguments.worktree),
        arguments.ref,
        expected_tree=arguments.expected_tree,
    ) as identity:
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
