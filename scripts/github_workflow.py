#!/usr/bin/env python3
"""Validate and read the GitHub authority for the QPBT workflow.

This module deliberately has no GitHub mutation API.  Its live preflight is a
small, GET-only boundary around ``gh``; callers inject a runner in tests.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = 1
EXPECTED_OWNER = "Dengnifer"
EXPECTED_REPOSITORY = "MIPStarRE-B"
EXPECTED_FULL_NAME = f"{EXPECTED_OWNER}/{EXPECTED_REPOSITORY}"
EXPECTED_HOST = "github.com"
EXPECTED_BASE_REF = "main"
MAX_JSON_BYTES = 4 * 1024 * 1024

ISSUE_STATUSES = frozenset(
    {
        "status:planned",
        "status:ready",
        "status:in-progress",
        "status:review",
        "status:blocked",
    }
)
PR_REVIEW_STATUSES = frozenset(
    {"review:required", "review:approved", "review:changes-requested"}
)
MIGRATION_LABEL = "migration:local-v1"

_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_NODE_ID_RE = re.compile(r"[A-Za-z0-9_+/=-]{4,}\Z")
_ISSUE_ID_RE = re.compile(r"QPBT-[0-9]{3,}\Z")
_PR_ID_RE = re.compile(r"LPR-[0-9]{3,}\Z")
_KIND_LABEL_RE = re.compile(r"kind:[a-z][a-z0-9-]*\Z")
_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
_TIMESTAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.+-]+Z\Z")
_MARKER_RE = re.compile(
    r"<!-- mipstarre-workflow:v1:(issue|pull-request):"
    r"(QPBT-[0-9]{3,}|LPR-[0-9]{3,}) -->"
)


class GitHubWorkflowError(RuntimeError):
    """A GitHub authority input failed closed."""


@dataclass(frozen=True)
class RepositoryIdentity:
    owner: str
    name: str
    database_id: int
    node_id: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True)
class IssueBinding:
    legacy_id: str
    number: int
    database_id: int
    node_id: str
    marker: str


@dataclass(frozen=True)
class PullRequestBinding:
    legacy_id: str
    number: int
    database_id: int
    node_id: str
    marker: str
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str


@dataclass(frozen=True)
class GitHubAuthority:
    config_path: Path
    manifest_path: Path
    repository: RepositoryIdentity
    base_ref: str
    cutover_main_sha: str
    issues: tuple[IssueBinding, ...]
    pull_requests: tuple[PullRequestBinding, ...]

    def issue_by_legacy_id(self, legacy_id: str) -> IssueBinding:
        matches = [item for item in self.issues if item.legacy_id == legacy_id]
        if len(matches) != 1:
            raise GitHubWorkflowError("unknown legacy issue marker")
        return matches[0]

    def issue_by_number(self, number: int) -> IssueBinding:
        matches = [item for item in self.issues if item.number == number]
        if len(matches) != 1:
            raise GitHubWorkflowError("unknown GitHub issue number")
        return matches[0]

    def optional_issue_by_number(self, number: int) -> IssueBinding | None:
        matches = [item for item in self.issues if item.number == number]
        if len(matches) > 1:
            raise GitHubWorkflowError("ambiguous GitHub issue number")
        return None if not matches else matches[0]

    def pull_request_by_legacy_id(self, legacy_id: str) -> PullRequestBinding:
        matches = [item for item in self.pull_requests if item.legacy_id == legacy_id]
        if len(matches) != 1:
            raise GitHubWorkflowError("unknown legacy pull-request marker")
        return matches[0]

    def optional_pull_request_by_number(
        self, number: int
    ) -> PullRequestBinding | None:
        matches = [item for item in self.pull_requests if item.number == number]
        if len(matches) > 1:
            raise GitHubWorkflowError("ambiguous GitHub pull-request number")
        return None if not matches else matches[0]


@dataclass(frozen=True)
class RepositorySnapshot:
    identity: RepositoryIdentity
    base_ref: str
    base_sha: str | None
    default_branch: str | None


@dataclass(frozen=True)
class IssueSnapshot:
    legacy_id: str | None
    number: int
    database_id: int
    node_id: str
    state: str
    state_reason: str | None
    status: str
    kind: str
    title: str
    labels: tuple[str, ...]
    parent_number: int | None
    parent_database_id: int | None
    parent_node_id: str | None
    parent_legacy_id: str | None
    child_numbers: tuple[int, ...]
    child_legacy_ids: tuple[str, ...]
    dependency_numbers: tuple[int, ...]
    dependency_legacy_ids: tuple[str, ...]


@dataclass(frozen=True)
class PullRequestSnapshot:
    legacy_id: str | None
    number: int
    database_id: int
    node_id: str
    state: str
    review_label: str | None
    title: str
    labels: tuple[str, ...]
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    review_comment: ReviewCommentSnapshot | None


@dataclass(frozen=True)
class ReviewCommentExpectation:
    comment_database_id: int
    comment_node_id: str
    body_sha256: str
    reviewer_session_name: str
    reviewer_external_id: str
    verdict: str
    disallowed_session_names: tuple[str, ...]
    disallowed_external_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReviewCommentSnapshot:
    comment_database_id: int
    comment_node_id: str
    body_sha256: str
    reviewer_session_name: str
    reviewer_external_id: str
    verdict: str


@dataclass(frozen=True)
class PullRequestExpectation:
    number: int
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    review_comment: ReviewCommentExpectation | None = None


@dataclass(frozen=True)
class PreflightSnapshot:
    repository: RepositorySnapshot
    cutover_main_sha: str
    issues: tuple[IssueSnapshot, ...]
    pull_requests: tuple[PullRequestSnapshot, ...]


Runner = Callable[[Sequence[str]], Any]


def issue_marker(legacy_id: str) -> str:
    """Return the stable marker used to find an imported local issue."""

    _legacy_issue_id(legacy_id, "legacy issue id")
    return f"<!-- mipstarre-workflow:v1:issue:{legacy_id} -->"


def pull_request_marker(legacy_id: str) -> str:
    """Return the stable marker used to find an imported local PR."""

    _legacy_pr_id(legacy_id, "legacy pull-request id")
    return f"<!-- mipstarre-workflow:v1:pull-request:{legacy_id} -->"


def _pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GitHubWorkflowError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(_value: str) -> None:
    raise GitHubWorkflowError("non-finite JSON number")


def _loads_json(payload: str, label: str) -> Any:
    if len(payload.encode("utf-8")) > MAX_JSON_BYTES:
        raise GitHubWorkflowError(f"{label} exceeds the JSON size limit")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_pairs_object,
            parse_constant=_reject_constant,
        )
    except GitHubWorkflowError:
        raise
    except (UnicodeError, json.JSONDecodeError) as error:
        raise GitHubWorkflowError(f"{label} is not valid JSON") from error


def _read_json(path: Path, label: str) -> Any:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise GitHubWorkflowError(f"{label} is unavailable") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise GitHubWorkflowError(f"{label} must be a regular, non-symlink file")
    if metadata.st_size > MAX_JSON_BYTES:
        raise GitHubWorkflowError(f"{label} exceeds the JSON size limit")
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise GitHubWorkflowError(
                f"{label} must be a regular, non-symlink file"
            )
        if opened.st_size > MAX_JSON_BYTES:
            raise GitHubWorkflowError(f"{label} exceeds the JSON size limit")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = None
            payload = handle.read(MAX_JSON_BYTES + 1)
        if len(payload) > MAX_JSON_BYTES:
            raise GitHubWorkflowError(f"{label} exceeds the JSON size limit")
        text = payload.decode("utf-8")
    except GitHubWorkflowError:
        raise
    except (OSError, UnicodeError) as error:
        raise GitHubWorkflowError(f"{label} cannot be read as UTF-8") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return _loads_json(text, label)


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise GitHubWorkflowError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GitHubWorkflowError(f"{label} must be an array")
    return value


def _connection_nodes(value: Any, label: str) -> list[Any]:
    """Fail closed when a live ``gh`` connection is incomplete or reshaped."""

    connection = _object(value, label)
    _exact_keys(connection, {"nodes", "totalCount"}, label)
    nodes = _list(connection["nodes"], f"{label}.nodes")
    total_count = connection["totalCount"]
    if type(total_count) is not int or total_count < 0:
        raise GitHubWorkflowError(
            f"{label}.totalCount must be a nonnegative integer"
        )
    if total_count != len(nodes):
        raise GitHubWorkflowError(f"{label} is incomplete")
    return nodes


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise GitHubWorkflowError(f"{label} has an unexpected field set")


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise GitHubWorkflowError(f"{label} must be a non-empty string")
    return value


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GitHubWorkflowError(f"{label} must be a positive integer")
    return value


def _schema(value: Any, label: str) -> None:
    if type(value) is not int or value != SCHEMA_VERSION:
        raise GitHubWorkflowError(f"{label} schema mismatch")


def _node_id(value: Any, label: str) -> str:
    result = _string(value, label)
    if _NODE_ID_RE.fullmatch(result) is None:
        raise GitHubWorkflowError(f"{label} is not a GitHub node id")
    return result


def _sha(value: Any, label: str) -> str:
    result = _string(value, label)
    if _SHA_RE.fullmatch(result) is None:
        raise GitHubWorkflowError(f"{label} must be a lowercase full commit SHA")
    return result


def _digest(value: Any, label: str) -> str:
    result = _string(value, label)
    if _DIGEST_RE.fullmatch(result) is None:
        raise GitHubWorkflowError(f"{label} must be a lowercase SHA-256 digest")
    return result


def _ref(value: Any, label: str) -> str:
    result = _string(value, label)
    forbidden = (
        _REF_RE.fullmatch(result) is None
        or ".." in result
        or "//" in result
        or "@{" in result
        or result.endswith(("/", ".", ".lock"))
    )
    if forbidden:
        raise GitHubWorkflowError(f"{label} is not a safe Git ref name")
    return result


def _legacy_issue_id(value: Any, label: str) -> str:
    result = _string(value, label)
    if _ISSUE_ID_RE.fullmatch(result) is None:
        raise GitHubWorkflowError(f"{label} is not a QPBT issue id")
    return result


def _legacy_pr_id(value: Any, label: str) -> str:
    result = _string(value, label)
    if _PR_ID_RE.fullmatch(result) is None:
        raise GitHubWorkflowError(f"{label} is not a local PR id")
    return result


def _repository_identity(value: Any, label: str) -> RepositoryIdentity:
    document = _object(value, label)
    _exact_keys(document, {"owner", "name", "database_id", "node_id"}, label)
    identity = RepositoryIdentity(
        owner=_string(document["owner"], f"{label}.owner"),
        name=_string(document["name"], f"{label}.name"),
        database_id=_positive_int(document["database_id"], f"{label}.database_id"),
        node_id=_node_id(document["node_id"], f"{label}.node_id"),
    )
    if identity.owner != EXPECTED_OWNER:
        raise GitHubWorkflowError("repository owner mismatch")
    if identity.name != EXPECTED_REPOSITORY:
        raise GitHubWorkflowError("repository name mismatch")
    return identity


def _legacy_sort_key(value: str) -> tuple[str, int]:
    prefix, sequence = value.rsplit("-", 1)
    return prefix, int(sequence)


def _require_unique(values: Sequence[Any], label: str) -> None:
    if len(values) != len(set(values)):
        raise GitHubWorkflowError(f"duplicate {label}")


def load_authority(config_path: str | Path) -> GitHubAuthority:
    """Load and cross-check the config and immutable cutover manifest offline."""

    supplied_path = Path(config_path)
    config = _object(_read_json(supplied_path, "authority config"), "authority config")
    _exact_keys(
        config,
        {"schema_version", "repository", "base_ref", "cutover_manifest"},
        "authority config",
    )
    _schema(config["schema_version"], "authority config")
    repository = _repository_identity(config["repository"], "authority repository")
    base_ref = _ref(config["base_ref"], "authority base_ref")
    if base_ref != EXPECTED_BASE_REF:
        raise GitHubWorkflowError("authority base_ref mismatch")

    manifest_setting = _string(config["cutover_manifest"], "cutover_manifest")
    manifest_path = Path(manifest_setting)
    if not manifest_path.is_absolute():
        manifest_path = supplied_path.parent / manifest_path
    manifest = _object(_read_json(manifest_path, "cutover manifest"), "cutover manifest")
    _exact_keys(
        manifest,
        {
            "schema_version",
            "repository",
            "base_ref",
            "cutover_main_sha",
            "issues",
            "pull_requests",
        },
        "cutover manifest",
    )
    _schema(manifest["schema_version"], "cutover manifest")
    manifest_repository = _repository_identity(
        manifest["repository"], "cutover repository"
    )
    if manifest_repository != repository:
        raise GitHubWorkflowError("cutover repository identity mismatch")
    manifest_base_ref = _ref(manifest["base_ref"], "cutover base_ref")
    if manifest_base_ref != base_ref:
        raise GitHubWorkflowError("cutover base_ref mismatch")
    cutover_main_sha = _sha(manifest["cutover_main_sha"], "cutover_main_sha")

    issues: list[IssueBinding] = []
    for index, raw in enumerate(_list(manifest["issues"], "cutover issues")):
        label = f"cutover issues[{index}]"
        item = _object(raw, label)
        _exact_keys(
            item,
            {"legacy_id", "number", "database_id", "node_id", "marker"},
            label,
        )
        legacy_id = _legacy_issue_id(item["legacy_id"], f"{label}.legacy_id")
        marker = _string(item["marker"], f"{label}.marker")
        if marker != issue_marker(legacy_id):
            raise GitHubWorkflowError(f"{label}.marker mismatch")
        issues.append(
            IssueBinding(
                legacy_id=legacy_id,
                number=_positive_int(item["number"], f"{label}.number"),
                database_id=_positive_int(
                    item["database_id"], f"{label}.database_id"
                ),
                node_id=_node_id(item["node_id"], f"{label}.node_id"),
                marker=marker,
            )
        )

    pull_requests: list[PullRequestBinding] = []
    for index, raw in enumerate(
        _list(manifest["pull_requests"], "cutover pull_requests")
    ):
        label = f"cutover pull_requests[{index}]"
        item = _object(raw, label)
        _exact_keys(
            item,
            {
                "legacy_id",
                "number",
                "database_id",
                "node_id",
                "marker",
                "base_ref",
                "base_sha",
                "head_ref",
                "head_sha",
            },
            label,
        )
        legacy_id = _legacy_pr_id(item["legacy_id"], f"{label}.legacy_id")
        marker = _string(item["marker"], f"{label}.marker")
        if marker != pull_request_marker(legacy_id):
            raise GitHubWorkflowError(f"{label}.marker mismatch")
        item_base_ref = _ref(item["base_ref"], f"{label}.base_ref")
        if item_base_ref != base_ref:
            raise GitHubWorkflowError(f"{label}.base_ref mismatch")
        pull_requests.append(
            PullRequestBinding(
                legacy_id=legacy_id,
                number=_positive_int(item["number"], f"{label}.number"),
                database_id=_positive_int(
                    item["database_id"], f"{label}.database_id"
                ),
                node_id=_node_id(item["node_id"], f"{label}.node_id"),
                marker=marker,
                base_ref=item_base_ref,
                base_sha=_sha(item["base_sha"], f"{label}.base_sha"),
                head_ref=_ref(item["head_ref"], f"{label}.head_ref"),
                head_sha=_sha(item["head_sha"], f"{label}.head_sha"),
            )
        )

    issue_order = [item.legacy_id for item in issues]
    pr_order = [item.legacy_id for item in pull_requests]
    if issue_order != sorted(issue_order, key=_legacy_sort_key):
        raise GitHubWorkflowError("cutover issues are not in deterministic legacy-id order")
    if pr_order != sorted(pr_order, key=_legacy_sort_key):
        raise GitHubWorkflowError(
            "cutover pull_requests are not in deterministic legacy-id order"
        )
    _require_unique(issue_order, "legacy issue id")
    _require_unique(pr_order, "legacy pull-request id")
    all_bindings: list[IssueBinding | PullRequestBinding] = [*issues, *pull_requests]
    _require_unique([item.number for item in all_bindings], "GitHub item number")
    _require_unique([item.database_id for item in all_bindings], "GitHub database id")
    _require_unique([item.node_id for item in all_bindings], "GitHub node id")

    return GitHubAuthority(
        config_path=supplied_path,
        manifest_path=manifest_path,
        repository=repository,
        base_ref=base_ref,
        cutover_main_sha=cutover_main_sha,
        issues=tuple(issues),
        pull_requests=tuple(pull_requests),
    )


def _coalesced(
    value: Mapping[str, Any], aliases: Sequence[str], label: str, *, required: bool
) -> Any:
    found = [value[name] for name in aliases if name in value]
    if not found:
        if required:
            raise GitHubWorkflowError(f"{label} is missing")
        return None
    if any(item != found[0] for item in found[1:]):
        raise GitHubWorkflowError(f"{label} aliases mismatch")
    return found[0]


def _database_id_from_fixture(value: Mapping[str, Any], label: str) -> int:
    candidates = [
        value[name]
        for name in ("database_id", "databaseId", "fullDatabaseId")
        if name in value
    ]
    if isinstance(value.get("id"), int):
        candidates.append(value["id"])
    if not candidates:
        raise GitHubWorkflowError(f"{label} is missing")
    parsed = [_positive_int(item, label) for item in candidates]
    if any(item != parsed[0] for item in parsed[1:]):
        raise GitHubWorkflowError(f"{label} aliases mismatch")
    return parsed[0]


def _node_id_from_fixture(value: Mapping[str, Any], label: str) -> str:
    candidates = [value[name] for name in ("node_id", "nodeId") if name in value]
    if isinstance(value.get("id"), str):
        candidates.append(value["id"])
    if not candidates:
        raise GitHubWorkflowError(f"{label} is missing")
    parsed = [_node_id(item, label) for item in candidates]
    if any(item != parsed[0] for item in parsed[1:]):
        raise GitHubWorkflowError(f"{label} aliases mismatch")
    return parsed[0]


def validate_repository_fixture(
    authority: GitHubAuthority,
    payload: Any,
    *,
    require_base_ref: bool = True,
    require_base_sha: bool = False,
) -> RepositorySnapshot:
    """Validate a REST/``gh --json`` repository fixture against authority."""

    value = _object(payload, "repository fixture")
    names: list[str] = []
    for key in ("full_name", "nameWithOwner"):
        if key in value:
            names.append(_string(value[key], f"repository fixture.{key}"))
    if "owner" in value and "name" in value:
        owner_value = value["owner"]
        owner = (
            _string(owner_value.get("login"), "repository fixture.owner.login")
            if isinstance(owner_value, dict)
            else _string(owner_value, "repository fixture.owner")
        )
        names.append(f"{owner}/{_string(value['name'], 'repository fixture.name')}")
    if not names or any(name != names[0] for name in names[1:]):
        raise GitHubWorkflowError("repository fixture owner/name mismatch")
    if names[0] != authority.repository.full_name:
        raise GitHubWorkflowError("repository fixture owner/name mismatch")

    database_id = _database_id_from_fixture(value, "repository fixture.database_id")
    node_id = _node_id_from_fixture(value, "repository fixture.node_id")
    if database_id != authority.repository.database_id:
        raise GitHubWorkflowError("repository fixture database_id mismatch")
    if node_id != authority.repository.node_id:
        raise GitHubWorkflowError("repository fixture node_id mismatch")

    default_branches: list[str] = []
    for key in ("default_branch", "defaultBranchRef"):
        if key not in value:
            continue
        raw_default = value[key]
        if isinstance(raw_default, dict):
            raw_default = raw_default.get("name")
        default_branches.append(_ref(raw_default, f"repository fixture.{key}"))
    if any(item != default_branches[0] for item in default_branches[1:]):
        raise GitHubWorkflowError("repository fixture default-branch aliases mismatch")
    default_branch = None if not default_branches else default_branches[0]
    if require_base_ref and "base_ref" not in value:
        raise GitHubWorkflowError("repository fixture base_ref is missing")
    base_ref = (
        authority.base_ref
        if "base_ref" not in value
        else _ref(value["base_ref"], "repository fixture base_ref")
    )
    if base_ref != authority.base_ref:
        raise GitHubWorkflowError("repository fixture base_ref mismatch")

    raw_base_sha = _coalesced(
        value,
        ("base_sha", "default_branch_sha"),
        "repository fixture base_sha",
        required=False,
    )
    base_sha = None if raw_base_sha is None else _sha(raw_base_sha, "base_sha")
    if require_base_sha and base_sha is None:
        raise GitHubWorkflowError("repository fixture base_sha is missing")
    return RepositorySnapshot(
        authority.repository, base_ref, base_sha, default_branch
    )


def _labels(value: Any, label: str) -> tuple[str, ...]:
    names: list[str] = []
    for index, raw in enumerate(_list(value, label)):
        item = _object(raw, f"{label}[{index}]")
        name = _string(item.get("name"), f"{label}[{index}].name")
        names.append(name)
    if len(names) != len(set(names)):
        raise GitHubWorkflowError(f"{label} contains duplicate names")
    return tuple(sorted(names))


def _primary_marker(body: str, expected_kind: str) -> str | None:
    matches = list(_MARKER_RE.finditer(body))
    scrubbed = _MARKER_RE.sub("", body)
    if "mipstarre-workflow:" in scrubbed:
        raise GitHubWorkflowError("body contains a malformed workflow marker")
    primary: list[str] = []
    for match in matches:
        kind, legacy_id = match.groups()
        if kind == expected_kind:
            primary.append(legacy_id)
        else:
            raise GitHubWorkflowError("body contains the wrong primary marker kind")
    if len(primary) > 1:
        raise GitHubWorkflowError("body contains duplicate primary workflow markers")
    return None if not primary else primary[0]


def _fixture_envelope(payload: Any, item_key: str) -> tuple[Mapping[str, Any], Any]:
    envelope = _object(payload, f"{item_key} fixture envelope")
    if "repository" not in envelope or item_key not in envelope:
        raise GitHubWorkflowError(
            f"{item_key} fixture must contain repository and {item_key}"
        )
    return _object(envelope["repository"], "repository fixture"), envelope[item_key]


def _state(value: Any, label: str, allowed: set[str]) -> str:
    raw = _string(value, label)
    if raw not in allowed and raw.upper() not in allowed:
        raise GitHubWorkflowError(f"{label} is not recognized")
    return raw.upper()


def _issue_state_reason(value: Mapping[str, Any]) -> str | None:
    raw = _coalesced(
        value,
        ("state_reason", "stateReason"),
        "issue fixture.state_reason",
        required=True,
    )
    if raw is None:
        return None
    reason = _string(raw, "issue fixture.state_reason").upper()
    if reason not in {"COMPLETED", "NOT_PLANNED", "REOPENED"}:
        raise GitHubWorkflowError("issue fixture.state_reason is not recognized")
    return reason


def _item_identity(
    value: Mapping[str, Any], label: str
) -> tuple[int, int, str]:
    return (
        _positive_int(value.get("number"), f"{label}.number"),
        _database_id_from_fixture(value, f"{label}.database_id"),
        _node_id_from_fixture(value, f"{label}.node_id"),
    )


def parse_issue_fixture(
    authority: GitHubAuthority,
    payload: Any,
    *,
    expected_number: int | None = None,
) -> IssueSnapshot:
    """Parse an injected, normalized issue fixture by canonical GitHub number.

    ``blockedBy`` and ``subIssues`` are bare lists here because the live
    boundary has already validated and removed their ``gh`` connection
    envelopes.
    """

    repository, raw_issue = _fixture_envelope(payload, "issue")
    validate_repository_fixture(authority, repository)
    issue = _object(raw_issue, "issue fixture")
    if "pull_request" in issue:
        raise GitHubWorkflowError("issue fixture unexpectedly describes a pull request")
    number, database_id, node_id = _item_identity(issue, "issue fixture")
    if expected_number is not None and number != _positive_int(
        expected_number, "expected issue number"
    ):
        raise GitHubWorkflowError("issue fixture number mismatch")
    title = _string(issue.get("title"), "issue fixture.title")
    body_value = issue.get("body")
    body = "" if body_value is None else _string(body_value, "issue fixture.body")
    legacy_id = _primary_marker(body, "issue")
    binding = authority.optional_issue_by_number(number)

    labels = _labels(issue.get("labels"), "issue fixture.labels")
    migration_labels = [item for item in labels if item.startswith("migration:")]
    if binding is None:
        if migration_labels or legacy_id is not None:
            raise GitHubWorkflowError(
                "unbound issue fixture carries migration provenance"
            )
    else:
        if migration_labels != [MIGRATION_LABEL] or legacy_id != binding.legacy_id:
            raise GitHubWorkflowError("issue fixture migration provenance mismatch")
        if (database_id, node_id) != (binding.database_id, binding.node_id):
            raise GitHubWorkflowError("issue fixture legacy binding mismatch")
    kind_labels = [item for item in labels if item.startswith("kind:")]
    if len(kind_labels) != 1 or _KIND_LABEL_RE.fullmatch(kind_labels[0]) is None:
        raise GitHubWorkflowError("issue fixture must have exactly one valid kind label")
    status_labels = [item for item in labels if item.startswith("status:")]
    state = _state(issue.get("state"), "issue fixture.state", {"OPEN", "CLOSED"})
    state_reason = _issue_state_reason(issue)
    if state == "OPEN":
        if state_reason not in {None, "REOPENED"}:
            raise GitHubWorkflowError("open issue fixture has a closed state reason")
        if len(status_labels) != 1 or status_labels[0] not in ISSUE_STATUSES:
            raise GitHubWorkflowError(
                "open issue fixture must have exactly one valid status label"
            )
        status = status_labels[0].removeprefix("status:")
    else:
        if state_reason not in {"COMPLETED", "NOT_PLANNED"}:
            raise GitHubWorkflowError("closed issue fixture lacks an exact close reason")
        if status_labels:
            raise GitHubWorkflowError("closed issue fixture retains an active status label")
        status = "done" if state_reason == "COMPLETED" else "not-planned"
    if any(item.startswith("review:") for item in labels):
        raise GitHubWorkflowError("issue fixture contains a pull-request review label")

    if "parent" not in issue:
        raise GitHubWorkflowError("issue fixture.parent is missing")
    raw_parent = issue["parent"]
    parent_number: int | None = None
    parent_database_id: int | None = None
    parent_node_id: str | None = None
    parent_legacy_id: str | None = None
    if raw_parent is not None:
        parent = _object(raw_parent, "issue fixture.parent")
        parent_number, parent_database_id, parent_node_id = _item_identity(
            parent, "issue fixture.parent"
        )
        if parent_number == number:
            raise GitHubWorkflowError("issue fixture is its own parent")
        parent_binding = authority.optional_issue_by_number(parent_number)
        if parent_binding is not None:
            if (parent_database_id, parent_node_id) != (
                parent_binding.database_id,
                parent_binding.node_id,
            ):
                raise GitHubWorkflowError("issue parent legacy binding mismatch")
            parent_legacy_id = parent_binding.legacy_id

    raw_children = _coalesced(
        issue,
        ("sub_issues", "subIssues"),
        "issue fixture.subIssues",
        required=True,
    )
    child_numbers: list[int] = []
    child_legacy_ids: list[str] = []
    child_closure: list[tuple[str, str | None]] = []
    for index, raw_child in enumerate(
        _list(raw_children, "issue fixture.subIssues")
    ):
        child = _object(raw_child, f"issue fixture.subIssues[{index}]")
        child_number, child_database_id, child_node_id = _item_identity(
            child, f"issue fixture.subIssues[{index}]"
        )
        if child_number == number:
            raise GitHubWorkflowError("issue fixture is its own child")
        child_binding = authority.optional_issue_by_number(child_number)
        if child_binding is not None:
            if (child_database_id, child_node_id) != (
                child_binding.database_id,
                child_binding.node_id,
            ):
                raise GitHubWorkflowError("issue child legacy binding mismatch")
            child_legacy_ids.append(child_binding.legacy_id)
        child_state = _state(
            child.get("state"),
            f"issue fixture.subIssues[{index}].state",
            {"OPEN", "CLOSED"},
        )
        child_closure.append((child_state, _issue_state_reason(child)))
        child_numbers.append(child_number)
    if len(child_numbers) != len(set(child_numbers)):
        raise GitHubWorkflowError("issue fixture has duplicate children")
    canonical_child_numbers = tuple(sorted(child_numbers))
    canonical_child_ids = tuple(sorted(child_legacy_ids, key=_legacy_sort_key))
    if kind_labels[0] == "kind:tracking" and state == "CLOSED":
        if not child_closure:
            raise GitHubWorkflowError("closed tracking issue has no native children")
        if any(
            child_state != "CLOSED" or child_reason != "COMPLETED"
            for child_state, child_reason in child_closure
        ):
            raise GitHubWorkflowError(
                "closed tracking issue has an incomplete native child"
            )

    raw_blocked_by = _coalesced(
        issue,
        ("blocked_by", "blockedBy"),
        "issue fixture.blockedBy",
        required=True,
    )
    dependency_numbers: list[int] = []
    dependency_legacy_ids: list[str] = []
    for index, raw_dependency in enumerate(
        _list(raw_blocked_by, "issue fixture.blockedBy")
    ):
        dependency = _object(raw_dependency, f"issue fixture.blockedBy[{index}]")
        (
            dependency_number,
            dependency_database_id,
            dependency_node_id,
        ) = _item_identity(
            dependency, f"issue fixture.blockedBy[{index}]"
        )
        dependency_binding = authority.optional_issue_by_number(dependency_number)
        if (
            dependency_binding is not None
            and (dependency_database_id, dependency_node_id)
            != (dependency_binding.database_id, dependency_binding.node_id)
        ):
            raise GitHubWorkflowError("issue dependency legacy identity mismatch")
        dependency_numbers.append(dependency_number)
        if dependency_binding is not None:
            dependency_legacy_ids.append(dependency_binding.legacy_id)
    if len(dependency_numbers) != len(set(dependency_numbers)):
        raise GitHubWorkflowError("issue fixture has duplicate dependencies")
    canonical_dependency_numbers = tuple(sorted(dependency_numbers))
    canonical_dependency_ids = tuple(
        sorted(dependency_legacy_ids, key=_legacy_sort_key)
    )
    if number in canonical_dependency_numbers:
        raise GitHubWorkflowError("issue fixture depends on itself")

    return IssueSnapshot(
        legacy_id=legacy_id,
        number=number,
        database_id=database_id,
        node_id=node_id,
        state=state,
        state_reason=state_reason,
        status=status,
        kind=kind_labels[0].removeprefix("kind:"),
        title=title,
        labels=labels,
        parent_number=parent_number,
        parent_database_id=parent_database_id,
        parent_node_id=parent_node_id,
        parent_legacy_id=parent_legacy_id,
        child_numbers=canonical_child_numbers,
        child_legacy_ids=canonical_child_ids,
        dependency_numbers=canonical_dependency_numbers,
        dependency_legacy_ids=canonical_dependency_ids,
    )


def _nested_pr_side(
    value: Mapping[str, Any], side: str, authority: GitHubAuthority
) -> tuple[str, str]:
    nested = value.get(side)
    if isinstance(nested, dict):
        ref = _ref(nested.get("ref"), f"pull_request fixture.{side}.ref")
        sha = _sha(nested.get("sha"), f"pull_request fixture.{side}.sha")
        if "repo" not in nested:
            raise GitHubWorkflowError(
                f"pull_request fixture.{side}.repo identity is missing"
            )
        repository = _object(nested["repo"], f"pull_request fixture.{side}.repo")
        validate_repository_fixture(authority, repository, require_base_ref=False)
        return ref, sha
    prefix = "base" if side == "base" else "head"
    ref = _ref(
        _coalesced(
            value,
            (f"{prefix}_ref", f"{prefix}RefName"),
            f"pull_request fixture.{prefix}_ref",
            required=True,
        ),
        f"pull_request fixture.{prefix}_ref",
    )
    sha = _sha(
        _coalesced(
            value,
            (f"{prefix}_sha", f"{prefix}RefOid"),
            f"pull_request fixture.{prefix}_sha",
            required=True,
        ),
        f"pull_request fixture.{prefix}_sha",
    )
    if side == "head":
        if value.get("isCrossRepository") is not False:
            raise GitHubWorkflowError(
                "flat pull_request fixture does not prove a same-repository head"
            )
        head_repository = _object(
            value.get("headRepository"), "pull_request fixture.headRepository"
        )
        head_name = _coalesced(
            head_repository,
            ("full_name", "nameWithOwner"),
            "pull_request fixture.headRepository name",
            required=True,
        )
        if head_name != authority.repository.full_name:
            raise GitHubWorkflowError("pull_request fixture head repository mismatch")
        if _node_id_from_fixture(
            head_repository, "pull_request fixture.headRepository node_id"
        ) != authority.repository.node_id:
            raise GitHubWorkflowError("pull_request fixture head repository mismatch")
    return ref, sha


def _validated_review_expectation(
    value: ReviewCommentExpectation,
) -> ReviewCommentExpectation:
    if not isinstance(value, ReviewCommentExpectation):
        raise GitHubWorkflowError("review-comment expectation has the wrong type")
    if not isinstance(value.disallowed_session_names, tuple) or not isinstance(
        value.disallowed_external_ids, tuple
    ):
        raise GitHubWorkflowError("disallowed reviewer identities must be tuples")
    if not value.disallowed_session_names or not value.disallowed_external_ids:
        raise GitHubWorkflowError(
            "review integration requires implementer/orchestrator exclusion identities"
        )
    disallowed_session_names = tuple(
        _string(item, "disallowed reviewer session name")
        for item in value.disallowed_session_names
    )
    disallowed_external_ids = tuple(
        _string(item, "disallowed reviewer external id")
        for item in value.disallowed_external_ids
    )
    _require_unique(disallowed_session_names, "disallowed reviewer session name")
    _require_unique(disallowed_external_ids, "disallowed reviewer external id")
    reviewer_session_name = _string(
        value.reviewer_session_name, "expected reviewer session name"
    )
    reviewer_external_id = _string(
        value.reviewer_external_id, "expected reviewer external id"
    )
    if reviewer_session_name in disallowed_session_names:
        raise GitHubWorkflowError("reviewer session is an implementer or orchestrator")
    if reviewer_external_id in disallowed_external_ids:
        raise GitHubWorkflowError(
            "reviewer external identity is an implementer or orchestrator"
        )
    verdict = _string(value.verdict, "expected review verdict")
    if verdict not in {"approve", "request_changes", "blocked"}:
        raise GitHubWorkflowError("expected review verdict is not recognized")
    return ReviewCommentExpectation(
        comment_database_id=_positive_int(
            value.comment_database_id, "expected review comment database_id"
        ),
        comment_node_id=_node_id(
            value.comment_node_id, "expected review comment node_id"
        ),
        body_sha256=_digest(
            value.body_sha256, "expected review comment body digest"
        ),
        reviewer_session_name=reviewer_session_name,
        reviewer_external_id=reviewer_external_id,
        verdict=verdict,
        disallowed_session_names=disallowed_session_names,
        disallowed_external_ids=disallowed_external_ids,
    )


def _validated_pr_expectation(
    authority: GitHubAuthority, value: PullRequestExpectation
) -> PullRequestExpectation:
    if not isinstance(value, PullRequestExpectation):
        raise GitHubWorkflowError("pull-request expectation has the wrong type")
    result = PullRequestExpectation(
        number=_positive_int(value.number, "expected pull-request number"),
        base_ref=_ref(value.base_ref, "expected pull-request base_ref"),
        base_sha=_sha(value.base_sha, "expected pull-request base_sha"),
        head_ref=_ref(value.head_ref, "expected pull-request head_ref"),
        head_sha=_sha(value.head_sha, "expected pull-request head_sha"),
        review_comment=(
            None
            if value.review_comment is None
            else _validated_review_expectation(value.review_comment)
        ),
    )
    if result.base_ref != authority.base_ref:
        raise GitHubWorkflowError("expected pull-request authority base mismatch")
    return result


def _binding_expectation(binding: PullRequestBinding) -> PullRequestExpectation:
    return PullRequestExpectation(
        binding.number,
        binding.base_ref,
        binding.base_sha,
        binding.head_ref,
        binding.head_sha,
    )


def _pr_expectation_identity(
    value: PullRequestExpectation,
) -> tuple[int, str, str, str, str]:
    return (
        value.number,
        value.base_ref,
        value.base_sha,
        value.head_ref,
        value.head_sha,
    )


def parse_pull_request_fixture(
    authority: GitHubAuthority,
    payload: Any,
    *,
    expected: PullRequestExpectation | None = None,
) -> PullRequestSnapshot:
    """Parse PR identity and labels; labels alone are never review authority."""

    repository, raw_pr = _fixture_envelope(payload, "pull_request")
    validate_repository_fixture(authority, repository)
    pull_request = _object(raw_pr, "pull_request fixture")
    number, database_id, node_id = _item_identity(
        pull_request, "pull_request fixture"
    )
    title = _string(pull_request.get("title"), "pull_request fixture.title")
    body_value = pull_request.get("body")
    body = "" if body_value is None else _string(body_value, "pull_request fixture.body")
    legacy_id = _primary_marker(body, "pull-request")
    binding = authority.optional_pull_request_by_number(number)
    if expected is None:
        if binding is None:
            raise GitHubWorkflowError(
                "unbound pull_request fixture requires exact base/head expectation"
            )
        expectation = _binding_expectation(binding)
    else:
        expectation = _validated_pr_expectation(authority, expected)
        if number != expectation.number:
            raise GitHubWorkflowError("pull_request fixture number mismatch")
        if binding is not None and _pr_expectation_identity(
            expectation
        ) != _pr_expectation_identity(_binding_expectation(binding)):
            raise GitHubWorkflowError(
                "pull-request expectation disagrees with cutover binding"
            )

    labels = _labels(pull_request.get("labels"), "pull_request fixture.labels")
    migration_labels = [item for item in labels if item.startswith("migration:")]
    if binding is None:
        if migration_labels or legacy_id is not None:
            raise GitHubWorkflowError(
                "unbound pull_request fixture carries migration provenance"
            )
    else:
        if migration_labels != [MIGRATION_LABEL] or legacy_id != binding.legacy_id:
            raise GitHubWorkflowError(
                "pull_request fixture migration provenance mismatch"
            )
        if (database_id, node_id) != (binding.database_id, binding.node_id):
            raise GitHubWorkflowError("pull_request fixture legacy binding mismatch")

    state = _state(
        pull_request.get("state"),
        "pull_request fixture.state",
        {"OPEN", "CLOSED", "MERGED"},
    )
    if not any(key in pull_request for key in ("merged_at", "mergedAt")):
        raise GitHubWorkflowError("pull_request fixture.merged_at is missing")
    merged_at = _coalesced(
        pull_request,
        ("merged_at", "mergedAt"),
        "pull_request fixture.merged_at",
        required=False,
    )
    if merged_at is not None and (
        not isinstance(merged_at, str) or _TIMESTAMP_RE.fullmatch(merged_at) is None
    ):
        raise GitHubWorkflowError("pull_request fixture.merged_at is malformed")
    if state == "CLOSED" and merged_at is not None:
        state = "MERGED"
    elif state == "OPEN" and merged_at is not None:
        raise GitHubWorkflowError("open pull_request fixture has merged_at")
    elif state == "MERGED" and merged_at is None:
        raise GitHubWorkflowError("merged pull_request fixture lacks merged_at")

    review_labels = [item for item in labels if item.startswith("review:")]
    if any(item not in PR_REVIEW_STATUSES for item in review_labels):
        raise GitHubWorkflowError("pull_request fixture has an invalid review label")
    if state == "OPEN" and len(review_labels) != 1:
        raise GitHubWorkflowError(
            "open pull_request fixture must have exactly one valid review label"
        )
    if state != "OPEN" and len(review_labels) > 1:
        raise GitHubWorkflowError(
            "closed pull_request fixture has conflicting review labels"
        )
    if any(item.startswith(("status:", "kind:")) for item in labels):
        raise GitHubWorkflowError("pull_request fixture contains an issue-only label")

    base_ref, base_sha = _nested_pr_side(pull_request, "base", authority)
    head_ref, head_sha = _nested_pr_side(pull_request, "head", authority)
    actual = (base_ref, base_sha, head_ref, head_sha)
    expected_refs = (
        expectation.base_ref,
        expectation.base_sha,
        expectation.head_ref,
        expectation.head_sha,
    )
    if actual != expected_refs:
        raise GitHubWorkflowError("pull_request fixture exact base/head mismatch")
    if base_ref != authority.base_ref:
        raise GitHubWorkflowError("pull_request fixture authority base mismatch")

    return PullRequestSnapshot(
        legacy_id=legacy_id,
        number=number,
        database_id=database_id,
        node_id=node_id,
        state=state,
        review_label=(
            None if not review_labels else review_labels[0].removeprefix("review:")
        ),
        title=title,
        labels=labels,
        base_ref=base_ref,
        base_sha=base_sha,
        head_ref=head_ref,
        head_sha=head_sha,
        review_comment=None,
    )


def _default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GH_HOST"] = EXPECTED_HOST
    return subprocess.run(
        list(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
        env=environment,
    )


def _run_json(runner: Runner, command: tuple[str, ...], label: str) -> Any:
    try:
        result = runner(command)
    except Exception:
        raise GitHubWorkflowError(f"GitHub {label} invocation failed") from None
    returncode = getattr(result, "returncode", None)
    stdout = getattr(result, "stdout", None)
    if returncode != 0:
        raise GitHubWorkflowError(f"GitHub {label} returned a failure status")
    if not isinstance(stdout, str):
        raise GitHubWorkflowError(f"GitHub {label} returned non-text output")
    return _loads_json(stdout, f"GitHub {label} output")


def _api_command(endpoint: str) -> tuple[str, ...]:
    return (
        "gh",
        "api",
        "--hostname",
        EXPECTED_HOST,
        "--method",
        "GET",
        endpoint,
    )


def _validate_review_comment(
    execute: Runner,
    pull_request: PullRequestSnapshot,
    expectation: ReviewCommentExpectation,
) -> ReviewCommentSnapshot:
    comment = _object(
        _run_json(
            execute,
            _api_command(
                f"repos/{EXPECTED_FULL_NAME}/issues/comments/"
                f"{expectation.comment_database_id}"
            ),
            "review comment preflight",
        ),
        "GitHub review comment output",
    )
    database_id = _database_id_from_fixture(
        comment, "GitHub review comment database_id"
    )
    node_id = _node_id_from_fixture(comment, "GitHub review comment node_id")
    if (database_id, node_id) != (
        expectation.comment_database_id,
        expectation.comment_node_id,
    ):
        raise GitHubWorkflowError("GitHub review comment identity mismatch")
    expected_issue_url = (
        f"https://api.github.com/repos/{EXPECTED_FULL_NAME}/issues/"
        f"{pull_request.number}"
    )
    if _string(comment.get("issue_url"), "review comment issue_url") != expected_issue_url:
        raise GitHubWorkflowError("GitHub review comment PR binding mismatch")
    body = _string(comment.get("body"), "GitHub review comment body")
    body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if body_sha256 != expectation.body_sha256:
        raise GitHubWorkflowError("GitHub review comment body digest mismatch")
    report = _object(_loads_json(body, "review comment body"), "review comment body")
    identity = _object(report.get("review_identity"), "review_identity")
    _exact_keys(
        identity,
        {
            "repository",
            "pull_request",
            "session_name",
            "external_id",
            "base_sha",
            "head_sha",
        },
        "review_identity",
    )
    if _string(identity.get("repository"), "review report repository") != EXPECTED_FULL_NAME:
        raise GitHubWorkflowError("review report repository mismatch")
    if _positive_int(
        identity.get("pull_request"), "review report pull-request number"
    ) != pull_request.number:
        raise GitHubWorkflowError("review report pull-request number mismatch")
    if _string(
        identity.get("session_name"), "review report session identity"
    ) != expectation.reviewer_session_name:
        raise GitHubWorkflowError("review report session identity mismatch")
    if _string(
        identity.get("external_id"), "review report external identity"
    ) != expectation.reviewer_external_id:
        raise GitHubWorkflowError("review report external identity mismatch")
    if identity.get("base_sha") != pull_request.base_sha:
        raise GitHubWorkflowError("review report base SHA mismatch")
    if identity.get("head_sha") != pull_request.head_sha:
        raise GitHubWorkflowError("review report head SHA mismatch")
    if report.get("verdict") != expectation.verdict:
        raise GitHubWorkflowError("review report verdict mismatch")
    expected_label = {
        "approve": "approved",
        "request_changes": "changes-requested",
        "blocked": "required",
    }[expectation.verdict]
    if pull_request.review_label != expected_label:
        raise GitHubWorkflowError("review label does not match the exact report")
    return ReviewCommentSnapshot(
        comment_database_id=database_id,
        comment_node_id=node_id,
        body_sha256=body_sha256,
        reviewer_session_name=expectation.reviewer_session_name,
        reviewer_external_id=expectation.reviewer_external_id,
        verdict=expectation.verdict,
    )


def _validate_cutover_lineage(
    execute: Runner,
    cutover_sha: str,
    current_base_sha: str,
) -> None:
    cutover = _object(
        _run_json(
            execute,
            _api_command(f"repos/{EXPECTED_FULL_NAME}/commits/{cutover_sha}"),
            "cutover commit preflight",
        ),
        "GitHub cutover commit output",
    )
    if _sha(cutover.get("sha"), "GitHub cutover commit SHA") != cutover_sha:
        raise GitHubWorkflowError("GitHub cutover commit SHA mismatch")
    comparison = _object(
        _run_json(
            execute,
            _api_command(
                f"repos/{EXPECTED_FULL_NAME}/compare/{cutover_sha}...{current_base_sha}"
            ),
            "cutover ancestry preflight",
        ),
        "GitHub cutover comparison output",
    )
    status_value = _string(comparison.get("status"), "cutover comparison status")
    if status_value not in {"ahead", "identical"}:
        raise GitHubWorkflowError("cutover commit is not an ancestor of current main")
    base_commit = _object(comparison.get("base_commit"), "comparison base_commit")
    merge_base = _object(
        comparison.get("merge_base_commit"), "comparison merge_base_commit"
    )
    if (
        _sha(base_commit.get("sha"), "comparison base SHA") != cutover_sha
        or _sha(merge_base.get("sha"), "comparison merge-base SHA") != cutover_sha
    ):
        raise GitHubWorkflowError("cutover comparison identity mismatch")
    if status_value == "identical":
        if current_base_sha != cutover_sha:
            raise GitHubWorkflowError("identical cutover comparison has different SHAs")
        raw_head = comparison.get("head_commit")
        if raw_head is not None and _sha(
            _object(raw_head, "comparison head_commit").get("sha"),
            "comparison head SHA",
        ) != current_base_sha:
            raise GitHubWorkflowError("cutover comparison identity mismatch")
    else:
        head_commit = _object(
            comparison.get("head_commit"), "comparison head_commit"
        )
        if _sha(head_commit.get("sha"), "comparison head SHA") != current_base_sha:
            raise GitHubWorkflowError("cutover comparison identity mismatch")


def _reconcile_issue_view(rest: Any, view: Any) -> dict[str, Any]:
    rest_issue = dict(_object(rest, "GitHub issue REST output"))
    view_issue = _object(view, "GitHub issue view output")
    rest_node_id = _node_id_from_fixture(rest_issue, "GitHub issue REST node_id")
    view_node_id = _node_id_from_fixture(view_issue, "GitHub issue view node_id")
    if rest_node_id != view_node_id:
        raise GitHubWorkflowError("GitHub issue REST/view node_id mismatch")
    for key in ("number", "title", "body"):
        if rest_issue.get(key) != view_issue.get(key):
            raise GitHubWorkflowError(f"GitHub issue REST/view {key} mismatch")
    rest_state = _state(
        rest_issue.get("state"), "REST issue state", {"OPEN", "CLOSED"}
    )
    view_state = _state(
        view_issue.get("state"), "view issue state", {"OPEN", "CLOSED"}
    )
    if rest_state != view_state:
        raise GitHubWorkflowError("GitHub issue REST/view state mismatch")
    view_for_reason = dict(view_issue)
    if view_state == "OPEN" and view_for_reason.get("stateReason") == "":
        view_for_reason["stateReason"] = None
    if _issue_state_reason(rest_issue) != _issue_state_reason(view_for_reason):
        raise GitHubWorkflowError("GitHub issue REST/view state_reason mismatch")
    if _labels(rest_issue.get("labels"), "REST issue labels") != _labels(
        view_issue.get("labels"), "view issue labels"
    ):
        raise GitHubWorkflowError("GitHub issue REST/view labels mismatch")
    if "blockedBy" not in view_issue:
        raise GitHubWorkflowError("GitHub issue view omitted blockedBy")
    if "parent" not in view_issue:
        raise GitHubWorkflowError("GitHub issue view omitted parent")
    if "subIssues" not in view_issue:
        raise GitHubWorkflowError("GitHub issue view omitted subIssues")
    rest_issue["blockedBy"] = view_issue["blockedBy"]
    rest_issue["parent"] = view_issue["parent"]
    rest_issue["subIssues"] = view_issue["subIssues"]
    return rest_issue


def _read_related_issue(
    execute: Runner,
    summary_payload: Any,
    endpoint: str,
    label: str,
) -> Mapping[str, Any]:
    summary = _object(summary_payload, f"{label} summary")
    related = _object(
        _run_json(execute, _api_command(endpoint), f"{label} preflight"),
        f"GitHub {label} output",
    )
    number, database_id, node_id = _item_identity(related, f"GitHub {label} output")
    if _positive_int(summary.get("number"), f"{label} summary number") != number:
        raise GitHubWorkflowError(f"GitHub {label} number mismatch")
    if "database_id" in summary or "databaseId" in summary or isinstance(
        summary.get("id"), int
    ):
        if _database_id_from_fixture(summary, f"{label} summary database_id") != database_id:
            raise GitHubWorkflowError(f"GitHub {label} database_id mismatch")
    if any(key in summary for key in ("node_id", "nodeId")) or isinstance(
        summary.get("id"), str
    ):
        if _node_id_from_fixture(summary, f"{label} summary node_id") != node_id:
            raise GitHubWorkflowError(f"GitHub {label} node_id mismatch")
    return related


def _read_issue_preflight(
    authority: GitHubAuthority,
    execute: Runner,
    repository: Mapping[str, Any],
    number: int,
) -> IssueSnapshot:
    rest = _run_json(
        execute,
        _api_command(f"repos/{EXPECTED_FULL_NAME}/issues/{number}"),
        "issue preflight",
    )
    view_command = (
        "gh",
        "issue",
        "view",
        str(number),
        "--repo",
        EXPECTED_FULL_NAME,
        "--json",
        "blockedBy,body,id,labels,number,parent,state,stateReason,subIssues,title",
    )
    view = _run_json(execute, view_command, "issue dependency preflight")
    reconciled = _reconcile_issue_view(rest, view)
    blocked_by: list[Mapping[str, Any]] = []
    for raw_dependency in _connection_nodes(
        reconciled.get("blockedBy"), "GitHub issue blockedBy connection"
    ):
        dependency_summary = _object(raw_dependency, "GitHub dependency summary")
        dependency_number = _positive_int(
            dependency_summary.get("number"), "GitHub dependency summary number"
        )
        blocked_by.append(
            _read_related_issue(
                execute,
                dependency_summary,
                f"repos/{EXPECTED_FULL_NAME}/issues/{dependency_number}",
                "issue dependency",
            )
        )
    reconciled["blockedBy"] = blocked_by
    children: list[Mapping[str, Any]] = []
    for raw_child in _connection_nodes(
        reconciled.get("subIssues"), "GitHub issue subIssues connection"
    ):
        child_summary = _object(raw_child, "GitHub child summary")
        child_number = _positive_int(
            child_summary.get("number"), "GitHub child summary number"
        )
        children.append(
            _read_related_issue(
                execute,
                child_summary,
                f"repos/{EXPECTED_FULL_NAME}/issues/{child_number}",
                "issue child",
            )
        )
    reconciled["subIssues"] = children
    parent_summary = reconciled.get("parent")
    if parent_summary is not None:
        reconciled["parent"] = _read_related_issue(
            execute,
            parent_summary,
            f"repos/{EXPECTED_FULL_NAME}/issues/{number}/parent",
            "issue parent",
        )
    return parse_issue_fixture(
        authority,
        {
            "repository": repository,
            "issue": reconciled,
        },
        expected_number=number,
    )


def live_preflight(
    config_path: str | Path,
    *,
    runner: Runner | None = None,
    repository_only: bool = False,
    expected_base_sha: str | None = None,
    issue_numbers: Sequence[int] | None = None,
    pull_request_expectations: Sequence[PullRequestExpectation] | None = None,
) -> PreflightSnapshot:
    """Read and validate current GitHub authority without making a write call."""

    authority = load_authority(config_path)
    execute = _default_runner if runner is None else runner
    repository_payload = _run_json(
        execute,
        _api_command(f"repos/{EXPECTED_FULL_NAME}"),
        "repository preflight",
    )
    commit_payload = _object(
        _run_json(
            execute,
            _api_command(f"repos/{EXPECTED_FULL_NAME}/commits/{authority.base_ref}"),
            "base preflight",
        ),
        "GitHub base output",
    )
    current_base_sha = _sha(commit_payload.get("sha"), "GitHub current base SHA")
    if expected_base_sha is not None and current_base_sha != _sha(
        expected_base_sha, "expected current base SHA"
    ):
        raise GitHubWorkflowError("GitHub current base SHA mismatch")
    _validate_cutover_lineage(
        execute, authority.cutover_main_sha, current_base_sha
    )
    repository_with_base = dict(_object(repository_payload, "repository output"))
    repository_with_base["base_ref"] = authority.base_ref
    repository_with_base["default_branch_sha"] = current_base_sha
    repository = validate_repository_fixture(
        authority, repository_with_base, require_base_sha=True
    )

    if repository_only and (
        issue_numbers is not None or pull_request_expectations is not None
    ):
        raise GitHubWorkflowError(
            "repository-only preflight cannot include issue or pull-request selectors"
        )
    if repository_only:
        return PreflightSnapshot(repository, authority.cutover_main_sha, (), ())

    selected_issue_numbers = (
        [item.number for item in authority.issues]
        if issue_numbers is None
        else [
            _positive_int(number, "preflight issue number")
            for number in issue_numbers
        ]
    )
    _require_unique(selected_issue_numbers, "preflight issue number")
    issues_by_number: dict[int, IssueSnapshot] = {}
    for number in selected_issue_numbers:
        issues_by_number[number] = _read_issue_preflight(
            authority, execute, repository_with_base, number
        )

    dependency_numbers = sorted(
        {
            dependency
            for issue in issues_by_number.values()
            if issue.state == "OPEN"
            and issue.status in {"ready", "in-progress", "review"}
            for dependency in issue.dependency_numbers
        }
    )
    for number in dependency_numbers:
        if number not in issues_by_number:
            issues_by_number[number] = _read_issue_preflight(
                authority, execute, repository_with_base, number
            )
    for issue in issues_by_number.values():
        if issue.state != "OPEN" or issue.status not in {
            "ready",
            "in-progress",
            "review",
        }:
            continue
        for dependency_number in issue.dependency_numbers:
            dependency = issues_by_number[dependency_number]
            if (
                dependency.state != "CLOSED"
                or dependency.state_reason != "COMPLETED"
            ):
                raise GitHubWorkflowError(
                    "ready or active issue has an incomplete dependency"
                )
    issues = [issues_by_number[number] for number in selected_issue_numbers]
    issues.extend(
        issues_by_number[number]
        for number in dependency_numbers
        if number not in selected_issue_numbers
    )

    selected_pr_expectations = (
        [_binding_expectation(item) for item in authority.pull_requests]
        if pull_request_expectations is None
        else [
            _validated_pr_expectation(authority, item)
            for item in pull_request_expectations
        ]
    )
    _require_unique(
        [item.number for item in selected_pr_expectations],
        "preflight pull-request number",
    )
    pull_requests: list[PullRequestSnapshot] = []
    for expectation in selected_pr_expectations:
        payload = _run_json(
            execute,
            _api_command(f"repos/{EXPECTED_FULL_NAME}/pulls/{expectation.number}"),
            "pull-request preflight",
        )
        pull_request = parse_pull_request_fixture(
            authority,
            {"repository": repository_with_base, "pull_request": payload},
            expected=expectation,
        )
        if expectation.review_comment is not None:
            review_comment = _validate_review_comment(
                execute, pull_request, expectation.review_comment
            )
            pull_request = replace(
                pull_request, review_comment=review_comment
            )
        pull_requests.append(pull_request)
    return PreflightSnapshot(
        repository,
        authority.cutover_main_sha,
        tuple(issues),
        tuple(pull_requests),
    )


def _summary(snapshot: PreflightSnapshot) -> dict[str, Any]:
    return {
        "repository": snapshot.repository.identity.full_name,
        "base_ref": snapshot.repository.base_ref,
        "base_sha": snapshot.repository.base_sha,
        "default_branch": snapshot.repository.default_branch,
        "cutover_main_sha": snapshot.cutover_main_sha,
        "issue_count": len(snapshot.issues),
        "pull_request_count": len(snapshot.pull_requests),
        "issues": [
            {
                "number": item.number,
                "legacy_id": item.legacy_id,
                "state": item.state,
                "state_reason": item.state_reason,
                "status": item.status,
                "kind": item.kind,
                "parent_number": item.parent_number,
                "child_numbers": list(item.child_numbers),
                "dependency_numbers": list(item.dependency_numbers),
            }
            for item in snapshot.issues
        ],
        "pull_requests": [
            {
                "number": item.number,
                "legacy_id": item.legacy_id,
                "state": item.state,
                "review_label": item.review_label,
                "base_ref": item.base_ref,
                "base_sha": item.base_sha,
                "head_ref": item.head_ref,
                "head_sha": item.head_sha,
                "review_comment": (
                    None
                    if item.review_comment is None
                    else {
                        "comment_database_id": (
                            item.review_comment.comment_database_id
                        ),
                        "comment_node_id": item.review_comment.comment_node_id,
                        "body_sha256": item.review_comment.body_sha256,
                        "reviewer_session_name": (
                            item.review_comment.reviewer_session_name
                        ),
                        "reviewer_external_id": (
                            item.review_comment.reviewer_external_id
                        ),
                        "verdict": item.review_comment.verdict,
                    }
                ),
            }
            for item in snapshot.pull_requests
        ],
        "status": "valid",
    }


def _pr_expectation_argument(value: str) -> PullRequestExpectation:
    parts = value.split(":")
    if len(parts) != 5:
        raise argparse.ArgumentTypeError(
            "expected NUMBER:BASE_REF:BASE_SHA:HEAD_REF:HEAD_SHA"
        )
    try:
        number = int(parts[0])
    except ValueError as error:
        raise argparse.ArgumentTypeError("pull-request number must be an integer") from error
    return PullRequestExpectation(number, parts[1], parts[2], parts[3], parts[4])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="validate config and cutover manifest offline")
    preflight = commands.add_parser("preflight", help="run a GET-only GitHub preflight")
    preflight.add_argument("--repository-only", action="store_true")
    preflight.add_argument("--expected-base-sha")
    preflight.add_argument("--issue-number", type=int, action="append")
    preflight.add_argument(
        "--pull-request-expectation",
        type=_pr_expectation_argument,
        action="append",
        metavar="NUMBER:BASE_REF:BASE_SHA:HEAD_REF:HEAD_SHA",
    )
    arguments = parser.parse_args(argv)
    try:
        authority = load_authority(arguments.config)
        if arguments.command == "validate":
            result = {
                "repository": authority.repository.full_name,
                "base_ref": authority.base_ref,
                "cutover_main_sha": authority.cutover_main_sha,
                "issue_count": len(authority.issues),
                "pull_request_count": len(authority.pull_requests),
                "status": "valid",
            }
        else:
            result = _summary(
                live_preflight(
                    arguments.config,
                    repository_only=arguments.repository_only,
                    expected_base_sha=arguments.expected_base_sha,
                    issue_numbers=arguments.issue_number,
                    pull_request_expectations=arguments.pull_request_expectation,
                )
            )
    except GitHubWorkflowError as error:
        print(f"github workflow: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
