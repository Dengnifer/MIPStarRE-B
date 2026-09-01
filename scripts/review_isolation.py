#!/usr/bin/env python3
"""Capability checks for production external-review process isolation.

The probe is deliberately independent of Codex and the network.  It proves an
actual filesystem denial in a disposable child, and treats missing descendant
network isolation as a production blocker rather than an advisory warning.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence


ISOLATION_SCHEMA_VERSION = 1
POLICY_ID = "landlock-read-v1+private-net-v1+clearenv-v1"

_PR_SET_NO_NEW_PRIVS = 38
_LANDLOCK_CREATE_RULESET_VERSION = 1
_LANDLOCK_RULE_PATH_BENEATH = 1
_LANDLOCK_ACCESS_FS_EXECUTE = 1 << 0
_LANDLOCK_ACCESS_FS_WRITE_FILE = 1 << 1
_LANDLOCK_ACCESS_FS_READ_FILE = 1 << 2
_LANDLOCK_ACCESS_FS_READ_DIR = 1 << 3
_LANDLOCK_ACCESS_FS_REMOVE_DIR = 1 << 4
_LANDLOCK_ACCESS_FS_REMOVE_FILE = 1 << 5
_LANDLOCK_ACCESS_FS_MAKE_CHAR = 1 << 6
_LANDLOCK_ACCESS_FS_MAKE_DIR = 1 << 7
_LANDLOCK_ACCESS_FS_MAKE_REG = 1 << 8
_LANDLOCK_ACCESS_FS_MAKE_SOCK = 1 << 9
_LANDLOCK_ACCESS_FS_MAKE_FIFO = 1 << 10
_LANDLOCK_ACCESS_FS_MAKE_BLOCK = 1 << 11
_LANDLOCK_ACCESS_FS_MAKE_SYM = 1 << 12
_LANDLOCK_ACCESS_FS_REFER = 1 << 13
_LANDLOCK_ABI1_ACCESS = (1 << 13) - 1
_LANDLOCK_READ_ACCESS = (
    _LANDLOCK_ACCESS_FS_EXECUTE
    | _LANDLOCK_ACCESS_FS_READ_FILE
    | _LANDLOCK_ACCESS_FS_READ_DIR
)
POLICY_DOCUMENT = {
    "policy_id": POLICY_ID,
    "landlock_abi_minimum": 1,
    "handled_access_fs": _LANDLOCK_ABI1_ACCESS,
    "projection_allowed_access_fs": _LANDLOCK_READ_ACCESS,
    "no_new_privs": True,
    "descendant_private_network_required": True,
    "environment": "exact-clearenv",
}
POLICY_SHA256 = hashlib.sha256(
    json.dumps(POLICY_DOCUMENT, sort_keys=True, separators=(",", ":")).encode("ascii")
).hexdigest()


class IsolationError(RuntimeError):
    """Raised when an isolation policy is malformed or unavailable."""


class _RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class _PathBeneathAttr(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]


def _syscall_numbers() -> tuple[int, int, int]:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return 444, 445, 446
    if machine in {"aarch64", "arm64"}:
        return 444, 445, 446
    raise IsolationError(f"Landlock syscall numbers are not pinned for architecture {machine!r}")


def _landlock_abi() -> int:
    create_ruleset, _, _ = _syscall_numbers()
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(
        create_ruleset, ctypes.c_void_p(), ctypes.c_size_t(0), _LANDLOCK_CREATE_RULESET_VERSION
    )
    return int(result)


def restrict_reads_to(root: Path) -> None:
    """Irreversibly restrict this process and descendants to reading ``root``.

    Call only in a disposable child after the interpreter and its libraries are
    loaded.  Landlock's deny-by-default rules apply to every later descendant.
    """

    root = root.resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise IsolationError("review projection must be a real directory")
    if _landlock_abi() < 1:
        raise IsolationError("Landlock ABI 1 is unavailable")
    create_ruleset, add_rule, restrict_self = _syscall_numbers()
    libc = ctypes.CDLL(None, use_errno=True)
    ruleset_attr = _RulesetAttr(_LANDLOCK_ABI1_ACCESS)
    ruleset_fd = libc.syscall(
        create_ruleset,
        ctypes.byref(ruleset_attr),
        ctypes.sizeof(ruleset_attr),
        0,
    )
    if ruleset_fd < 0:
        raise IsolationError(f"could not create Landlock ruleset: errno {ctypes.get_errno()}")
    root_fd = -1
    try:
        root_fd = os.open(root, os.O_PATH | os.O_CLOEXEC)
        path_attr = _PathBeneathAttr(_LANDLOCK_READ_ACCESS, root_fd)
        if libc.syscall(
            add_rule,
            ruleset_fd,
            _LANDLOCK_RULE_PATH_BENEATH,
            ctypes.byref(path_attr),
            0,
        ) < 0:
            raise IsolationError(f"could not add Landlock projection rule: errno {ctypes.get_errno()}")
        if libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0:
            raise IsolationError(f"could not set no_new_privs: errno {ctypes.get_errno()}")
        if libc.syscall(restrict_self, ruleset_fd, 0) < 0:
            raise IsolationError(f"could not enforce Landlock ruleset: errno {ctypes.get_errno()}")
    finally:
        if root_fd >= 0:
            os.close(root_fd)
        os.close(ruleset_fd)


def _probe_child(projection: Path, sentinel: Path) -> int:
    expected = (projection / "allowed.txt").read_bytes()
    restrict_reads_to(projection)
    if (projection / "allowed.txt").read_bytes() != expected:
        return 3
    try:
        sentinel.read_bytes()
    except PermissionError:
        return 0
    except OSError as error:
        return 0 if error.errno in {errno.EACCES, errno.EPERM} else 4
    return 5


def _network_namespace_probe() -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["unshare", "--net", "--", "true"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=5,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, type(error).__name__
    return completed.returncode == 0, hashlib.sha256(completed.stderr.encode()).hexdigest()


def probe_production_isolation() -> dict[str, Any]:
    """Return non-secret evidence for the complete production boundary."""

    with tempfile.TemporaryDirectory(prefix="review-isolation-probe-") as temporary:
        root = Path(temporary)
        projection = root / "projection"
        projection.mkdir()
        (projection / "allowed.txt").write_bytes(b"authorized projection\n")
        sentinel = root / "unmanifested-host-sentinel"
        sentinel.write_bytes(b"must not be readable\n")
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--probe-child", str(projection), str(sentinel)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=10,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
        )
    filesystem_enforced = completed.returncode == 0
    network_enforced, network_evidence = _network_namespace_probe()
    environment = minimal_reviewer_environment()
    sensitive_environment_names = {
        name for name in environment
        if any(marker in name.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))
    }
    return {
        "schema_version": ISOLATION_SCHEMA_VERSION,
        "policy_id": POLICY_ID,
        "policy_sha256": POLICY_SHA256,
        "filesystem_enforced": filesystem_enforced,
        "sentinel_denied": filesystem_enforced,
        "environment_mode": "exact-clearenv",
        "minimal_environment_credential_names_present": bool(sensitive_environment_names),
        "descendant_network_egress_denied": network_enforced,
        "available": filesystem_enforced and network_enforced,
        "filesystem_probe_returncode": completed.returncode,
        "filesystem_probe_stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "network_probe_evidence": network_evidence,
    }


def require_production_isolation(capability: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version", "policy_id", "policy_sha256", "filesystem_enforced",
        "sentinel_denied", "environment_mode", "minimal_environment_credential_names_present",
        "descendant_network_egress_denied", "available", "filesystem_probe_returncode",
        "filesystem_probe_stderr_sha256", "network_probe_evidence",
    }
    if set(capability) != expected:
        raise IsolationError("production isolation capability has an invalid schema")
    if capability.get("schema_version") != ISOLATION_SCHEMA_VERSION:
        raise IsolationError("production isolation capability version is unsupported")
    if capability.get("policy_id") != POLICY_ID or capability.get("policy_sha256") != POLICY_SHA256:
        raise IsolationError("production isolation capability policy does not match")
    required = (
        capability.get("filesystem_enforced") is True,
        capability.get("sentinel_denied") is True,
        capability.get("environment_mode") == "exact-clearenv",
        capability.get("minimal_environment_credential_names_present") is False,
        capability.get("descendant_network_egress_denied") is True,
        capability.get("available") is True,
    )
    if not all(required):
        raise IsolationError("enforceable production review isolation is unavailable")
    return dict(capability)


def minimal_reviewer_environment() -> dict[str, str]:
    """Environment visible to reviewer-directed descendants; no credentials."""

    return {
        "HOME": "/nonexistent",
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-child", action="store_true")
    parser.add_argument("paths", nargs="*")
    arguments = parser.parse_args(argv)
    if arguments.probe_child:
        if len(arguments.paths) != 2:
            return 2
        return _probe_child(Path(arguments.paths[0]), Path(arguments.paths[1]))
    print(json.dumps(probe_production_isolation(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
