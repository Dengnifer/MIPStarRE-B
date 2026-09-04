#!/usr/bin/env python3
"""Verify and locally materialize the exact unlicensed MIPStarRE foundation."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
import ctypes
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
import struct
import sys
import time
from typing import Any, Callable, Iterator, Mapping, Sequence
import zlib


SCHEMA_VERSION = 1
HARD_MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
HARD_MAX_TAR_BYTES = 64 * 1024 * 1024
HARD_MAX_MEMBERS = 5000
HARD_MAX_MEMBER_BYTES = 2 * 1024 * 1024
HARD_MAX_REGULAR_BYTES = 64 * 1024 * 1024
BLOCK = 512
TRANSACTION_SAFETY_VERSION = 2
RENAME_NOREPLACE = 1
RENAME_EXCHANGE = 2
AT_EMPTY_PATH = 0x1000
_RENAMEAT2_FILESYSTEM_MAGICS = {
    0xEF53,  # ext2/ext3/ext4
    0x58465342,  # XFS
    0x9123683E,  # Btrfs
    0x01021994,  # tmpfs
    0x794C7630,  # overlayfs
    0xF2F52010,  # F2FS
}
_IN_MODIFY = 0x00000002
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
_IN_MASK_ADD = 0x20000000
_INOTIFY_EVENT = struct.Struct("iIII")


class MaterializationError(Exception):
    """A pinned-source operation failed without making upstream bytes canonical."""


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _linux_libc() -> Any:
    if sys.platform != "linux":
        raise MaterializationError("safe materialization requires Linux renameat2 and inotify")
    return ctypes.CDLL(None, use_errno=True)


def _linux_renameat2(
    source_parent: int,
    source_name: str,
    destination_parent: int,
    destination_name: str,
    flags: int,
) -> None:
    if flags not in {RENAME_NOREPLACE, RENAME_EXCHANGE}:
        raise MaterializationError("materialization rename requires no-replace or exchange")
    for name in (source_name, destination_name):
        encoded = os.fsencode(name)
        if not encoded or encoded in {b".", b".."} or b"/" in encoded or b"\0" in encoded:
            raise MaterializationError("materialization rename operands must be child names")
    for descriptor in (source_parent, destination_parent):
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise MaterializationError("materialization rename parent is not a directory")
    renameat2 = getattr(_linux_libc(), "renameat2", None)
    if renameat2 is None:
        raise MaterializationError("safe materialization requires Linux renameat2")
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


def _linux_link_unnamed_file(
    descriptor: int, destination_parent: int, destination_name: str
) -> None:
    """Link the populated inode at the caller-selected name."""

    encoded = os.fsencode(destination_name)
    if not encoded or encoded in {b".", b".."} or b"/" in encoded or b"\0" in encoded:
        raise MaterializationError("unnamed-file publication requires one safe child name")
    linkat = getattr(_linux_libc(), "linkat", None)
    if linkat is None:
        raise MaterializationError("safe materialization requires Linux linkat")
    linkat.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    linkat.restype = ctypes.c_int
    ctypes.set_errno(0)
    if linkat(descriptor, b"", destination_parent, encoded, AT_EMPTY_PATH) == 0:
        return
    direct_error = ctypes.get_errno()
    ctypes.set_errno(0)
    if linkat(
        -100,
        os.fsencode(f"/proc/self/fd/{descriptor}"),
        destination_parent,
        encoded,
        getattr(os, "AT_SYMLINK_FOLLOW", 0x400),
    ) == 0:
        return
    fallback_error = ctypes.get_errno()
    raise OSError(
        fallback_error,
        "could not publish unnamed materialized output: "
        f"{os.strerror(fallback_error)} (direct linkat: {os.strerror(direct_error)})",
    )


def _linux_filesystem_magic(descriptor: int) -> int:
    fstatfs = getattr(_linux_libc(), "fstatfs", None)
    if fstatfs is None:
        raise MaterializationError("safe materialization requires Linux fstatfs")
    buffer = ctypes.create_string_buffer(256)
    fstatfs.argtypes = [ctypes.c_int, ctypes.c_void_p]
    fstatfs.restype = ctypes.c_int
    ctypes.set_errno(0)
    if fstatfs(descriptor, ctypes.byref(buffer)) != 0:
        error_number = ctypes.get_errno()
        raise MaterializationError(
            f"could not identify materialization filesystem: {os.strerror(error_number)}"
        )
    width = ctypes.sizeof(ctypes.c_long)
    return int.from_bytes(buffer.raw[:width], sys.byteorder, signed=False)


def _assert_bound_name(parent: int, name: str, descriptor: int, label: str) -> None:
    try:
        lexical = os.stat(name, dir_fd=parent, follow_symlinks=False)
        bound = os.fstat(descriptor)
    except OSError as error:
        raise MaterializationError(f"{label} identity changed") from error
    if (
        stat.S_ISLNK(lexical.st_mode)
        or (lexical.st_dev, lexical.st_ino, stat.S_IFMT(lexical.st_mode))
        != (bound.st_dev, bound.st_ino, stat.S_IFMT(bound.st_mode))
    ):
        raise MaterializationError(f"{label} identity changed")


def _assert_name_absent(parent: int, name: str, label: str) -> None:
    try:
        os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as error:
        raise MaterializationError(f"could not prove absent {label}") from error
    raise MaterializationError(f"{label} appeared concurrently")


class _InotifyHub:
    """Route one inotify event stream to independently consumed logical monitors."""

    def __init__(self) -> None:
        libc = _linux_libc()
        initialize = getattr(libc, "inotify_init1", None)
        add_watch = getattr(libc, "inotify_add_watch", None)
        if initialize is None or add_watch is None:
            raise MaterializationError("safe materialization requires Linux inotify")
        initialize.argtypes = [ctypes.c_int]
        initialize.restype = ctypes.c_int
        add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        add_watch.restype = ctypes.c_int
        descriptor = initialize(os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
        if descriptor < 0:
            error_number = ctypes.get_errno()
            raise MaterializationError(
                f"could not initialize materialization monitor: {os.strerror(error_number)}"
            )
        self.descriptor = descriptor
        self._add_watch_call = add_watch
        self._mask = (
            _IN_MODIFY
            | _IN_ATTRIB
            | _IN_MOVED_FROM
            | _IN_MOVED_TO
            | _IN_CREATE
            | _IN_DELETE
            | _IN_DELETE_SELF
            | _IN_MOVE_SELF
            | _IN_UNMOUNT
            | _IN_Q_OVERFLOW
        )
        self._subscribers: dict[int, set[_BoundNameMonitor]] = {}
        self._watch_identities: dict[int, tuple[int, int, int]] = {}
        self._poisoned_watches: set[int] = set()
        self.poisoned = False
        self.closed = False

    @staticmethod
    def _identity(descriptor: int) -> tuple[int, int, int]:
        metadata = os.fstat(descriptor)
        return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)

    def _poison_all(self) -> None:
        self.poisoned = True
        for subscribers in self._subscribers.values():
            for subscriber in subscribers:
                subscriber.poisoned = True

    def _poison_watch(self, watch: int) -> None:
        self._poisoned_watches.add(watch)
        for subscriber in self._subscribers.get(watch, ()):
            subscriber.poisoned = True

    def _route(self, watch: int, mask: int, name: bytes) -> None:
        if mask & _IN_Q_OVERFLOW:
            self._poison_all()
            return
        if watch == -1 or watch not in self._watch_identities:
            self._poison_all()
            return
        if mask & (_IN_IGNORED | _IN_UNMOUNT | _IN_DELETE_SELF):
            self._poison_watch(watch)
            return
        for subscriber in tuple(self._subscribers.get(watch, ())):
            if subscriber.closed:
                continue
            if mask & _IN_MOVE_SELF:
                subscriber._events.append((b"", _IN_MOVE_SELF))
            elif subscriber.names is None or name in subscriber.names:
                operation = mask & (
                    _IN_MODIFY
                    | _IN_ATTRIB
                    | _IN_MOVED_FROM
                    | _IN_MOVED_TO
                    | _IN_CREATE
                    | _IN_DELETE
                )
                subscriber._events.append((name, operation))

    def drain(self) -> None:
        if self.closed:
            self._poison_all()
            return
        while True:
            try:
                payload = os.read(self.descriptor, 64 * 1024)
            except BlockingIOError:
                return
            except OSError:
                self._poison_all()
                return
            if not payload:
                self._poison_all()
                return
            offset = 0
            while offset < len(payload):
                if len(payload) - offset < _INOTIFY_EVENT.size:
                    self._poison_all()
                    return
                watch, mask, _cookie, name_size = _INOTIFY_EVENT.unpack_from(payload, offset)
                offset += _INOTIFY_EVENT.size
                if len(payload) - offset < name_size:
                    self._poison_all()
                    return
                raw_name = payload[offset : offset + name_size]
                offset += name_size
                if name_size:
                    name, terminator, padding = raw_name.partition(b"\0")
                    if not terminator or any(padding):
                        self._poison_all()
                        return
                else:
                    name = b""
                self._route(watch, mask, name)

    def subscribe(self, monitor: _BoundNameMonitor, parent_descriptor: int) -> int:
        if self.closed:
            monitor.poisoned = True
            raise MaterializationError("materialization monitor authority is closed")
        self.drain()
        identity = self._identity(parent_descriptor)
        ctypes.set_errno(0)
        watch = self._add_watch_call(
            self.descriptor,
            os.fsencode(f"/proc/self/fd/{parent_descriptor}"),
            self._mask | _IN_MASK_ADD,
        )
        if watch < 0:
            error_number = ctypes.get_errno()
            raise MaterializationError(
                f"could not bind materialization monitor: {os.strerror(error_number)}"
            )
        prior_identity = self._watch_identities.setdefault(watch, identity)
        self._subscribers.setdefault(watch, set()).add(monitor)
        if prior_identity != identity or watch in self._poisoned_watches or self.poisoned:
            self._poison_watch(watch)
        self.drain()
        return watch

    def unsubscribe(self, monitor: _BoundNameMonitor) -> None:
        if self.closed:
            return
        self.drain()
        subscribers = self._subscribers.get(monitor.watch)
        if subscribers is not None:
            subscribers.discard(monitor)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self._poison_all()
        os.close(self.descriptor)


_ACTIVE_INOTIFY_HUB: ContextVar[_InotifyHub | None] = ContextVar(
    "materialize_mipstarre_inotify_hub", default=None
)


@contextmanager
def _monitor_authority() -> Iterator[_InotifyHub]:
    existing = _ACTIVE_INOTIFY_HUB.get()
    if existing is not None:
        yield existing
        return
    hub = _InotifyHub()
    token = _ACTIVE_INOTIFY_HUB.set(hub)
    try:
        yield hub
    finally:
        _ACTIVE_INOTIFY_HUB.reset(token)
        try:
            hub.close()
        except OSError:
            pass


class _BoundNameMonitor:
    """Permanently reject substitution or ABA of selected directory children."""

    def __init__(self, parent_descriptor: int, names: Sequence[str] | None):
        hub = _ACTIVE_INOTIFY_HUB.get()
        if hub is None:
            raise MaterializationError("materialization monitor lacks a shared event authority")
        self.hub = hub
        self.names = None if names is None else {os.fsencode(name) for name in names}
        self._events: list[tuple[bytes, int]] = []
        self.poisoned = False
        self.closed = False
        self.watch = -1
        self.watch = hub.subscribe(self, parent_descriptor)

    def _drain(self) -> tuple[list[tuple[bytes, int]], bool]:
        self.hub.drain()
        relevant = self._events
        self._events = []
        return relevant, self.poisoned

    def assert_clean(self) -> None:
        relevant, fatal = self._drain()
        if relevant or fatal:
            self.poisoned = True
        if self.poisoned:
            raise MaterializationError("materialization object changed or monitor became ambiguous")

    def accept_owned_change(self, expected: Sequence[tuple[str, int]]) -> None:
        relevant, fatal = self._drain()
        expected_events = Counter((os.fsencode(name), mask) for name, mask in expected)
        if self.poisoned or fatal or Counter(relevant) != expected_events:
            self.poisoned = True
            raise MaterializationError("materialization mutation lacked its exact monitor events")

    def close(self) -> None:
        if self.closed:
            return
        self.hub.unsubscribe(self)
        self.closed = True


def _atomic_move_bound(
    source_parent: int,
    source_name: str,
    source_descriptor: int,
    destination_parent: int,
    destination_name: str,
    label: str,
    renamed: Callable[[], None] | None = None,
) -> None:
    _assert_bound_name(source_parent, source_name, source_descriptor, label)
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
            raise MaterializationError(
                f"{label} destination appeared concurrently; source retained"
            ) from error
        raise MaterializationError(f"atomic no-replace move failed for {label}: {error}") from error
    if renamed is not None:
        renamed()
    _assert_bound_name(destination_parent, destination_name, source_descriptor, label)


def _atomic_exchange_bound(
    first_parent: int,
    first_name: str,
    first_descriptor: int,
    second_parent: int,
    second_name: str,
    second_descriptor: int,
    label: str,
    renamed: Callable[[], None] | None = None,
) -> None:
    _assert_bound_name(first_parent, first_name, first_descriptor, label)
    _assert_bound_name(second_parent, second_name, second_descriptor, label)
    try:
        _linux_renameat2(
            first_parent,
            first_name,
            second_parent,
            second_name,
            RENAME_EXCHANGE,
        )
    except OSError as error:
        raise MaterializationError(f"atomic exchange failed for {label}: {error}") from error
    if renamed is not None:
        renamed()
    _assert_bound_name(second_parent, second_name, first_descriptor, label)
    _assert_bound_name(first_parent, first_name, second_descriptor, label)


def _require_transaction_capabilities(target_descriptor: int) -> None:
    """Check descriptor and atomic-rename capabilities used by the transaction."""

    required = (os.open, os.mkdir, os.stat)
    if any(operation not in os.supports_dir_fd for operation in required):
        raise MaterializationError("safe materialization requires descriptor-relative calls")
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise MaterializationError("safe materialization requires no-follow directory opens")
    if _linux_filesystem_magic(target_descriptor) not in _RENAMEAT2_FILESYSTEM_MAGICS:
        raise MaterializationError("target filesystem is not approved for atomic materialization")
    for flags, label in ((RENAME_NOREPLACE, "no-replace"), (RENAME_EXCHANGE, "exchange")):
        try:
            _linux_renameat2(-1, "probe-source", -1, "probe-destination", flags)
        except OSError as error:
            if error.errno != errno.EBADF:
                raise MaterializationError(
                    f"kernel does not provide atomic {label} materialization"
                ) from error
        else:
            raise MaterializationError(f"atomic {label} probe unexpectedly mutated a name")


def _bind_or_create_directory(
    parent_descriptor: int,
    name: str,
    monitor: _BoundNameMonitor,
    *,
    mode: int = 0o700,
) -> int:
    monitor.assert_clean()
    try:
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_descriptor)
    except FileNotFoundError:
        try:
            os.mkdir(name, mode, dir_fd=parent_descriptor)
        except FileExistsError as error:
            raise MaterializationError(f"directory appeared concurrently: {name}") from error
        monitor.accept_owned_change(((name, _IN_CREATE),))
        try:
            descriptor = os.open(name, _directory_flags(), dir_fd=parent_descriptor)
        except BaseException:
            raise
    except OSError as error:
        try:
            metadata = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        except OSError:
            metadata = None
        if metadata is not None and stat.S_ISLNK(metadata.st_mode):
            raise MaterializationError(f"path contains a symlink component: {name}") from error
        raise MaterializationError(f"unsafe materialization directory: {name}") from error
    try:
        _assert_bound_name(parent_descriptor, name, descriptor, f"materialization directory {name}")
        monitor.assert_clean()
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


@contextmanager
def _locked_at(
    parent_descriptor: int,
    name: str,
    monitor: _BoundNameMonitor,
) -> Iterator[None]:
    flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    existed = True
    try:
        descriptor = os.open(name, flags | os.O_EXCL, 0o600, dir_fd=parent_descriptor)
        existed = False
    except FileExistsError:
        descriptor = os.open(name, flags, 0o600, dir_fd=parent_descriptor)
    if not existed:
        try:
            monitor.accept_owned_change(((name, _IN_CREATE),))
        except BaseException:
            os.close(descriptor)
            raise
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise MaterializationError("materialization lock is not a regular file")
        _assert_bound_name(parent_descriptor, name, descriptor, "materialization lock")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        monitor.assert_clean()
        _assert_bound_name(parent_descriptor, name, descriptor, "materialization lock")
        yield
        monitor.assert_clean()
        _assert_bound_name(parent_descriptor, name, descriptor, "materialization lock")
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise MaterializationError(
            f"{label} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def _lower_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise MaterializationError(f"{label} must be 64 lowercase hexadecimal characters")
    return value


def _positive_int(value: Any, label: str, *, allow_zero: bool = False) -> int:
    lower = 0 if allow_zero else 1
    if not isinstance(value, int) or isinstance(value, bool) or value < lower:
        raise MaterializationError(f"{label} must be an integer >= {lower}")
    return value


def load_pin(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object_without_duplicates
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise MaterializationError(f"could not load upstream pin: {error}") from error
    if not isinstance(value, dict):
        raise MaterializationError("upstream pin must be an object")
    _exact_keys(
        value,
        {"schema_version", "source", "rights", "archive", "output", "lean_pins", "foundations"},
        "upstream pin",
    )
    if value["schema_version"] != SCHEMA_VERSION:
        raise MaterializationError("unsupported upstream pin schema version")
    source = value["source"]
    rights = value["rights"]
    archive = value["archive"]
    output = value["output"]
    lean_pins = value["lean_pins"]
    foundations = value["foundations"]
    for label, item in (
        ("source", source),
        ("rights", rights),
        ("archive", archive),
        ("output", output),
        ("lean_pins", lean_pins),
    ):
        if not isinstance(item, dict):
            raise MaterializationError(f"{label} pin must be an object")
    _exact_keys(
        source,
        {"id", "repository", "repository_url", "commit", "archive_url", "acquisition_evidence"},
        "source",
    )
    _exact_keys(rights, {"license_file", "redistribution_permission", "policy"}, "rights")
    _exact_keys(
        archive,
        {
            "format", "sha256", "bytes", "tar_sha256", "tar_bytes", "exact_prefix",
            "global_pax_comment", "members", "regular_files", "directories",
            "regular_bytes", "max_member_bytes",
        },
        "archive",
    )
    _exact_keys(
        output,
        {
            "path", "archive_subtree", "reserved_authored_subtree", "directories", "files",
            "bytes", "max_file_bytes", "inventory_sha256",
        },
        "output",
    )
    _exact_keys(
        lean_pins, {"toolchain", "mathlib_input_revision", "mathlib_commit"}, "lean_pins"
    )
    if rights["license_file"] is not None:
        raise MaterializationError("pin must not imply a license file absent from the snapshot")
    if rights["redistribution_permission"] != "not-established":
        raise MaterializationError("pin must preserve the unresolved redistribution status")
    commit = source["commit"]
    if not isinstance(commit, str) or len(commit) != 40 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise MaterializationError("source commit must be a full lowercase Git SHA")
    if archive["global_pax_comment"] != commit:
        raise MaterializationError("global PAX comment must equal the source commit")
    if archive["format"] != "gzip-ustar-with-exact-global-pax-comment":
        raise MaterializationError("unsupported archive format")
    if archive["exact_prefix"] != f"MIPStarRE-{commit}/":
        raise MaterializationError("archive prefix does not bind the source commit")
    for key in ("sha256", "tar_sha256"):
        _lower_sha(archive[key], f"archive.{key}")
    for key in (
        "bytes", "tar_bytes", "members", "regular_files", "directories", "regular_bytes",
        "max_member_bytes",
    ):
        _positive_int(archive[key], f"archive.{key}")
    if archive["bytes"] > HARD_MAX_ARCHIVE_BYTES or archive["tar_bytes"] > HARD_MAX_TAR_BYTES:
        raise MaterializationError("archive pin exceeds the hard byte bounds")
    if archive["members"] > HARD_MAX_MEMBERS or archive["max_member_bytes"] > HARD_MAX_MEMBER_BYTES:
        raise MaterializationError("archive pin exceeds the hard member bounds")
    if archive["regular_bytes"] > HARD_MAX_REGULAR_BYTES:
        raise MaterializationError("archive pin exceeds the hard regular-byte bound")
    if output["path"] != "MIPStarRE" or output["archive_subtree"] != "MIPStarRE/":
        raise MaterializationError("output paths must retain the MIPStarRE module namespace")
    if output["reserved_authored_subtree"] != "QPBT/":
        raise MaterializationError("QPBT/ must remain reserved for project-authored files")
    for key in ("directories", "files", "bytes", "max_file_bytes"):
        _positive_int(output[key], f"output.{key}", allow_zero=key in {"files", "bytes"})
    _lower_sha(output["inventory_sha256"], "output.inventory_sha256")
    if not isinstance(foundations, list) or not foundations:
        raise MaterializationError("foundations must be a non-empty array")
    foundation_paths: set[str] = set()
    for index, foundation in enumerate(foundations):
        if not isinstance(foundation, dict):
            raise MaterializationError(f"foundations[{index}] must be an object")
        _exact_keys(foundation, {"module", "path", "sha256", "purpose"}, f"foundations[{index}]")
        path_value = foundation["path"]
        if not isinstance(path_value, str) or not path_value.startswith("MIPStarRE/"):
            raise MaterializationError(f"foundations[{index}].path is outside MIPStarRE")
        if path_value in foundation_paths:
            raise MaterializationError(f"duplicate foundation path {path_value!r}")
        foundation_paths.add(path_value)
        _lower_sha(foundation["sha256"], f"foundations[{index}].sha256")
        for key in ("module", "purpose"):
            if not isinstance(foundation[key], str) or not foundation[key]:
                raise MaterializationError(f"foundations[{index}].{key} must be non-empty")
    return value


def _assert_real_directory(path: Path) -> None:
    try:
        metadata = path.stat(follow_symlinks=False)
    except OSError as error:
        raise MaterializationError(f"required directory is unavailable: {path}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise MaterializationError(f"required path is not a real directory: {path}")


def _reject_symlink_components(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        except OSError as error:
            raise MaterializationError(f"could not inspect path component {current}") from error
        if stat.S_ISLNK(mode):
            raise MaterializationError(f"path contains a symlink component: {current}")


def _read_regular_exact(path: Path, expected_bytes: int) -> bytes:
    _reject_symlink_components(path.parent)
    flags = os.O_RDONLY
    for name in ("O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, name, 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise MaterializationError(f"could not open pinned archive: {path}") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise MaterializationError("pinned archive must be a regular file")
        if before.st_size != expected_bytes:
            raise MaterializationError(
                f"pinned archive size differs: expected {expected_bytes}, got {before.st_size}"
            )
        chunks: list[bytes] = []
        total = 0
        while total <= expected_bytes:
            block = os.read(descriptor, min(1024 * 1024, expected_bytes + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
        after = os.fstat(descriptor)
        identity = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
        if identity(before) != identity(after):
            raise MaterializationError("pinned archive changed while it was read")
        if total != expected_bytes:
            raise MaterializationError(
                f"pinned archive read differs: expected {expected_bytes}, got {total}"
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _decompress_gzip_exact(compressed: bytes, expected_bytes: int) -> bytes:
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    output = bytearray()
    try:
        for start in range(0, len(compressed), 64 * 1024):
            remaining = expected_bytes + 1 - len(output)
            if remaining <= 0:
                raise MaterializationError("gzip output exceeds the pinned tar byte bound")
            output.extend(decompressor.decompress(compressed[start : start + 64 * 1024], remaining))
            if decompressor.unconsumed_tail:
                raise MaterializationError("gzip output exceeds the pinned tar byte bound")
        if len(output) > expected_bytes:
            raise MaterializationError("gzip output exceeds the pinned tar byte bound")
        output.extend(decompressor.flush(expected_bytes + 1 - len(output)))
    except zlib.error as error:
        raise MaterializationError(f"invalid or truncated gzip archive: {error}") from error
    if not decompressor.eof:
        raise MaterializationError("gzip archive ended before the compressed stream")
    if decompressor.unused_data:
        raise MaterializationError("gzip archive contains a concatenated stream or trailing bytes")
    if len(output) != expected_bytes:
        raise MaterializationError(
            f"tar byte count differs: expected {expected_bytes}, got {len(output)}"
        )
    return bytes(output)


def _octal(field: bytes, label: str) -> int:
    stripped = field.rstrip(b"\0 ").lstrip(b" ")
    if not stripped:
        return 0
    if any(character not in b"01234567" for character in stripped):
        raise MaterializationError(f"tar {label} is not canonical octal")
    return int(stripped, 8)


def _string_field(field: bytes, label: str) -> str:
    raw, separator, padding = field.partition(b"\0")
    if separator and any(padding):
        raise MaterializationError(f"tar {label} has nonzero bytes after NUL")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MaterializationError(f"tar {label} is not UTF-8") from error


def _pax_records(payload: bytes) -> dict[str, str]:
    records: dict[str, str] = {}
    offset = 0
    while offset < len(payload):
        space = payload.find(b" ", offset)
        if space < 0 or not payload[offset:space].isdigit():
            raise MaterializationError("global PAX record has an invalid length")
        length = int(payload[offset:space])
        record = payload[offset : offset + length]
        if length <= space - offset + 2 or len(record) != length or not record.endswith(b"\n"):
            raise MaterializationError("global PAX record length does not match its bytes")
        key_value = record[space - offset + 1 : -1]
        key, separator, value = key_value.partition(b"=")
        if not separator:
            raise MaterializationError("global PAX record lacks '='")
        try:
            decoded_key = key.decode("ascii")
            decoded_value = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise MaterializationError("global PAX record is not valid text") from error
        if decoded_key in records:
            raise MaterializationError(f"duplicate global PAX key {decoded_key!r}")
        records[decoded_key] = decoded_value
        offset += length
    return records


def _safe_member_path(name: str, exact_prefix: str, *, directory: bool) -> str:
    if "\\" in name or name.startswith("/"):
        raise MaterializationError(f"unsafe tar member path {name!r}")
    if directory and not name.endswith("/"):
        raise MaterializationError(f"tar directory lacks a trailing slash: {name!r}")
    normalized_name = name[:-1] if directory else name
    root = exact_prefix[:-1]
    if normalized_name == root:
        relative = ""
    elif normalized_name.startswith(exact_prefix):
        relative = normalized_name[len(exact_prefix) :]
    else:
        raise MaterializationError(f"tar member is outside exact prefix {exact_prefix!r}: {name!r}")
    parts = relative.split("/") if relative else []
    if relative and any(part in {"", ".", ".."} for part in parts):
        raise MaterializationError(f"unsafe normalized tar path {relative!r}")
    return "/".join(parts)


def _inventory_digest(
    directories: Sequence[str], files: Sequence[tuple[str, bytes]]
) -> str:
    digest = hashlib.sha256()
    for relative in sorted(directories):
        digest.update(f"d\0MIPStarRE{('/' + relative) if relative else ''}\n".encode("utf-8"))
    for relative, payload in sorted(files):
        path = f"MIPStarRE/{relative}"
        digest.update(
            f"f\0{path}\0{len(payload)}\0{hashlib.sha256(payload).hexdigest()}\n".encode("utf-8")
        )
    return digest.hexdigest()


def inspect_archive_bytes(
    compressed: bytes,
    *,
    commit: str,
    exact_prefix: str,
    archive_subtree: str = "MIPStarRE/",
    reserved_authored_subtree: str = "QPBT/",
    expected_tar_bytes: int,
) -> tuple[dict[str, Any], list[str], list[tuple[str, bytes]]]:
    if len(compressed) > HARD_MAX_ARCHIVE_BYTES:
        raise MaterializationError("compressed archive exceeds the hard byte bound")
    tar_bytes = _decompress_gzip_exact(compressed, expected_tar_bytes)
    if len(tar_bytes) > HARD_MAX_TAR_BYTES:
        raise MaterializationError("tar archive exceeds the hard byte bound")
    offset = 0
    members = 0
    regular_files = 0
    directories = 0
    regular_bytes = 0
    max_member_bytes = 0
    seen: set[str] = set()
    global_pax_seen = False
    output_directories: list[str] = []
    output_files: list[tuple[str, bytes]] = []
    while offset + BLOCK <= len(tar_bytes):
        header = tar_bytes[offset : offset + BLOCK]
        if header == bytes(BLOCK):
            if tar_bytes[offset + BLOCK : offset + 2 * BLOCK] != bytes(BLOCK):
                raise MaterializationError("tar archive lacks the second end marker")
            if any(tar_bytes[offset + 2 * BLOCK :]):
                raise MaterializationError("tar archive has nonzero bytes after its end markers")
            break
        stored_checksum = _octal(header[148:156], "checksum")
        checksum_header = header[:148] + b" " * 8 + header[156:]
        if sum(checksum_header) != stored_checksum:
            raise MaterializationError("tar header checksum mismatch")
        if header[257:263] != b"ustar\0" or header[263:265] != b"00":
            raise MaterializationError("tar member is not canonical POSIX ustar")
        name = _string_field(header[:100], "name")
        prefix = _string_field(header[345:500], "prefix")
        if prefix:
            name = f"{prefix}/{name}"
        link_name = _string_field(header[157:257], "link name")
        size = _octal(header[124:136], "size")
        type_flag = header[156:157]
        payload_start = offset + BLOCK
        payload_end = payload_start + size
        padded_end = payload_start + ((size + BLOCK - 1) // BLOCK) * BLOCK
        if payload_end > len(tar_bytes) or padded_end > len(tar_bytes):
            raise MaterializationError("tar member payload is truncated")
        payload = tar_bytes[payload_start:payload_end]
        if any(tar_bytes[payload_end:padded_end]):
            raise MaterializationError("tar member padding is nonzero")
        offset = padded_end
        if size > HARD_MAX_MEMBER_BYTES:
            raise MaterializationError("tar member exceeds the hard size bound")
        if type_flag == b"g":
            if global_pax_seen or members or name != "pax_global_header":
                raise MaterializationError("global PAX header must occur exactly once before members")
            if _pax_records(payload) != {"comment": commit}:
                raise MaterializationError("global PAX header differs from the exact commit comment")
            global_pax_seen = True
            continue
        if type_flag not in {b"0", b"5"}:
            raise MaterializationError(
                f"tar type {type_flag!r} is forbidden (links, devices, local PAX, and GNU extensions)"
            )
        if link_name:
            raise MaterializationError("regular/directory tar member has a link target")
        directory = type_flag == b"5"
        if directory and size:
            raise MaterializationError("tar directory has a nonzero payload")
        relative = _safe_member_path(name, exact_prefix, directory=directory)
        if relative in seen:
            raise MaterializationError(f"duplicate tar member path {relative!r}")
        seen.add(relative)
        members += 1
        if members > HARD_MAX_MEMBERS:
            raise MaterializationError("tar member count exceeds the hard bound")
        if directory:
            directories += 1
        else:
            regular_files += 1
            regular_bytes += size
            max_member_bytes = max(max_member_bytes, size)
            if regular_bytes > HARD_MAX_REGULAR_BYTES:
                raise MaterializationError("tar regular bytes exceed the hard bound")
        if relative == archive_subtree[:-1] and directory:
            output_directories.append("")
        elif relative.startswith(archive_subtree):
            output_relative = relative[len(archive_subtree) :]
            if output_relative == reserved_authored_subtree[:-1] or output_relative.startswith(
                reserved_authored_subtree
            ):
                raise MaterializationError("upstream archive occupies the project-authored QPBT namespace")
            if directory:
                output_directories.append(output_relative)
            else:
                output_files.append((output_relative, payload))
    else:
        raise MaterializationError("tar archive has no complete end markers")
    if not global_pax_seen:
        raise MaterializationError("tar archive lacks the exact global provenance header")
    output_bytes = sum(len(payload) for _, payload in output_files)
    facts = {
        "archive": {
            "sha256": hashlib.sha256(compressed).hexdigest(),
            "bytes": len(compressed),
            "tar_sha256": hashlib.sha256(tar_bytes).hexdigest(),
            "tar_bytes": len(tar_bytes),
            "members": members,
            "regular_files": regular_files,
            "directories": directories,
            "regular_bytes": regular_bytes,
            "max_member_bytes": max_member_bytes,
        },
        "output": {
            "directories": len(output_directories),
            "files": len(output_files),
            "bytes": output_bytes,
            "max_file_bytes": max((len(payload) for _, payload in output_files), default=0),
            "inventory_sha256": _inventory_digest(output_directories, output_files),
        },
    }
    return facts, output_directories, output_files


def _compare_facts(pin: Mapping[str, Any], facts: Mapping[str, Any]) -> None:
    for section in ("archive", "output"):
        for key, observed in facts[section].items():
            expected = pin[section][key]
            if observed != expected:
                raise MaterializationError(
                    f"{section}.{key} differs: expected {expected!r}, got {observed!r}"
                )


def inspect_archive(path: Path, pin: Mapping[str, Any]) -> tuple[dict[str, Any], list[str], list[tuple[str, bytes]]]:
    compressed = _read_regular_exact(path, pin["archive"]["bytes"])
    facts, directories, files = inspect_archive_bytes(
        compressed,
        commit=pin["source"]["commit"],
        exact_prefix=pin["archive"]["exact_prefix"],
        archive_subtree=pin["output"]["archive_subtree"],
        reserved_authored_subtree=pin["output"]["reserved_authored_subtree"],
        expected_tar_bytes=pin["archive"]["tar_bytes"],
    )
    _compare_facts(pin, facts)
    foundation_hashes = {f"MIPStarRE/{relative}": hashlib.sha256(payload).hexdigest() for relative, payload in files}
    for foundation in pin["foundations"]:
        if foundation_hashes.get(foundation["path"]) != foundation["sha256"]:
            raise MaterializationError(f"foundation pin differs for {foundation['path']}")
    return facts, directories, files


def _read_output_file(path: Path, max_bytes: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise MaterializationError(f"could not safely open materialized file: {path}") from error
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > max_bytes
        ):
            raise MaterializationError(f"unsafe or oversized materialized file: {path}")
        chunks: list[bytes] = []
        total = 0
        while total <= max_bytes:
            block = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink
        ):
            raise MaterializationError(f"materialized file changed while read: {path}")
        if total != before.st_size:
            raise MaterializationError(f"materialized file size changed while read: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _scan_authored_tree(root: Path) -> tuple[int, int, str]:
    if not root.exists() and not root.is_symlink():
        return 0, 0, hashlib.sha256().hexdigest()
    metadata = root.stat(follow_symlinks=False)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise MaterializationError("project-authored QPBT path must be a real directory")
    records: list[tuple[str, bytes]] = []
    for directory, names, file_names in os.walk(root, followlinks=False):
        base = Path(directory)
        names.sort()
        file_names.sort()
        for name in names:
            path = base / name
            mode = path.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise MaterializationError(f"unsafe project-authored directory: {path}")
        for name in file_names:
            path = base / name
            records.append((path.relative_to(root).as_posix(), _read_output_file(path, HARD_MAX_MEMBER_BYTES)))
    digest = hashlib.sha256()
    for relative, payload in records:
        digest.update(f"{relative}\0{len(payload)}\0{hashlib.sha256(payload).hexdigest()}\n".encode())
    return len(records), sum(len(payload) for _, payload in records), digest.hexdigest()


def verify_materialized(repo_root: Path, pin: Mapping[str, Any]) -> dict[str, Any]:
    destination = repo_root / pin["output"]["path"]
    try:
        metadata = destination.stat(follow_symlinks=False)
    except OSError as error:
        raise MaterializationError("materialized MIPStarRE root is unavailable") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise MaterializationError("materialized MIPStarRE root is not a real directory")
    directories: list[str] = [""]
    files: list[tuple[str, bytes]] = []
    authored = destination / pin["output"]["reserved_authored_subtree"][:-1]
    authored_facts = _scan_authored_tree(authored)
    for directory, names, file_names in os.walk(destination, topdown=True, followlinks=False):
        base = Path(directory)
        relative_base = base.relative_to(destination).as_posix()
        names.sort()
        file_names.sort()
        retained: list[str] = []
        for name in names:
            path = base / name
            mode = path.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise MaterializationError(f"unsafe materialized directory: {path}")
            if base == destination and path == authored:
                continue
            retained.append(name)
            directories.append(path.relative_to(destination).as_posix())
        names[:] = retained
        if relative_base == pin["output"]["reserved_authored_subtree"][:-1]:
            continue
        for name in file_names:
            path = base / name
            files.append(
                (path.relative_to(destination).as_posix(), _read_output_file(path, pin["output"]["max_file_bytes"]))
            )
    observed = {
        "directories": len(directories),
        "files": len(files),
        "bytes": sum(len(payload) for _, payload in files),
        "max_file_bytes": max((len(payload) for _, payload in files), default=0),
        "inventory_sha256": _inventory_digest(directories, files),
    }
    for key, value in observed.items():
        if value != pin["output"][key]:
            raise MaterializationError(
                f"materialized output {key} differs: expected {pin['output'][key]!r}, got {value!r}"
            )
    foundation_hashes = {f"MIPStarRE/{relative}": hashlib.sha256(payload).hexdigest() for relative, payload in files}
    for foundation in pin["foundations"]:
        if foundation_hashes.get(foundation["path"]) != foundation["sha256"]:
            raise MaterializationError(f"materialized foundation differs: {foundation['path']}")
    return {
        "status": "verified",
        **observed,
        "authored_qpbt_files": authored_facts[0],
        "authored_qpbt_bytes": authored_facts[1],
        "authored_qpbt_sha256": authored_facts[2],
    }


def _child_name(name: str, label: str) -> str:
    encoded = os.fsencode(name)
    if not encoded or encoded in {b".", b".."} or b"/" in encoded or b"\0" in encoded:
        raise MaterializationError(f"unsafe {label} child name")
    return name


def _open_bound_directory(parent_descriptor: int, name: str, label: str) -> int:
    name = _child_name(name, label)
    monitor = _BoundNameMonitor(parent_descriptor, (name,))
    descriptor: int | None = None
    try:
        monitor.assert_clean()
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_descriptor)
        _assert_bound_name(parent_descriptor, name, descriptor, label)
        monitor.assert_clean()
        return descriptor
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    finally:
        monitor.close()


class _OutputBinding:
    def __init__(
        self,
        parent_descriptor: int,
        name: str,
        descriptor: int,
        parent_monitor: _BoundNameMonitor,
        self_monitor: _BoundNameMonitor,
        label: str,
    ) -> None:
        self.parent_descriptor = parent_descriptor
        self.name = name
        self.descriptor = descriptor
        self.parent_monitor = parent_monitor
        self.self_monitor = self_monitor
        self.label = label

    def assert_current(self) -> None:
        self.self_monitor.assert_clean()
        self.parent_monitor.assert_clean()
        _assert_bound_name(
            self.parent_descriptor, self.name, self.descriptor, self.label
        )

    def close(self) -> None:
        self.self_monitor.close()


class _DetachedOutputFile:
    def __init__(
        self,
        parent_descriptor: int,
        name: str,
        descriptor: int,
        parent_monitor: _BoundNameMonitor,
        label: str,
    ) -> None:
        self.parent_descriptor = parent_descriptor
        self.name = name
        self.descriptor = descriptor
        self.parent_monitor = parent_monitor
        self.label = label
        self.self_monitor: _BoundNameMonitor | None = None

    def accept_payload_change(self, operation: int) -> None:
        inode_name = f"#{os.fstat(self.descriptor).st_ino}"
        self.parent_monitor.accept_owned_change(((inode_name, operation),))

    def assert_detached(self) -> None:
        self.parent_monitor.assert_clean()
        metadata = os.fstat(self.descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 0:
            raise MaterializationError(f"{self.label} lost its zero-link inode")
        _assert_name_absent(self.parent_descriptor, self.name, self.label)

    def publish(self) -> None:
        self.assert_detached()
        try:
            _linux_link_unnamed_file(self.descriptor, self.parent_descriptor, self.name)
        except OSError as error:
            raise MaterializationError(f"could not publish {self.label}: {error}") from error
        self.parent_monitor.accept_owned_change(((self.name, _IN_CREATE),))
        self.self_monitor = _BoundNameMonitor(self.descriptor, None)
        self.assert_current()

    def assert_current(self) -> None:
        if self.self_monitor is None:
            raise MaterializationError(f"{self.label} has not been published")
        self.self_monitor.assert_clean()
        self.parent_monitor.assert_clean()
        _assert_bound_name(
            self.parent_descriptor, self.name, self.descriptor, self.label
        )
        if os.fstat(self.descriptor).st_nlink != 1:
            raise MaterializationError(f"{self.label} is not single-link at validation")

    def close(self) -> None:
        if self.self_monitor is not None:
            self.self_monitor.close()


def _create_detached_output_file(
    parent_descriptor: int,
    name: str,
    label: str,
    parent_monitor: _BoundNameMonitor,
) -> _DetachedOutputFile:
    """Create a zero-link inode for population before this program publishes it."""

    name = _child_name(name, label)
    parent_monitor.assert_clean()
    try:
        descriptor = os.open(
            ".",
            os.O_TMPFILE | os.O_RDWR | getattr(os, "O_CLOEXEC", 0),
            0o644,
            dir_fd=parent_descriptor,
        )
    except (AttributeError, OSError) as error:
        raise MaterializationError("safe materialization requires O_TMPFILE") from error
    detached = _DetachedOutputFile(
        parent_descriptor, name, descriptor, parent_monitor, label
    )
    try:
        detached.assert_detached()
    except BaseException:
        os.close(descriptor)
        raise
    return detached


def _create_continuous_directory(
    parent_descriptor: int,
    name: str,
    label: str,
    parent_monitor: _BoundNameMonitor,
) -> _OutputBinding:
    """Create a directory whose own move watch precedes the parent handoff."""

    name = _child_name(name, label)
    parent_monitor.assert_clean()
    os.mkdir(name, 0o700, dir_fd=parent_descriptor)
    descriptor: int | None = None
    try:
        parent_monitor.accept_owned_change(((name, _IN_CREATE),))
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_descriptor)
        self_monitor = _BoundNameMonitor(descriptor, ())
        try:
            _assert_bound_name(parent_descriptor, name, descriptor, label)
            self_monitor.assert_clean()
            parent_monitor.assert_clean()
        except BaseException:
            self_monitor.close()
            raise
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    return _OutputBinding(
        parent_descriptor,
        name,
        descriptor,
        parent_monitor,
        self_monitor,
        label,
    )


def _create_continuous_file(
    parent_descriptor: int,
    name: str,
    label: str,
    parent_monitor: _BoundNameMonitor,
) -> _OutputBinding:
    """Create a file whose own move watch precedes the parent handoff."""

    name = _child_name(name, label)
    parent_monitor.assert_clean()
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o644,
        dir_fd=parent_descriptor,
    )
    try:
        parent_monitor.accept_owned_change(((name, _IN_CREATE),))
        self_monitor = _BoundNameMonitor(descriptor, ())
        try:
            _assert_bound_name(parent_descriptor, name, descriptor, label)
            self_monitor.assert_clean()
            parent_monitor.assert_clean()
        except BaseException:
            self_monitor.close()
            raise
    except BaseException:
        os.close(descriptor)
        raise
    return _OutputBinding(
        parent_descriptor,
        name,
        descriptor,
        parent_monitor,
        self_monitor,
        label,
    )


def _create_bound_directory(parent_descriptor: int, name: str, label: str) -> int:
    name = _child_name(name, label)
    monitor = _BoundNameMonitor(parent_descriptor, (name,))
    descriptor: int | None = None
    try:
        monitor.assert_clean()
        os.mkdir(name, 0o700, dir_fd=parent_descriptor)
        monitor.accept_owned_change(((name, _IN_CREATE),))
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_descriptor)
        _assert_bound_name(parent_descriptor, name, descriptor, label)
        monitor.assert_clean()
        return descriptor
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    finally:
        monitor.close()


def _create_new_file(
    parent_descriptor: int,
    name: str,
    payload: bytes,
    *,
    readable: bool = False,
    monitor: _BoundNameMonitor | None = None,
) -> int:
    name = _child_name(name, "materialized file")
    descriptor = os.open(
        name,
        (os.O_RDWR if readable else os.O_WRONLY) | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o644,
        dir_fd=parent_descriptor,
    )
    try:
        if monitor is not None:
            monitor.accept_owned_change(((name, _IN_CREATE),))
            _assert_bound_name(
                parent_descriptor,
                name,
                descriptor,
                "new materialized control file",
            )
            monitor.assert_clean()
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise MaterializationError("new materialized output is not a regular file")
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short materialized file write")
            view = view[written:]
        os.fsync(descriptor)
        if monitor is not None and payload:
            monitor.accept_owned_change(((name, _IN_MODIFY),))
            _assert_bound_name(
                parent_descriptor,
                name,
                descriptor,
                "new materialized control file",
            )
            monitor.assert_clean()
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _write_new_file(parent_descriptor: int, name: str, payload: bytes) -> None:
    descriptor = _create_new_file(parent_descriptor, name, payload)
    os.close(descriptor)


def _read_bound_file(parent_descriptor: int, name: str, max_bytes: int) -> bytes:
    name = _child_name(name, "authored file")
    monitor = _BoundNameMonitor(parent_descriptor, (name,))
    descriptor: int | None = None
    try:
        monitor.assert_clean()
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
            dir_fd=parent_descriptor,
        )
        _assert_bound_name(parent_descriptor, name, descriptor, "project-authored file")
        monitor.assert_clean()
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            raise MaterializationError("unsafe or oversized project-authored file")
        chunks: list[bytes] = []
        total = 0
        while total <= max_bytes:
            block = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
        after = os.fstat(descriptor)
        monitor.assert_clean()
        _assert_bound_name(parent_descriptor, name, descriptor, "project-authored file")
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ) or total != before.st_size:
            raise MaterializationError("project-authored file changed while copied")
        return b"".join(chunks)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        monitor.close()


def _snapshot_bound_tree(
    root_descriptor: int,
) -> tuple[list[str], list[tuple[str, bytes]], list[_BoundNameMonitor]]:
    directories: list[str] = []
    files: list[tuple[str, bytes]] = []
    monitors: list[_BoundNameMonitor] = []

    def visit(descriptor: int, relative: PurePosixPath) -> None:
        monitor = _BoundNameMonitor(descriptor, None)
        monitors.append(monitor)
        monitor.assert_clean()
        names = sorted(os.listdir(descriptor))
        for name in names:
            monitor.assert_clean()
            _child_name(name, "project-authored tree")
            try:
                metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except OSError as error:
                raise MaterializationError("project-authored tree changed while copied") from error
            child_relative = relative / name
            if stat.S_ISDIR(metadata.st_mode):
                child = _open_bound_directory(
                    descriptor, name, "project-authored directory"
                )
                monitor.assert_clean()
                directories.append(child_relative.as_posix())
                try:
                    visit(child, child_relative)
                finally:
                    os.close(child)
            elif stat.S_ISREG(metadata.st_mode):
                files.append(
                    (
                        child_relative.as_posix(),
                        _read_bound_file(descriptor, name, HARD_MAX_MEMBER_BYTES),
                    )
                )
            else:
                raise MaterializationError("unsafe project-authored tree entry")
        monitor.assert_clean()
        if sorted(os.listdir(descriptor)) != names:
            raise MaterializationError("project-authored directory changed while copied")
        monitor.assert_clean()

    try:
        visit(root_descriptor, PurePosixPath())
    except BaseException:
        for monitor in reversed(monitors):
            monitor.close()
        raise
    return directories, files, monitors


def _populate_bound_tree(
    root_descriptor: int,
    directories: Sequence[str],
    files: Sequence[tuple[str, bytes]],
    *,
    root_binding: _OutputBinding | None = None,
) -> None:
    required_directories: set[str] = set()
    for relative in (*directories, *(name for name, _ in files)):
        path = PurePosixPath(relative)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise MaterializationError("unsafe materialized output path")
        limit = len(path.parts) if relative in directories else len(path.parts) - 1
        for depth in range(1, limit + 1):
            required_directories.add(PurePosixPath(*path.parts[:depth]).as_posix())

    descriptors: dict[str, int] = {"": os.dup(root_descriptor)}
    content_monitors: dict[str, _BoundNameMonitor] = {
        "": _BoundNameMonitor(root_descriptor, None)
    }
    bindings: dict[str, _OutputBinding] = {}

    def assert_continuity() -> None:
        if root_binding is not None:
            root_binding.assert_current()
        for relative in sorted(bindings, key=lambda value: (value.count("/"), value)):
            bindings[relative].assert_current()
        for relative in sorted(
            content_monitors, key=lambda value: (value.count("/"), value)
        ):
            content_monitors[relative].assert_clean()

    try:
        assert_continuity()
        for relative in sorted(
            required_directories, key=lambda value: (value.count("/"), value)
        ):
            path = PurePosixPath(relative)
            parent = path.parent.as_posix()
            if parent == ".":
                parent = ""
            assert_continuity()
            binding = _create_continuous_directory(
                descriptors[parent],
                path.name,
                f"materialized directory {relative}",
                content_monitors[parent],
            )
            bindings[relative] = binding
            descriptors[relative] = binding.descriptor
            content_monitors[relative] = _BoundNameMonitor(binding.descriptor, None)
            assert_continuity()
        for relative, payload in sorted(files):
            path = PurePosixPath(relative)
            parent = path.parent.as_posix()
            if parent == ".":
                parent = ""
            assert_continuity()
            binding = _create_detached_output_file(
                descriptors[parent],
                path.name,
                f"materialized file {relative}",
                content_monitors[parent],
            )
            try:
                binding.assert_detached()
                assert_continuity()
                view = memoryview(payload)
                while view:
                    binding.assert_detached()
                    assert_continuity()
                    written = os.write(binding.descriptor, view)
                    if written <= 0:
                        raise OSError("short materialized file write")
                    view = view[written:]
                    binding.accept_payload_change(_IN_MODIFY)
                    binding.assert_detached()
                    assert_continuity()
                os.fsync(binding.descriptor)
                binding.assert_detached()
                binding.publish()
                binding.assert_current()
                assert_continuity()
            finally:
                binding.close()
                os.close(binding.descriptor)
        for relative in sorted(
            descriptors, key=lambda value: (value.count("/"), value), reverse=True
        ):
            assert_continuity()
            os.fsync(descriptors[relative])
        assert_continuity()
    finally:
        for monitor in reversed(tuple(content_monitors.values())):
            monitor.close()
        for binding in reversed(tuple(bindings.values())):
            binding.close()
        for descriptor in reversed(tuple(descriptors.values())):
            os.close(descriptor)


def _copy_authored_tree(
    source_root_descriptor: int, destination_root_descriptor: int
) -> tuple[int, int, str]:
    source_name_monitor = _BoundNameMonitor(source_root_descriptor, ("QPBT",))
    source_descriptor: int | None = None
    source_monitors: list[_BoundNameMonitor] = []
    destination_parent_monitor: _BoundNameMonitor | None = None
    destination_binding: _OutputBinding | None = None
    try:
        source_name_monitor.assert_clean()
        try:
            source_descriptor = os.open(
                "QPBT", _directory_flags(), dir_fd=source_root_descriptor
            )
        except FileNotFoundError:
            source_name_monitor.assert_clean()
            return 0, 0, hashlib.sha256().hexdigest()
        _assert_bound_name(
            source_root_descriptor,
            "QPBT",
            source_descriptor,
            "project-authored QPBT directory",
        )
        source_name_monitor.assert_clean()
        directories, files, source_monitors = _snapshot_bound_tree(source_descriptor)
        destination_parent_monitor = _BoundNameMonitor(
            destination_root_descriptor, ("QPBT",)
        )
        destination_binding = _create_continuous_directory(
            destination_root_descriptor,
            "QPBT",
            "staged project-authored QPBT directory",
            destination_parent_monitor,
        )
        destination_descriptor = destination_binding.descriptor
        try:
            destination_binding.assert_current()
            _populate_bound_tree(
                destination_descriptor,
                directories,
                files,
                root_binding=destination_binding,
            )
            destination_binding.assert_current()
            os.fsync(destination_descriptor)
        finally:
            destination_binding.close()
            destination_binding = None
            os.close(destination_descriptor)
            destination_parent_monitor.close()
            destination_parent_monitor = None
        for monitor in source_monitors:
            monitor.assert_clean()
        source_name_monitor.assert_clean()
        _assert_bound_name(
            source_root_descriptor,
            "QPBT",
            source_descriptor,
            "project-authored QPBT directory",
        )
    finally:
        for monitor in reversed(source_monitors):
            monitor.close()
        if destination_binding is not None:
            destination_binding.close()
            os.close(destination_binding.descriptor)
        if destination_parent_monitor is not None:
            destination_parent_monitor.close()
        if source_descriptor is not None:
            os.close(source_descriptor)
        source_name_monitor.close()
    digest = hashlib.sha256()
    for relative, payload in sorted(files):
        digest.update(
            f"{relative}\0{len(payload)}\0{hashlib.sha256(payload).hexdigest()}\n".encode()
        )
    return len(files), sum(len(payload) for _, payload in files), digest.hexdigest()


def _cleanup_tombstone(transaction: Path) -> Path:
    return transaction.with_name(f"{transaction.name}.cleanup")


def _finish_cleanup(cleanup: Path) -> None:
    if cleanup.exists() or cleanup.is_symlink():
        raise MaterializationError(
            f"cleanup state has no continuous live binding and was preserved: {cleanup}"
        )


def _commit_cleanup(transaction: Path) -> None:
    raise MaterializationError(
        f"legacy pathname cleanup is disabled; transaction preserved: {transaction}"
    )


def _rollback(transaction: Path, destination: Path, original_present: bool) -> list[str]:
    return [
        "legacy pathname rollback is disabled; live rollback requires held descriptors "
        f"(transaction preserved: {transaction}, destination: {destination}, "
        f"original_present: {original_present})"
    ]


def _transaction_document(destination: Path, original_present: bool) -> bytes:
    return (
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "destination": str(destination.resolve()),
                "original_present": original_present,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("ascii")


def _descriptor_evidence_identity(descriptor: int) -> dict[str, int]:
    metadata = os.fstat(descriptor)
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "type": stat.S_IFMT(metadata.st_mode),
    }


def _descriptor_tree_inventory(
    root_descriptor: int, label: str, *, require_single_link: bool = False
) -> dict[str, Any]:
    """Return a monitored descriptor-relative recursive traversal record."""

    content_digest = hashlib.sha256()
    identity_digest = hashlib.sha256()
    files = 0
    directories = 0
    symlinks = 0
    total_bytes = 0

    def add_content(kind: str, relative: str, payload: str = "") -> None:
        content_digest.update(kind.encode("ascii"))
        content_digest.update(b"\0")
        content_digest.update(relative.encode("utf-8"))
        content_digest.update(b"\0")
        content_digest.update(payload.encode("utf-8"))
        content_digest.update(b"\n")

    def add_identity(kind: str, relative: str, metadata: os.stat_result) -> None:
        identity_digest.update(
            (
                f"{kind}\0{relative}\0{metadata.st_dev}:{metadata.st_ino}:"
                f"{stat.S_IFMT(metadata.st_mode)}:{stat.S_IMODE(metadata.st_mode)}:"
                f"{metadata.st_nlink}:{metadata.st_size}\n"
            ).encode("utf-8")
        )

    def visit(directory_descriptor: int, relative: PurePosixPath) -> None:
        nonlocal files, directories, symlinks, total_bytes
        monitor = _BoundNameMonitor(directory_descriptor, None)
        try:
            monitor.assert_clean()
            names = sorted(os.listdir(directory_descriptor))
            for name in names:
                _child_name(name, label)
                monitor.assert_clean()
                before = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
                child_relative = (relative / name).as_posix()
                if stat.S_ISDIR(before.st_mode):
                    child = os.open(name, _directory_flags(), dir_fd=directory_descriptor)
                    try:
                        _assert_bound_name(
                            directory_descriptor, name, child, f"{label} directory {child_relative}"
                        )
                        monitor.assert_clean()
                        add_content("directory", child_relative)
                        add_identity("directory", child_relative, before)
                        directories += 1
                        visit(child, relative / name)
                        after = os.fstat(child)
                        if (
                            after.st_dev,
                            after.st_ino,
                            stat.S_IFMT(after.st_mode),
                            stat.S_IMODE(after.st_mode),
                            after.st_nlink,
                            after.st_size,
                        ) != (
                            before.st_dev,
                            before.st_ino,
                            stat.S_IFMT(before.st_mode),
                            stat.S_IMODE(before.st_mode),
                            before.st_nlink,
                            before.st_size,
                        ):
                            raise MaterializationError(
                                f"{label} directory changed while inventoried"
                            )
                        _assert_bound_name(
                            directory_descriptor, name, child, f"{label} directory {child_relative}"
                        )
                    finally:
                        os.close(child)
                elif stat.S_ISREG(before.st_mode):
                    if require_single_link and before.st_nlink != 1:
                        raise MaterializationError(
                            f"{label} file is not single-link at traversal"
                        )
                    child = os.open(
                        name,
                        os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
                        dir_fd=directory_descriptor,
                    )
                    child_monitor: _BoundNameMonitor | None = None
                    try:
                        _assert_bound_name(
                            directory_descriptor, name, child, f"{label} file {child_relative}"
                        )
                        child_monitor = _BoundNameMonitor(child, ())
                        child_monitor.assert_clean()
                        monitor.assert_clean()
                        file_digest = hashlib.sha256()
                        read_bytes = 0
                        while True:
                            block = os.read(child, 1024 * 1024)
                            if not block:
                                break
                            file_digest.update(block)
                            read_bytes += len(block)
                            child_monitor.assert_clean()
                            monitor.assert_clean()
                        after = os.fstat(child)
                        if (
                            after.st_dev,
                            after.st_ino,
                            stat.S_IFMT(after.st_mode),
                            stat.S_IMODE(after.st_mode),
                            after.st_nlink,
                            after.st_size,
                        ) != (
                            before.st_dev,
                            before.st_ino,
                            stat.S_IFMT(before.st_mode),
                            stat.S_IMODE(before.st_mode),
                            before.st_nlink,
                            before.st_size,
                        ) or read_bytes != before.st_size or (
                            require_single_link and after.st_nlink != 1
                        ):
                            raise MaterializationError(f"{label} file changed while inventoried")
                        add_content(
                            "file", child_relative, f"{read_bytes}:{file_digest.hexdigest()}"
                        )
                        add_identity("file", child_relative, before)
                        files += 1
                        total_bytes += read_bytes
                    finally:
                        if child_monitor is not None:
                            child_monitor.close()
                        os.close(child)
                elif stat.S_ISLNK(before.st_mode):
                    link_target = os.readlink(name, dir_fd=directory_descriptor)
                    after = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
                    monitor.assert_clean()
                    if (
                        after.st_dev,
                        after.st_ino,
                        stat.S_IFMT(after.st_mode),
                        stat.S_IMODE(after.st_mode),
                        after.st_nlink,
                        after.st_size,
                    ) != (
                        before.st_dev,
                        before.st_ino,
                        stat.S_IFMT(before.st_mode),
                        stat.S_IMODE(before.st_mode),
                        before.st_nlink,
                        before.st_size,
                    ):
                        raise MaterializationError(f"{label} symlink changed while inventoried")
                    add_content("symlink", child_relative, link_target)
                    add_identity("symlink", child_relative, before)
                    symlinks += 1
                else:
                    raise MaterializationError(f"{label} contains an unsupported entry type")
            monitor.assert_clean()
            if sorted(os.listdir(directory_descriptor)) != names:
                raise MaterializationError(f"{label} directory changed while inventoried")
            monitor.assert_clean()
        finally:
            monitor.close()

    root = os.fstat(root_descriptor)
    if not stat.S_ISDIR(root.st_mode):
        raise MaterializationError(f"{label} root is not a directory")
    visit(root_descriptor, PurePosixPath())
    return {
        "schema_version": 1,
        "sha256": content_digest.hexdigest(),
        "identity_sha256": identity_digest.hexdigest(),
        "files": files,
        "directories": directories,
        "symlinks": symlinks,
        "bytes": total_bytes,
    }


def _descriptor_tree_identity(descriptor: int, label: str) -> dict[str, Any]:
    return {
        **_descriptor_evidence_identity(descriptor),
        "inventory": _descriptor_tree_inventory(descriptor, label),
    }


def _retained_transaction_inventory(
    transaction_descriptor: int,
    transaction_document_descriptor: int,
    transaction_document: bytes,
    stage_descriptor: int,
    backup_descriptor: int,
    original_descriptor: int | None,
    original_identity: dict[str, Any] | None,
) -> dict[str, Any]:
    document = {
        **_descriptor_evidence_identity(transaction_document_descriptor),
        "size": len(transaction_document),
        "sha256": hashlib.sha256(transaction_document).hexdigest(),
    }
    stage_names = sorted(os.listdir(stage_descriptor))
    backup_names = sorted(os.listdir(backup_descriptor))
    if backup_names:
        raise MaterializationError("retained materialization backup is not empty")
    if original_descriptor is not None:
        if original_identity is None:
            raise MaterializationError("retained original output lacks its pre-exchange identity")
        stage_destination = _descriptor_tree_identity(
            original_descriptor, "retained original MIPStarRE output"
        )
        if stage_destination != original_identity:
            raise MaterializationError(
                "retained original MIPStarRE output identity or recursive inventory changed"
            )
    else:
        stage_destination = None
    return {
        "schema_version": 1,
        "transaction_entries": sorted(os.listdir(transaction_descriptor)),
        "transaction_document": document,
        "stage": {
            **_descriptor_evidence_identity(stage_descriptor),
            "entries": stage_names,
        },
        "backup": {
            **_descriptor_evidence_identity(backup_descriptor),
            "entries": backup_names,
        },
        "stage_destination": stage_destination,
    }


def _recover(transaction: Path, destination: Path, pin: Mapping[str, Any]) -> None:
    if transaction.exists() or transaction.is_symlink():
        raise MaterializationError(
            f"persisted materialization state has no live authority and was preserved: {transaction}"
        )


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise MaterializationError(f"could not safely open materialization lock: {path}") from error
    with os.fdopen(descriptor, "a+", encoding="utf-8") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise MaterializationError(f"materialization lock is not a regular file: {path}")
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def validate_project_pins(repo_root: Path, pin: Mapping[str, Any]) -> None:
    try:
        toolchain = (repo_root / "lean-toolchain").read_text(encoding="ascii").strip()
        manifest = json.loads((repo_root / "lake-manifest.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MaterializationError(f"could not validate authored Lean pins: {error}") from error
    if toolchain != pin["lean_pins"]["toolchain"]:
        raise MaterializationError("lean-toolchain differs from the upstream factual pin")
    packages = manifest.get("packages") if isinstance(manifest, dict) else None
    mathlib = next(
        (package for package in packages or [] if isinstance(package, dict) and package.get("name") == "mathlib"),
        None,
    )
    if (
        mathlib is None
        or mathlib.get("inputRev") != pin["lean_pins"]["mathlib_input_revision"]
        or mathlib.get("rev") != pin["lean_pins"]["mathlib_commit"]
    ):
        raise MaterializationError("lake-manifest mathlib pin differs from provenance")


def materialize(
    repo_root: Path,
    pin_path: Path,
    archive_path: Path,
    *,
    replace_existing: bool = False,
) -> dict[str, Any]:
    with _monitor_authority():
        return _materialize(
            repo_root,
            pin_path,
            archive_path,
            replace_existing=replace_existing,
        )


def _materialize(
    repo_root: Path,
    pin_path: Path,
    archive_path: Path,
    *,
    replace_existing: bool = False,
) -> dict[str, Any]:
    started = time.monotonic()
    repo_root = Path(os.path.abspath(repo_root))
    _assert_real_directory(repo_root)
    expected_pin = repo_root / "references" / "mipstarre-upstream.json"
    if Path(os.path.abspath(pin_path)) != expected_pin:
        raise MaterializationError("pin path must be repository-local references/mipstarre-upstream.json")
    pin = load_pin(pin_path)
    validate_project_pins(repo_root, pin)
    destination = repo_root / pin["output"]["path"]
    facts, directories, files = inspect_archive(archive_path, pin)
    token = secrets.token_hex(16)
    transaction_name = "MIPStarRE.transaction"
    preparation_name = "MIPStarRE.transaction.preparing"
    cleanup_name = "MIPStarRE.transaction.cleanup"
    retained_name = f"MIPStarRE.transaction.retained-{token}"
    failed_name = f"MIPStarRE.transaction.failed-{token}"

    root_descriptor = os.open(repo_root, _directory_flags())
    root_monitor: _BoundNameMonitor | None = None
    workflow_descriptor: int | None = None
    workflow_monitor: _BoundNameMonitor | None = None
    runtime_descriptor: int | None = None
    runtime_monitor: _BoundNameMonitor | None = None
    transaction_descriptor: int | None = None
    transaction_monitor: _BoundNameMonitor | None = None
    transaction_document_descriptor: int | None = None
    transaction_document: bytes | None = None
    stage_descriptor: int | None = None
    backup_descriptor: int | None = None
    backup_monitor: _BoundNameMonitor | None = None
    stage_monitor: _BoundNameMonitor | None = None
    candidate_descriptor: int | None = None
    original_descriptor: int | None = None
    original_identity: dict[str, Any] | None = None
    candidate_inventory: dict[str, Any] | None = None
    published = False
    original_present = False
    transaction_current_name: str | None = None

    def assert_transaction_current(name: str) -> None:
        assert runtime_descriptor is not None
        assert runtime_monitor is not None
        assert transaction_descriptor is not None
        runtime_monitor.assert_clean()
        _assert_bound_name(
            runtime_descriptor, name, transaction_descriptor, "materialization transaction"
        )

    def retire_transaction(name: str, destination_name: str) -> None:
        nonlocal transaction_current_name
        assert runtime_descriptor is not None
        assert runtime_monitor is not None
        assert transaction_descriptor is not None
        if transaction_current_name != name:
            raise MaterializationError("materialization transaction state is ambiguous")
        assert_transaction_current(name)

        def mark_retired() -> None:
            nonlocal transaction_current_name
            transaction_current_name = destination_name

        _atomic_move_bound(
            runtime_descriptor,
            name,
            transaction_descriptor,
            runtime_descriptor,
            destination_name,
            "materialization transaction retention",
            mark_retired,
        )
        runtime_monitor.accept_owned_change(
            ((name, _IN_MOVED_FROM), (destination_name, _IN_MOVED_TO))
        )
        if transaction_monitor is not None:
            transaction_monitor.accept_owned_change((("", _IN_MOVE_SELF),))
        os.fsync(runtime_descriptor)
        runtime_monitor.assert_clean()
        _assert_bound_name(
            runtime_descriptor,
            destination_name,
            transaction_descriptor,
            "retained materialization transaction",
        )

    def assert_retained_transaction_contents() -> None:
        assert runtime_descriptor is not None
        assert runtime_monitor is not None
        assert transaction_descriptor is not None
        assert transaction_monitor is not None
        assert transaction_document_descriptor is not None
        assert transaction_document is not None
        assert stage_descriptor is not None
        assert backup_descriptor is not None
        assert backup_monitor is not None
        assert stage_monitor is not None
        assert transaction_current_name is not None
        runtime_monitor.assert_clean()
        _assert_bound_name(
            runtime_descriptor,
            transaction_current_name,
            transaction_descriptor,
            "retained materialization transaction",
        )
        transaction_monitor.assert_clean()
        if set(os.listdir(transaction_descriptor)) != {"transaction.json", "stage", "backup"}:
            raise MaterializationError("retained materialization transaction contents changed")
        _assert_bound_name(
            transaction_descriptor,
            "transaction.json",
            transaction_document_descriptor,
            "retained materialization transaction document",
        )
        document_stat = os.fstat(transaction_document_descriptor)
        if (
            not stat.S_ISREG(document_stat.st_mode)
            or document_stat.st_size != len(transaction_document)
            or os.pread(transaction_document_descriptor, len(transaction_document) + 1, 0)
            != transaction_document
        ):
            raise MaterializationError("retained materialization transaction document changed")
        _assert_bound_name(
            transaction_descriptor, "stage", stage_descriptor, "retained materialization stage"
        )
        _assert_bound_name(
            transaction_descriptor, "backup", backup_descriptor, "retained materialization backup"
        )
        backup_monitor.assert_clean()
        if os.listdir(backup_descriptor):
            raise MaterializationError("retained materialization backup is not empty")
        stage_monitor.assert_clean()
        expected_stage_names = {destination.name} if original_present else set()
        if set(os.listdir(stage_descriptor)) != expected_stage_names:
            raise MaterializationError("retained materialization stage contents changed")
        if original_present:
            assert original_descriptor is not None
            _assert_bound_name(
                stage_descriptor,
                destination.name,
                original_descriptor,
                "retained original MIPStarRE output",
            )
            if original_identity is None or _descriptor_tree_identity(
                original_descriptor, "retained original MIPStarRE output"
            ) != original_identity:
                raise MaterializationError(
                    "retained original MIPStarRE output identity or recursive inventory changed"
                )
        else:
            _assert_name_absent(
                stage_descriptor,
                destination.name,
                "retained MIPStarRE stage slot",
            )
        transaction_monitor.assert_clean()
        stage_monitor.assert_clean()
        backup_monitor.assert_clean()

    def mark_published() -> None:
        nonlocal published
        published = True

    try:
        _require_transaction_capabilities(root_descriptor)
        root_monitor = _BoundNameMonitor(root_descriptor, (".workflow-runtime", destination.name))
        workflow_descriptor = _bind_or_create_directory(
            root_descriptor, ".workflow-runtime", root_monitor
        )
        workflow_monitor = _BoundNameMonitor(
            workflow_descriptor, ("mipstarre-materialization",)
        )
        runtime_descriptor = _bind_or_create_directory(
            workflow_descriptor, "mipstarre-materialization", workflow_monitor
        )
        if os.fstat(root_descriptor).st_dev != os.fstat(runtime_descriptor).st_dev:
            raise MaterializationError("runtime and destination must share one filesystem")
        runtime_monitor = _BoundNameMonitor(
            runtime_descriptor,
            (
                "MIPStarRE.lock",
                transaction_name,
                preparation_name,
                cleanup_name,
                retained_name,
                failed_name,
            ),
        )
        with _locked_at(runtime_descriptor, "MIPStarRE.lock", runtime_monitor):
            for stale_name in (transaction_name, preparation_name, cleanup_name):
                try:
                    os.stat(stale_name, dir_fd=runtime_descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                raise MaterializationError(
                    f"persisted materialization state has no live authority and was preserved: "
                    f"{repo_root / '.workflow-runtime' / 'mipstarre-materialization' / stale_name}"
                )

            root_monitor.assert_clean()
            try:
                original_descriptor = os.open(
                    destination.name, _directory_flags(), dir_fd=root_descriptor
                )
            except FileNotFoundError:
                original_present = False
            else:
                original_present = True
                _assert_bound_name(
                    root_descriptor,
                    destination.name,
                    original_descriptor,
                    "existing MIPStarRE output",
                )
                root_monitor.assert_clean()
                original_identity = _descriptor_tree_identity(
                    original_descriptor, "existing MIPStarRE output"
                )
                root_monitor.assert_clean()
                _assert_bound_name(
                    root_descriptor,
                    destination.name,
                    original_descriptor,
                    "existing MIPStarRE output",
                )
                try:
                    evidence = verify_materialized(
                        Path("/proc/self/fd") / str(root_descriptor), pin
                    )
                except (OSError, MaterializationError) as error:
                    root_monitor.assert_clean()
                    _assert_bound_name(
                        root_descriptor,
                        destination.name,
                        original_descriptor,
                        "existing MIPStarRE output",
                    )
                    if not replace_existing:
                        raise MaterializationError(
                            "invalid existing MIPStarRE output was preserved"
                        ) from error
                else:
                    root_monitor.assert_clean()
                    evidence.update(
                        {
                            "status": "cached",
                            "elapsed_seconds": round(time.monotonic() - started, 6),
                        }
                    )
                    return evidence

            try:
                os.mkdir(transaction_name, 0o700, dir_fd=runtime_descriptor)
            except FileExistsError as error:
                raise MaterializationError(
                    "materialization preparation appeared concurrently"
                ) from error
            runtime_monitor.accept_owned_change(((transaction_name, _IN_CREATE),))
            transaction_descriptor = os.open(
                transaction_name, _directory_flags(), dir_fd=runtime_descriptor
            )
            _assert_bound_name(
                runtime_descriptor,
                transaction_name,
                transaction_descriptor,
                "materialization preparation",
            )
            runtime_monitor.assert_clean()
            transaction_current_name = transaction_name
            transaction_monitor = _BoundNameMonitor(transaction_descriptor, None)
            try:
                transaction_document = _transaction_document(destination, original_present)
                transaction_document_descriptor = _create_new_file(
                    transaction_descriptor,
                    "transaction.json",
                    transaction_document,
                    readable=True,
                    monitor=transaction_monitor,
                )
                stage_descriptor = _bind_or_create_directory(
                    transaction_descriptor, "stage", transaction_monitor
                )
                backup_descriptor = _bind_or_create_directory(
                    transaction_descriptor, "backup", transaction_monitor
                )
                backup_monitor = _BoundNameMonitor(backup_descriptor, None)
                backup_monitor.assert_clean()
                if os.listdir(backup_descriptor):
                    raise MaterializationError("materialization backup must start empty")
                backup_monitor.assert_clean()
                os.fsync(backup_descriptor)
                stage_monitor = _BoundNameMonitor(stage_descriptor, None)
                try:
                    os.mkdir(destination.name, 0o700, dir_fd=stage_descriptor)
                except FileExistsError as error:
                    raise MaterializationError("staged foundation appeared concurrently") from error
                stage_monitor.accept_owned_change(((destination.name, _IN_CREATE),))
                candidate_descriptor = os.open(
                    destination.name, _directory_flags(), dir_fd=stage_descriptor
                )
                _assert_bound_name(
                    stage_descriptor,
                    destination.name,
                    candidate_descriptor,
                    "staged MIPStarRE output",
                )
                stage_monitor.assert_clean()
                _populate_bound_tree(candidate_descriptor, directories, files)
                if original_present:
                    assert original_descriptor is not None
                    _copy_authored_tree(original_descriptor, candidate_descriptor)
                os.fsync(candidate_descriptor)
                os.fsync(stage_descriptor)
                os.fsync(transaction_descriptor)
                os.fsync(runtime_descriptor)
                candidate_inventory = _descriptor_tree_inventory(
                    candidate_descriptor,
                    "staged MIPStarRE output",
                    require_single_link=True,
                )
                assert_transaction_current(transaction_name)
            except BaseException as error:
                try:
                    retire_transaction(transaction_name, failed_name)
                except BaseException as retention_error:
                    raise MaterializationError(
                        "could not prepare transaction; ambiguous state was preserved"
                    ) from retention_error
                raise MaterializationError("could not prepare materialization transaction") from error

            try:
                assert stage_descriptor is not None
                assert stage_monitor is not None
                assert candidate_descriptor is not None
                assert_transaction_current(transaction_name)
                transaction_monitor.assert_clean()
                stage_monitor.assert_clean()
                root_monitor.assert_clean()
                assert candidate_inventory is not None
                if _descriptor_tree_inventory(
                    candidate_descriptor,
                    "staged MIPStarRE output",
                    require_single_link=True,
                ) != candidate_inventory:
                    raise MaterializationError(
                        "staged MIPStarRE output changed before publication"
                    )
                if original_present:
                    assert original_descriptor is not None
                    assert original_identity is not None
                    if _descriptor_tree_identity(
                        original_descriptor, "existing MIPStarRE output"
                    ) != original_identity:
                        raise MaterializationError(
                            "existing MIPStarRE output identity or recursive inventory changed"
                        )
                    root_monitor.assert_clean()
                    _atomic_exchange_bound(
                        stage_descriptor,
                        destination.name,
                        candidate_descriptor,
                        root_descriptor,
                        destination.name,
                        original_descriptor,
                        "MIPStarRE foundation publication",
                        mark_published,
                    )
                    stage_monitor.accept_owned_change(
                        (
                            (destination.name, _IN_MOVED_FROM),
                            (destination.name, _IN_MOVED_TO),
                        )
                    )
                    root_monitor.accept_owned_change(
                        (
                            (destination.name, _IN_MOVED_FROM),
                            (destination.name, _IN_MOVED_TO),
                        )
                    )
                    if _descriptor_tree_identity(
                        original_descriptor, "displaced original MIPStarRE output"
                    ) != original_identity:
                        raise MaterializationError(
                            "displaced original MIPStarRE output identity or recursive inventory changed"
                        )
                else:
                    _atomic_move_bound(
                        stage_descriptor,
                        destination.name,
                        candidate_descriptor,
                        root_descriptor,
                        destination.name,
                        "MIPStarRE foundation publication",
                        mark_published,
                    )
                    stage_monitor.accept_owned_change(
                        ((destination.name, _IN_MOVED_FROM),)
                    )
                    root_monitor.accept_owned_change(
                        ((destination.name, _IN_MOVED_TO),)
                    )
                os.fsync(root_descriptor)
                verified = verify_materialized(Path("/proc/self/fd") / str(root_descriptor), pin)
                if _descriptor_tree_inventory(
                    candidate_descriptor,
                    "published MIPStarRE output",
                    require_single_link=True,
                ) != candidate_inventory:
                    raise MaterializationError(
                        "published MIPStarRE output changed during verification"
                    )
                root_monitor.assert_clean()
                retire_transaction(transaction_name, retained_name)
                root_monitor.assert_clean()
                _assert_bound_name(
                    root_descriptor,
                    destination.name,
                    candidate_descriptor,
                    "published MIPStarRE output",
                )
                assert_retained_transaction_contents()
                transaction_evidence_identity = _descriptor_evidence_identity(
                    transaction_descriptor
                )
                transaction_evidence_inventory = _retained_transaction_inventory(
                    transaction_descriptor,
                    transaction_document_descriptor,
                    transaction_document,
                    stage_descriptor,
                    backup_descriptor,
                    original_descriptor if original_present else None,
                    original_identity,
                )
                assert_retained_transaction_contents()
                verified.update(
                    {
                        "status": "published",
                        "archive_sha256": facts["archive"]["sha256"],
                        "source_commit": pin["source"]["commit"],
                        "transaction_evidence": str(
                            repo_root
                            / ".workflow-runtime"
                            / "mipstarre-materialization"
                            / retained_name
                        ),
                        "transaction_evidence_identity": transaction_evidence_identity,
                        "transaction_evidence_inventory": transaction_evidence_inventory,
                        "elapsed_seconds": round(time.monotonic() - started, 6),
                    }
                )
                if _retained_transaction_inventory(
                    transaction_descriptor,
                    transaction_document_descriptor,
                    transaction_document,
                    stage_descriptor,
                    backup_descriptor,
                    original_descriptor if original_present else None,
                    original_identity,
                ) != transaction_evidence_inventory:
                    raise MaterializationError(
                        "retained materialization evidence changed after result construction"
                    )
                if _descriptor_tree_inventory(
                    candidate_descriptor,
                    "published MIPStarRE output",
                    require_single_link=True,
                ) != candidate_inventory:
                    raise MaterializationError(
                        "published MIPStarRE output changed at the final result gate"
                    )
                assert_retained_transaction_contents()
                root_monitor.assert_clean()
                _assert_bound_name(
                    root_descriptor,
                    destination.name,
                    candidate_descriptor,
                    "published MIPStarRE output",
                )
            except BaseException as error:
                rollback_errors: list[str] = []
                if published:
                    try:
                        assert stage_descriptor is not None
                        assert stage_monitor is not None
                        assert candidate_descriptor is not None
                        stage_monitor.assert_clean()
                        root_monitor.assert_clean()
                        if original_present:
                            assert original_descriptor is not None
                            _atomic_exchange_bound(
                                root_descriptor,
                                destination.name,
                                candidate_descriptor,
                                stage_descriptor,
                                destination.name,
                                original_descriptor,
                                "MIPStarRE foundation rollback",
                            )
                            root_monitor.accept_owned_change(
                                (
                                    (destination.name, _IN_MOVED_FROM),
                                    (destination.name, _IN_MOVED_TO),
                                )
                            )
                            stage_monitor.accept_owned_change(
                                (
                                    (destination.name, _IN_MOVED_FROM),
                                    (destination.name, _IN_MOVED_TO),
                                )
                            )
                        else:
                            assert transaction_monitor is not None
                            transaction_monitor.assert_clean()
                            _atomic_move_bound(
                                root_descriptor,
                                destination.name,
                                candidate_descriptor,
                                transaction_descriptor,
                                "incomplete-MIPStarRE",
                                "failed MIPStarRE foundation retention",
                            )
                            root_monitor.accept_owned_change(
                                ((destination.name, _IN_MOVED_FROM),)
                            )
                            transaction_monitor.accept_owned_change(
                                (("incomplete-MIPStarRE", _IN_MOVED_TO),)
                            )
                        published = False
                        os.fsync(root_descriptor)
                    except BaseException as rollback_error:
                        rollback_errors.append(str(rollback_error))
                if not rollback_errors:
                    try:
                        assert transaction_current_name is not None
                        retire_transaction(transaction_current_name, failed_name)
                    except BaseException as retention_error:
                        rollback_errors.append(str(retention_error))
                if rollback_errors:
                    raise MaterializationError(
                        "publication failed and rollback is incomplete; all ambiguous objects were "
                        "preserved: " + "; ".join(rollback_errors)
                    ) from error
                raise

            return verified
    finally:
        for monitor in (
            stage_monitor,
            backup_monitor,
            transaction_monitor,
            runtime_monitor,
            workflow_monitor,
            root_monitor,
        ):
            if monitor is not None:
                try:
                    monitor.close()
                except OSError:
                    pass
        for descriptor in (
            candidate_descriptor,
            stage_descriptor,
            transaction_descriptor,
            backup_descriptor,
            transaction_document_descriptor,
            original_descriptor,
            runtime_descriptor,
            workflow_descriptor,
            root_descriptor,
        ):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass


def build_parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(root))
    parser.add_argument("--pin", default="references/mipstarre-upstream.json")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="verify the exact archive without publication")
    materialize_parser = commands.add_parser("materialize", help="publish the ignored local foundation")
    for command in (inspect, materialize_parser):
        archive = command.add_mutually_exclusive_group(required=True)
        archive.add_argument("--archive")
        archive.add_argument("--archive-env")
    materialize_parser.add_argument("--replace-existing", action="store_true")
    commands.add_parser("verify", help="verify the existing ignored foundation")
    return parser


def _archive_argument(arguments: argparse.Namespace) -> Path:
    if arguments.archive:
        return Path(arguments.archive)
    value = os.environ.get(arguments.archive_env)
    if not value:
        raise MaterializationError(
            f"archive environment variable {arguments.archive_env!r} is unset or empty"
        )
    return Path(value)


def run_cli(arguments: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(arguments.repo_root).resolve()
    pin_path = Path(arguments.pin)
    if not pin_path.is_absolute():
        pin_path = repo_root / pin_path
    expected_pin = repo_root / "references" / "mipstarre-upstream.json"
    if Path(os.path.abspath(pin_path)) != expected_pin:
        raise MaterializationError("pin path must be repository-local references/mipstarre-upstream.json")
    pin = load_pin(pin_path)
    validate_project_pins(repo_root, pin)
    if arguments.command == "verify":
        return verify_materialized(repo_root, pin)
    archive_path = _archive_argument(arguments)
    if arguments.command == "inspect":
        facts, _, _ = inspect_archive(archive_path, pin)
        return {"status": "verified", "source_commit": pin["source"]["commit"], **facts}
    return materialize(
        repo_root,
        pin_path,
        archive_path,
        replace_existing=arguments.replace_existing,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run_cli(build_parser().parse_args(argv))
    except (MaterializationError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
