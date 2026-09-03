#!/usr/bin/env python3
"""Build, publish, and seed a local hot cache for Lean's ``.lake`` tree.

One process wins an ``fcntl`` lock for each exact main snapshot.  It builds in a
detached local clone, then publishes the immutable staged result with one
rename.  Issue worktrees receive private copy-on-write reflink copies (with a
byte-copy fallback), never a symlink or hardlink to writable build output.
"""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import ctypes
from dataclasses import asdict, dataclass
import datetime as dt
import errno
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import secrets
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import types
from typing import Any, Callable, Mapping, Sequence
import zlib


SCHEMA_VERSION = 3
BUILD_RECIPE_SCHEMA_VERSION = 3
ARTIFACT_INVENTORY_SCHEMA_VERSION = 1
SOURCE_EVIDENCE_SCHEMA_VERSION = 1
AUTHORED_QPBT_CHECK_PHASES = (
    "before_materialization",
    "after_materialization",
    "after_dependency_retrieval",
    "after_build",
    "before_publication",
)
FICLONE = 0x40049409
REFLINK_FALLBACK_ERRNOS = {
    errno.EXDEV,
    errno.EINVAL,
    errno.ENOTTY,
    errno.EOPNOTSUPP,
    errno.ENOSYS,
    errno.EPERM,
}
RENAME_NOREPLACE = 1
RENAME_EXCHANGE = 2
_RENAMEAT2_FILESYSTEM_MAGICS = {
    0xEF53,  # ext2/ext3/ext4
    0x58465342,  # XFS
    0x9123683E,  # Btrfs
    0x01021994,  # tmpfs
    0x794C7630,  # overlayfs
    0xF2F52010,  # F2FS
}
_IN_ATTRIB = 0x00000004
_IN_MOVED_FROM = 0x00000040
_IN_MOVED_TO = 0x00000080
_IN_CREATE = 0x00000100
_IN_DELETE = 0x00000200
_IN_DELETE_SELF = 0x00000400
_IN_MOVE_SELF = 0x00000800
_IN_UNMOUNT = 0x00002000
_IN_Q_OVERFLOW = 0x00004000
_IN_IGNORED = 0x00008000
_INOTIFY_EVENT = struct.Struct("iIII")


def _linux_libc() -> Any:
    if sys.platform != "linux":
        raise CacheError("safe seed publication requires Linux renameat2 and inotify")
    return ctypes.CDLL(None, use_errno=True)


def _linux_renameat2(
    source_parent: int,
    source_name: str,
    destination_parent: int,
    destination_name: str,
    flags: int,
) -> None:
    if flags not in {RENAME_NOREPLACE, RENAME_EXCHANGE}:
        raise CacheError("renameat2 publication requires no-replace or exchange")
    for name in (source_name, destination_name):
        encoded = os.fsencode(name)
        if not encoded or encoded in {b".", b".."} or b"/" in encoded or b"\0" in encoded:
            raise CacheError("renameat2 operands must be single child names")
    for descriptor in (source_parent, destination_parent):
        try:
            mode = os.fstat(descriptor).st_mode
        except OSError:
            mode = stat.S_IFDIR if descriptor == -1 else 0
        if descriptor != -1 and not stat.S_ISDIR(mode):
            raise CacheError("renameat2 parent descriptor is not a directory")
    libc = _linux_libc()
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise CacheError("safe seed publication requires Linux renameat2")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    ctypes.set_errno(0)
    if renameat2(
        source_parent,
        os.fsencode(source_name),
        destination_parent,
        os.fsencode(destination_name),
        flags,
    ) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def _linux_filesystem_magic(descriptor: int) -> int:
    libc = _linux_libc()
    fstatfs = getattr(libc, "fstatfs", None)
    if fstatfs is None:
        raise CacheError("safe seed publication requires Linux fstatfs")
    buffer = ctypes.create_string_buffer(256)
    fstatfs.argtypes = [ctypes.c_int, ctypes.c_void_p]
    fstatfs.restype = ctypes.c_int
    ctypes.set_errno(0)
    if fstatfs(descriptor, ctypes.byref(buffer)) != 0:
        error_number = ctypes.get_errno()
        raise CacheError(f"could not identify target filesystem: {os.strerror(error_number)}")
    width = ctypes.sizeof(ctypes.c_long)
    return int.from_bytes(buffer.raw[:width], sys.byteorder, signed=False)


def _assert_renameat2_kernel_capability(flags: int, label: str) -> None:
    try:
        _linux_renameat2(-1, "probe-source", -1, "probe-destination", flags)
    except OSError as error:
        if error.errno == errno.EBADF:
            return
        raise CacheError(f"kernel does not provide atomic {label} publication") from error
    raise CacheError(f"atomic {label} capability probe unexpectedly mutated a name")


def _probe_renameat2_semantics(target_descriptor: int) -> None:
    temporary_descriptor = os.open("/tmp", _authored_directory_flags())
    root_descriptor: int | None = None
    root_monitor: _BoundNameMonitor | None = None
    child_monitor: _BoundNameMonitor | None = None
    child_descriptors: dict[str, int] = {}
    try:
        if os.fstat(temporary_descriptor).st_dev != os.fstat(target_descriptor).st_dev:
            raise CacheError(
                "safe seed publication requires a same-device /tmp capability probe"
            )
        root_name = f"mipstarre-renameat2-probe-retained-{secrets.token_hex(16)}"
        root_monitor = _BoundNameMonitor(temporary_descriptor, (root_name,))
        os.mkdir(root_name, 0o700, dir_fd=temporary_descriptor)
        root_monitor.accept_exact_change(((root_name, _IN_CREATE),))
        root_descriptor = os.open(
            root_name, _authored_directory_flags(), dir_fd=temporary_descriptor
        )
        HotMainCache._assert_bound_name(
            temporary_descriptor, root_name, root_descriptor, "semantic probe root"
        )
        root_monitor.assert_clean()
        child_monitor = _BoundNameMonitor(
            root_descriptor, ("first", "second", "moving", "moved")
        )
        for child in ("first", "second", "moving"):
            child_monitor.assert_clean()
            os.mkdir(child, 0o700, dir_fd=root_descriptor)
            child_monitor.accept_exact_change(((child, _IN_CREATE),))
            descriptor = os.open(child, _authored_directory_flags(), dir_fd=root_descriptor)
            child_descriptors[child] = descriptor
            HotMainCache._assert_bound_name(
                root_descriptor, child, descriptor, f"semantic probe {child}"
            )
            child_monitor.assert_clean()
        try:
            _linux_renameat2(
                root_descriptor,
                "moving",
                root_descriptor,
                "second",
                RENAME_NOREPLACE,
            )
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise CacheError("atomic no-replace semantic probe failed") from error
        else:
            raise CacheError("atomic no-replace probe replaced an existing object")
        HotMainCache._assert_bound_name(
            root_descriptor, "moving", child_descriptors["moving"], "no-replace probe source"
        )
        HotMainCache._assert_bound_name(
            root_descriptor, "second", child_descriptors["second"], "no-replace probe destination"
        )
        child_monitor.assert_clean()
        _linux_renameat2(
            root_descriptor,
            "moving",
            root_descriptor,
            "moved",
            RENAME_NOREPLACE,
        )
        child_monitor.accept_exact_change(
            (("moving", _IN_MOVED_FROM), ("moved", _IN_MOVED_TO))
        )
        HotMainCache._assert_bound_name(
            root_descriptor, "moved", child_descriptors["moving"], "no-replace probe publication"
        )
        _linux_renameat2(
            root_descriptor,
            "first",
            root_descriptor,
            "second",
            RENAME_EXCHANGE,
        )
        child_monitor.accept_exact_change(
            (
                ("first", _IN_MOVED_FROM),
                ("second", _IN_MOVED_FROM),
                ("first", _IN_MOVED_TO),
                ("second", _IN_MOVED_TO),
            )
        )
        HotMainCache._assert_bound_name(
            root_descriptor, "second", child_descriptors["first"], "exchange probe first"
        )
        HotMainCache._assert_bound_name(
            root_descriptor, "first", child_descriptors["second"], "exchange probe second"
        )
        _linux_renameat2(
            root_descriptor,
            "first",
            root_descriptor,
            "second",
            RENAME_EXCHANGE,
        )
        child_monitor.accept_exact_change(
            (
                ("first", _IN_MOVED_FROM),
                ("second", _IN_MOVED_FROM),
                ("first", _IN_MOVED_TO),
                ("second", _IN_MOVED_TO),
            )
        )
        HotMainCache._assert_bound_name(
            root_descriptor, "first", child_descriptors["first"], "exchange probe restoration"
        )
        HotMainCache._assert_bound_name(
            root_descriptor, "second", child_descriptors["second"], "exchange probe restoration"
        )
        os.fsync(root_descriptor)
    finally:
        if child_monitor is not None:
            child_monitor.close()
        if root_monitor is not None:
            root_monitor.close()
        for descriptor in child_descriptors.values():
            os.close(descriptor)
        if root_descriptor is not None:
            os.close(root_descriptor)
        os.close(temporary_descriptor)


class _NamespaceMonitor:
    """Fail closed when a lexical ancestor is renamed during seed/prepare."""

    def __init__(self, paths: Sequence[Path]):
        libc = _linux_libc()
        initialize = getattr(libc, "inotify_init1", None)
        add_watch = getattr(libc, "inotify_add_watch", None)
        if initialize is None or add_watch is None:
            raise CacheError("safe seed publication requires Linux inotify")
        initialize.argtypes = [ctypes.c_int]
        initialize.restype = ctypes.c_int
        add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        add_watch.restype = ctypes.c_int
        flags = os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
        ctypes.set_errno(0)
        descriptor = initialize(flags)
        if descriptor < 0:
            error_number = ctypes.get_errno()
            raise CacheError(f"could not initialize target namespace monitor: {os.strerror(error_number)}")
        self.descriptor = descriptor
        self.watches: dict[int, set[bytes]] = {}
        self.bindings: list[tuple[int, str, int]] = []
        self.bound_descriptors: list[int] = []
        self.changed = False
        mask = (
            _IN_ATTRIB
            | _IN_MOVED_FROM
            | _IN_MOVED_TO
            | _IN_CREATE
            | _IN_DELETE
            | _IN_DELETE_SELF
            | _IN_MOVE_SELF
            | _IN_UNMOUNT
            | _IN_Q_OVERFLOW
        )
        try:
            for supplied in paths:
                absolute = Path(os.path.abspath(supplied))
                parent_descriptor = os.open(
                    absolute.anchor, _authored_directory_flags()
                )
                self.bound_descriptors.append(parent_descriptor)
                for component in absolute.parts[1:]:
                    encoded_component = os.fsencode(component)
                    ctypes.set_errno(0)
                    watch = add_watch(
                        descriptor,
                        os.fsencode(f"/proc/self/fd/{parent_descriptor}"),
                        mask,
                    )
                    if watch < 0:
                        error_number = ctypes.get_errno()
                        raise CacheError(
                            "could not bind target ancestor namespace monitor: "
                            f"{absolute}: {os.strerror(error_number)}"
                        )
                    self.watches.setdefault(watch, set()).add(encoded_component)
                    child_descriptor = os.open(
                        component,
                        _authored_directory_flags(),
                        dir_fd=parent_descriptor,
                    )
                    self.bound_descriptors.append(child_descriptor)
                    self.bindings.append(
                        (parent_descriptor, component, child_descriptor)
                    )
                    parent_descriptor = child_descriptor
            self.assert_clean()
        except BaseException:
            for bound_descriptor in reversed(self.bound_descriptors):
                os.close(bound_descriptor)
            os.close(descriptor)
            raise

    def assert_clean(self) -> None:
        while True:
            try:
                payload = os.read(self.descriptor, 64 * 1024)
            except BlockingIOError:
                break
            except OSError as error:
                raise CacheError("target namespace monitor became unavailable") from error
            if not payload:
                raise CacheError("target namespace monitor closed unexpectedly")
            offset = 0
            while offset < len(payload):
                if len(payload) - offset < _INOTIFY_EVENT.size:
                    self.changed = True
                    break
                watch, mask, _cookie, name_size = _INOTIFY_EVENT.unpack_from(payload, offset)
                offset += _INOTIFY_EVENT.size
                if len(payload) - offset < name_size:
                    self.changed = True
                    break
                name = payload[offset : offset + name_size].split(b"\0", 1)[0]
                offset += name_size
                if watch not in self.watches or mask & (
                    _IN_Q_OVERFLOW
                    | _IN_IGNORED
                    | _IN_UNMOUNT
                    | _IN_DELETE_SELF
                    | _IN_MOVE_SELF
                ):
                    self.changed = True
                elif name and name in self.watches.get(watch, set()):
                    self.changed = True
        for parent_descriptor, name, child_descriptor in self.bindings:
            try:
                lexical = os.stat(
                    name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                bound = os.fstat(child_descriptor)
            except OSError:
                self.changed = True
                break
            if (
                stat.S_ISLNK(lexical.st_mode)
                or (lexical.st_dev, lexical.st_ino, stat.S_IFMT(lexical.st_mode))
                != (bound.st_dev, bound.st_ino, stat.S_IFMT(bound.st_mode))
            ):
                self.changed = True
                break
        if self.changed:
            raise CacheError("target ancestor namespace changed during seed/prepare")

    def close(self) -> None:
        for bound_descriptor in reversed(self.bound_descriptors):
            os.close(bound_descriptor)
        os.close(self.descriptor)


class _BoundNameMonitor:
    """Detect substitution or ABA of exact children of one held directory."""

    def __init__(self, parent_descriptor: int, names: Sequence[str]):
        libc = _linux_libc()
        initialize = getattr(libc, "inotify_init1", None)
        add_watch = getattr(libc, "inotify_add_watch", None)
        if initialize is None or add_watch is None:
            raise CacheError("safe transaction binding requires Linux inotify")
        initialize.argtypes = [ctypes.c_int]
        initialize.restype = ctypes.c_int
        add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        add_watch.restype = ctypes.c_int
        descriptor = initialize(os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
        if descriptor < 0:
            error_number = ctypes.get_errno()
            raise CacheError(f"could not initialize transaction monitor: {os.strerror(error_number)}")
        mask = (
            _IN_ATTRIB
            | _IN_MOVED_FROM
            | _IN_MOVED_TO
            | _IN_CREATE
            | _IN_DELETE
            | _IN_DELETE_SELF
            | _IN_MOVE_SELF
            | _IN_UNMOUNT
            | _IN_Q_OVERFLOW
        )
        ctypes.set_errno(0)
        watch = add_watch(descriptor, os.fsencode(f"/proc/self/fd/{parent_descriptor}"), mask)
        if watch < 0:
            error_number = ctypes.get_errno()
            os.close(descriptor)
            raise CacheError(f"could not bind transaction monitor: {os.strerror(error_number)}")
        self.descriptor = descriptor
        self.watch = watch
        self.names = {os.fsencode(name) for name in names}
        self.poisoned = False

    def _drain(self) -> tuple[list[tuple[bytes, int]], bool]:
        relevant: list[tuple[bytes, int]] = []
        fatal = False
        while True:
            try:
                payload = os.read(self.descriptor, 64 * 1024)
            except BlockingIOError:
                break
            except OSError:
                self.poisoned = True
                return relevant, True
            if not payload:
                self.poisoned = True
                return relevant, True
            offset = 0
            while offset < len(payload):
                if len(payload) - offset < _INOTIFY_EVENT.size:
                    fatal = True
                    break
                watch, mask, _cookie, name_size = _INOTIFY_EVENT.unpack_from(payload, offset)
                offset += _INOTIFY_EVENT.size
                if len(payload) - offset < name_size:
                    fatal = True
                    break
                name = payload[offset : offset + name_size].split(b"\0", 1)[0]
                offset += name_size
                if watch not in {-1, self.watch} or mask & (
                    _IN_Q_OVERFLOW
                    | _IN_IGNORED
                    | _IN_UNMOUNT
                    | _IN_DELETE_SELF
                    | _IN_MOVE_SELF
                ):
                    fatal = True
                elif name in self.names:
                    operation = mask & (
                        _IN_ATTRIB | _IN_MOVED_FROM | _IN_MOVED_TO | _IN_CREATE | _IN_DELETE
                    )
                    relevant.append((name, operation))
        if fatal:
            self.poisoned = True
        return relevant, fatal

    def assert_clean(self) -> None:
        relevant, fatal = self._drain()
        if relevant or fatal:
            self.poisoned = True
        if self.poisoned:
            raise CacheError("transaction object name changed or monitor became ambiguous")

    def accept_owned_change(self) -> None:
        relevant, fatal = self._drain()
        if self.poisoned or fatal or not relevant:
            self.poisoned = True
            raise CacheError("atomic transaction rename lacked an exact monitor event")

    def accept_exact_change(self, expected: Sequence[tuple[str, int]]) -> None:
        relevant, fatal = self._drain()
        expected_events = Counter((os.fsencode(name), mask) for name, mask in expected)
        if self.poisoned or fatal or Counter(relevant) != expected_events:
            self.poisoned = True
            raise CacheError("transaction mutation lacked its exact monitor events")

    def close(self) -> None:
        os.close(self.descriptor)


class CacheError(Exception):
    """A cache operation failed in a way suitable for concise CLI output."""


@dataclass
class _SeedReplacement:
    """Caller-owned state for one rollback-capable seed publication."""

    destination: Path
    backup: Path
    rollback_root: Path
    transaction_id: str
    journal_dir: Path
    journal_path: Path
    journal_digest_path: Path
    committed_path: Path
    staging_root: Path | None = None
    old_moved: bool = False
    new_published: bool = False
    metric_committed: bool = False
    original_identity: dict[str, Any] | None = None
    original_descriptor: int | None = None
    staging_descriptor: int | None = None
    staging_lake_descriptor: int | None = None
    journal_parent_descriptor: int | None = None
    journal_descriptor: int | None = None
    journal_file_descriptors: dict[str, int] | None = None
    journal_digest: str | None = None
    failed_retained: str | None = None
    staging_parent_monitor: _BoundNameMonitor | None = None
    staging_entry_monitor: _BoundNameMonitor | None = None
    destination_monitor: _BoundNameMonitor | None = None
    journal_parent_monitor: _BoundNameMonitor | None = None
    journal_entry_monitor: _BoundNameMonitor | None = None


@dataclass
class _BoundSeedTarget:
    """Descriptor-bound registered worktree identity for one target operation."""

    target_project: Path
    worktree_root: Path
    worktree_head: str
    project_descriptor: int
    worktree_descriptor: int
    worktree_parent_descriptor: int
    project_identity: tuple[int, int]
    worktree_identity: tuple[int, int]
    worktree_parent_identity: tuple[int, int]
    project_generation: tuple[int, ...]
    worktree_generation: tuple[int, ...]
    worktree_parent_generation: tuple[int, ...]
    namespace_monitor: _NamespaceMonitor

    @property
    def access_path(self) -> Path:
        return Path("/proc/self/fd") / str(self.project_descriptor)

    def assert_current(self) -> None:
        self.namespace_monitor.assert_clean()
        for path, descriptor, identity, generation, label in (
            (
                self.target_project,
                self.project_descriptor,
                self.project_identity,
                self.project_generation,
                "target project",
            ),
            (
                self.worktree_root,
                self.worktree_descriptor,
                self.worktree_identity,
                self.worktree_generation,
                "target worktree",
            ),
            (
                self.worktree_root.parent,
                self.worktree_parent_descriptor,
                self.worktree_parent_identity,
                self.worktree_parent_generation,
                "target worktree parent",
            ),
        ):
            try:
                lexical = path.stat(follow_symlinks=False)
                bound = os.fstat(descriptor)
            except OSError as error:
                raise CacheError(f"{label} identity changed during seed/prepare") from error
            if (
                stat.S_ISLNK(lexical.st_mode)
                or _authored_directory_identity(lexical) != identity
                or _authored_directory_identity(bound) != identity
                or _authored_directory_scan_identity(bound) != generation
            ):
                raise CacheError(f"{label} identity changed during seed/prepare")

    def refresh_after_project_mutation(self) -> None:
        """Admit only a descriptor-relative mutation performed by this operation."""

        self.namespace_monitor.assert_clean()
        try:
            lexical = self.target_project.stat(follow_symlinks=False)
            lexical_worktree = self.worktree_root.stat(follow_symlinks=False)
            lexical_parent = self.worktree_root.parent.stat(follow_symlinks=False)
            project = os.fstat(self.project_descriptor)
            worktree = os.fstat(self.worktree_descriptor)
            worktree_parent = os.fstat(self.worktree_parent_descriptor)
        except OSError as error:
            raise CacheError("target identity changed during seed/prepare mutation") from error
        if (
            stat.S_ISLNK(lexical.st_mode)
            or _authored_directory_identity(lexical) != self.project_identity
            or stat.S_ISLNK(lexical_worktree.st_mode)
            or _authored_directory_identity(lexical_worktree) != self.worktree_identity
            or stat.S_ISLNK(lexical_parent.st_mode)
            or _authored_directory_identity(lexical_parent) != self.worktree_parent_identity
            or _authored_directory_identity(project) != self.project_identity
            or _authored_directory_identity(worktree) != self.worktree_identity
            or _authored_directory_identity(worktree_parent)
            != self.worktree_parent_identity
            or _authored_directory_scan_identity(worktree_parent)
            != self.worktree_parent_generation
            or (
                self.worktree_identity != self.project_identity
                and _authored_directory_scan_identity(worktree)
                != self.worktree_generation
            )
        ):
            raise CacheError("target identity changed during seed/prepare mutation")
        self.project_generation = _authored_directory_scan_identity(project)
        if self.worktree_identity == self.project_identity:
            self.worktree_generation = _authored_directory_scan_identity(worktree)

    def close(self) -> None:
        try:
            self.namespace_monitor.close()
        finally:
            os.close(self.project_descriptor)
            os.close(self.worktree_descriptor)
            os.close(self.worktree_parent_descriptor)


@dataclass(frozen=True)
class _CapturedInputPath:
    """An exact virtual path whose content is an authenticated byte payload."""

    relative_path: str
    payload: bytes

    def read_text(self, encoding: str | None = None, errors: str | None = None) -> str:
        return self.payload.decode(encoding or "utf-8", errors or "strict")

    def __str__(self) -> str:
        return f"<captured:{self.relative_path}>"


@dataclass(frozen=True)
class _CapturedInputRoot:
    """Resolve only an explicitly admitted set of captured project paths."""

    payloads: Mapping[str, bytes]

    def __truediv__(self, requested: object) -> _CapturedInputPath:
        relative = PurePosixPath(str(requested))
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise CacheError(f"captured verifier requested an unsafe path: {requested}")
        key = relative.as_posix()
        try:
            payload = self.payloads[key]
        except KeyError as error:
            raise CacheError(f"captured verifier requested an unauthenticated path: {key}") from error
        return _CapturedInputPath(key, payload)


LAKE_OVERRIDE_ARGUMENT = "--packages=.lake/package-overrides.json"

# The root manifest and provenance pin identify this exact Mathlib revision.  A
# local source path is deliberately runtime input, not cache-key input: the
# Git commit/tree below are the stable identity that every accepted mirror must
# expose.  The archive digest covers the normalized shallow repository emitted
# by the acquisition audit; source repositories may be repacked without
# changing their Git identity.
MATHLIB_SOURCE_ENV = "MATHLIB_SOURCE"
MATHLIB_ARCHIVE_ENV = "MATHLIB_ARCHIVE"
MIPSTARRE_ARCHIVE_ENV = "MIPSTARRE_ARCHIVE"
LAKE_PACKAGE_ARCHIVES_ENV = "LAKE_PACKAGE_ARCHIVES"
MATHLIB_PACKAGE_NAME = "mathlib"
MATHLIB_REPOSITORY_URL = "https://github.com/leanprover-community/mathlib4"
MATHLIB_COMMIT = "81a5d257c8e410db227a6665ed08f64fea08e997"
MATHLIB_TREE = "5ea66b811b8461daae82f14d356fed2a287d7c40"
MATHLIB_ARCHIVE_SHA256 = "c29325b477966a6f8eb784723f19da26800c71458f7c24cc668713725eba78d7"
MATHLIB_ARCHIVE_BYTES = 51_938_317
MATHLIB_ARCHIVE_TAR_SHA256 = "ad9a60b01736070112fbc1008ea98c67e68fa045c5b69e66873e0b9444ddd3ba"
MATHLIB_ARCHIVE_TAR_BYTES = 147_712_000
MATHLIB_SOURCE_EVIDENCE_SCHEMA_VERSION = 1
MATHLIB_ARCHIVE_MAX_BYTES = 64 * 1024 * 1024
MATHLIB_TAR_MAX_BYTES = 256 * 1024 * 1024
MATHLIB_TAR_MAX_MEMBERS = 20_000
# The pinned shallow mirror has one 27,574,578-byte Git pack member.  Keep a
# bounded margin for that exact artifact while retaining the aggregate tar
# limit below.
MATHLIB_TAR_MAX_MEMBER_BYTES = 32 * 1024 * 1024
IDENTITY_INPUT_MAX_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class MathlibSourceBinding:
    """An authenticated local Mathlib repository and its Lake URL."""

    path: Path
    lake_url: str
    evidence: dict[str, Any]
    owned_path: Path | None = None


MATHLIB_EVIDENCE_KEYS = {
    "schema_version",
    "repository_url",
    "commit",
    "tree",
    "mode",
    "archive_sha256",
    "archive_bytes",
    "pack_sha256",
    "pack_bytes",
}

TRUSTED_GIT_CONFIG_OVERRIDES = (
    ("core.fsmonitor", "false"),
    ("core.hooksPath", os.devnull),
    ("core.pager", ""),
    ("credential.helper", ""),
    ("protocol.ext.allow", "never"),
)


def _validate_lake_command(command: Sequence[str]) -> None:
    """Require the exact local package override and reject manifest updates."""

    if command[0] != "lake":
        return
    package_arguments = [token for token in command if token.startswith("--packages")]
    if package_arguments != [LAKE_OVERRIDE_ARGUMENT]:
        raise ValueError(
            f"Lake commands require exactly {LAKE_OVERRIDE_ARGUMENT!r}"
        )
    if any(token == "update" or token == "--update" or token.startswith("--update=") for token in command):
        raise ValueError("Lake update modes are forbidden in the hot-cache build recipe")
    if any(
        token.startswith("-")
        and not token.startswith("--")
        and "U" in token[1:]
        for token in command
    ):
        raise ValueError("Lake short update modes are forbidden in the hot-cache build recipe")


@dataclass(frozen=True)
class BuildRecipe:
    """An identity-bearing, immutable recipe for one cache build."""

    recipe_id: str
    version: int
    dependency_command: tuple[str, ...]
    build_command: tuple[str, ...]
    test_only: bool = False
    materialize_command: tuple[str, ...] = ()
    package_materialize_command: tuple[str, ...] = ()
    package_verify_command: tuple[str, ...] = ()
    additional_identity_files: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.recipe_id or self.version < 1:
            raise ValueError("a build recipe needs a non-empty id and positive version")
        if not self.dependency_command or not self.build_command:
            raise ValueError("dependency and build commands cannot be empty")
        if bool(self.package_materialize_command) != bool(self.package_verify_command):
            raise ValueError("package materialization and verification commands must be paired")
        _validate_lake_command(self.dependency_command)
        _validate_lake_command(self.build_command)
        for relative in self.additional_identity_files:
            path = Path(relative)
            if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
                raise ValueError(f"identity file must be a safe project-relative path: {relative!r}")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": BUILD_RECIPE_SCHEMA_VERSION,
            "recipe_id": self.recipe_id,
            "version": self.version,
            "dependency_command": list(self.dependency_command),
            "build_command": list(self.build_command),
            "materialize_command": list(self.materialize_command),
            "package_materialize_command": list(self.package_materialize_command),
            "package_verify_command": list(self.package_verify_command),
            "additional_identity_files": list(self.additional_identity_files),
            "test_only": self.test_only,
        }

    @classmethod
    def for_testing(
        cls,
        *,
        dependency_command: Sequence[str],
        build_command: Sequence[str],
        materialize_command: Sequence[str] = (),
        package_materialize_command: Sequence[str] = (),
        package_verify_command: Sequence[str] = (),
        additional_identity_files: Sequence[str] = (),
        recipe_id: str = "test-fake-build",
        version: int = 1,
    ) -> "BuildRecipe":
        """Create a recipe whose artifacts cannot share the canonical key."""

        return cls(
            recipe_id=recipe_id,
            version=version,
            dependency_command=tuple(dependency_command),
            build_command=tuple(build_command),
            materialize_command=tuple(materialize_command),
            package_materialize_command=tuple(package_materialize_command),
            package_verify_command=tuple(package_verify_command),
            additional_identity_files=tuple(additional_identity_files),
            test_only=True,
        )


CANONICAL_BUILD_RECIPE = BuildRecipe(
    recipe_id="qpbt-hot-main",
    version=7,
    dependency_command=("lake", LAKE_OVERRIDE_ARGUMENT, "exe", "cache", "get"),
    build_command=("lake", LAKE_OVERRIDE_ARGUMENT, "build"),
    materialize_command=(
        "python3", "scripts/materialize_mipstarre.py", "materialize",
        "--archive-env", "MIPSTARRE_ARCHIVE",
        "--replace-existing",
    ),
    package_materialize_command=(
        "python3", "scripts/materialize_lake_packages.py", "materialize",
        "--archive-directory-env", "LAKE_PACKAGE_ARCHIVES",
    ),
    package_verify_command=(
        "python3", "scripts/materialize_lake_packages.py", "verify",
        "--remove-validated-generated-sidecars",
    ),
    additional_identity_files=(
        "references/mipstarre-upstream.json",
        "scripts/materialize_mipstarre.py",
        "references/lake-packages.json",
        "references/mathlib-lake-manifest.json",
        "scripts/materialize_lake_packages.py",
    ),
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def artifact_inventory(root: Path) -> dict[str, Any]:
    """Return a content-addressed inventory without following symlinks."""

    if not root.is_dir() or root.is_symlink():
        raise CacheError(f"artifact inventory root must be a real directory: {root}")
    digest = hashlib.sha256()
    files = 0
    directories = 0
    symlinks = 0
    total_bytes = 0

    def add(kind: str, relative: str, payload: str = "") -> None:
        digest.update(kind.encode("ascii"))
        digest.update(b"\0")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload.encode("utf-8"))
        digest.update(b"\n")

    for directory, dir_names, file_names in os.walk(root, followlinks=False):
        base = Path(directory)
        relative_base = base.relative_to(root).as_posix()
        if relative_base != ".":
            add("directory", relative_base)
            directories += 1
        dir_names.sort()
        file_names.sort()
        retained: list[str] = []
        for name in dir_names:
            path = base / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                add("symlink", relative, os.readlink(path))
                symlinks += 1
            elif path.is_dir():
                retained.append(name)
            else:
                raise CacheError(f"unsupported artifact entry type: {path}")
        dir_names[:] = retained
        for name in file_names:
            path = base / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                add("symlink", relative, os.readlink(path))
                symlinks += 1
            elif path.is_file():
                size = path.stat(follow_symlinks=False).st_size
                add("file", relative, f"{size}:{sha256_file(path)}")
                files += 1
                total_bytes += size
            else:
                raise CacheError(f"unsupported artifact entry type: {path}")
    return {
        "schema_version": ARTIFACT_INVENTORY_SCHEMA_VERSION,
        "sha256": digest.hexdigest(),
        "files": files,
        "directories": directories,
        "symlinks": symlinks,
        "bytes": total_bytes,
    }


def _is_lower_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_source_evidence(value: Any, expected_contract: Mapping[str, Any]) -> bool:
    """Validate the bounded source-verification record sealed into a snapshot."""

    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "pin_sha256",
        "source_commit",
        "inventory_sha256",
        "files",
        "bytes",
        "authored_qpbt_files",
        "authored_qpbt_bytes",
        "authored_qpbt_sha256",
    }:
        return False
    counts = (
        value["files"],
        value["bytes"],
        value["authored_qpbt_files"],
        value["authored_qpbt_bytes"],
    )
    return value == expected_contract and (
        value["schema_version"] == SOURCE_EVIDENCE_SCHEMA_VERSION
        and _is_lower_hex(value["pin_sha256"], 64)
        and _is_lower_hex(value["source_commit"], 40)
        and _is_lower_hex(value["inventory_sha256"], 64)
        and _is_lower_hex(value["authored_qpbt_sha256"], 64)
        and all(
            isinstance(count, int) and not isinstance(count, bool) and count >= 0
            for count in counts
        )
    )


def _trusted_git_environment(
    inherited: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an environment isolated from executable Git configuration."""

    environment = dict(os.environ if inherited is None else inherited)
    for variable in tuple(environment):
        if variable.startswith("GIT_") or variable in {
            "SSH_ASKPASS",
            "SSH_ASKPASS_REQUIRE",
            "PAGER",
            "LESS",
            "LESSOPEN",
            "LESSCLOSE",
        }:
            environment.pop(variable, None)
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_COUNT": str(len(TRUSTED_GIT_CONFIG_OVERRIDES)),
        }
    )
    for index, (key, value) in enumerate(TRUSTED_GIT_CONFIG_OVERRIDES):
        environment[f"GIT_CONFIG_KEY_{index}"] = key
        environment[f"GIT_CONFIG_VALUE_{index}"] = value
    return environment


def _git_command_bytes(repo_root: Path, arguments: Sequence[str]) -> bytes:
    command = ["git", "-C", str(repo_root), *arguments]
    environment = _trusted_git_environment()
    try:
        result = subprocess.run(
            command, capture_output=True, check=False, shell=False, env=environment
        )
    except OSError as error:
        raise CacheError(f"could not run git: {error}") from error
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip() or f"exit {result.returncode}"
        raise CacheError(f"git command failed: {message}")
    return result.stdout


def authored_tree_facts_at_commit(
    repo_root: Path,
    project_dir: Path,
    commit: str,
) -> dict[str, Any]:
    try:
        project_relative = project_dir.resolve().relative_to(repo_root.resolve())
    except ValueError as error:
        raise CacheError("project directory must be inside the repository") from error
    authored_prefix = project_relative / "MIPStarRE" / "QPBT"
    listing = _git_command_bytes(
        repo_root,
        ["ls-tree", "-rz", "--full-tree", commit, "--", authored_prefix.as_posix()],
    )
    records: list[tuple[str, bytes]] = []
    for raw_record in listing.split(b"\0"):
        if not raw_record:
            continue
        metadata, separator, raw_path = raw_record.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3 or fields[1] != b"blob":
            raise CacheError("committed QPBT tree contains an unsupported Git entry")
        mode, _, object_id = fields
        if mode not in (b"100644", b"100755"):
            raise CacheError("committed QPBT tree contains a non-regular entry")
        path = Path(os.fsdecode(raw_path))
        try:
            relative = path.relative_to(authored_prefix).as_posix()
        except ValueError as error:
            raise CacheError("Git returned a QPBT entry outside the requested tree") from error
        payload = _git_command_bytes(repo_root, ["cat-file", "blob", object_id.decode("ascii")])
        records.append((relative, payload))
    records.sort(key=lambda item: item[0])
    digest = hashlib.sha256()
    for relative, payload in records:
        digest.update(
            f"{relative}\0{len(payload)}\0{hashlib.sha256(payload).hexdigest()}\n".encode()
        )
    return {
        "authored_qpbt_files": len(records),
        "authored_qpbt_bytes": sum(len(payload) for _, payload in records),
        "authored_qpbt_sha256": digest.hexdigest(),
    }


def _authored_directory_identity(value: os.stat_result) -> tuple[int, int]:
    if not stat.S_ISDIR(value.st_mode):
        raise CacheError("bound authored QPBT path is no longer a directory")
    return value.st_dev, value.st_ino


def _authored_directory_scan_identity(value: os.stat_result) -> tuple[int, ...]:
    _authored_directory_identity(value)
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_nlink,
    )


def _authored_regular_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_nlink,
    )


def _authored_directory_flags() -> int:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise CacheError("safe authored QPBT traversal requires O_DIRECTORY and O_NOFOLLOW")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@dataclass(frozen=True)
class _BoundAuthoredDirectory:
    lexical_path: Path
    descriptor: int
    identity: tuple[int, int]
    label: str

    def assert_current(self) -> None:
        try:
            current = self.lexical_path.stat(follow_symlinks=False)
        except OSError as error:
            raise CacheError(f"{self.label} path incarnation changed") from error
        if (
            stat.S_ISLNK(current.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or _authored_directory_identity(current) != self.identity
        ):
            raise CacheError(f"{self.label} path incarnation changed")


def _bind_authored_root_directory(path: Path, label: str) -> _BoundAuthoredDirectory:
    absolute = Path(os.path.abspath(path))
    try:
        before = absolute.stat(follow_symlinks=False)
    except OSError as error:
        raise CacheError(f"could not inspect {label}") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise CacheError(f"{label} must be a real directory")
    try:
        descriptor = os.open(absolute, _authored_directory_flags())
    except OSError as error:
        raise CacheError(f"could not bind {label}") from error
    try:
        try:
            descriptor_value = os.fstat(descriptor)
        except OSError as error:
            raise CacheError(f"could not inspect bound {label}") from error
        bound = _BoundAuthoredDirectory(
            absolute,
            descriptor,
            _authored_directory_identity(descriptor_value),
            label,
        )
        if bound.identity != _authored_directory_identity(before):
            raise CacheError(f"{label} changed while binding")
        bound.assert_current()
        return bound
    except Exception:
        os.close(descriptor)
        raise


def _bind_authored_child_directory(
    parent: _BoundAuthoredDirectory,
    name: str,
    label: str,
    *,
    missing_ok: bool = False,
) -> _BoundAuthoredDirectory | None:
    parent.assert_current()
    try:
        before = os.stat(name, dir_fd=parent.descriptor, follow_symlinks=False)
    except FileNotFoundError as error:
        if not missing_ok:
            raise CacheError(f"{label} disappeared while scanning") from error
        parent.assert_current()
        try:
            os.stat(name, dir_fd=parent.descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return None
        except OSError as recheck_error:
            raise CacheError(f"could not recheck absent {label}") from recheck_error
        raise CacheError(f"{label} changed while checking absence")
    except OSError as error:
        raise CacheError(f"could not inspect {label}") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise CacheError(f"{label} must be a real directory")
    try:
        descriptor = os.open(
            name,
            _authored_directory_flags(),
            dir_fd=parent.descriptor,
        )
    except OSError as error:
        raise CacheError(f"could not bind {label}") from error
    lexical_path = parent.lexical_path / name
    try:
        try:
            descriptor_value = os.fstat(descriptor)
        except OSError as error:
            raise CacheError(f"could not inspect bound {label}") from error
        bound = _BoundAuthoredDirectory(
            lexical_path,
            descriptor,
            _authored_directory_identity(descriptor_value),
            label,
        )
        if bound.identity != _authored_directory_identity(before):
            raise CacheError(f"{label} changed while binding")
        parent.assert_current()
        bound.assert_current()
        return bound
    except Exception:
        os.close(descriptor)
        raise


def _authored_file_facts(
    directory: _BoundAuthoredDirectory,
    name: str,
) -> tuple[int, str]:
    path = directory.lexical_path / name
    directory.assert_current()
    try:
        name_before = os.stat(name, dir_fd=directory.descriptor, follow_symlinks=False)
    except OSError as error:
        raise CacheError(f"could not inspect authored QPBT source: {path}") from error
    if not stat.S_ISREG(name_before.st_mode) or name_before.st_nlink != 1:
        raise CacheError(f"authored QPBT source must be a single-link regular file: {path}")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory.descriptor)
    except OSError as error:
        raise CacheError(f"could not safely open authored QPBT source: {path}") from error
    try:
        try:
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or _authored_regular_identity(before)
                != _authored_regular_identity(name_before)
            ):
                raise CacheError(f"authored QPBT source changed while binding: {path}")
            digest = hashlib.sha256()
            total = 0
            while True:
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
                total += len(block)
            after = os.fstat(descriptor)
            name_after = os.stat(
                name,
                dir_fd=directory.descriptor,
                follow_symlinks=False,
            )
        except OSError as error:
            raise CacheError(f"could not safely read authored QPBT source: {path}") from error
        directory.assert_current()
        identity = _authored_regular_identity(before)
        if (
            before.st_nlink != 1
            or after.st_nlink != 1
            or name_after.st_nlink != 1
            or _authored_regular_identity(after) != identity
            or _authored_regular_identity(name_after) != identity
            or total != before.st_size
        ):
            raise CacheError(f"authored QPBT source changed while read: {path}")
        return total, digest.hexdigest()
    finally:
        os.close(descriptor)


def _authored_component(name: str, path: Path) -> str:
    if not name or name in (".", "..") or "/" in name:
        raise CacheError(f"unsafe authored QPBT entry name: {path}")
    try:
        name.encode("utf-8")
    except UnicodeEncodeError as error:
        raise CacheError(f"authored QPBT entry name is not UTF-8: {path}") from error
    return name


def _scan_authored_directory(
    directory: _BoundAuthoredDirectory,
    relative_parts: tuple[str, ...],
    records: list[tuple[str, int, str]],
) -> None:
    directory.assert_current()
    try:
        scan_before = os.fstat(directory.descriptor)
        with os.scandir(directory.descriptor) as entries:
            names = sorted(
                _authored_component(entry.name, directory.lexical_path / entry.name)
                for entry in entries
            )
    except OSError as error:
        raise CacheError(
            f"could not scan authored QPBT directory: {directory.lexical_path}"
        ) from error
    for name in names:
        path = directory.lexical_path / name
        try:
            value = os.stat(name, dir_fd=directory.descriptor, follow_symlinks=False)
        except OSError as error:
            raise CacheError(f"could not inspect authored QPBT entry: {path}") from error
        if stat.S_ISDIR(value.st_mode):
            child = _bind_authored_child_directory(
                directory,
                name,
                f"authored QPBT directory {path}",
            )
            if child is None:
                raise CacheError(f"authored QPBT directory disappeared while scanning: {path}")
            try:
                _scan_authored_directory(child, (*relative_parts, name), records)
            finally:
                os.close(child.descriptor)
        elif stat.S_ISREG(value.st_mode):
            size, digest = _authored_file_facts(directory, name)
            relative = PurePosixPath(*relative_parts, name).as_posix()
            records.append((relative, size, digest))
        else:
            raise CacheError(f"unsafe authored QPBT entry: {path}")
    try:
        scan_after = os.fstat(directory.descriptor)
    except OSError as error:
        raise CacheError(
            f"could not recheck authored QPBT directory: {directory.lexical_path}"
        ) from error
    directory.assert_current()
    if _authored_directory_scan_identity(scan_before) != _authored_directory_scan_identity(
        scan_after
    ):
        raise CacheError(
            f"authored QPBT directory changed while scanned: {directory.lexical_path}"
        )


def authored_tree_facts_on_disk(project_dir: Path) -> dict[str, Any]:
    """Inventory the reserved authored tree through descriptor-bound directories."""

    empty = {
        "authored_qpbt_files": 0,
        "authored_qpbt_bytes": 0,
        "authored_qpbt_sha256": hashlib.sha256().hexdigest(),
    }
    project = _bind_authored_root_directory(project_dir, "authored QPBT project root")
    foundation: _BoundAuthoredDirectory | None = None
    root: _BoundAuthoredDirectory | None = None
    records: list[tuple[str, int, str]] = []
    try:
        foundation = _bind_authored_child_directory(
            project,
            "MIPStarRE",
            "authored QPBT parent",
            missing_ok=True,
        )
        if foundation is None:
            project.assert_current()
            return empty
        root = _bind_authored_child_directory(
            foundation,
            "QPBT",
            "authored QPBT root",
            missing_ok=True,
        )
        if root is None:
            foundation.assert_current()
            project.assert_current()
            return empty
        _scan_authored_directory(root, (), records)
        root.assert_current()
        foundation.assert_current()
        project.assert_current()
    finally:
        if root is not None:
            os.close(root.descriptor)
        if foundation is not None:
            os.close(foundation.descriptor)
        os.close(project.descriptor)

    records.sort(key=lambda item: item[0])
    digest = hashlib.sha256()
    for relative, size, file_digest in records:
        digest.update(f"{relative}\0{size}\0{file_digest}\n".encode("utf-8"))
    return {
        "authored_qpbt_files": len(records),
        "authored_qpbt_bytes": sum(size for _, size, _ in records),
        "authored_qpbt_sha256": digest.hexdigest(),
    }


def authored_contract_facts(source_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: source_contract[key]
        for key in (
            "authored_qpbt_files",
            "authored_qpbt_bytes",
            "authored_qpbt_sha256",
        )
    }


def authored_verification_record(source_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "inventory": authored_contract_facts(source_contract),
        "phases": list(AUTHORED_QPBT_CHECK_PHASES),
    }


def source_contract_at_commit(
    repo_root: Path,
    project_dir: Path,
    commit: str,
    inputs: Mapping[str, str],
    recipe: BuildRecipe,
) -> dict[str, Any] | None:
    if not recipe.materialize_command:
        return None
    pin_relative = Path("references/mipstarre-upstream.json")
    expected_pin_sha256 = inputs.get(pin_relative.as_posix())
    if not isinstance(expected_pin_sha256, str):
        raise CacheError("materializing cache identity omits the upstream provenance pin")
    try:
        project_relative = project_dir.resolve().relative_to(repo_root.resolve())
        pin_bytes = git_blob(repo_root, commit, project_relative / pin_relative)
        pin = json.loads(pin_bytes)
        source = pin["source"]
        output = pin["output"]
        contract = {
            "schema_version": SOURCE_EVIDENCE_SCHEMA_VERSION,
            "pin_sha256": expected_pin_sha256,
            "source_commit": source["commit"],
            "inventory_sha256": output["inventory_sha256"],
            "files": output["files"],
            "bytes": output["bytes"],
            **authored_tree_facts_at_commit(repo_root, project_dir, commit),
        }
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CacheError("could not derive exact source provenance from the committed pin") from error
    if not validate_source_evidence(contract, contract):
        raise CacheError("committed source provenance contains invalid exact facts")
    return contract


def discover_inputs(project_dir: Path, recipe: BuildRecipe | None = None) -> list[Path]:
    """Resolve every versioned identity input in the local detached clone."""

    required = [
        project_dir / "lean-toolchain",
        project_dir / "lakefile.toml",
        project_dir / "lake-manifest.json",
    ] + [project_dir / relative for relative in (recipe.additional_identity_files if recipe else ())]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise CacheError("missing cache-key input(s): " + ", ".join(missing))
    return required


def hash_inputs(
    project_dir: Path, recipe: BuildRecipe | None = None
) -> dict[str, str]:
    return {
        path.relative_to(project_dir).as_posix(): sha256_file(path)
        for path in discover_inputs(project_dir, recipe)
    }


def git_blob(repo_root: Path, commit: str, relative_path: Path) -> bytes:
    git_path = relative_path.as_posix()
    command = ["git", "-C", str(repo_root), "show", f"{commit}:{git_path}"]
    try:
        result = subprocess.run(
            command, capture_output=True, check=False, shell=False, env=_trusted_git_environment()
        )
    except OSError as error:
        raise CacheError(f"could not run git: {error}") from error
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip() or f"exit {result.returncode}"
        raise CacheError(f"could not read {git_path!r} from main commit {commit}: {message}")
    return result.stdout


def hash_inputs_at_commit(
    repo_root: Path, project_dir: Path, commit: str, recipe: BuildRecipe | None = None
) -> dict[str, str]:
    try:
        project_relative = project_dir.resolve().relative_to(repo_root.resolve())
    except ValueError as error:
        raise CacheError("project directory must be inside the repository") from error
    names = (
        "lean-toolchain", "lakefile.toml", "lake-manifest.json",
        *(recipe.additional_identity_files if recipe else ()),
    )
    inputs: dict[str, str] = {}
    for name in names:
        relative = project_relative / name
        inputs[name] = hashlib.sha256(git_blob(repo_root, commit, relative)).hexdigest()
    return inputs


def git_commit(repo_root: Path, ref: str) -> str:
    command = ["git", "-C", str(repo_root), "rev-parse", f"{ref}^{{commit}}"]
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=_trusted_git_environment(),
        )
    except OSError as error:
        raise CacheError(f"could not run git: {error}") from error
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise CacheError(f"could not resolve {ref!r}: {message}")
    commit = result.stdout.strip()
    if not re_full_sha(commit):
        raise CacheError(f"git returned an invalid commit id: {commit!r}")
    return commit


def re_full_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdefABCDEF" for character in value)


def git_source_changes(repo_root: Path) -> list[str]:
    command = [
        "git",
        "-C",
        str(repo_root),
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
    ]
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=_trusted_git_environment(),
        )
    except OSError as error:
        raise CacheError(f"could not run git: {error}") from error
    diagnostics = result.stderr.strip()
    if result.returncode != 0:
        message = diagnostics or result.stdout.strip() or f"exit {result.returncode}"
        raise CacheError(f"could not inspect detached checkout cleanliness: {message}")
    if diagnostics:
        first_line = diagnostics.splitlines()[0][:500]
        raise CacheError(
            f"git emitted diagnostics while inspecting detached checkout cleanliness: {first_line}"
        )
    return [line for line in result.stdout.splitlines() if line]


@dataclass(frozen=True)
class WorktreeRecord:
    path: Path
    head: str | None
    bare: bool
    prunable: bool


def git_worktrees(repo_root: Path) -> list[WorktreeRecord]:
    """Read registered worktrees using Git's stable porcelain format."""

    command = ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"]
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=_trusted_git_environment(),
        )
    except OSError as error:
        raise CacheError(f"could not run git: {error}") from error
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise CacheError(f"could not list registered worktrees: {message}")

    records: list[WorktreeRecord] = []
    for block in result.stdout.strip().split("\n\n"):
        if not block:
            continue
        values: dict[str, str] = {}
        flags: set[str] = set()
        for line in block.splitlines():
            key, separator, value = line.partition(" ")
            if separator:
                values[key] = value
            else:
                flags.add(key)
        path = values.get("worktree")
        if path is None:
            raise CacheError("git worktree porcelain output omitted a worktree path")
        records.append(
            WorktreeRecord(
                path=Path(path),
                head=values.get("HEAD"),
                bare="bare" in flags,
                prunable="prunable" in flags or "prunable" in values,
            )
        )
    return records


def default_runtime_dir(repo_root: Path) -> Path:
    """Return the runtime directory shared by all linked worktrees.

    The command-line default used to be resolved beneath the checkout that
    contained the script. Linked issue worktrees therefore received distinct
    lock files and could rebuild one main snapshot independently. Git's
    porcelain worktree list identifies the primary worktree (the only normal
    worktree with a real ``.git`` directory); use that root for the omitted
    runtime argument. Callers that supply ``--runtime-dir`` keep their explicit
    path semantics.
    """

    try:
        resolved_root = repo_root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise CacheError(
            "could not resolve the repository root for the default runtime directory; "
            "pass --runtime-dir explicitly"
        ) from error
    records = git_worktrees(resolved_root)
    candidates: list[Path] = []
    for record in records:
        if record.bare or record.prunable:
            continue
        try:
            candidate = record.path.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        metadata = candidate / ".git"
        if metadata.is_dir() and not metadata.is_symlink():
            candidates.append(candidate)
    if not candidates:
        raise CacheError(
            "could not identify a primary Git worktree for the default runtime directory; "
            "pass --runtime-dir explicitly"
        )
    # Porcelain lists the primary worktree first. Prefer the caller when it is
    # itself primary, otherwise retain that deterministic ordering.
    if resolved_root in candidates:
        primary = resolved_root
    else:
        primary = candidates[0]
    return primary / ".workflow-runtime"


def git_resolved_path(repo_root: Path, argument: str) -> Path:
    command = ["git", "-C", str(repo_root), "rev-parse", argument]
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
            env=_trusted_git_environment(),
        )
    except OSError as error:
        raise CacheError(f"could not run git: {error}") from error
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise CacheError(f"target is not a live Git worktree: {message}")
    value = Path(result.stdout.strip())
    if not value.is_absolute():
        value = repo_root / value
    try:
        return value.resolve(strict=True)
    except FileNotFoundError as error:
        raise CacheError(f"Git returned a missing path for {argument}: {value}") from error


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def reject_symlink_components(path: Path) -> Path:
    """Return a lexical absolute path after rejecting ``..`` and symlinks."""

    if ".." in path.parts:
        raise CacheError(f"target worktree path cannot contain '..': {path}")
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        if component in ("", "."):
            continue
        current /= component
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        except OSError as error:
            raise CacheError(f"could not inspect target path component {current}: {error}") from error
        if stat.S_ISLNK(mode):
            raise CacheError(f"target worktree path contains a symlink component: {current}")
    return absolute


def _absolute_local_path(value: str, label: str, *, must_exist: bool = True) -> Path:
    """Resolve an environment path without permitting aliases or traversal."""

    if not isinstance(value, str) or not value or value != value.strip():
        raise CacheError(f"{label} must be a non-empty absolute path")
    candidate = Path(value)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise CacheError(f"{label} must be an absolute path without '..'")
    absolute = reject_symlink_components(candidate)
    try:
        metadata = absolute.stat(follow_symlinks=False)
    except FileNotFoundError:
        if must_exist:
            raise CacheError(f"{label} is unavailable: {absolute}")
    except OSError as error:
        raise CacheError(f"{label} is unavailable: {absolute}") from error
    else:
        if stat.S_ISLNK(metadata.st_mode):
            raise CacheError(f"{label} must not be a symlink: {absolute}")
    return absolute


def _read_bounded_descriptor(descriptor: int, maximum: int, label: str) -> bytes:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise CacheError(f"{label} must be one regular file")
    if before.st_size > maximum:
        raise CacheError(f"{label} exceeds the {maximum}-byte bound")
    chunks: list[bytes] = []
    total = 0
    while total <= before.st_size:
        chunk = os.read(descriptor, min(1024 * 1024, before.st_size + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
    after = os.fstat(descriptor)
    identity = lambda item: (
        item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_nlink
    )
    if identity(before) != identity(after) or total != before.st_size:
        raise CacheError(f"{label} changed while read")
    return b"".join(chunks)


def _read_bounded_regular_file(path: Path, maximum: int, label: str) -> bytes:
    """Read one regular file while checking its identity before and after I/O."""

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise CacheError(f"could not open {label}: {error}") from error
    try:
        return _read_bounded_descriptor(descriptor, maximum, label)
    finally:
        os.close(descriptor)


def _read_bounded_project_file(
    project: Path, relative_path: str, maximum: int, label: str
) -> bytes:
    """Read a project-relative file through a no-follow directory chain."""

    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise CacheError(f"{label} has an unsafe project-relative path")
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptors: list[int] = []
    try:
        descriptor = os.open(project, directory_flags)
        descriptors.append(descriptor)
        for component in relative.parts[:-1]:
            descriptor = os.open(component, directory_flags, dir_fd=descriptor)
            descriptors.append(descriptor)
        file_flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        file_descriptor = os.open(relative.parts[-1], file_flags, dir_fd=descriptor)
        try:
            return _read_bounded_descriptor(file_descriptor, maximum, label)
        finally:
            os.close(file_descriptor)
    except CacheError:
        raise
    except OSError as error:
        raise CacheError(f"could not open {label} without following links: {error}") from error
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _json_object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CacheError(f"JSON object repeats key {key!r}")
        result[key] = value
    return result


def _parse_isolated_git_config(payload: bytes) -> dict[str, str]:
    """Parse one config payload without following includes or ambient config."""

    command = [
        "git",
        "config",
        "--no-includes",
        "--file",
        "-",
        "--null",
        "--list",
    ]
    try:
        result = subprocess.run(
            command,
            input=payload,
            capture_output=True,
            check=False,
            shell=False,
            env=_trusted_git_environment(),
        )
    except OSError as error:
        raise CacheError(f"could not parse Mathlib Git configuration: {error}") from error
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise CacheError(f"Mathlib Git configuration is invalid: {message or 'parse failed'}")
    parsed: dict[str, str] = {}
    for raw_record in result.stdout.split(b"\0"):
        if not raw_record:
            continue
        raw_key, separator, raw_value = raw_record.partition(b"\n")
        if not separator:
            raise CacheError("Mathlib Git configuration produced a malformed record")
        try:
            key = raw_key.decode("utf-8").lower()
            value = raw_value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CacheError("Mathlib Git configuration is not UTF-8") from error
        if key in parsed:
            raise CacheError(f"Mathlib Git configuration repeats key {key!r}")
        parsed[key] = value
    return parsed


def _safe_git_config_text(value: str, label: str, *, maximum: int = 4096) -> None:
    if (
        not value
        or len(value.encode("utf-8")) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise CacheError(f"Mathlib Git configuration has an unsafe {label}")


def _safe_git_branch_name(value: str) -> bool:
    forbidden = set(" ~^:?*[\\")
    return (
        0 < len(value) <= 255
        and value not in {".", ".."}
        and not value.startswith(("/", "."))
        and not value.endswith(("/", ".", ".lock"))
        and ".." not in value
        and "@{" not in value
        and "//" not in value
        and not any(character in forbidden or ord(character) < 32 for character in value)
    )


def _validate_mathlib_git_config(git_dir: Path) -> None:
    """Allow only inert structural settings in the supplied repository."""

    payload = _read_bounded_regular_file(
        git_dir / "config", 1024 * 1024, "Mathlib Git configuration"
    )
    config = _parse_isolated_git_config(payload)
    required = {
        "core.repositoryformatversion": "0",
        "core.bare": "false",
        "core.logallrefupdates": "true",
    }
    for key, expected in required.items():
        if config.get(key) != expected:
            raise CacheError(f"Mathlib Git configuration requires {key}={expected}")
    if config.get("core.filemode") not in {"true", "false"}:
        raise CacheError("Mathlib Git configuration requires a Boolean core.filemode")

    for key, value in config.items():
        if key in {*required, "core.filemode"}:
            continue
        if key in {"user.name", "user.email"}:
            _safe_git_config_text(value, key)
            continue
        if key == "remote.origin.url":
            _safe_git_config_text(value, key)
            normalized = value.rstrip("/")
            if not (
                normalized in {MATHLIB_REPOSITORY_URL, f"{MATHLIB_REPOSITORY_URL}.git"}
                or value.startswith("file:///")
            ):
                raise CacheError("Mathlib Git remote URL is outside the local/pinned contract")
            continue
        if key == "remote.origin.tagopt" and value == "--no-tags":
            continue
        if key == "remote.origin.fetch":
            wildcard = "+refs/heads/*:refs/remotes/origin/*"
            if value == wildcard:
                continue
            prefix = "+refs/heads/"
            separator = ":refs/remotes/origin/"
            if value.startswith(prefix) and separator in value:
                source_branch, target_branch = value[len(prefix):].split(separator, 1)
                if source_branch == target_branch and _safe_git_branch_name(source_branch):
                    continue
            raise CacheError("Mathlib Git fetch refspec is outside the pinned contract")
        if key.startswith("branch.") and key.endswith((".remote", ".merge")):
            suffix = ".remote" if key.endswith(".remote") else ".merge"
            branch = key[len("branch."):-len(suffix)]
            if _safe_git_branch_name(branch) and (
                (suffix == ".remote" and value == "origin")
                or (suffix == ".merge" and value == f"refs/heads/{branch}")
            ):
                continue
        raise CacheError(f"Mathlib Git configuration key is not allowed: {key}")


def _git_directory(source: Path) -> Path:
    marker = source / ".git"
    try:
        marker_stat = marker.stat(follow_symlinks=False)
    except OSError as error:
        raise CacheError("Mathlib source must contain standalone Git metadata") from error
    if stat.S_ISLNK(marker_stat.st_mode) or not stat.S_ISDIR(marker_stat.st_mode):
        raise CacheError("Mathlib source must contain a real standalone .git directory")
    # Inspect the local metadata tree before asking Git to resolve anything.
    # In particular, a symlinked objects/ directory could otherwise redirect a
    # seemingly local repository to an external object store.
    _validate_git_metadata_layout(marker)
    _validate_mathlib_git_config(marker)
    raw = _git_command_bytes(source, ["rev-parse", "--git-dir"]).decode("utf-8", errors="strict").strip()
    if not raw:
        raise CacheError("Mathlib source returned an empty Git directory")
    git_dir = Path(raw)
    if not git_dir.is_absolute():
        git_dir = source / git_dir
    git_dir = _absolute_local_path(str(git_dir), "Mathlib source Git directory")
    if git_dir.resolve(strict=True) != marker.resolve(strict=True):
        raise CacheError("Mathlib source Git directory must be its local .git directory")
    metadata = git_dir.stat(follow_symlinks=False)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CacheError("Mathlib source Git directory is not a real directory")
    _validate_git_metadata_layout(git_dir)
    return git_dir


def _validate_git_metadata_layout(git_dir: Path) -> None:
    """Reject symlinked or special Git metadata before Git reads objects."""

    required_directories = (git_dir / "objects", git_dir / "refs")
    required_files = (git_dir / "HEAD", git_dir / "config", git_dir / "index")
    for path in required_directories:
        try:
            metadata = path.stat(follow_symlinks=False)
        except OSError as error:
            raise CacheError(f"Mathlib Git metadata is unavailable: {path}") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise CacheError(f"Mathlib Git metadata directory is not real: {path}")
    for path in required_files:
        try:
            metadata = path.stat(follow_symlinks=False)
        except OSError as error:
            raise CacheError(f"Mathlib Git metadata is unavailable: {path}") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise CacheError(f"Mathlib Git metadata file is not regular: {path}")
    commondir = git_dir / "commondir"
    try:
        commondir_stat = commondir.stat(follow_symlinks=False)
    except FileNotFoundError:
        commondir_stat = None
    except OSError as error:
        raise CacheError(f"could not inspect Mathlib Git common-directory marker: {commondir}") from error
    if commondir_stat is not None:
        raise CacheError("Mathlib source must not use an external Git common directory")

    entries = 0

    def onerror(error: OSError) -> None:
        raise CacheError(f"could not inspect Mathlib Git metadata: {error}") from error

    for directory, directory_names, file_names in os.walk(
        git_dir, topdown=True, followlinks=False, onerror=onerror
    ):
        entries += len(directory_names) + len(file_names)
        if entries > 100_000:
            raise CacheError("Mathlib Git metadata exceeds its entry bound")
        for name in (*directory_names, *file_names):
            path = Path(directory) / name
            try:
                metadata = path.stat(follow_symlinks=False)
            except OSError as error:
                raise CacheError(f"could not inspect Mathlib Git metadata: {path}") from error
            if stat.S_ISLNK(metadata.st_mode):
                raise CacheError(f"Mathlib Git metadata contains a symlink: {path}")
            if not stat.S_ISDIR(metadata.st_mode) and not stat.S_ISREG(metadata.st_mode):
                raise CacheError(f"Mathlib Git metadata contains a special entry: {path}")


def _git_pack_facts(git_dir: Path) -> tuple[str | None, int | None]:
    pack_dir = git_dir / "objects" / "pack"
    try:
        metadata = pack_dir.stat(follow_symlinks=False)
    except OSError as error:
        raise CacheError("Mathlib source Git object directory is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CacheError("Mathlib source Git pack directory is not real")
    packs = sorted(pack_dir.glob("*.pack"))
    if not packs:
        return None, None
    # A mirror can be repacked without changing its commit/tree identity.  We
    # report the digest when there is one canonical pack but do not make it a
    # cache key input.
    for pack in packs:
        pack_metadata = pack.stat(follow_symlinks=False)
        if stat.S_ISLNK(pack_metadata.st_mode) or not stat.S_ISREG(pack_metadata.st_mode):
            raise CacheError("Mathlib source pack contains a non-regular entry")
        if pack_metadata.st_nlink != 1:
            raise CacheError("Mathlib source pack must not be hard-linked")
    if len(packs) != 1:
        return None, None
    pack = packs[0]
    return sha256_file(pack), pack.stat(follow_symlinks=False).st_size


def validate_mathlib_source(
    source: Path,
    *,
    expected_commit: str | None = None,
    expected_tree: str | None = None,
) -> dict[str, Any]:
    """Authenticate a local Mathlib Git repository to the pinned commit/tree."""

    expected_commit = MATHLIB_COMMIT if expected_commit is None else expected_commit
    expected_tree = MATHLIB_TREE if expected_tree is None else expected_tree
    if not _is_lower_hex(expected_commit, 40) or not _is_lower_hex(expected_tree, 40):
        raise CacheError("Mathlib authenticated pin must contain lowercase full Git IDs")
    source = _absolute_local_path(str(source), "Mathlib source")
    metadata = source.stat(follow_symlinks=False)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CacheError("Mathlib source must be a real Git worktree directory")
    # Resolve and reject external object stores before any object-reading Git
    # command (including status or revision resolution) is allowed to run.
    git_dir = _git_directory(source)
    _validate_git_metadata_layout(git_dir)
    alternates = git_dir / "objects" / "info" / "alternates"
    try:
        alternates_stat = alternates.stat(follow_symlinks=False)
    except FileNotFoundError:
        alternates_stat = None
    except OSError as error:
        raise CacheError("could not inspect Mathlib object alternates") from error
    if alternates_stat is not None:
        raise CacheError("Mathlib source must not use Git object alternates")
    replace_refs = git_dir / "refs" / "replace"
    try:
        replace_stat = replace_refs.stat(follow_symlinks=False)
    except FileNotFoundError:
        replace_stat = None
    except OSError as error:
        raise CacheError("could not inspect Mathlib replacement refs") from error
    if replace_stat is not None:
        raise CacheError("Mathlib source must not contain replacement refs")
    packed_refs = git_dir / "packed-refs"
    if packed_refs.exists() and b" refs/replace/" in _read_bounded_regular_file(
        packed_refs, 16 * 1024 * 1024, "Mathlib packed refs"
    ):
        raise CacheError("Mathlib source must not contain packed replacement refs")
    shallow = git_dir / "shallow"
    try:
        shallow_stat = shallow.stat(follow_symlinks=False)
    except FileNotFoundError:
        shallow_stat = None
    except OSError as error:
        raise CacheError("could not inspect Mathlib shallow boundary") from error
    if shallow_stat is not None:
        if stat.S_ISLNK(shallow_stat.st_mode):
            raise CacheError("Mathlib shallow boundary must be a regular file")
        shallow_bytes = _read_bounded_regular_file(shallow, 1024 * 1024, "Mathlib shallow boundary")
        try:
            boundaries = {line.decode("ascii") for line in shallow_bytes.splitlines() if line}
        except UnicodeDecodeError as error:
            raise CacheError("Mathlib shallow boundary is not ASCII") from error
        if boundaries != {expected_commit}:
            raise CacheError("Mathlib shallow boundary is not the pinned commit")
    inside = _git_command_bytes(source, ["rev-parse", "--is-inside-work-tree"]).decode().strip()
    bare = _git_command_bytes(source, ["rev-parse", "--is-bare-repository"]).decode().strip()
    if inside != "true" or bare != "false":
        raise CacheError("Mathlib source must be a non-bare Git worktree")
    top = Path(_git_command_bytes(source, ["rev-parse", "--show-toplevel"]).decode().strip())
    if not top.is_absolute() or top.resolve(strict=True) != source.resolve(strict=True):
        raise CacheError("Mathlib source Git top-level differs from the supplied path")
    commit = _git_command_bytes(source, ["rev-parse", "HEAD^{commit}"]).decode().strip().lower()
    tree = _git_command_bytes(source, ["rev-parse", "HEAD^{tree}"]).decode().strip().lower()
    if commit != expected_commit:
        raise CacheError(
            f"Mathlib source commit differs: expected {expected_commit}, got {commit}"
        )
    if tree != expected_tree:
        raise CacheError(f"Mathlib source tree differs: expected {expected_tree}, got {tree}")
    changes = _git_command_bytes(
        source,
        ["status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"],
    ).decode("utf-8", errors="replace").strip()
    if changes:
        raise CacheError("Mathlib source has tracked or untracked changes")
    index = _git_command_bytes(source, ["ls-files", "--stage", "-z"])
    if any(record.startswith(b"160000 ") for record in index.split(b"\0") if record):
        raise CacheError("Mathlib source must not contain Git submodules")
    index_flags = _git_command_bytes(source, ["ls-files", "-v", "-z"])
    if any(not record.startswith(b"H ") for record in index_flags.split(b"\0") if record):
        raise CacheError("Mathlib source index contains noncanonical visibility flags")
    # fsck is deliberately local and does not contact the configured remote;
    # check alternates first so it cannot traverse an external object store.
    _git_command_bytes(source, ["fsck", "--full", "--no-progress"])
    pack_sha256, pack_bytes = _git_pack_facts(git_dir)
    _validate_git_metadata_layout(git_dir)
    _validate_mathlib_git_config(git_dir)
    return {
        "commit": commit,
        "tree": tree,
        "pack_sha256": pack_sha256,
        "pack_bytes": pack_bytes,
    }


def _safe_archive_relative(name: str) -> str:
    if not name or "\\" in name or "\0" in name or name.startswith("/"):
        raise CacheError(f"unsafe Mathlib archive member path: {name!r}")
    normalized = name[:-1] if name.endswith("/") else name
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise CacheError(f"unsafe Mathlib archive member path: {name!r}")
    if normalized == "mathlib":
        return ""
    prefix = "mathlib/"
    if not normalized.startswith(prefix):
        raise CacheError("Mathlib archive contains a member outside its exact mathlib/ prefix")
    return normalized[len(prefix):]


def _safe_archive_link(relative: str, target: str) -> None:
    if not target or "\\" in target or "\0" in target or target.startswith("/"):
        raise CacheError(f"unsafe Mathlib archive symlink target: {target!r}")
    pieces = list(PurePosixPath(relative).parent.parts)
    for part in PurePosixPath(target).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not pieces:
                raise CacheError("Mathlib archive symlink escapes its root")
            pieces.pop()
        else:
            pieces.append(part)


def _validate_archive_link_graph(records: Mapping[str, tarfile.TarInfo]) -> None:
    """Resolve archive symlink chains component-wise and reject escapes/cycles."""

    links = {
        relative: member.linkname
        for relative, member in records.items()
        if member.issym()
    }
    for relative, target in links.items():
        parent = PurePosixPath(relative).parent
        resolved = [] if parent == PurePosixPath(".") else list(parent.parts)
        pending = list(PurePosixPath(target).parts)
        expanded: set[str] = set()
        steps = 0
        while pending:
            steps += 1
            if steps > len(records) + MATHLIB_TAR_MAX_MEMBERS:
                raise CacheError("Mathlib archive symlink graph exceeds its step bound")
            part = pending.pop(0)
            if part in {"", "."}:
                continue
            if part == "..":
                if not resolved:
                    raise CacheError("Mathlib archive symlink chain escapes its root")
                resolved.pop()
                continue
            candidate = "/".join((*resolved, part))
            nested_target = links.get(candidate)
            if nested_target is None:
                resolved.append(part)
                continue
            if candidate in expanded:
                raise CacheError("Mathlib archive symlink graph contains a cycle")
            expanded.add(candidate)
            pending = list(PurePosixPath(nested_target).parts) + pending


def _decompress_mathlib_archive(payload: bytes) -> bytes:
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    try:
        raw = decompressor.decompress(payload, MATHLIB_TAR_MAX_BYTES + 1)
        if decompressor.unconsumed_tail:
            raise CacheError("Mathlib archive tar output exceeds its hard bound")
        remaining = MATHLIB_TAR_MAX_BYTES + 1 - len(raw)
        if remaining < 0:
            raise CacheError("Mathlib archive tar output exceeds its hard bound")
        raw += decompressor.flush(remaining)
    except zlib.error as error:
        raise CacheError(f"Mathlib archive is not a valid gzip stream: {error}") from error
    if not decompressor.eof or decompressor.unused_data or len(raw) > MATHLIB_TAR_MAX_BYTES:
        raise CacheError("Mathlib archive gzip stream is truncated or has trailing data")
    if len(raw) != MATHLIB_ARCHIVE_TAR_BYTES:
        raise CacheError(
            f"Mathlib archive tar size differs: expected {MATHLIB_ARCHIVE_TAR_BYTES}, got {len(raw)}"
        )
    if hashlib.sha256(raw).hexdigest() != MATHLIB_ARCHIVE_TAR_SHA256:
        raise CacheError("Mathlib archive tar checksum differs from the pinned digest")
    return raw


def materialize_mathlib_archive(
    archive: Path,
    destination: Path,
    *,
    expected_commit: str | None = None,
    expected_tree: str | None = None,
) -> dict[str, Any]:
    """Verify and safely unpack the pinned shallow-repository archive."""

    archive = _absolute_local_path(str(archive), "Mathlib archive")
    destination = _absolute_local_path(
        str(destination), "Mathlib archive destination", must_exist=False
    )
    if destination.exists() or destination.is_symlink():
        raise CacheError(f"Mathlib archive destination already exists: {destination}")
    payload = _read_bounded_regular_file(archive, MATHLIB_ARCHIVE_MAX_BYTES, "Mathlib archive")
    if len(payload) != MATHLIB_ARCHIVE_BYTES:
        raise CacheError(
            f"Mathlib archive size differs: expected {MATHLIB_ARCHIVE_BYTES}, got {len(payload)}"
        )
    if hashlib.sha256(payload).hexdigest() != MATHLIB_ARCHIVE_SHA256:
        raise CacheError("Mathlib archive checksum differs from the pinned digest")
    raw_tar = _decompress_mathlib_archive(payload)
    try:
        with tarfile.open(fileobj=io.BytesIO(raw_tar), mode="r:") as tar:
            members = tar.getmembers()
            if len(members) > MATHLIB_TAR_MAX_MEMBERS:
                raise CacheError("Mathlib archive member count exceeds its hard bound")
            records: dict[str, tarfile.TarInfo] = {}
            regular_bytes = 0
            for member in members:
                relative = _safe_archive_relative(member.name)
                if relative in records:
                    raise CacheError(f"duplicate Mathlib archive member: {relative!r}")
                if member.isdir():
                    if member.size != 0:
                        raise CacheError("Mathlib archive directory has a nonzero size")
                elif member.isfile():
                    if member.size < 0:
                        raise CacheError("Mathlib archive member has a negative size")
                    if member.size > MATHLIB_TAR_MAX_MEMBER_BYTES:
                        raise CacheError("Mathlib archive member exceeds its hard bound")
                    regular_bytes += member.size
                    if regular_bytes > MATHLIB_TAR_MAX_BYTES:
                        raise CacheError("Mathlib archive regular bytes exceed its hard bound")
                elif member.issym():
                    _safe_archive_link(relative, member.linkname)
                else:
                    raise CacheError("Mathlib archive contains a hardlink or special file")
                records[relative] = member
            _validate_archive_link_graph(records)
            if "" not in records or not records[""].isdir():
                raise CacheError("Mathlib archive lacks its exact root directory")
            required = (".git", ".git/HEAD", ".git/shallow", ".git/objects")
            for required_path in required:
                item = records.get(required_path)
                if item is None:
                    raise CacheError(f"Mathlib archive lacks required Git entry {required_path}")
                if required_path in {".git", ".git/objects"} and not item.isdir():
                    raise CacheError(f"Mathlib archive Git entry {required_path} is not a directory")
                if required_path in {".git/HEAD", ".git/shallow"} and not item.isfile():
                    raise CacheError(f"Mathlib archive Git entry {required_path} is not a file")
            kinds = {
                relative: "directory" if member.isdir() else "symlink" if member.issym() else "file"
                for relative, member in records.items()
            }
            for relative in records:
                parent = PurePosixPath(relative).parent
                while parent != PurePosixPath("."):
                    parent_text = parent.as_posix()
                    if kinds.get(parent_text) != "directory":
                        raise CacheError(f"Mathlib archive member has a non-directory parent: {relative}")
                    parent = parent.parent
            destination.mkdir(parents=True)
            # Create all directories before files so archive symlinks can never
            # become an intermediate path component during extraction.
            for relative, member in sorted(records.items(), key=lambda item: (item[0].count("/"), item[0])):
                if not member.isdir() or relative == "":
                    continue
                path = destination / relative
                path.mkdir(exist_ok=False)
                path.chmod(member.mode & 0o777 or 0o755)
            for relative, member in records.items():
                if not member.isfile():
                    continue
                path = destination / relative
                descriptor = os.open(
                    path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    member.mode & 0o777 or 0o644,
                )
                try:
                    stream = tar.extractfile(member)
                    if stream is None:
                        raise CacheError(f"could not read Mathlib archive member {relative}")
                    copied = 0
                    while copied < member.size:
                        chunk = stream.read(min(1024 * 1024, member.size - copied))
                        if not chunk:
                            break
                        view = memoryview(chunk)
                        while view:
                            written = os.write(descriptor, view)
                            if written <= 0:
                                raise CacheError(
                                    f"could not write Mathlib archive member {relative}"
                                )
                            view = view[written:]
                        copied += len(chunk)
                    if copied != member.size or stream.read(1):
                        raise CacheError(f"Mathlib archive member changed while extracted: {relative}")
                finally:
                    os.close(descriptor)
                (destination / relative).chmod(member.mode & 0o777 or 0o644)
            for relative, member in records.items():
                if member.issym():
                    os.symlink(member.linkname, destination / relative)
    except (CacheError, tarfile.TarError, OSError) as error:
        if destination.exists() or destination.is_symlink():
            try:
                make_owner_writable(destination)
                shutil.rmtree(destination)
            except OSError as cleanup_error:
                raise CacheError(
                    f"could not unpack Mathlib archive ({error}); cleanup failed: {cleanup_error}"
                ) from error
        if isinstance(error, CacheError):
            raise
        raise CacheError(f"could not unpack Mathlib archive: {error}") from error
    try:
        facts = validate_mathlib_source(
            destination, expected_commit=expected_commit, expected_tree=expected_tree
        )
    except Exception:
        if destination.exists() or destination.is_symlink():
            make_owner_writable(destination)
            shutil.rmtree(destination)
        raise
    facts.update(
        {
            "mode": "archive",
            "archive_sha256": MATHLIB_ARCHIVE_SHA256,
            "archive_bytes": MATHLIB_ARCHIVE_BYTES,
        }
    )
    return facts


def validate_mathlib_evidence(value: Any) -> bool:
    """Check the stable, path-independent Mathlib evidence in a cache manifest."""

    if not isinstance(value, dict) or set(value) != MATHLIB_EVIDENCE_KEYS:
        return False
    if (
        value["schema_version"] != MATHLIB_SOURCE_EVIDENCE_SCHEMA_VERSION
        or value["repository_url"] != MATHLIB_REPOSITORY_URL
        or value["commit"] != MATHLIB_COMMIT
        or value["tree"] != MATHLIB_TREE
        or value["mode"] not in {"source", "archive"}
    ):
        return False
    for field in ("archive_sha256", "pack_sha256"):
        digest = value[field]
        if digest is not None and not _is_lower_hex(digest, 64):
            return False
    for field in ("archive_bytes", "pack_bytes"):
        number = value[field]
        if number is not None and (not isinstance(number, int) or isinstance(number, bool) or number < 0):
            return False
    if value["mode"] == "archive":
        if value["archive_sha256"] != MATHLIB_ARCHIVE_SHA256 or value["archive_bytes"] != MATHLIB_ARCHIVE_BYTES:
            return False
    elif value["archive_sha256"] is not None or value["archive_bytes"] is not None:
        return False
    return (value["pack_sha256"] is None) == (value["pack_bytes"] is None)


@dataclass(frozen=True)
class CacheIdentity:
    cache_key: str
    main_commit: str
    inputs: dict[str, str]
    recipe: dict[str, Any]
    source_contract: dict[str, Any] | None

    @classmethod
    def create(
        cls,
        repo_root: Path,
        project_dir: Path,
        recipe: BuildRecipe,
        main_ref: str = "main",
        main_commit: str | None = None,
    ) -> "CacheIdentity":
        commit = main_commit or git_commit(repo_root, main_ref)
        if not re_full_sha(commit):
            raise CacheError(f"invalid main commit {commit!r}; expected a full 40-character SHA")
        inputs = hash_inputs_at_commit(repo_root, project_dir, commit, recipe)
        recipe_payload = recipe.identity_payload()
        source_contract = source_contract_at_commit(
            repo_root, project_dir, commit, inputs, recipe
        )
        payload = json.dumps(
            {
                "main_commit": commit.lower(),
                "inputs": inputs,
                "recipe": recipe_payload,
                "source_contract": source_contract,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        return cls(
            hashlib.sha256(payload).hexdigest(),
            commit.lower(),
            inputs,
            recipe_payload,
            source_contract,
        )


@dataclass
class CopyStats:
    files: int = 0
    bytes: int = 0
    reflinked: int = 0
    copied: int = 0
    symlinks: int = 0


def _copy_regular_file(source: Path, destination: Path, stats: CopyStats) -> None:
    size = source.stat(follow_symlinks=False).st_size
    source_fd = os.open(source, os.O_RDONLY)
    destination_fd: int | None = None
    try:
        destination_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            fcntl.ioctl(destination_fd, FICLONE, source_fd)
            stats.reflinked += 1
        except OSError as error:
            if error.errno not in REFLINK_FALLBACK_ERRNOS:
                raise
            os.close(destination_fd)
            destination_fd = None
            destination.unlink()
            shutil.copy2(source, destination, follow_symlinks=False)
            stats.copied += 1
        else:
            shutil.copystat(source, destination, follow_symlinks=False)
    finally:
        os.close(source_fd)
        if destination_fd is not None:
            os.close(destination_fd)
    stats.files += 1
    stats.bytes += size


def reflink_copytree(source: Path, destination: Path) -> CopyStats:
    """Copy a tree using Linux reflinks where available, never hardlinks."""

    if not source.is_dir() or source.is_symlink():
        raise CacheError(f"copy source must be a real directory: {source}")
    if destination.exists() or destination.is_symlink():
        raise CacheError(f"copy destination already exists: {destination}")
    stats = CopyStats()
    destination.mkdir(parents=True)

    def visit(source_dir: Path, destination_dir: Path) -> None:
        for entry in os.scandir(source_dir):
            source_path = Path(entry.path)
            destination_path = destination_dir / entry.name
            if entry.is_symlink():
                os.symlink(os.readlink(source_path), destination_path)
                try:
                    shutil.copystat(source_path, destination_path, follow_symlinks=False)
                except (NotImplementedError, OSError):
                    pass
                stats.symlinks += 1
            elif entry.is_dir(follow_symlinks=False):
                destination_path.mkdir()
                visit(source_path, destination_path)
                shutil.copystat(source_path, destination_path, follow_symlinks=False)
            elif entry.is_file(follow_symlinks=False):
                _copy_regular_file(source_path, destination_path, stats)
            else:
                raise CacheError(f"unsupported cache entry type: {source_path}")

    visit(source, destination)
    shutil.copystat(source, destination, follow_symlinks=False)
    return stats


def _walk_without_following(root: Path) -> list[Path]:
    paths: list[Path] = [root]
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        paths.extend(base / name for name in names)
        paths.extend(base / name for name in files)
    return paths


def _strict_walk_without_following(root: Path) -> list[Path]:
    """Walk a tree without following links, surfacing every traversal error."""

    paths: list[Path] = [root]

    def fail(error: OSError) -> None:
        raise CacheError(f"could not inspect Lake tree {error.filename or root}: {error}") from error

    for directory, names, files in os.walk(root, followlinks=False, onerror=fail):
        base = Path(directory)
        paths.extend(base / name for name in names)
        paths.extend(base / name for name in files)
    return paths


def _validate_lake_symlink_policy(root: Path) -> None:
    """Reject links whose first hop or final target escapes the private tree."""

    if not root.is_dir() or root.is_symlink():
        raise CacheError(f"Lake root must be a real directory: {root}")
    root_resolved = root.resolve(strict=True)
    for path in _strict_walk_without_following(root):
        if not path.is_symlink():
            continue
        raw_target = Path(os.readlink(path))
        first_hop = (
            raw_target
            if raw_target.is_absolute()
            else root_resolved / path.relative_to(root).parent / raw_target
        )
        first_hop = Path(os.path.abspath(first_hop))
        if not path_is_within(first_hop, root_resolved):
            raise CacheError(f"symlink first hop escapes private Lake tree: {path}")
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise CacheError(f"symlink target cannot be resolved: {path}: {error}") from error
        if not path_is_within(resolved, root_resolved):
            raise CacheError(f"symlink target escapes private Lake tree: {path}")


def make_read_only(root: Path) -> None:
    for path in reversed(_walk_without_following(root)):
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
        path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH), follow_symlinks=False)


def make_owner_writable(root: Path) -> None:
    for path in _walk_without_following(root):
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
        path.chmod(mode | stat.S_IWUSR, follow_symlinks=False)


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


class ExclusiveLock:
    def __init__(self, path: Path):
        self.path = path
        self.stream: Any = None
        self.waited = False
        self.wait_seconds = 0.0

    def __enter__(self) -> "ExclusiveLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+", encoding="utf-8")
        started = time.monotonic()
        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.waited = True
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX)
            self.wait_seconds = time.monotonic() - started
        return self

    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
        if self.stream is None:
            return
        cleanup_error: BaseException | None = None
        try:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        except BaseException as error:
            cleanup_error = error
        try:
            self.stream.close()
        except BaseException as error:
            if cleanup_error is None:
                cleanup_error = error
        if cleanup_error is not None:
            raise cleanup_error


CommandCallback = Callable[[Path, Sequence[str], Path], int | None]
SourceVerifier = Callable[[Path], Mapping[str, Any]]


class HotMainCache:
    """Operations for one identity-keyed main cache snapshot."""

    def __init__(
        self,
        repo_root: Path,
        project_dir: Path,
        runtime_dir: Path,
        *,
        main_ref: str = "main",
        main_commit: str | None = None,
        _test_recipe: BuildRecipe | None = None,
    ):
        self.repo_root = repo_root.resolve()
        self.project_dir = project_dir.resolve()
        self.runtime_dir = runtime_dir.resolve()
        self.main_ref = main_ref
        if _test_recipe is not None and not _test_recipe.test_only:
            raise CacheError("the internal recipe override only accepts test-only recipes")
        self.recipe = _test_recipe or CANONICAL_BUILD_RECIPE
        self.identity = CacheIdentity.create(
            self.repo_root,
            self.project_dir,
            self.recipe,
            main_ref=main_ref,
            main_commit=main_commit,
        )
        self.cache_root = self.runtime_dir / "cache" / "main"
        self.snapshot_dir = self.cache_root / self.identity.cache_key
        self.lake_dir = self.snapshot_dir / ".lake"
        self.build_dir = self.lake_dir / "build"
        self.manifest_path = self.snapshot_dir / "manifest.json"
        self.ready_path = self.snapshot_dir / "READY"
        self.lock_path = self.runtime_dir / "locks" / f"hot-main-{self.identity.cache_key}.lock"
        self.metrics_path = self.runtime_dir / "metrics" / "hot-main.jsonl"
        self.metrics_lock_path = self.runtime_dir / "locks" / "hot-main-metrics.lock"
        self._command_environment: dict[str, str] | None = None

    def _requires_mathlib_source(self) -> bool:
        """Return whether this recipe executes Lake against the pinned project."""

        return self.recipe == CANONICAL_BUILD_RECIPE

    @staticmethod
    def _lake_url_map(environment: Mapping[str, str], lake_url: str) -> dict[str, str]:
        raw = environment.get("LAKE_PKG_URL_MAP")
        if raw is None or raw == "":
            mapping: Any = {}
        else:
            try:
                mapping = json.loads(raw, object_pairs_hook=_json_object_without_duplicates)
            except (TypeError, json.JSONDecodeError) as error:
                raise CacheError("LAKE_PKG_URL_MAP must be valid JSON") from error
        if not isinstance(mapping, dict) or any(
            not isinstance(key, str) or not key or not isinstance(value, str) or not value
            for key, value in mapping.items()
        ):
            raise CacheError("LAKE_PKG_URL_MAP must be a string-to-string JSON object")
        existing = mapping.get(MATHLIB_PACKAGE_NAME)
        if existing is not None and existing != lake_url:
            raise CacheError("LAKE_PKG_URL_MAP already binds mathlib to a different URL")
        mapping[MATHLIB_PACKAGE_NAME] = lake_url
        return mapping

    def _command_environment_for_mathlib(
        self, binding: MathlibSourceBinding
    ) -> dict[str, str]:
        environment = _trusted_git_environment()
        mapping = self._lake_url_map(environment, binding.lake_url)
        environment["LAKE_PKG_URL_MAP"] = json.dumps(
            mapping, sort_keys=True, separators=(",", ":")
        )
        # A malformed local setup must fail promptly rather than waiting for a
        # credential prompt if a non-Mathlib dependency is accidentally fetched.
        environment["GIT_TERMINAL_PROMPT"] = "0"
        return environment

    @staticmethod
    def _validate_project_mathlib_pin_payload(payload: bytes) -> dict[str, str]:
        """Parse captured root-manifest bytes and bind the Mathlib contract."""

        try:
            document = json.loads(
                payload.decode("utf-8"),
                object_pairs_hook=_json_object_without_duplicates,
            )
        except CacheError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CacheError("root Lake manifest is not valid JSON") from error
        if not isinstance(document, dict):
            raise CacheError("root Lake manifest must be a JSON object")
        packages = document.get("packages")
        if not isinstance(packages, list):
            raise CacheError("root Lake manifest packages must be a JSON array")
        matches = [
            package
            for package in packages
            if isinstance(package, dict) and package.get("name") == MATHLIB_PACKAGE_NAME
        ]
        if len(matches) != 1:
            raise CacheError("root Lake manifest must contain exactly one mathlib package")
        package = matches[0]
        if (
            package.get("type") != "git"
            or package.get("url") != MATHLIB_REPOSITORY_URL
            or package.get("rev") != MATHLIB_COMMIT
        ):
            raise CacheError("root Lake manifest mathlib pin differs from the authenticated contract")
        # Use the URL and revision parsed above for the source binding.  The
        # tree is the second half of the authenticated exact contract; keeping
        # it separate avoids confusing the project's own source commit with
        # Mathlib's revision.
        return {
            "repository_url": package["url"],
            "commit": package["rev"],
            "tree": MATHLIB_TREE,
        }

    @classmethod
    def _validate_project_mathlib_pin(cls, project: Path) -> dict[str, str]:
        """Read one stable root manifest and bind it to the Mathlib contract."""

        payload = _read_bounded_regular_file(
            project / "lake-manifest.json", IDENTITY_INPUT_MAX_BYTES, "root Lake manifest"
        )
        return cls._validate_project_mathlib_pin_payload(payload)

    def _prepare_mathlib_source(self, staging: Path, project: Path) -> MathlibSourceBinding:
        """Resolve and authenticate the local Mathlib source before Lake runs."""

        if not self._requires_mathlib_source():
            raise CacheError("Mathlib source preparation is only valid for the canonical recipe")
        captured_inputs = self._capture_identity_inputs(project)
        pin = self._validate_project_mathlib_pin_payload(
            captured_inputs["lake-manifest.json"]
        )
        source_value = os.environ.get(MATHLIB_SOURCE_ENV)
        archive_value = os.environ.get(MATHLIB_ARCHIVE_ENV)
        if bool(source_value) == bool(archive_value):
            raise CacheError(
                f"set exactly one of {MATHLIB_SOURCE_ENV} or {MATHLIB_ARCHIVE_ENV}"
            )
        owned_path: Path | None = None
        if source_value:
            source = _absolute_local_path(source_value, MATHLIB_SOURCE_ENV)
            facts = validate_mathlib_source(
                source, expected_commit=pin["commit"], expected_tree=pin["tree"]
            )
            mode = "source"
            archive_sha256 = None
            archive_bytes = None
        else:
            archive = _absolute_local_path(archive_value or "", MATHLIB_ARCHIVE_ENV)
            owned_path = staging / "mathlib-source"
            facts = materialize_mathlib_archive(
                archive,
                owned_path,
                expected_commit=pin["commit"],
                expected_tree=pin["tree"],
            )
            source = owned_path
            mode = "archive"
            archive_sha256 = MATHLIB_ARCHIVE_SHA256
            archive_bytes = MATHLIB_ARCHIVE_BYTES
        evidence = {
            "schema_version": MATHLIB_SOURCE_EVIDENCE_SCHEMA_VERSION,
            "repository_url": pin["repository_url"],
            "commit": facts["commit"],
            "tree": facts["tree"],
            "mode": mode,
            "archive_sha256": archive_sha256,
            "archive_bytes": archive_bytes,
            "pack_sha256": facts.get("pack_sha256"),
            "pack_bytes": facts.get("pack_bytes"),
        }
        if not validate_mathlib_evidence(evidence):
            raise CacheError("authenticated Mathlib source evidence has an invalid shape")
        return MathlibSourceBinding(
            path=source,
            lake_url=source.as_uri(),
            evidence=evidence,
            owned_path=owned_path,
        )

    @staticmethod
    def _validate_mathlib_archive_input(archive: Path) -> None:
        """Check an archive's stable bytes before a cache hit or build decision."""

        payload = _read_bounded_regular_file(
            archive, MATHLIB_ARCHIVE_MAX_BYTES, "Mathlib archive"
        )
        if len(payload) != MATHLIB_ARCHIVE_BYTES:
            raise CacheError(
                f"Mathlib archive size differs: expected {MATHLIB_ARCHIVE_BYTES}, got {len(payload)}"
            )
        if hashlib.sha256(payload).hexdigest() != MATHLIB_ARCHIVE_SHA256:
            raise CacheError("Mathlib archive checksum differs from the pinned digest")

    def _preflight_mathlib_input(
        self, captured_inputs: Mapping[str, bytes] | None = None
    ) -> None:
        """Fail closed when the canonical warm input is absent or malformed."""

        if not self._requires_mathlib_source():
            return
        pin = (
            self._validate_project_mathlib_pin_payload(captured_inputs["lake-manifest.json"])
            if captured_inputs is not None
            else self._validate_project_mathlib_pin(self.project_dir)
        )
        source_value = os.environ.get(MATHLIB_SOURCE_ENV)
        archive_value = os.environ.get(MATHLIB_ARCHIVE_ENV)
        if bool(source_value) == bool(archive_value):
            raise CacheError(
                f"set exactly one of {MATHLIB_SOURCE_ENV} or {MATHLIB_ARCHIVE_ENV}"
        )
        if source_value:
            validate_mathlib_source(
                _absolute_local_path(source_value, MATHLIB_SOURCE_ENV),
                expected_commit=pin["commit"],
                expected_tree=pin["tree"],
            )
        else:
            archive = _absolute_local_path(archive_value or "", MATHLIB_ARCHIVE_ENV)
            self._validate_mathlib_archive_input(archive)

    def _capture_identity_inputs(self, project: Path) -> dict[str, bytes]:
        """Capture and authenticate every commit-bound input without reopening it."""

        captured: dict[str, bytes] = {}
        for relative_path, expected_sha256 in self.identity.inputs.items():
            payload = _read_bounded_project_file(
                project,
                relative_path,
                IDENTITY_INPUT_MAX_BYTES,
                f"identity input {relative_path}",
            )
            if hashlib.sha256(payload).hexdigest() != expected_sha256:
                raise CacheError(
                    f"identity input {relative_path} differs from the exact main cache identity"
                )
            captured[relative_path] = payload
        return captured

    @staticmethod
    def _load_identity_module(
        relative_path: str, name: str, payload: bytes, display_root: Path
    ) -> Any:
        """Execute only the already authenticated module payload."""

        path = display_root / relative_path
        module = types.ModuleType(name)
        module.__file__ = str(path)
        module.__package__ = ""
        try:
            code = compile(payload, str(path), "exec", dont_inherit=True)
            exec(code, module.__dict__)
        except Exception as error:
            raise CacheError(f"could not load identity-bound input verifier {relative_path}: {error}") from error
        return module

    @staticmethod
    def _load_captured_pin(module: Any, relative_path: str, payload: bytes) -> dict[str, Any]:
        """Parse only captured pin bytes through the identity-bound verifier."""

        path = _CapturedInputPath(relative_path, payload)
        with HotMainCache._captured_module_io(module):
            return module.load_pin(path)

    @staticmethod
    @contextmanager
    def _captured_module_io(module: Any) -> Any:
        """Adapt private path helpers to captured payloads, then restore them."""

        replacements: dict[str, Any] = {}
        if hasattr(module, "_load_json"):
            object_pairs_hook = getattr(module, "_object_without_duplicates", None)
            materialization_error = getattr(module, "MaterializationError", CacheError)

            def load_json(path: object, label: str) -> dict[str, Any]:
                if not isinstance(path, _CapturedInputPath):
                    raise CacheError(
                        f"captured verifier requested JSON through an unauthenticated path: {path}"
                    )
                try:
                    value = json.loads(
                        path.payload.decode("utf-8"),
                        object_pairs_hook=object_pairs_hook,
                    )
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                    raise materialization_error(f"could not load {label}: {error}") from error
                if not isinstance(value, dict):
                    raise materialization_error(f"{label} must be a JSON object")
                return value

            replacements["_load_json"] = load_json
        if hasattr(module, "_file_sha256"):

            def file_sha256(path: object) -> str:
                if not isinstance(path, _CapturedInputPath):
                    raise CacheError(
                        f"captured verifier requested hashing through an unauthenticated path: {path}"
                    )
                return hashlib.sha256(path.payload).hexdigest()

            replacements["_file_sha256"] = file_sha256

        originals = {name: getattr(module, name) for name in replacements}
        try:
            for name, replacement in replacements.items():
                setattr(module, name, replacement)
            yield
        finally:
            for name, original in originals.items():
                setattr(module, name, original)

    @staticmethod
    def _validate_captured_project(
        module: Any,
        validator_name: str,
        captured_inputs: Mapping[str, bytes],
        pin: Mapping[str, Any],
    ) -> None:
        """Run path-oriented validation against exact captured byte payloads."""

        admitted_paths = {
            "validate_project_pins": ("lean-toolchain", "lake-manifest.json"),
            "validate_manifests": (
                "lake-manifest.json",
                "references/mathlib-lake-manifest.json",
            ),
        }
        try:
            required = admitted_paths[validator_name]
            payloads = {relative: captured_inputs[relative] for relative in required}
        except KeyError as error:
            raise CacheError(
                f"unsupported or incomplete captured verifier request: {validator_name}"
            ) from error
        root = _CapturedInputRoot(payloads)
        with HotMainCache._captured_module_io(module):
            getattr(module, validator_name)(root, pin)

    @staticmethod
    def _authenticate_pinned_file(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> None:
        payload = _read_bounded_regular_file(path, expected_bytes, label)
        if len(payload) != expected_bytes:
            raise CacheError(f"{label} size differs: expected {expected_bytes}, got {len(payload)}")
        if hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise CacheError(f"{label} checksum differs from the pinned digest")

    def _preflight_authenticated_inputs(self) -> dict[str, Any]:
        """Authenticate the complete canonical local-input tuple before election."""

        if not self._requires_mathlib_source():
            self._preflight_mathlib_input()
            return {"required": False}
        captured_inputs = self._capture_identity_inputs(self.project_dir)
        self._preflight_mathlib_input(captured_inputs)
        mip_value = os.environ.get(MIPSTARRE_ARCHIVE_ENV)
        packages_value = os.environ.get(LAKE_PACKAGE_ARCHIVES_ENV)
        if not mip_value:
            raise CacheError(f"{MIPSTARRE_ARCHIVE_ENV} is unset or empty")
        if not packages_value:
            raise CacheError(f"{LAKE_PACKAGE_ARCHIVES_ENV} is unset or empty")
        mip_archive = _absolute_local_path(mip_value, MIPSTARRE_ARCHIVE_ENV)
        package_directory = _absolute_local_path(packages_value, LAKE_PACKAGE_ARCHIVES_ENV)
        try:
            metadata = package_directory.stat(follow_symlinks=False)
        except OSError as error:
            raise CacheError(f"could not inspect {LAKE_PACKAGE_ARCHIVES_ENV}: {error}") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise CacheError(f"{LAKE_PACKAGE_ARCHIVES_ENV} must name a real directory")

        try:
            mip_module = self._load_identity_module(
                "scripts/materialize_mipstarre.py",
                "_hot_cache_input_mipstarre",
                captured_inputs["scripts/materialize_mipstarre.py"],
                self.project_dir,
            )
            mip_pin = self._load_captured_pin(
                mip_module,
                "references/mipstarre-upstream.json",
                captured_inputs["references/mipstarre-upstream.json"],
            )
            self._validate_captured_project(
                mip_module, "validate_project_pins", captured_inputs, mip_pin
            )
            self._authenticate_pinned_file(
                mip_archive, mip_pin["archive"]["bytes"], mip_pin["archive"]["sha256"],
                "MIPStarRE archive",
            )
            package_module = self._load_identity_module(
                "scripts/materialize_lake_packages.py",
                "_hot_cache_input_packages",
                captured_inputs["scripts/materialize_lake_packages.py"],
                self.project_dir,
            )
            package_pin = self._load_captured_pin(
                package_module,
                "references/lake-packages.json",
                captured_inputs["references/lake-packages.json"],
            )
            self._validate_captured_project(
                package_module, "validate_manifests", captured_inputs, package_pin
            )
            for package in package_pin["packages"]:
                archive = package_directory / f"{package['name']}-{package['revision']}.tar.gz"
                self._authenticate_pinned_file(
                    archive, package["archive"]["bytes"], package["archive"]["sha256"],
                    f"Lake package archive {package['name']}",
                )
        except CacheError:
            raise
        except Exception as error:
            raise CacheError(f"authenticated local-input preflight failed: {error}") from error
        return {
            "required": True,
            "mathlib_selector": MATHLIB_SOURCE_ENV if os.environ.get(MATHLIB_SOURCE_ENV) else MATHLIB_ARCHIVE_ENV,
            "mipstarre_archive": str(mip_archive),
            "lake_package_archives": str(package_directory),
            "lake_package_count": len(package_pin["packages"]),
        }

    @staticmethod
    def _verify_mathlib_source(binding: MathlibSourceBinding) -> None:
        expected = binding.evidence
        facts = validate_mathlib_source(
            binding.path,
            expected_commit=expected["commit"],
            expected_tree=expected["tree"],
        )
        if (
            facts.get("pack_sha256") != expected.get("pack_sha256")
            or facts.get("pack_bytes") != expected.get("pack_bytes")
        ):
            raise CacheError("Mathlib source object pack changed during the cache build")

    @staticmethod
    def _cleanup_mathlib_source(binding: MathlibSourceBinding | None) -> None:
        if binding is None or binding.owned_path is None:
            return
        if binding.owned_path.exists() or binding.owned_path.is_symlink():
            make_owner_writable(binding.owned_path)
            shutil.rmtree(binding.owned_path)

    def is_ready(self, *, deep: bool = False) -> bool:
        if not self.ready_path.is_file() or not self.manifest_path.is_file() or not self.build_dir.is_dir():
            return False
        try:
            with self.manifest_path.open("r", encoding="utf-8") as stream:
                manifest = json.load(stream)
        except (OSError, json.JSONDecodeError):
            return False
        try:
            ready_digest = self.ready_path.read_text(encoding="ascii").strip()
            manifest_digest = sha256_file(self.manifest_path)
        except (OSError, UnicodeDecodeError):
            return False
        if ready_digest != manifest_digest:
            return False
        source_evidence_ready = (
            validate_source_evidence(
                manifest.get("source_evidence"), self.identity.source_contract
            )
            if self.recipe.materialize_command
            and isinstance(self.identity.source_contract, dict)
            else manifest.get("source_evidence") is None
        )
        authored_verification_ready = (
            manifest.get("authored_qpbt_verification")
            == authored_verification_record(self.identity.source_contract)
            if self.recipe.materialize_command
            and isinstance(self.identity.source_contract, dict)
            else manifest.get("authored_qpbt_verification") is None
        )
        mathlib_evidence_ready = (
            validate_mathlib_evidence(manifest.get("mathlib_source"))
            if self._requires_mathlib_source()
            else manifest.get("mathlib_source") is None
        )
        shallow_ready = (
            manifest.get("schema_version") == SCHEMA_VERSION
            and manifest.get("cache_key") == self.identity.cache_key
            and manifest.get("main_commit") == self.identity.main_commit
            and manifest.get("inputs") == self.identity.inputs
            and manifest.get("recipe") == self.identity.recipe
            and manifest.get("source_contract") == self.identity.source_contract
            and isinstance(manifest.get("artifact_inventory"), dict)
            and source_evidence_ready
            and authored_verification_ready
            and mathlib_evidence_ready
        )
        if not shallow_ready or not deep:
            return shallow_ready
        try:
            return manifest["artifact_inventory"] == artifact_inventory(self.lake_dir)
        except (CacheError, OSError):
            return False

    def status(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            **asdict(self.identity),
            "status": "hit" if self.is_ready() else "miss",
            "snapshot_dir": str(self.snapshot_dir),
            "build_dir": str(self.build_dir),
            "lock_path": str(self.lock_path),
        }

    def _append_metric(
        self,
        metric: Mapping[str, Any],
        commit_guard: Callable[[], None] | None = None,
    ) -> None:
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "timestamp": utc_now(),
            "pid": os.getpid(),
            "cache_key": self.identity.cache_key,
            "main_commit": self.identity.main_commit,
            **metric,
        }
        encoded = (json.dumps(envelope, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        lock = ExclusiveLock(self.metrics_lock_path)
        lock.__enter__()
        descriptor: int | None = None
        committed = False
        try:
            descriptor = os.open(
                self.metrics_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644
            )
            checkpoint = os.fstat(descriptor).st_size
            try:
                if commit_guard is not None:
                    commit_guard()
                written = os.write(descriptor, encoded)
                if written != len(encoded):
                    raise OSError(errno.EIO, "short hot-cache metric write")
                if commit_guard is not None:
                    commit_guard()
                os.fsync(descriptor)
                if commit_guard is not None:
                    commit_guard()
                committed = True
            except BaseException as error:
                try:
                    self._rollback_metric_append_locked(descriptor, checkpoint)
                except BaseException as rollback_error:
                    raise OSError(
                        f"hot-cache metric append failed ({error}); rollback failed: {rollback_error}"
                    ) from error
                raise
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException:
                    if not committed and sys.exc_info()[0] is None:
                        raise
            try:
                lock.__exit__(None, None, None)
            except BaseException:
                if not committed and sys.exc_info()[0] is None:
                    raise

    @staticmethod
    def _rollback_metric_append_locked(descriptor: int, checkpoint: int) -> None:
        """Durably roll back on the descriptor while its original lock is held."""

        os.ftruncate(descriptor, checkpoint)
        os.fsync(descriptor)

    def _run_logged(
        self,
        build_root: Path,
        command: Sequence[str],
        log_path: Path,
        *,
        environment: Mapping[str, str] | None = None,
    ) -> int:
        try:
            with log_path.open("ab") as log:
                result = subprocess.run(
                    list(command),
                    cwd=build_root,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=False,
                    shell=False,
                    env=dict(environment) if environment is not None else None,
                )
        except OSError as error:
            raise CacheError(f"could not run build command {command[0]!r}: {error}") from error
        return result.returncode

    def _detached_clone(self, staging: Path, log_path: Path) -> Path:
        checkout = staging / "checkout"
        clone = ["git", "clone", "--local", "--no-checkout", str(self.repo_root), str(checkout)]
        try:
            clone_log_offset = log_path.stat().st_size
        except FileNotFoundError:
            clone_log_offset = 0
        return_code = self._run_logged(staging, clone, log_path)
        if return_code != 0:
            try:
                with log_path.open("rb") as log:
                    log.seek(clone_log_offset)
                    clone_log = log.read().decode("utf-8", errors="replace").lower()
            except OSError:
                clone_log = ""
            cross_device = "cross-device" in clone_log or "exdev" in clone_log
            if cross_device:
                if checkout.is_symlink() or checkout.is_file():
                    checkout.unlink()
                elif checkout.is_dir():
                    shutil.rmtree(checkout)
                with log_path.open("ab") as log:
                    log.write(b"[hot-main-cache] local clone failed with EXDEV; retrying --no-local\n")
                clone[2] = "--no-local"
                return_code = self._run_logged(staging, clone, log_path)
        if return_code != 0:
            raise CacheError(f"detached clone command failed with exit code {return_code}")

        checkout_command = [
            "git", "-C", str(checkout), "checkout", "--detach", self.identity.main_commit
        ]
        return_code = self._run_logged(staging, checkout_command, log_path)
        if return_code != 0:
            raise CacheError(f"detached clone command failed with exit code {return_code}")
        return checkout

    def _verify_materialized_source(
        self,
        detached_project: Path,
        test_verifier: SourceVerifier | None,
    ) -> dict[str, Any] | None:
        if not self.recipe.materialize_command:
            if test_verifier is not None:
                raise CacheError("a source verifier requires a materializing build recipe")
            return None

        pin_relative = "references/mipstarre-upstream.json"
        expected_pin_sha256 = self.identity.inputs.get(pin_relative)
        if not isinstance(expected_pin_sha256, str):
            raise CacheError("materializing cache identity omits the upstream provenance pin")

        if test_verifier is not None:
            raw_evidence = dict(test_verifier(detached_project))
        else:
            if self.recipe.test_only:
                raise CacheError("a materializing test recipe requires an exact test source verifier")
            try:
                captured_inputs = self._capture_identity_inputs(detached_project)
                module_relative = "scripts/materialize_mipstarre.py"
                module = self._load_identity_module(
                    module_relative,
                    "_hot_cache_materializer",
                    captured_inputs[module_relative],
                    detached_project,
                )
                pin = self._load_captured_pin(
                    module, pin_relative, captured_inputs[pin_relative]
                )
                self._validate_captured_project(
                    module, "validate_project_pins", captured_inputs, pin
                )
                verified = module.verify_materialized(detached_project, pin)
                raw_evidence = {
                    "schema_version": SOURCE_EVIDENCE_SCHEMA_VERSION,
                    "pin_sha256": expected_pin_sha256,
                    "source_commit": pin["source"]["commit"],
                    "inventory_sha256": verified["inventory_sha256"],
                    "files": verified["files"],
                    "bytes": verified["bytes"],
                    "authored_qpbt_files": verified["authored_qpbt_files"],
                    "authored_qpbt_bytes": verified["authored_qpbt_bytes"],
                    "authored_qpbt_sha256": verified["authored_qpbt_sha256"],
                }
            except Exception as error:
                raise CacheError(f"foundation source verification failed: {error}") from error

        if not isinstance(self.identity.source_contract, dict) or not validate_source_evidence(
            raw_evidence, self.identity.source_contract
        ):
            raise CacheError("foundation source verifier differs from exact committed provenance")
        return raw_evidence

    def _verify_authored_qpbt_inventory(
        self,
        detached_project: Path,
        phase: str,
    ) -> dict[str, Any] | None:
        if not self.recipe.materialize_command:
            return None
        if phase not in AUTHORED_QPBT_CHECK_PHASES:
            raise CacheError(f"unknown authored QPBT verification phase: {phase}")
        if not isinstance(self.identity.source_contract, dict):
            raise CacheError("materializing cache identity omits the authored QPBT contract")
        expected = authored_contract_facts(self.identity.source_contract)
        try:
            observed = authored_tree_facts_on_disk(detached_project)
        except CacheError as error:
            raise CacheError(
                f"authored QPBT inventory could not be verified at {phase}: {error}"
            ) from error
        if observed != expected:
            raise CacheError(
                f"authored QPBT inventory differs from the exact main commit at {phase}"
            )
        return observed

    def warm(
        self,
        *,
        dry_run: bool = False,
        _test_command_callback: CommandCallback | None = None,
        _test_source_verifier: SourceVerifier | None = None,
    ) -> dict[str, Any]:
        if (
            _test_command_callback is not None or _test_source_verifier is not None
        ) and not self.recipe.test_only:
            raise CacheError("test callbacks are allowed only with an identity-isolated test recipe")
        dependency_command = self.recipe.dependency_command
        materialize_command = self.recipe.materialize_command
        package_materialize_command = self.recipe.package_materialize_command
        package_verify_command = self.recipe.package_verify_command
        command = self.recipe.build_command
        if dry_run:
            return {
                **self.status(),
                "action": "warm",
                "dry_run": True,
                "source": f"detached local clone at {self.identity.main_commit}",
                "materialize_command": list(materialize_command),
                "package_materialize_command": list(package_materialize_command),
                "package_verify_command": list(package_verify_command),
                "dependency_command": list(dependency_command),
                "command": list(command),
                "mathlib_source_required": self._requires_mathlib_source(),
                "mathlib_source_inputs": (
                    [MATHLIB_SOURCE_ENV, MATHLIB_ARCHIVE_ENV]
                    if self._requires_mathlib_source()
                    else []
                ),
                "would_build": not self.is_ready(),
            }
        # Validate the runtime source before either hit path.  This keeps a
        # stale or missing local binding from silently masquerading as a hit.
        self._preflight_authenticated_inputs()
        started = time.monotonic()
        if self.is_ready():
            result = {
                **self.status(),
                "action": "warm",
                "result": "hit",
                "cache_hit": 1,
                "cache_miss": 0,
                "lock_waited": 0,
                "lock_wait_seconds": 0.0,
                "builds": 0,
                "build_seconds": 0.0,
                "mathlib_source_required": self._requires_mathlib_source(),
                "elapsed_seconds": round(time.monotonic() - started, 6),
            }
            self._append_metric(result)
            return result

        with ExclusiveLock(self.lock_path) as cache_lock:
            self._preflight_authenticated_inputs()
            if self.is_ready():
                result = {
                    **self.status(),
                    "action": "warm",
                    "result": "hit_after_wait" if cache_lock.waited else "hit",
                    "cache_hit": 1,
                    "cache_miss": 0,
                    "lock_waited": int(cache_lock.waited),
                    "lock_wait_seconds": round(cache_lock.wait_seconds, 6),
                    "builds": 0,
                    "build_seconds": 0.0,
                    "mathlib_source_required": self._requires_mathlib_source(),
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                }
                self._append_metric(result)
                return result

            build_started = time.monotonic()
            authored_verification = (
                authored_verification_record(self.identity.source_contract)
                if self.recipe.materialize_command
                and isinstance(self.identity.source_contract, dict)
                else None
            )
            metric_base = {
                "action": "warm",
                "cache_hit": 0,
                "cache_miss": 1,
                "lock_waited": int(cache_lock.waited),
                "lock_wait_seconds": round(cache_lock.wait_seconds, 6),
                "builds": 1,
                "elected_owner": {"pid": os.getpid(), "host": socket.gethostname()},
                "materialize_command": list(materialize_command),
                "package_materialize_command": list(package_materialize_command),
                "package_verify_command": list(package_verify_command),
                "dependency_command": list(dependency_command),
                "command": list(command),
                "mathlib_source_required": self._requires_mathlib_source(),
                "authored_qpbt_verification": authored_verification,
            }
            test_callback = _test_command_callback

            def invoke(
                project: Path, command_tokens: Sequence[str], command_log: Path
            ) -> int | None:
                if test_callback is not None:
                    return test_callback(project, command_tokens, command_log)
                environment = (
                    self._command_environment
                    if tuple(command_tokens) in (dependency_command, command)
                    else None
                )
                return self._run_logged(
                    project,
                    command_tokens,
                    command_log,
                    environment=environment,
                )

            self.cache_root.mkdir(parents=True, exist_ok=True)
            staging = Path(
                tempfile.mkdtemp(prefix=f".{self.identity.cache_key}.staging-", dir=self.cache_root)
            )
            log_path = staging / "build.log"
            mathlib_binding: MathlibSourceBinding | None = None
            try:
                checkout = self._detached_clone(staging, log_path)
                project_relative = self.project_dir.relative_to(self.repo_root)
                detached_project = checkout / project_relative
                if hash_inputs(detached_project, self.recipe) != self.identity.inputs:
                    raise CacheError("detached clone metadata does not match the main cache identity")
                self._verify_authored_qpbt_inventory(
                    detached_project, "before_materialization"
                )

                materialize_seconds = 0.0
                if materialize_command:
                    materialize_started = time.monotonic()
                    return_code = invoke(detached_project, materialize_command, log_path)
                    materialize_seconds = time.monotonic() - materialize_started
                    if return_code not in (None, 0):
                        raise CacheError(
                            f"foundation materialization command failed with exit code {return_code}"
                        )
                self._verify_authored_qpbt_inventory(
                    detached_project, "after_materialization"
                )

                package_materialize_seconds = 0.0
                package_verify_seconds = 0.0
                if package_materialize_command:
                    package_materialize_started = time.monotonic()
                    return_code = invoke(detached_project, package_materialize_command, log_path)
                    package_materialize_seconds = time.monotonic() - package_materialize_started
                    if return_code not in (None, 0):
                        raise CacheError(
                            f"Lake package materialization command failed with exit code {return_code}"
                        )
                    package_verify_started = time.monotonic()
                    return_code = invoke(detached_project, package_verify_command, log_path)
                    package_verify_seconds = time.monotonic() - package_verify_started
                    if return_code not in (None, 0):
                        raise CacheError(
                            f"Lake package verification command failed with exit code {return_code}"
                        )

                if self._requires_mathlib_source():
                    mathlib_binding = self._prepare_mathlib_source(staging, detached_project)
                    self._command_environment = self._command_environment_for_mathlib(
                        mathlib_binding
                    )
                    metric_base["mathlib_source"] = mathlib_binding.evidence

                dependency_started = time.monotonic()
                return_code = invoke(detached_project, dependency_command, log_path)
                dependency_seconds = time.monotonic() - dependency_started
                if return_code not in (None, 0):
                    raise CacheError(f"dependency cache command failed with exit code {return_code}")
                self._verify_authored_qpbt_inventory(
                    detached_project, "after_dependency_retrieval"
                )

                compilation_started = time.monotonic()
                return_code = invoke(detached_project, command, log_path)
                compilation_seconds = time.monotonic() - compilation_started
                if return_code not in (None, 0):
                    raise CacheError(f"build command failed with exit code {return_code}")
                self._verify_authored_qpbt_inventory(detached_project, "after_build")
                if package_verify_command:
                    package_verify_started = time.monotonic()
                    return_code = invoke(detached_project, package_verify_command, log_path)
                    package_verify_seconds += time.monotonic() - package_verify_started
                    if return_code not in (None, 0):
                        raise CacheError(
                            f"Lake package verification command failed with exit code {return_code}"
                        )
                if git_commit(checkout, "HEAD") != self.identity.main_commit:
                    raise CacheError("detached checkout HEAD changed during the cache build")
                if hash_inputs(detached_project, self.recipe) != self.identity.inputs:
                    raise CacheError("cache-key inputs changed during the cache build")
                source_changes = git_source_changes(checkout)
                if source_changes:
                    preview = ", ".join(source_changes[:5])
                    raise CacheError(f"project source changed during the cache build: {preview}")
                source_evidence = self._verify_materialized_source(
                    detached_project, _test_source_verifier
                )
                if mathlib_binding is not None:
                    self._verify_mathlib_source(mathlib_binding)
                source_lake = detached_project / ".lake"
                source_build = source_lake / "build"
                if not source_build.is_dir() or source_build.is_symlink():
                    raise CacheError(f"build succeeded but produced no real directory at {source_build}")
                self._verify_authored_qpbt_inventory(
                    detached_project, "before_publication"
                )

                # An archive source is only a staging input; never publish it
                # alongside the immutable .lake artifact tree.
                if mathlib_binding is not None and mathlib_binding.owned_path is not None:
                    self._cleanup_mathlib_source(mathlib_binding)
                os.replace(source_lake, staging / ".lake")
                shutil.rmtree(checkout)
                build_seconds = time.monotonic() - build_started
                make_read_only(staging / ".lake")
                inventory = artifact_inventory(staging / ".lake")
                manifest = {
                    "schema_version": SCHEMA_VERSION,
                    **asdict(self.identity),
                    "created_at": utc_now(),
                    "source": "detached-local-clone",
                    "materialize_command": list(materialize_command),
                    "package_materialize_command": list(package_materialize_command),
                    "package_verify_command": list(package_verify_command),
                    "dependency_command": list(dependency_command),
                    "command": list(command),
                    "materialize_seconds": round(materialize_seconds, 6),
                    "package_materialize_seconds": round(package_materialize_seconds, 6),
                    "package_verify_seconds": round(package_verify_seconds, 6),
                    "dependency_cache_seconds": round(dependency_seconds, 6),
                    "build_seconds": round(compilation_seconds, 6),
                    "total_prepare_seconds": round(build_seconds, 6),
                    "log_path": str(self.snapshot_dir / "build.log"),
                    "artifact_inventory": inventory,
                    "source_evidence": source_evidence,
                    "authored_qpbt_verification": authored_verification,
                    "mathlib_source": (
                        mathlib_binding.evidence if mathlib_binding is not None else None
                    ),
                }
                atomic_write_json(staging / "manifest.json", manifest)
                (staging / "READY").write_text(
                    f"{sha256_file(staging / 'manifest.json')}\n", encoding="ascii"
                )
                make_read_only(staging)
                if self.snapshot_dir.exists():
                    raise CacheError(
                        f"an invalid cache snapshot already exists at {self.snapshot_dir}; "
                        "cache cleanup is an explicit maintenance operation"
                    )
                os.replace(staging, self.snapshot_dir)
                result = {
                    **self.status(),
                    **metric_base,
                    "result": "built",
                    "materialize_seconds": round(materialize_seconds, 6),
                    "package_materialize_seconds": round(package_materialize_seconds, 6),
                    "package_verify_seconds": round(package_verify_seconds, 6),
                    "dependency_cache_seconds": round(dependency_seconds, 6),
                    "build_seconds": round(compilation_seconds, 6),
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    "log_path": str(self.snapshot_dir / "build.log"),
                }
                self._append_metric(result)
                return result
            except Exception as error:
                build_seconds = time.monotonic() - build_started
                retained_path: Path | None = None
                if staging.exists():
                    failures = self.runtime_dir / "cache" / "failures"
                    failures.mkdir(parents=True, exist_ok=True)
                    retained_path = failures / (
                        f"{self.identity.cache_key}-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
                    )
                    retained_path.mkdir()
                    if (staging / "build.log").is_file():
                        os.replace(staging / "build.log", retained_path / "build.log")
                    atomic_write_json(
                        retained_path / "failure.json",
                        {
                            "schema_version": SCHEMA_VERSION,
                            **asdict(self.identity),
                            "failed_at": utc_now(),
                            "error": str(error),
                            "mathlib_source_required": self._requires_mathlib_source(),
                            "mathlib_source": metric_base.get("mathlib_source"),
                        },
                    )
                    make_owner_writable(staging)
                    shutil.rmtree(staging)
                failed = {
                    **metric_base,
                    "result": "failed",
                    "build_seconds": round(build_seconds, 6),
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    "error": str(error),
                    "log_path": str(retained_path / "build.log") if retained_path else None,
                }
                self._append_metric(failed)
                if isinstance(error, CacheError):
                    raise
                raise CacheError(str(error)) from error
            finally:
                self._command_environment = None
                if mathlib_binding is not None and mathlib_binding.owned_path is not None:
                    # Failure paths retain only the log/evidence envelope, not
                    # the unpacked source tree.
                    self._cleanup_mathlib_source(mathlib_binding)

    def _eligible_seed_target(
        self, supplied_target: Path, *, check_inputs: bool = True
    ) -> _BoundSeedTarget:
        lexical_target = reject_symlink_components(supplied_target)
        if not lexical_target.is_dir():
            raise CacheError(f"target worktree must be an existing real directory: {lexical_target}")
        target_project = lexical_target.resolve(strict=True)
        project_relative = self.project_dir.relative_to(self.repo_root)

        matched: WorktreeRecord | None = None
        matched_root: Path | None = None
        for record in git_worktrees(self.repo_root):
            try:
                worktree_root = record.path.resolve(strict=True)
            except FileNotFoundError:
                continue
            candidate = (worktree_root / project_relative).resolve(strict=False)
            if candidate == target_project:
                matched = record
                matched_root = worktree_root
                break
        if matched is None or matched_root is None:
            raise CacheError(
                f"target is not the project root of a registered Git worktree: {target_project}"
            )
        if matched.bare or matched.prunable or not matched.head or not re_full_sha(matched.head):
            raise CacheError(f"target is not an eligible live Git worktree: {matched_root}")
        if matched_root == self.repo_root:
            raise CacheError("refusing to seed the main worktree")
        if path_is_within(target_project, self.cache_root) or path_is_within(
            self.cache_root, target_project
        ):
            raise CacheError("target worktree must be distinct from the hot-cache storage")
        if git_resolved_path(matched_root, "--show-toplevel") != matched_root:
            raise CacheError(f"target path is not its Git worktree root: {matched_root}")
        if git_resolved_path(matched_root, "--git-common-dir") != git_resolved_path(
            self.repo_root, "--git-common-dir"
        ):
            raise CacheError("target worktree is not attached to the main repository")

        flags = _authored_directory_flags()
        project_descriptor: int | None = None
        worktree_descriptor: int | None = None
        worktree_parent_descriptor: int | None = None
        namespace_monitor: _NamespaceMonitor | None = None
        try:
            project_descriptor = os.open(target_project, flags)
            worktree_descriptor = os.open(matched_root, flags)
            worktree_parent_descriptor = os.open(matched_root.parent, flags)
            namespace_monitor = _NamespaceMonitor(
                (target_project, matched_root, matched_root.parent)
            )
            project = os.fstat(project_descriptor)
            worktree = os.fstat(worktree_descriptor)
            worktree_parent = os.fstat(worktree_parent_descriptor)
            binding = _BoundSeedTarget(
                target_project=target_project,
                worktree_root=matched_root,
                worktree_head=matched.head,
                project_descriptor=project_descriptor,
                worktree_descriptor=worktree_descriptor,
                worktree_parent_descriptor=worktree_parent_descriptor,
                project_identity=_authored_directory_identity(project),
                worktree_identity=_authored_directory_identity(worktree),
                worktree_parent_identity=_authored_directory_identity(worktree_parent),
                project_generation=_authored_directory_scan_identity(project),
                worktree_generation=_authored_directory_scan_identity(worktree),
                worktree_parent_generation=_authored_directory_scan_identity(worktree_parent),
                namespace_monitor=namespace_monitor,
            )
            binding.assert_current()
            if git_resolved_path(matched_root, "--show-toplevel") != matched_root:
                raise CacheError("target worktree identity changed while binding")
            binding.assert_current()
            if check_inputs:
                try:
                    self._capture_identity_inputs(binding.target_project)
                except CacheError as error:
                    raise CacheError(
                        f"target worktree has cache-key inputs incompatible with this cache: {error}"
                    ) from error
                binding.assert_current()
            return binding
        except Exception:
            if namespace_monitor is not None:
                namespace_monitor.close()
            if project_descriptor is not None:
                os.close(project_descriptor)
            if worktree_descriptor is not None:
                os.close(worktree_descriptor)
            if worktree_parent_descriptor is not None:
                os.close(worktree_parent_descriptor)
            raise

    @staticmethod
    def _require_seed_capabilities(target: _BoundSeedTarget) -> None:
        """Refuse before transaction mutation unless the strong Linux primitives exist."""

        target.assert_current()
        required_dir_fd = (os.open, os.mkdir, os.stat, os.unlink, os.rmdir)
        if any(operation not in os.supports_dir_fd for operation in required_dir_fd):
            raise CacheError("safe seed publication requires descriptor-relative filesystem calls")
        if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
            raise CacheError("safe seed publication requires O_DIRECTORY and O_NOFOLLOW")
        filesystem_magic = _linux_filesystem_magic(target.project_descriptor)
        if filesystem_magic not in _RENAMEAT2_FILESYSTEM_MAGICS:
            raise CacheError(
                "target filesystem is not conservatively approved for atomic seed publication"
            )
        _assert_renameat2_kernel_capability(RENAME_NOREPLACE, "no-replace")
        _assert_renameat2_kernel_capability(RENAME_EXCHANGE, "exchange")
        _probe_renameat2_semantics(target.project_descriptor)
        target.assert_current()

    @staticmethod
    def _assert_bound_name(
        parent_descriptor: int,
        name: str,
        descriptor: int,
        label: str,
    ) -> None:
        try:
            lexical = os.stat(
                name, dir_fd=parent_descriptor, follow_symlinks=False
            )
            bound = os.fstat(descriptor)
        except OSError as error:
            raise CacheError(f"{label} identity changed") from error
        if (
            stat.S_ISLNK(lexical.st_mode)
            or (lexical.st_dev, lexical.st_ino, stat.S_IFMT(lexical.st_mode))
            != (bound.st_dev, bound.st_ino, stat.S_IFMT(bound.st_mode))
        ):
            raise CacheError(f"{label} identity changed")

    @classmethod
    def _atomic_move_bound(
        cls,
        source_parent: int,
        source_name: str,
        source_descriptor: int,
        destination_parent: int,
        destination_name: str,
        label: str,
    ) -> None:
        cls._assert_bound_name(source_parent, source_name, source_descriptor, label)
        try:
            _linux_renameat2(
                source_parent,
                source_name,
                destination_parent,
                destination_name,
                RENAME_NOREPLACE,
            )
        except OSError as error:
            if error.errno == errno.EEXIST:
                raise CacheError(f"{label} destination appeared concurrently; source retained") from error
            raise CacheError(f"atomic no-replace move failed for {label}: {error}") from error
        cls._assert_bound_name(
            destination_parent, destination_name, source_descriptor, label
        )

    @classmethod
    def _atomic_exchange_bound(
        cls,
        first_parent: int,
        first_name: str,
        first_descriptor: int,
        second_parent: int,
        second_name: str,
        second_descriptor: int,
        label: str,
    ) -> None:
        cls._assert_bound_name(first_parent, first_name, first_descriptor, label)
        cls._assert_bound_name(second_parent, second_name, second_descriptor, label)
        try:
            _linux_renameat2(
                first_parent,
                first_name,
                second_parent,
                second_name,
                RENAME_EXCHANGE,
            )
        except OSError as error:
            raise CacheError(f"atomic exchange failed for {label}: {error}") from error
        cls._assert_bound_name(second_parent, second_name, first_descriptor, label)
        cls._assert_bound_name(first_parent, first_name, second_descriptor, label)

    def _validate_seeded_destination(self, destination: Path) -> None:
        if not self.is_ready(deep=True):
            raise CacheError("published cache changed or lost source evidence during seed")
        if not destination.is_dir() or destination.is_symlink():
            raise CacheError(f"seed publication did not create a real directory: {destination}")
        build = destination / "build"
        if not build.is_dir() or build.is_symlink():
            raise CacheError(f"seed publication has no real build directory: {build}")
        _validate_lake_symlink_policy(destination)
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CacheError(f"could not read cache manifest after seed: {error}") from error
        if artifact_inventory(destination) != manifest.get("artifact_inventory"):
            raise CacheError("seeded cache artifact inventory does not match the published cache")

    @staticmethod
    def _lake_tree_identity(path: Path) -> dict[str, Any]:
        if not path.is_dir() or path.is_symlink():
            raise CacheError(f"seed transaction tree must be a real directory: {path}")
        metadata = path.stat(follow_symlinks=False)
        return {
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
            "type": stat.S_IFMT(metadata.st_mode),
            "inventory": artifact_inventory(path),
        }

    @classmethod
    def _lake_tree_matches(cls, path: Path, expected: Any) -> bool:
        try:
            return cls._lake_tree_identity(path) == expected
        except (CacheError, OSError):
            return False

    @staticmethod
    def _seed_target_digest(target_project: Path) -> str:
        destination = target_project / ".lake"
        return hashlib.sha256(str(destination).encode("utf-8")).hexdigest()

    def _seed_transaction_dir(self, target_project: Path) -> Path:
        return (
            self.runtime_dir
            / "transactions"
            / "seed"
            / self._seed_target_digest(target_project)
        )

    @staticmethod
    def _journal_bytes(value: Mapping[str, Any]) -> bytes:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            + "\n"
        ).encode("ascii")

    def _write_seed_journal(
        self,
        replacement: _SeedReplacement,
        target: _BoundSeedTarget,
        staging_lake: Path,
    ) -> None:
        target_project = target.target_project
        original = self._lake_tree_identity(replacement.destination)
        replacement_identity = self._lake_tree_identity(staging_lake)
        staging_root = replacement.staging_root
        if staging_root is None:
            raise CacheError("seed transaction has no staging root")
        value = {
            "schema_version": 1,
            "transaction_version": 1,
            "transaction_id": replacement.transaction_id,
            "target_project": str(target_project),
            "destination": str(replacement.destination),
            "target_lock_digest": self._seed_target_digest(target_project),
            "replace": True,
            "staging_basename": staging_root.name,
            "retained_basename": f".lake.retained-{replacement.transaction_id}",
            "original_slot": f"{staging_root.name}/.lake",
            "original": original,
            "replacement": replacement_identity,
            "cache_key": self.identity.cache_key,
            "main_commit": self.identity.main_commit,
            "cache_manifest_sha256": sha256_file(self.manifest_path),
        }
        payload = self._journal_bytes(value)
        replacement.journal_dir.parent.mkdir(parents=True, exist_ok=True)
        reject_symlink_components(replacement.journal_dir.parent)
        parent_descriptor = os.open(
            replacement.journal_dir.parent, _authored_directory_flags()
        )
        replacement.journal_parent_descriptor = parent_descriptor
        retained_name = (
            f"{replacement.journal_dir.name}.retained-{replacement.transaction_id}"
        )
        replacement.journal_parent_monitor = _BoundNameMonitor(
            parent_descriptor, (replacement.journal_dir.name, retained_name)
        )
        try:
            os.mkdir(replacement.journal_dir.name, 0o700, dir_fd=parent_descriptor)
        except FileExistsError as error:
            raise CacheError(
                f"seed transaction journal already exists: {replacement.journal_dir}"
            ) from error
        replacement.journal_parent_monitor.accept_owned_change()
        journal_descriptor = os.open(
            replacement.journal_dir.name,
            _authored_directory_flags(),
            dir_fd=parent_descriptor,
        )
        replacement.journal_descriptor = journal_descriptor
        self._assert_bound_name(
            parent_descriptor,
            replacement.journal_dir.name,
            journal_descriptor,
            "seed transaction journal",
        )
        replacement.journal_file_descriptors = {}

        def write_owned(name: str, content: bytes) -> None:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
            descriptor = os.open(name, flags, 0o600, dir_fd=journal_descriptor)
            replacement.journal_file_descriptors[name] = descriptor
            view = memoryview(content)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("short seed journal write")
                view = view[written:]
            os.fsync(descriptor)

        digest = hashlib.sha256(payload).hexdigest()
        write_owned("journal.json", payload)
        write_owned("journal.sha256", (digest + "\n").encode("ascii"))
        replacement.journal_digest = digest
        os.fsync(journal_descriptor)
        os.fsync(parent_descriptor)
        replacement.journal_entry_monitor = _BoundNameMonitor(
            journal_descriptor, ("journal.json", "journal.sha256", "COMMITTED")
        )

    @classmethod
    def _clear_seed_journal(cls, replacement: _SeedReplacement) -> None:
        parent_descriptor = replacement.journal_parent_descriptor
        journal_descriptor = replacement.journal_descriptor
        files = replacement.journal_file_descriptors
        if parent_descriptor is None or journal_descriptor is None or files is None:
            if replacement.journal_dir.exists() or replacement.journal_dir.is_symlink():
                raise CacheError("seed transaction journal has no continuous live binding")
            return
        if replacement.journal_parent_monitor is None or replacement.journal_entry_monitor is None:
            raise CacheError("seed transaction journal lost its continuous name monitor")
        replacement.journal_parent_monitor.assert_clean()
        replacement.journal_entry_monitor.assert_clean()
        cls._assert_bound_name(
            parent_descriptor,
            replacement.journal_dir.name,
            journal_descriptor,
            "seed transaction journal",
        )
        names = set(os.listdir(journal_descriptor))
        if names != set(files):
            raise CacheError("seed transaction journal changed; retained for manual recovery")
        for name in sorted(files):
            cls._assert_bound_name(
                journal_descriptor,
                name,
                files[name],
                f"seed transaction journal file {name}",
            )
        retained_name = (
            f"{replacement.journal_dir.name}.retained-{replacement.transaction_id}"
        )
        cls._atomic_move_bound(
            parent_descriptor,
            replacement.journal_dir.name,
            journal_descriptor,
            parent_descriptor,
            retained_name,
            "seed transaction journal retention",
        )
        replacement.journal_parent_monitor.accept_owned_change()
        os.fsync(parent_descriptor)

    def _mark_seed_committed(self, replacement: _SeedReplacement) -> None:
        if not replacement.old_moved:
            return
        journal_descriptor = replacement.journal_descriptor
        files = replacement.journal_file_descriptors
        digest = replacement.journal_digest
        monitor = replacement.journal_entry_monitor
        if journal_descriptor is None or files is None or digest is None or monitor is None:
            raise CacheError("seed transaction journal lost its live commit binding")
        monitor.assert_clean()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open("COMMITTED", flags, 0o600, dir_fd=journal_descriptor)
        files["COMMITTED"] = descriptor
        payload = (digest + "\n").encode("ascii")
        if os.write(descriptor, payload) != len(payload):
            raise OSError("short seed transaction commit-marker write")
        os.fsync(descriptor)
        os.fsync(journal_descriptor)
        monitor.accept_owned_change()

    def _recover_interrupted_seed(self, target: _BoundSeedTarget) -> None:
        """Reject persistent transaction state without treating it as authority."""

        target.assert_current()
        target_project = target.target_project
        journal_dir = self._seed_transaction_dir(target_project)
        names = sorted(os.listdir(target.project_descriptor))
        interrupted = [
            target_project / name
            for name in names
            if name.startswith((".lake.backup-", ".lake-seed-", ".lake-prepare-"))
        ]
        if journal_dir.exists() or journal_dir.is_symlink() or interrupted:
            retained = [journal_dir, *interrupted]
            raise CacheError(
                "interrupted seed state has no independent ownership proof and requires "
                "manual recovery; retained paths: " + ", ".join(map(str, retained))
            )
        target.assert_current()

    @classmethod
    def _rollback_seed_replacement(
        cls,
        target: _BoundSeedTarget,
        replacement: _SeedReplacement,
    ) -> list[str]:
        errors: list[str] = []
        staging_descriptor = replacement.staging_descriptor
        staged_lake_descriptor = replacement.staging_lake_descriptor
        original_descriptor = replacement.original_descriptor
        staging = replacement.staging_root
        if staging_descriptor is None or staged_lake_descriptor is None or staging is None:
            return errors
        if replacement.new_published and replacement.old_moved:
            if original_descriptor is None:
                errors.append("original cache has no continuous rollback binding")
            else:
                try:
                    if replacement.staging_entry_monitor is None or replacement.destination_monitor is None:
                        raise CacheError("seed rollback lost its continuous name monitors")
                    replacement.staging_entry_monitor.assert_clean()
                    replacement.destination_monitor.assert_clean()
                    cls._atomic_exchange_bound(
                        target.project_descriptor,
                        replacement.destination.name,
                        staged_lake_descriptor,
                        staging_descriptor,
                        ".lake",
                        original_descriptor,
                        "seed rollback",
                    )
                    replacement.staging_entry_monitor.accept_owned_change()
                    replacement.destination_monitor.accept_owned_change()
                    replacement.new_published = False
                    replacement.old_moved = False
                    os.fsync(target.project_descriptor)
                except (OSError, CacheError) as error:
                    errors.append(f"could not atomically restore original cache: {error}")
        elif replacement.new_published:
            try:
                if replacement.destination_monitor is None:
                    raise CacheError("failed publication lost its destination monitor")
                replacement.destination_monitor.assert_clean()
                failed_name = f".lake.failed-{replacement.transaction_id}"
                cls._atomic_move_bound(
                    target.project_descriptor,
                    replacement.destination.name,
                    staged_lake_descriptor,
                    target.project_descriptor,
                    failed_name,
                    "failed seed publication",
                )
                replacement.destination_monitor.accept_owned_change()
                replacement.failed_retained = str(target.target_project / failed_name)
                replacement.new_published = False
                os.fsync(target.project_descriptor)
            except (OSError, CacheError) as error:
                errors.append(f"could not retain failed publication: {error}")
        if not errors and not replacement.new_published:
            try:
                failed_name = f".lake.failed-{replacement.transaction_id}"
                if replacement.failed_retained is None and os.listdir(staging_descriptor):
                    if replacement.staging_parent_monitor is None:
                        raise CacheError("failed staging tree lost its parent monitor")
                    replacement.staging_parent_monitor.assert_clean()
                    cls._atomic_move_bound(
                        target.project_descriptor,
                        staging.name,
                        staging_descriptor,
                        target.project_descriptor,
                        failed_name,
                        "failed seed staging tree",
                    )
                    replacement.staging_parent_monitor.accept_owned_change()
                    replacement.failed_retained = str(target.target_project / failed_name)
                    os.fsync(target.project_descriptor)
            except (OSError, CacheError) as error:
                errors.append(f"could not retain failed staging tree: {error}")
        return errors

    def _new_seed_replacement(
        self, target: _BoundSeedTarget, *, rollback_prefix: str
    ) -> _SeedReplacement:
        target.assert_current()
        target_project = target.target_project
        transaction_id = secrets.token_hex(16)
        journal_dir = self._seed_transaction_dir(target_project)
        return _SeedReplacement(
            destination=target_project / ".lake",
            backup=target_project / f".lake.backup-{transaction_id}",
            rollback_root=target_project / f"{rollback_prefix}{transaction_id}",
            transaction_id=transaction_id,
            journal_dir=journal_dir,
            journal_path=journal_dir / "journal.json",
            journal_digest_path=journal_dir / "journal.sha256",
            committed_path=journal_dir / "COMMITTED",
        )

    @staticmethod
    def _discard_seed_rollback_root(
        target: _BoundSeedTarget, replacement: _SeedReplacement
    ) -> None:
        try:
            descriptor = replacement.staging_descriptor
            staging = replacement.staging_root
            if descriptor is None or staging is None:
                return
            if os.listdir(descriptor):
                return
            HotMainCache._assert_bound_name(
                target.project_descriptor,
                staging.name,
                descriptor,
                "seed staging root",
            )
            if replacement.staging_parent_monitor is None:
                return
            replacement.staging_parent_monitor.assert_clean()
            retained_name = f".lake.transaction-evidence-{replacement.transaction_id}"
            HotMainCache._atomic_move_bound(
                target.project_descriptor,
                staging.name,
                descriptor,
                target.project_descriptor,
                retained_name,
                "seed staging-root retention",
            )
            replacement.staging_parent_monitor.accept_owned_change()
            target.refresh_after_project_mutation()
            os.fsync(target.project_descriptor)
        except BaseException:
            pass

    @staticmethod
    def _close_seed_replacement(replacement: _SeedReplacement) -> None:
        descriptors: list[int] = []
        if replacement.journal_file_descriptors is not None:
            descriptors.extend(replacement.journal_file_descriptors.values())
        for descriptor in (
            replacement.journal_descriptor,
            replacement.journal_parent_descriptor,
            replacement.staging_lake_descriptor,
            replacement.staging_descriptor,
            replacement.original_descriptor,
        ):
            if descriptor is not None:
                descriptors.append(descriptor)
        closed: set[int] = set()
        for descriptor in descriptors:
            if descriptor in closed:
                continue
            closed.add(descriptor)
            try:
                os.close(descriptor)
            except OSError:
                pass
        for monitor in (
            replacement.journal_entry_monitor,
            replacement.journal_parent_monitor,
            replacement.destination_monitor,
            replacement.staging_entry_monitor,
            replacement.staging_parent_monitor,
        ):
            if monitor is not None:
                try:
                    monitor.close()
                except OSError:
                    pass

    def _target_lock_path(self, supplied_target: Path) -> tuple[Path, Path]:
        lexical_target = reject_symlink_components(supplied_target)
        destination = lexical_target / ".lake"
        target_digest = self._seed_target_digest(lexical_target)
        return lexical_target, self.runtime_dir / "locks" / f"seed-{target_digest}.lock"

    def _assert_seed_target_registered(self, target: _BoundSeedTarget) -> None:
        target.assert_current()
        checked = self._eligible_seed_target(target.target_project, check_inputs=False)
        try:
            if (
                checked.project_identity != target.project_identity
                or checked.worktree_identity != target.worktree_identity
                or checked.worktree_parent_identity != target.worktree_parent_identity
                or checked.worktree_head != target.worktree_head
            ):
                raise CacheError("target worktree identity changed during seed/prepare")
        finally:
            checked.close()
        target.assert_current()

    @staticmethod
    def _adapt_materializer_to_bound_target(
        module: Any, target: _BoundSeedTarget
    ) -> None:
        """Let the authenticated materializer traverse the bound project fd."""

        required = {
            "MaterializationError",
            "TRANSACTION_SAFETY_VERSION",
            "_assert_real_directory",
            "_reject_symlink_components",
            "_finish_cleanup",
            "_recover",
            "_require_transaction_capabilities",
        }
        missing = sorted(name for name in required if not hasattr(module, name))
        if missing:
            raise CacheError(
                "foundation materializer lacks the bound fail-closed interface: "
                + ", ".join(missing)
            )
        if module.TRANSACTION_SAFETY_VERSION != 1:
            raise CacheError("foundation materializer has an unsupported transaction-safety interface")
        bound_root = target.access_path
        original_assert = module._assert_real_directory
        original_reject = module._reject_symlink_components

        def assert_real_directory(path: Path) -> None:
            absolute = Path(os.path.abspath(path))
            if absolute != bound_root:
                original_assert(path)
                return
            value = os.fstat(target.project_descriptor)
            if not stat.S_ISDIR(value.st_mode):
                raise module.MaterializationError("bound project is no longer a directory")

        def reject_symlink_components(path: Path) -> None:
            absolute = Path(os.path.abspath(path))
            try:
                relative = absolute.relative_to(bound_root)
            except ValueError:
                original_reject(path)
                return
            descriptor = os.dup(target.project_descriptor)
            try:
                for component in relative.parts:
                    try:
                        value = os.stat(
                            component, dir_fd=descriptor, follow_symlinks=False
                        )
                    except FileNotFoundError:
                        return
                    if stat.S_ISLNK(value.st_mode):
                        raise module.MaterializationError(
                            f"path contains a symlink component: {path}"
                        )
                    if not stat.S_ISDIR(value.st_mode):
                        return
                    child = os.open(
                        component,
                        _authored_directory_flags(),
                        dir_fd=descriptor,
                    )
                    os.close(descriptor)
                    descriptor = child
            finally:
                os.close(descriptor)

        module._assert_real_directory = assert_real_directory
        module._reject_symlink_components = reject_symlink_components

        def finish_cleanup(path: Path) -> None:
            if path.exists() or path.is_symlink():
                raise module.MaterializationError(
                    "materializer cleanup has no independent ownership proof and was preserved"
                )

        def recover(transaction: Path, destination: Path, pin: Mapping[str, Any]) -> None:
            if transaction.exists() or transaction.is_symlink():
                raise module.MaterializationError(
                    "persisted materializer transaction has no independent ownership proof"
                )

        def require_transaction_capabilities(_descriptor: int) -> None:
            target.assert_current()
            HotMainCache._require_seed_capabilities(target)

        module._finish_cleanup = finish_cleanup
        module._recover = recover
        module._require_transaction_capabilities = require_transaction_capabilities

    @staticmethod
    def _assert_no_materializer_recovery_state(target: _BoundSeedTarget) -> None:
        target.assert_current()
        runtime = target.access_path / ".workflow-runtime" / "mipstarre-materialization"
        transaction = runtime / "MIPStarRE.transaction"
        cleanup = runtime / "MIPStarRE.transaction.cleanup"
        preparation = runtime / "MIPStarRE.transaction.preparing"
        retained = [
            path
            for path in (transaction, cleanup, preparation)
            if path.exists() or path.is_symlink()
        ]
        if retained:
            raise CacheError(
                "persisted materializer state has no independent ownership proof and requires "
                "manual recovery; retained paths: " + ", ".join(map(str, retained))
            )
        target.assert_current()

    def _publish_seed_locked(
        self,
        target: _BoundSeedTarget,
        *,
        replace: bool,
        cache_lock: ExclusiveLock,
        target_lock: ExclusiveLock,
        started: float,
        replacement: _SeedReplacement,
    ) -> dict[str, Any]:
        """Publish a seed while the caller retains the target operation lock."""

        target.assert_current()
        target_project = target.target_project
        destination = target.access_path / replacement.destination.name
        if replacement.destination != target_project / ".lake":
            raise CacheError("seed replacement state does not match the target project")
        if destination.is_symlink():
            raise CacheError(f"refusing to replace symlinked .lake directory: {destination}")
        if destination.exists() and not destination.is_dir():
            raise CacheError(f"target .lake must be a real directory: {destination}")
        if destination.exists() and not replace:
            raise CacheError(
                f"target .lake already exists; pass --replace to replace it: {destination}"
            )
        staging_root = target.access_path / f".lake-seed-{replacement.transaction_id}"
        if staging_root.exists() or staging_root.is_symlink():
            raise CacheError(f"seed staging path already exists: {staging_root}")
        replacement.staging_parent_monitor = _BoundNameMonitor(
            target.project_descriptor,
            (
                staging_root.name,
                f".lake.transaction-evidence-{replacement.transaction_id}",
            ),
        )
        os.mkdir(staging_root.name, dir_fd=target.project_descriptor)
        replacement.staging_parent_monitor.accept_owned_change()
        target.refresh_after_project_mutation()
        replacement.staging_root = target_project / staging_root.name
        replacement.staging_descriptor = os.open(
            staging_root.name,
            _authored_directory_flags(),
            dir_fd=target.project_descriptor,
        )
        self._assert_bound_name(
            target.project_descriptor,
            staging_root.name,
            replacement.staging_descriptor,
            "seed staging root",
        )
        staging_lake = staging_root / ".lake"
        copy_stats = reflink_copytree(self.lake_dir, staging_lake)
        make_owner_writable(staging_lake)
        replacement.staging_lake_descriptor = os.open(
            ".lake",
            _authored_directory_flags(),
            dir_fd=replacement.staging_descriptor,
        )
        self._assert_bound_name(
            replacement.staging_descriptor,
            ".lake",
            replacement.staging_lake_descriptor,
            "staged Lake tree",
        )
        replacement.staging_entry_monitor = _BoundNameMonitor(
            replacement.staging_descriptor, (".lake",)
        )
        replacement.destination_monitor = _BoundNameMonitor(
            target.project_descriptor, (replacement.destination.name,)
        )
        self._validate_seeded_destination(staging_lake)
        self._assert_seed_target_registered(target)
        if destination.exists():
            replacement.original_identity = self._lake_tree_identity(destination)
            replacement.original_descriptor = os.open(
                replacement.destination.name,
                _authored_directory_flags(),
                dir_fd=target.project_descriptor,
            )
            original_stat = os.fstat(replacement.original_descriptor)
            if _authored_directory_identity(original_stat) != (
                replacement.original_identity["device"],
                replacement.original_identity["inode"],
            ):
                raise CacheError("target .lake identity changed while binding replacement")
            self._write_seed_journal(replacement, target, staging_lake)
            self._assert_seed_target_registered(target)
            replacement.staging_entry_monitor.assert_clean()
            replacement.destination_monitor.assert_clean()
            try:
                self._atomic_exchange_bound(
                    replacement.staging_descriptor,
                    ".lake",
                    replacement.staging_lake_descriptor,
                    target.project_descriptor,
                    replacement.destination.name,
                    replacement.original_descriptor,
                    "seed replacement publication",
                )
                replacement.staging_entry_monitor.accept_owned_change()
                replacement.destination_monitor.accept_owned_change()
            finally:
                try:
                    self._assert_bound_name(
                        target.project_descriptor,
                        replacement.destination.name,
                        replacement.staging_lake_descriptor,
                        "published Lake tree",
                    )
                    self._assert_bound_name(
                        replacement.staging_descriptor,
                        ".lake",
                        replacement.original_descriptor,
                        "displaced original Lake tree",
                    )
                except CacheError:
                    pass
                else:
                    replacement.old_moved = True
                    replacement.new_published = True
        else:
            replacement.staging_entry_monitor.assert_clean()
            replacement.destination_monitor.assert_clean()
            try:
                self._atomic_move_bound(
                    replacement.staging_descriptor,
                    ".lake",
                    replacement.staging_lake_descriptor,
                    target.project_descriptor,
                    replacement.destination.name,
                    "seed no-replace publication",
                )
                replacement.staging_entry_monitor.accept_owned_change()
                replacement.destination_monitor.accept_owned_change()
            finally:
                try:
                    self._assert_bound_name(
                        target.project_descriptor,
                        replacement.destination.name,
                        replacement.staging_lake_descriptor,
                        "published Lake tree",
                    )
                except CacheError:
                    pass
                else:
                    replacement.new_published = True
        target.refresh_after_project_mutation()
        os.fsync(target.project_descriptor)
        self._validate_seeded_destination(destination)
        self._assert_seed_target_registered(target)
        return {
            **self.status(),
            "action": "seed",
            "result": "seeded",
            "target": str(replacement.destination),
            "worktree_root": str(target.worktree_root),
            "replaced": replacement.old_moved,
            "transaction_id": replacement.transaction_id,
            "backup_retained": None,
            "cache_hit": 1,
            "cache_miss": 0,
            "lock_waited": int(cache_lock.waited or target_lock.waited),
            "lock_wait_seconds": round(cache_lock.wait_seconds + target_lock.wait_seconds, 6),
            "builds": 0,
            "build_seconds": 0.0,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "copy": asdict(copy_stats),
        }

    def _retain_seed_backup(
        self, target: _BoundSeedTarget, replacement: _SeedReplacement
    ) -> str | None:
        if not replacement.old_moved:
            return None
        target.assert_current()
        expected = replacement.original_identity
        descriptor = replacement.original_descriptor
        retained_name = f".lake.retained-{replacement.transaction_id}"
        retained = target.access_path / retained_name
        staging_descriptor = replacement.staging_descriptor
        if expected is None or descriptor is None or staging_descriptor is None:
            raise CacheError("seed backup has no live ownership binding")
        if replacement.staging_entry_monitor is None:
            raise CacheError("seed backup lost its continuous name monitor")
        replacement.staging_entry_monitor.assert_clean()
        try:
            descriptor_identity = os.fstat(descriptor)
        except OSError as error:
            raise CacheError("seed backup ownership descriptor is unavailable") from error
        if (
            _authored_directory_identity(descriptor_identity)
            != (expected.get("device"), expected.get("inode"))
        ):
            raise CacheError("seed backup identity changed; retained for manual recovery")
        self._atomic_move_bound(
            staging_descriptor,
            ".lake",
            descriptor,
            target.project_descriptor,
            retained_name,
            "displaced original Lake tree",
        )
        replacement.staging_entry_monitor.accept_owned_change()
        self._assert_bound_name(
            target.project_descriptor,
            retained_name,
            descriptor,
            "retained original Lake tree",
        )
        target.refresh_after_project_mutation()
        os.fsync(target.project_descriptor)
        return str(target.target_project / retained_name)

    def _rollback_seed_transaction(
        self,
        target: _BoundSeedTarget,
        replacement: _SeedReplacement,
        error: BaseException,
        *,
        action: str,
    ) -> None:
        rollback_errors = self._rollback_seed_replacement(target, replacement)
        if not rollback_errors and replacement.journal_descriptor is not None:
            try:
                os.fsync(target.project_descriptor)
                self._clear_seed_journal(replacement)
            except BaseException as journal_error:
                rollback_errors.append(f"could not clear recovered transaction journal: {journal_error}")
        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise CacheError(
                f"{action} failed ({error}); rollback incomplete: {details}"
            ) from error

    def seed(self, target_project: Path, *, replace: bool = False, dry_run: bool = False) -> dict[str, Any]:
        lexical_target, target_lock_path = self._target_lock_path(target_project)
        if dry_run:
            target = self._eligible_seed_target(lexical_target, check_inputs=False)
            try:
                self._require_seed_capabilities(target)
                checked_target = self._eligible_seed_target(lexical_target)
                old_target, target = target, checked_target
                old_target.close()
                self._require_seed_capabilities(target)
                return {
                    **self.status(),
                    "action": "seed",
                    "dry_run": True,
                    "target": str(target.target_project / ".lake"),
                    "worktree_root": str(target.worktree_root),
                    "replace": replace,
                }
            finally:
                target.close()
        started = time.monotonic()
        with ExclusiveLock(target_lock_path) as target_lock:
            target = self._eligible_seed_target(lexical_target, check_inputs=False)
            replacement: _SeedReplacement | None = None
            try:
                self._recover_interrupted_seed(target)
                self._require_seed_capabilities(target)
                checked_target = self._eligible_seed_target(lexical_target)
                old_target, target = target, checked_target
                old_target.close()
                self._require_seed_capabilities(target)
                destination = target.access_path / ".lake"
                if destination.exists() and not replace:
                    raise CacheError(
                        "target .lake already exists; pass --replace to replace it: "
                        f"{target.target_project / '.lake'}"
                    )
                with ExclusiveLock(self.lock_path) as cache_lock:
                    if not self.is_ready(deep=True):
                        raise CacheError(
                            "hot-main cache is missing or failed deep artifact verification"
                        )
                replacement = self._new_seed_replacement(
                    target, rollback_prefix=".lake-seed-rollback-"
                )
                try:
                    result = self._publish_seed_locked(
                        target,
                        replace=replace,
                        cache_lock=cache_lock,
                        target_lock=target_lock,
                        started=started,
                        replacement=replacement,
                    )
                    self._assert_seed_target_registered(target)
                    self._append_metric(
                        result, lambda: self._assert_seed_target_registered(target)
                    )
                    replacement.metric_committed = True
                    self._mark_seed_committed(replacement)
                    self._assert_seed_target_registered(target)
                except BaseException as error:
                    if replacement.metric_committed:
                        self._discard_seed_rollback_root(target, replacement)
                        raise CacheError(
                            f"seed committed but transaction finalization failed: {error}"
                        ) from error
                    try:
                        self._rollback_seed_transaction(target, replacement, error, action="seed")
                    finally:
                        self._discard_seed_rollback_root(target, replacement)
                    raise
                result["backup_retained"] = self._retain_seed_backup(target, replacement)
                if replacement.journal_descriptor is not None:
                    os.fsync(target.project_descriptor)
                    self._clear_seed_journal(replacement)
                self._discard_seed_rollback_root(target, replacement)
                self._assert_seed_target_registered(target)
                return result
            finally:
                if replacement is not None:
                    self._close_seed_replacement(replacement)
                target.close()

    def prepare(self, target_project: Path, *, replace_seed: bool = False, dry_run: bool = False) -> dict[str, Any]:
        """Seed and verify a build-ready issue worktree without compiling it."""

        lexical_target, target_lock_path = self._target_lock_path(target_project)
        if dry_run:
            return {
                **self.seed(lexical_target, replace=replace_seed, dry_run=True),
                "action": "prepare",
                "foundation_replace_existing": True,
                "foundation_verify": True,
            }
        started = time.monotonic()
        with ExclusiveLock(target_lock_path) as target_lock:
            target = self._eligible_seed_target(lexical_target, check_inputs=False)
            replacement: _SeedReplacement | None = None
            try:
                self._recover_interrupted_seed(target)
                self._assert_no_materializer_recovery_state(target)
                self._require_seed_capabilities(target)
                destination = target.access_path / ".lake"
                if destination.exists() and not replace_seed:
                    raise CacheError(
                        "target .lake already exists; pass --replace to replace it: "
                        f"{target.target_project / '.lake'}"
                    )
                inputs = self._preflight_authenticated_inputs()
                checked_target = self._eligible_seed_target(lexical_target)
                old_target, target = target, checked_target
                old_target.close()
                self._require_seed_capabilities(target)
                authored_before = authored_tree_facts_on_disk(target.target_project)
                target.assert_current()
                operational_project = target.access_path
                target_inputs = self._capture_identity_inputs(target.target_project)
                module_relative = "scripts/materialize_mipstarre.py"
                pin_relative = "references/mipstarre-upstream.json"
                module = self._load_identity_module(
                    module_relative,
                    "_hot_cache_prepare_mipstarre",
                    target_inputs[module_relative],
                    target.target_project,
                )
                self._adapt_materializer_to_bound_target(module, target)
                module_project = operational_project
                pin = self._load_captured_pin(
                    module, pin_relative, target_inputs[pin_relative]
                )
                self._validate_captured_project(
                    module, "validate_project_pins", target_inputs, pin
                )
                pin_path = module_project / pin_relative

                def captured_pin_loader(requested: Path) -> Mapping[str, Any]:
                    if Path(os.path.abspath(requested)) != pin_path:
                        raise CacheError("foundation materializer requested an unauthenticated pin path")
                    return pin

                def captured_project_validator(
                    requested_root: Path, requested_pin: Mapping[str, Any]
                ) -> None:
                    if Path(os.path.abspath(requested_root)) != module_project or requested_pin is not pin:
                        raise CacheError("foundation materializer changed its authenticated project inputs")
                    target.assert_current()
                    if self._capture_identity_inputs(target.target_project) != target_inputs:
                        raise CacheError("target cache-key inputs changed during foundation materialization")

                module.load_pin = captured_pin_loader
                module.validate_project_pins = captured_project_validator
                self._assert_no_materializer_recovery_state(target)
                with ExclusiveLock(self.lock_path) as cache_lock:
                    if not self.is_ready(deep=True):
                        raise CacheError(
                            "hot-main cache is missing or failed deep artifact verification"
                        )
                replacement = self._new_seed_replacement(
                    target, rollback_prefix=".lake-prepare-rollback-"
                )
                seeded = self._publish_seed_locked(
                    target,
                    replace=replace_seed,
                    cache_lock=cache_lock,
                    target_lock=target_lock,
                    started=started,
                    replacement=replacement,
                )
                target.assert_current()
                self._assert_no_materializer_recovery_state(target)
                materialized = module.materialize(
                    module_project,
                    pin_path,
                    Path(os.environ[MIPSTARRE_ARCHIVE_ENV]),
                    replace_existing=True,
                )
                target.refresh_after_project_mutation()
                authored_after_materialize = authored_tree_facts_on_disk(target.target_project)
                if authored_after_materialize != authored_before:
                    raise CacheError("authored QPBT inventory changed during issue-worktree preparation")
                if self._capture_identity_inputs(target.target_project) != target_inputs:
                    raise CacheError("target cache-key inputs changed during foundation materialization")
                verified = module.verify_materialized(module_project, pin)
                target.assert_current()
                authored_final = authored_tree_facts_on_disk(target.target_project)
                verifier_authored = {
                    key: verified.get(key)
                    for key in (
                        "authored_qpbt_files",
                        "authored_qpbt_bytes",
                        "authored_qpbt_sha256",
                    )
                }
                if (
                    authored_final != authored_before
                    or authored_final != authored_after_materialize
                    or verifier_authored != authored_final
                ):
                    raise CacheError(
                        "authored QPBT inventory changed or verifier evidence differs during issue-worktree preparation"
                    )
                if self._capture_identity_inputs(target.target_project) != target_inputs:
                    raise CacheError("target cache-key inputs changed during foundation verification")
                self._assert_seed_target_registered(target)
                self._validate_seeded_destination(operational_project / ".lake")
                target.assert_current()
                seeded["elapsed_seconds"] = round(time.monotonic() - started, 6)
                prepared = {
                    "action": "prepare", "result": "prepared", "inputs": inputs,
                    "seed": seeded, "foundation": materialized, "verification": verified,
                    "authored_qpbt": authored_final,
                }
                self._append_metric(
                    seeded, lambda: self._assert_seed_target_registered(target)
                )
                replacement.metric_committed = True
                self._mark_seed_committed(replacement)
                self._assert_seed_target_registered(target)
                seeded["backup_retained"] = self._retain_seed_backup(target, replacement)
                if replacement.journal_descriptor is not None:
                    os.fsync(target.project_descriptor)
                    self._clear_seed_journal(replacement)
                self._discard_seed_rollback_root(target, replacement)
                self._assert_seed_target_registered(target)
                return prepared
            except BaseException as error:
                if replacement is not None and replacement.metric_committed:
                    self._discard_seed_rollback_root(target, replacement)
                    raise CacheError(
                        "issue-worktree preparation committed but transaction "
                        f"finalization failed: {error}"
                    ) from error
                if replacement is not None:
                    try:
                        self._rollback_seed_transaction(
                            target,
                            replacement,
                            error,
                            action="issue-worktree preparation",
                        )
                    finally:
                        self._discard_seed_rollback_root(target, replacement)
                if isinstance(error, CacheError):
                    raise
                raise CacheError(f"issue-worktree foundation preparation failed: {error}") from error
            finally:
                if replacement is not None:
                    self._close_seed_replacement(replacement)
                target.close()


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--repo-root", default=str(default_root))
    parser.add_argument("--project-dir", default=".", help="Lake project root, relative to repository")
    parser.add_argument(
        "--runtime-dir",
        default=None,
        help="runtime/cache root (omitted: .workflow-runtime under the primary Git worktree)",
    )
    parser.add_argument("--main-ref", default="main")
    parser.add_argument("--main-commit", help="full SHA override, useful for detached/offline operation")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("status", help="report the current identity and cache availability")

    warm = commands.add_parser("warm", help="elect one builder and atomically publish the main cache")
    warm.add_argument("--dry-run", action="store_true")

    seed = commands.add_parser("seed", help="copy the hot cache into an issue worktree")
    seed.add_argument("--worktree", required=True, help="target issue worktree / Lake project root")
    seed.add_argument("--replace", action="store_true")
    seed.add_argument("--dry-run", action="store_true")
    prepare = commands.add_parser(
        "prepare", help="seed and materialize a verified build-ready issue worktree"
    )
    prepare.add_argument("--worktree", required=True, help="target issue worktree / Lake project root")
    prepare.add_argument("--replace", action="store_true", help="replace an existing private .lake")
    prepare.add_argument("--dry-run", action="store_true")
    return parser


def run_cli(arguments: argparse.Namespace) -> dict[str, Any]:
    try:
        repo_root = Path(arguments.repo_root).resolve()
    except (OSError, RuntimeError) as error:
        raise CacheError(
            "could not resolve the repository root for the cache command; "
            "pass --runtime-dir explicitly"
        ) from error
    try:
        project_dir = _resolve(repo_root, arguments.project_dir).resolve()
    except (OSError, RuntimeError) as error:
        raise CacheError(f"could not resolve the project directory: {error}") from error
    runtime_dir = (
        default_runtime_dir(repo_root)
        if arguments.runtime_dir is None
        else _resolve(repo_root, arguments.runtime_dir)
    )
    cache = HotMainCache(
        repo_root,
        project_dir,
        runtime_dir,
        main_ref=arguments.main_ref,
        main_commit=arguments.main_commit,
    )
    if arguments.command == "status":
        return cache.status()
    if arguments.command == "warm":
        return cache.warm(dry_run=arguments.dry_run)
    if arguments.command == "seed":
        return cache.seed(
            _resolve(repo_root, arguments.worktree),
            replace=arguments.replace,
            dry_run=arguments.dry_run,
        )
    if arguments.command == "prepare":
        return cache.prepare(
            _resolve(repo_root, arguments.worktree),
            replace_seed=arguments.replace,
            dry_run=arguments.dry_run,
        )
    raise CacheError(f"unsupported command {arguments.command!r}")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        result = run_cli(arguments)
    except CacheError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
