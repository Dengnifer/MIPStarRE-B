#!/usr/bin/env python3
"""Validate and update the local issue, PR, session, and stage ledgers.

The JSON files are the durable source of truth.  A single advisory lock protects
cooperating writers, each changed file is replaced atomically, and a JSONL event
is appended after a successful mutation.  Unknown object fields are preserved
so the workflow can evolve without requiring a lock-step CLI release.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import sys
import tempfile
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Sequence


SCHEMA_VERSION = 1
STATE_FILES = {
    "issue": ("issues.json", "issues"),
    "pr": ("prs.json", "pull_requests"),
    "planned-session": ("sessions.json", "planned"),
    "issued-session": ("sessions.json", "issued"),
    "stage": ("stages.json", "stages"),
}
DEFAULT_DOCUMENTS: dict[str, dict[str, Any]] = {
    "issues.json": {"schema_version": 1, "next_sequence": 1, "issues": []},
    "prs.json": {"schema_version": 1, "next_sequence": 1, "pull_requests": []},
    "sessions.json": {"schema_version": 1, "planned": [], "issued": []},
    "stages.json": {"schema_version": 1, "stages": []},
    "protocols.json": {"schema_version": 1, "active_revision": None, "revisions": []},
}

ISSUE_STATUSES = {
    "planned",
    "ready",
    "in_progress",
    "review",
    "blocked",
    "done",
    "cancelled",
}
PR_STATUSES = {
    "draft",
    "ready",
    "changes_requested",
    "approved",
    "merged",
    "closed",
}
SESSION_STATUSES = {"issued", "running", "finished", "failed", "archived"}
STAGE_STATUSES = {"planned", "in_progress", "completed", "blocked"}
ACTIVE_SESSION_STATUSES = {"issued", "running"}
ARCHIVE_STATUSES = {
    "active",
    "not_requested",
    "pending",
    "archived",
    "retired-locally-no-cli-session",
    "failed",
}
CHECK_STATUSES = {"passed", "failed", "blocked"}
REVIEW_VERDICTS = {"approve", "request_changes", "blocked"}
FINDING_SEVERITIES = {"blocker", "high", "medium", "low"}
FINDING_STATUSES = {"open", "resolved"}
FINDING_DISPOSITIONS = {"pending", "fixed", "rejected"}
IMPLEMENTATION_ISSUE_KINDS = {"formalization"}
ISSUE_EXECUTION_CATEGORIES = {"implementation", "preflight", "tracking"}
BOUNDED_TIMING_QUALITY = "bounded-by-parent-window"
TIMING_QUALITIES = {
    "runtime-exact",
    "runtime-measured",
    "agent-measured",
    "agent-reported-approximate",
    "derived-from-reported-elapsed",
    "derived-from-agent-reported-elapsed",
    "derived-from-reviewer-observed-wall-clock",
    BOUNDED_TIMING_QUALITY,
}
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SESSION_NAME_RE = re.compile(
    r"^i[0-9]+-[a-z0-9]+(?:-[a-z0-9]+)*-a[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*$"
)

ISSUE_TRANSITIONS = {
    "planned": {"ready", "blocked", "cancelled"},
    "ready": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"ready", "review", "blocked", "cancelled"},
    "review": {"in_progress", "done", "blocked", "cancelled"},
    "blocked": {"planned", "ready", "cancelled"},
    "done": set(),
    "cancelled": {"planned"},
}
PR_TRANSITIONS = {
    "draft": {"ready", "closed"},
    "ready": {"changes_requested", "approved", "closed"},
    "changes_requested": {"ready", "closed"},
    "approved": {"changes_requested", "merged", "closed"},
    "merged": set(),
    "closed": {"draft"},
}
SESSION_TRANSITIONS = {
    "issued": {"running", "failed"},
    "running": {"finished", "failed"},
    "finished": {"archived"},
    "failed": {"archived"},
    "archived": set(),
}
STAGE_TRANSITIONS = {
    "planned": {"in_progress", "blocked"},
    "in_progress": {"completed", "blocked"},
    "blocked": {"in_progress"},
    "completed": set(),
}


class WorkflowError(Exception):
    """Base class for errors that should be presented without a traceback."""


class ValidationError(WorkflowError):
    """One or more ledger validation failures."""

    def __init__(self, errors: Sequence[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def utc_now() -> str:
    """Return a stable UTC timestamp suitable for ledger records."""

    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any, location: str, errors: list[str], *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value:
        errors.append(f"{location}: expected a non-empty ISO-8601 timestamp")
        return
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{location}: invalid ISO-8601 timestamp {value!r}")
        return
    if parsed.tzinfo is None:
        errors.append(f"{location}: timestamp must include a UTC offset")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_keys(record: Mapping[str, Any], required: Iterable[str], location: str, errors: list[str]) -> None:
    for key in required:
        if key not in record:
            errors.append(f"{location}: missing required field {key!r}")


def _nonempty_string(value: Any, location: str, errors: list[str], *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location}: expected a non-empty string")


def _string_list(value: Any, location: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{location}: expected a list of strings")


def _unique_string_list(value: Any, location: str, errors: list[str]) -> list[str]:
    _string_list(value, location, errors)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return []
    if any(not item.strip() for item in value):
        errors.append(f"{location}: entries must be non-empty strings")
    if len(value) != len(set(value)):
        errors.append(f"{location}: duplicate entries")
    return value


def _validate_sha(value: Any, location: str, errors: list[str], *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        errors.append(f"{location}: expected a lowercase 40- or 64-character Git object id")


def _timestamp_value(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _issue_execution_category(issue: Mapping[str, Any]) -> str:
    """Classify work that requires an active issue orchestrator.

    ``kind`` is the durable category used by the bootstrap ledger.  A later
    issue may override it explicitly when a formalization-shaped preflight or
    a non-Lean implementation task needs a different scheduling contract.
    """

    if issue.get("kind") in IMPLEMENTATION_ISSUE_KINDS:
        return "implementation"
    explicit = issue.get("execution_category")
    if isinstance(explicit, str) and explicit in ISSUE_EXECUTION_CATEGORIES:
        return explicit
    if issue.get("kind") == "tracking":
        return "tracking"
    return "preflight"


def _owned_path_parts(worktree: str, owned_path: str) -> tuple[str, ...] | None:
    """Normalize an ownership claim for conservative overlap detection."""

    raw = Path(owned_path)
    if raw.is_absolute():
        try:
            relative = raw.resolve(strict=False).relative_to(Path(worktree).resolve(strict=False))
        except ValueError:
            normalized = PurePosixPath(raw.as_posix())
        else:
            normalized = PurePosixPath(relative.as_posix())
    else:
        normalized = PurePosixPath(owned_path)
    parts = tuple(part for part in normalized.parts if part not in {"", "."})
    if not parts or ".." in parts:
        return None
    return parts


def _paths_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    shared = min(len(left), len(right))
    return left[:shared] == right[:shared]


def _ownership_scope(worktree: str, owned_path: str) -> str:
    raw = Path(owned_path)
    resolved_worktree = Path(worktree).resolve(strict=False)
    if not raw.is_absolute():
        return str(resolved_worktree)
    try:
        raw.resolve(strict=False).relative_to(resolved_worktree)
    except ValueError:
        return "<absolute>"
    return str(resolved_worktree)


def _record_list(document: Mapping[str, Any], key: str, location: str, errors: list[str]) -> list[dict[str, Any]]:
    value = document.get(key)
    if not isinstance(value, list):
        errors.append(f"{location}.{key}: expected a list")
        return []
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{location}.{key}[{index}]: expected an object")
        else:
            records.append(item)
    return records


def _validate_document_header(document: Any, filename: str, errors: list[str]) -> Mapping[str, Any]:
    if not isinstance(document, dict):
        errors.append(f"{filename}: top level must be an object")
        return {}
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{filename}.schema_version: expected {SCHEMA_VERSION}")
    return document


def _validate_unique_ids(records: Sequence[Mapping[str, Any]], location: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for index, record in enumerate(records):
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{location}[{index}].id: expected a non-empty string")
        elif record_id in seen:
            errors.append(f"{location}: duplicate id {record_id!r}")
        else:
            seen.add(record_id)
    return seen


def _validate_token_usage(value: Any, location: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location}: expected an object")
        return
    _require_keys(value, ("input", "output", "total", "availability_reason"), location, errors)
    values: dict[str, int | None] = {}
    for key in ("input", "output", "total"):
        item = value.get(key)
        if item is not None and (not _is_int(item) or item < 0):
            errors.append(f"{location}.{key}: expected null or a non-negative integer")
        values[key] = item if _is_int(item) and item >= 0 else None
    reason = value.get("availability_reason")
    if reason is not None and (not isinstance(reason, str) or not reason.strip()):
        errors.append(f"{location}.availability_reason: expected null or a non-empty string")
    if all(values[key] is not None for key in ("input", "output", "total")):
        if values["input"] + values["output"] != values["total"]:
            errors.append(f"{location}.total: must equal input + output")
    if any(values[key] is None for key in ("input", "output", "total")) and not reason:
        errors.append(f"{location}.availability_reason: required when token counts are unavailable")


def _validate_cycle(
    nodes: Iterable[str],
    edges: Callable[[str], Iterable[str]],
    label: str,
    errors: list[str],
) -> None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        marker = state.get(node, 0)
        if marker == 2:
            return
        if marker == 1:
            start = stack.index(node)
            cycle = stack[start:] + [node]
            errors.append(f"{label}: cycle detected: {' -> '.join(cycle)}")
            return
        state[node] = 1
        stack.append(node)
        adjacent = edges(node)
        try:
            iterator = iter(adjacent)
        except TypeError:
            iterator = iter(())
        for dependency in iterator:
            if not isinstance(dependency, str):
                continue
            if dependency in state or dependency in node_set:
                visit(dependency)
        stack.pop()
        state[node] = 2

    node_set = set(nodes)
    for item in sorted(node_set):
        if state.get(item, 0) == 0:
            visit(item)


def _evidence_records(value: Any, location: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{location}: expected a list")
        return []
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{location}[{index}]: expected an object")
        else:
            records.append(item)
    return records


def _validate_pr_evidence(
    pull_request: Mapping[str, Any],
    location: str,
    errors: list[str],
    *,
    issue_by_id: Mapping[str, Mapping[str, Any]],
    issued_by_id: Mapping[str, Mapping[str, Any]],
) -> None:
    """Validate immutable check/review evidence and the PR status claim."""

    pr_id = pull_request.get("id")
    base_sha = pull_request.get("base_sha")
    head_sha = pull_request.get("head_sha")
    status = pull_request.get("status")

    implementer_ids = _unique_string_list(
        pull_request.get("implementer_session_ids"),
        f"{location}.implementer_session_ids",
        errors,
    )
    for session_id in implementer_ids:
        session = issued_by_id.get(session_id)
        if session is None:
            errors.append(f"{location}.implementer_session_ids: unknown issued session {session_id!r}")
        elif session.get("read_only") is not False:
            errors.append(f"{location}.implementer_session_ids: session {session_id!r} is not writable")
        elif session.get("pr_id") != pr_id:
            errors.append(
                f"{location}.implementer_session_ids: session {session_id!r} is not bound to PR {pr_id!r}"
            )
    bound_writable_ids = {
        str(session.get("id"))
        for session in issued_by_id.values()
        if session.get("pr_id") == pr_id
        and session.get("read_only") is False
        and isinstance(session.get("id"), str)
    }
    if status in {"ready", "approved", "merged"} and set(implementer_ids) != bound_writable_ids:
        errors.append(
            f"{location}.implementer_session_ids: must list exactly the writable sessions bound to this PR"
        )

    checks = _evidence_records(pull_request.get("checks"), f"{location}.checks", errors)
    reviews = _evidence_records(pull_request.get("reviews"), f"{location}.reviews", errors)
    findings = _evidence_records(pull_request.get("findings"), f"{location}.findings", errors)

    check_ids = _validate_unique_ids(checks, f"{location}.checks", errors)
    review_ids = _validate_unique_ids(reviews, f"{location}.reviews", errors)
    finding_ids = _validate_unique_ids(findings, f"{location}.findings", errors)
    check_times: dict[str, dt.datetime] = {}
    review_times: dict[str, dt.datetime] = {}
    review_starts: dict[str, dt.datetime] = {}
    reviewer_session_ids: set[str] = set()

    check_required = (
        "id",
        "name",
        "command",
        "status",
        "base_sha",
        "head_sha",
        "completed_at",
        "result_path",
    )
    for index, check in enumerate(checks):
        loc = f"{location}.checks[{index}]"
        _require_keys(check, check_required, loc, errors)
        for key in ("name", "command", "result_path"):
            _nonempty_string(check.get(key), f"{loc}.{key}", errors)
        if check.get("status") not in CHECK_STATUSES:
            errors.append(f"{loc}.status: invalid check status {check.get('status')!r}")
        _validate_sha(check.get("base_sha"), f"{loc}.base_sha", errors)
        _validate_sha(check.get("head_sha"), f"{loc}.head_sha", errors)
        if isinstance(base_sha, str) and check.get("base_sha") != base_sha:
            errors.append(f"{loc}.base_sha: evidence is not bound to PR base_sha")
        parse_timestamp(check.get("completed_at"), f"{loc}.completed_at", errors)
        parsed = _timestamp_value(check.get("completed_at"))
        if parsed is not None and isinstance(check.get("id"), str):
            check_times[check["id"]] = parsed

    review_required = (
        "id",
        "reviewer_session_id",
        "verdict",
        "base_sha",
        "head_sha",
        "started_at",
        "completed_at",
        "result_path",
        "finding_ids",
    )
    linked_issue_ids = pull_request.get("issue_ids")
    linked_issue_ids = linked_issue_ids if isinstance(linked_issue_ids, list) else []
    owner_ids = {
        issue_by_id[issue_id].get("owner_session_id")
        for issue_id in linked_issue_ids
        if isinstance(issue_id, str) and issue_id in issue_by_id
    }
    owner_ids.discard(None)
    for index, review in enumerate(reviews):
        loc = f"{location}.reviews[{index}]"
        _require_keys(review, review_required, loc, errors)
        reviewer_id = review.get("reviewer_session_id")
        _nonempty_string(reviewer_id, f"{loc}.reviewer_session_id", errors)
        if isinstance(reviewer_id, str):
            if reviewer_id in reviewer_session_ids:
                errors.append(f"{location}.reviews: reviewer session {reviewer_id!r} is reused")
            reviewer_session_ids.add(reviewer_id)
            reviewer = issued_by_id.get(reviewer_id)
            if reviewer is None:
                errors.append(f"{loc}.reviewer_session_id: unknown issued session {reviewer_id!r}")
            else:
                if reviewer.get("role") != "reviewer" or reviewer.get("read_only") is not True:
                    errors.append(f"{loc}.reviewer_session_id: reviewer must be a read-only reviewer session")
                if reviewer.get("status") not in {"finished", "archived"}:
                    errors.append(f"{loc}.reviewer_session_id: reviewer session has not finished")
                if reviewer.get("pr_id") != pr_id:
                    errors.append(f"{loc}.reviewer_session_id: reviewer session is not bound to PR {pr_id!r}")
                if reviewer.get("base_revision") != base_sha:
                    errors.append(f"{loc}.reviewer_session_id: reviewer base_revision differs from PR base_sha")
                if not isinstance(reviewer.get("external_id"), str) or not reviewer.get("external_id"):
                    errors.append(f"{loc}.reviewer_session_id: reviewer lacks a persistent external identity")
            if reviewer_id in implementer_ids or reviewer_id in owner_ids:
                errors.append(f"{loc}.reviewer_session_id: reviewer is not independent of implementation")
        if review.get("verdict") not in REVIEW_VERDICTS:
            errors.append(f"{loc}.verdict: invalid review verdict {review.get('verdict')!r}")
        _validate_sha(review.get("base_sha"), f"{loc}.base_sha", errors)
        _validate_sha(review.get("head_sha"), f"{loc}.head_sha", errors)
        if isinstance(base_sha, str) and review.get("base_sha") != base_sha:
            errors.append(f"{loc}.base_sha: evidence is not bound to PR base_sha")
        parse_timestamp(review.get("started_at"), f"{loc}.started_at", errors)
        parse_timestamp(review.get("completed_at"), f"{loc}.completed_at", errors)
        started = _timestamp_value(review.get("started_at"))
        completed = _timestamp_value(review.get("completed_at"))
        if started is not None and completed is not None and completed < started:
            errors.append(f"{loc}: completed_at precedes started_at")
        if isinstance(reviewer_id, str):
            reviewer = issued_by_id.get(reviewer_id)
            if reviewer is not None:
                session_start = _timestamp_value(reviewer.get("started_at"))
                session_end = _timestamp_value(reviewer.get("ended_at"))
                if started is not None and session_start is not None and started < session_start:
                    errors.append(f"{loc}.started_at: review predates its reviewer session")
                if completed is not None and session_end is not None and completed > session_end:
                    errors.append(f"{loc}.completed_at: review outlives its reviewer session")
        if isinstance(review.get("id"), str):
            if started is not None:
                review_starts[review["id"]] = started
            if completed is not None:
                review_times[review["id"]] = completed
        _nonempty_string(review.get("result_path"), f"{loc}.result_path", errors)
        refs = _unique_string_list(review.get("finding_ids"), f"{loc}.finding_ids", errors)
        for finding_id in refs:
            if finding_id not in finding_ids:
                errors.append(f"{loc}.finding_ids: unknown finding {finding_id!r}")

    finding_required = (
        "id",
        "introduced_review_id",
        "base_sha",
        "head_sha",
        "severity",
        "status",
        "disposition",
        "disposition_evidence",
        "resolved_by_review_id",
    )
    finding_by_id = {
        finding["id"]: finding for finding in findings if isinstance(finding.get("id"), str)
    }
    for index, finding in enumerate(findings):
        loc = f"{location}.findings[{index}]"
        _require_keys(finding, finding_required, loc, errors)
        introduced = finding.get("introduced_review_id")
        if introduced not in review_ids:
            errors.append(f"{loc}.introduced_review_id: unknown review {introduced!r}")
        _validate_sha(finding.get("base_sha"), f"{loc}.base_sha", errors)
        _validate_sha(finding.get("head_sha"), f"{loc}.head_sha", errors)
        if isinstance(base_sha, str) and finding.get("base_sha") != base_sha:
            errors.append(f"{loc}.base_sha: finding is not bound to PR base_sha")
        if finding.get("severity") not in FINDING_SEVERITIES:
            errors.append(f"{loc}.severity: invalid finding severity {finding.get('severity')!r}")
        finding_status = finding.get("status")
        disposition = finding.get("disposition")
        if finding_status not in FINDING_STATUSES:
            errors.append(f"{loc}.status: invalid finding status {finding_status!r}")
        if disposition not in FINDING_DISPOSITIONS:
            errors.append(f"{loc}.disposition: invalid finding disposition {disposition!r}")
        evidence = finding.get("disposition_evidence")
        resolved_by = finding.get("resolved_by_review_id")
        if finding_status == "open":
            if disposition != "pending" or evidence is not None or resolved_by is not None:
                errors.append(f"{loc}: open finding must have pending disposition and no resolution evidence")
        elif finding_status == "resolved":
            if disposition not in {"fixed", "rejected"}:
                errors.append(f"{loc}.disposition: resolved finding must be fixed or rejected")
            _nonempty_string(evidence, f"{loc}.disposition_evidence", errors)
            if resolved_by not in review_ids:
                errors.append(f"{loc}.resolved_by_review_id: unknown review {resolved_by!r}")
        source_review = next((review for review in reviews if review.get("id") == introduced), None)
        if source_review is not None:
            if finding.get("base_sha") != source_review.get("base_sha"):
                errors.append(f"{loc}.base_sha: differs from introducing review")
            if finding.get("head_sha") != source_review.get("head_sha"):
                errors.append(f"{loc}.head_sha: differs from introducing review")
        resolution_review = next((review for review in reviews if review.get("id") == resolved_by), None)
        if finding_status == "resolved" and resolution_review is not None and source_review is not None:
            if resolved_by == introduced:
                errors.append(f"{loc}.resolved_by_review_id: finding requires a later review round")
            introduced_at = review_times.get(str(introduced))
            resolved_at = review_times.get(str(resolved_by))
            if introduced_at is not None and resolved_at is not None and resolved_at <= introduced_at:
                errors.append(f"{loc}.resolved_by_review_id: resolution review is not later than introduction")
            if disposition == "fixed" and resolution_review.get("head_sha") == finding.get("head_sha"):
                errors.append(f"{loc}.resolved_by_review_id: fixed finding requires a changed head SHA")

    for review in reviews:
        review_id = review.get("id")
        refs = review.get("finding_ids")
        if not isinstance(review_id, str) or not isinstance(refs, list):
            continue
        expected = {
            finding_id
            for finding_id, finding in finding_by_id.items()
            if finding.get("introduced_review_id") == review_id
        }
        actual = {item for item in refs if isinstance(item, str)}
        if actual != expected:
            errors.append(f"{location}.reviews[{review_id!r}].finding_ids: must list exactly introduced findings")

    current_checks = [
        check
        for check in checks
        if check.get("base_sha") == base_sha and check.get("head_sha") == head_sha
    ]
    current_reviews = [
        review
        for review in reviews
        if review.get("base_sha") == base_sha and review.get("head_sha") == head_sha
    ]
    current_reviews.sort(
        key=lambda review: review_times.get(
            str(review.get("id")), dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        )
    )
    for review in reviews:
        matching_checks = [
            check
            for check in checks
            if check.get("base_sha") == review.get("base_sha")
            and check.get("head_sha") == review.get("head_sha")
        ]
        if not matching_checks:
            errors.append(
                f"{location}.reviews[{review.get('id')!r}]: review has no checks for its immutable base/head"
            )
            continue
        if any(check.get("status") != "passed" for check in matching_checks):
            errors.append(
                f"{location}.reviews[{review.get('id')!r}]: review was issued without passing checks"
            )
        matching_times = [
            check_times[str(check.get("id"))]
            for check in matching_checks
            if str(check.get("id")) in check_times
        ]
        review_start = review_starts.get(str(review.get("id")))
        if matching_times and review_start is not None and review_start < max(matching_times):
            errors.append(
                f"{location}.reviews[{review.get('id')!r}]: review started before checks completed"
            )
    requires_frozen_head = status in {"ready", "changes_requested", "approved", "merged"}
    if requires_frozen_head:
        _validate_sha(base_sha, f"{location}.base_sha", errors)
        _validate_sha(head_sha, f"{location}.head_sha", errors)
        if base_sha == head_sha:
            errors.append(f"{location}: base_sha and head_sha must differ")
    if status in {"ready", "approved", "merged"}:
        if not current_checks:
            errors.append(f"{location}: status {status!r} requires checks for the current base/head")
        elif any(check.get("status") != "passed" for check in current_checks):
            errors.append(f"{location}: all current checks must pass before status {status!r}")
    if status in {"approved", "merged"}:
        if not implementer_ids:
            errors.append(f"{location}: status {status!r} requires identified implementer sessions")
        latest_review = current_reviews[-1] if current_reviews else None
        if latest_review is None or latest_review.get("verdict") != "approve":
            errors.append(f"{location}: status {status!r} requires a current approving review")
        if any(finding.get("status") != "resolved" for finding in findings):
            errors.append(f"{location}: status {status!r} requires every finding to be resolved")
        for finding in findings:
            if finding.get("status") != "resolved":
                continue
            resolution = next(
                (review for review in reviews if review.get("id") == finding.get("resolved_by_review_id")),
                None,
            )
            if resolution is None or resolution.get("base_sha") != base_sha or resolution.get("head_sha") != head_sha:
                errors.append(
                    f"{location}.findings[{finding.get('id')!r}]: resolution is not confirmed on current base/head"
                )
        if latest_review is not None and current_checks:
            current_check_times = [
                check_times[str(check.get("id"))]
                for check in current_checks
                if str(check.get("id")) in check_times
            ]
            latest_check_time = max(current_check_times, default=None)
            latest_review_start = review_starts.get(str(latest_review.get("id")))
            if (
                latest_check_time is not None
                and latest_review_start is not None
                and latest_review_start < latest_check_time
            ):
                errors.append(f"{location}: approving review started before current checks completed")

    integration_sha = pull_request.get("integration_sha")
    if integration_sha is not None:
        _validate_sha(integration_sha, f"{location}.integration_sha", errors)
    merged_at = pull_request.get("merged_at")
    parse_timestamp(merged_at, f"{location}.merged_at", errors, nullable=True)
    if status == "merged":
        _validate_sha(integration_sha, f"{location}.integration_sha", errors)
        if merged_at is None:
            errors.append(f"{location}.merged_at: required for merged PR")


def validate_documents(documents: Mapping[str, Any]) -> None:
    """Validate the complete cross-file workflow state.

    Raises ``ValidationError`` containing all independently discoverable
    failures.  Additional fields are intentionally ignored.
    """

    errors: list[str] = []
    missing = sorted(set(DEFAULT_DOCUMENTS) - set(documents))
    if missing:
        errors.append(f"missing state documents: {', '.join(missing)}")

    issues_doc = _validate_document_header(documents.get("issues.json"), "issues.json", errors)
    prs_doc = _validate_document_header(documents.get("prs.json"), "prs.json", errors)
    sessions_doc = _validate_document_header(documents.get("sessions.json"), "sessions.json", errors)
    stages_doc = _validate_document_header(documents.get("stages.json"), "stages.json", errors)
    protocols_doc = _validate_document_header(documents.get("protocols.json"), "protocols.json", errors)

    for filename, document in (("issues.json", issues_doc), ("prs.json", prs_doc)):
        next_sequence = document.get("next_sequence")
        if not _is_int(next_sequence) or next_sequence < 1:
            errors.append(f"{filename}.next_sequence: expected a positive integer")

    issues = _record_list(issues_doc, "issues", "issues.json", errors)
    prs = _record_list(prs_doc, "pull_requests", "prs.json", errors)
    planned = _record_list(sessions_doc, "planned", "sessions.json", errors)
    issued = _record_list(sessions_doc, "issued", "sessions.json", errors)
    stages = _record_list(stages_doc, "stages", "stages.json", errors)
    revisions = _record_list(protocols_doc, "revisions", "protocols.json", errors)

    issue_ids = _validate_unique_ids(issues, "issues.json.issues", errors)
    pr_ids = _validate_unique_ids(prs, "prs.json.pull_requests", errors)
    planned_ids = _validate_unique_ids(planned, "sessions.json.planned", errors)
    issued_ids = _validate_unique_ids(issued, "sessions.json.issued", errors)
    stage_ids = _validate_unique_ids(stages, "stages.json.stages", errors)
    del stage_ids
    overlap = planned_ids & issued_ids
    if overlap:
        errors.append(f"sessions.json: ids appear in both planned and issued: {', '.join(sorted(overlap))}")

    issue_by_id = {record["id"]: record for record in issues if isinstance(record.get("id"), str)}
    issued_by_id = {record["id"]: record for record in issued if isinstance(record.get("id"), str)}
    all_session_ids = planned_ids | issued_ids

    issue_required = (
        "id",
        "title",
        "kind",
        "status",
        "parent_id",
        "dependency_ids",
        "labels",
        "acceptance_gates",
        "owner_session_id",
        "source_refs",
        "created_at",
        "updated_at",
    )
    for index, issue in enumerate(issues):
        loc = f"issues.json.issues[{index}]"
        _require_keys(issue, issue_required, loc, errors)
        for key in ("title", "kind"):
            _nonempty_string(issue.get(key), f"{loc}.{key}", errors)
        status = issue.get("status")
        if status not in ISSUE_STATUSES:
            errors.append(f"{loc}.status: invalid issue status {status!r}")
        execution_category = issue.get("execution_category")
        if execution_category is not None and execution_category not in ISSUE_EXECUTION_CATEGORIES:
            errors.append(
                f"{loc}.execution_category: expected one of {', '.join(sorted(ISSUE_EXECUTION_CATEGORIES))}"
            )
        if issue.get("kind") in IMPLEMENTATION_ISSUE_KINDS and execution_category not in {
            None,
            "implementation",
        }:
            errors.append(f"{loc}.execution_category: formalization issues cannot bypass implementation gates")
        parent_id = issue.get("parent_id")
        if parent_id is not None and parent_id not in issue_ids:
            errors.append(f"{loc}.parent_id: unknown issue {parent_id!r}")
        if parent_id == issue.get("id"):
            errors.append(f"{loc}.parent_id: issue cannot be its own parent")
        dependencies = issue.get("dependency_ids")
        if not isinstance(dependencies, list) or any(not isinstance(item, str) for item in dependencies):
            errors.append(f"{loc}.dependency_ids: expected a list of issue ids")
            dependencies = []
        elif len(dependencies) != len(set(dependencies)):
            errors.append(f"{loc}.dependency_ids: duplicate dependency")
        for dependency in dependencies:
            if dependency not in issue_ids:
                errors.append(f"{loc}.dependency_ids: unknown issue {dependency!r}")
            if dependency == issue.get("id"):
                errors.append(f"{loc}.dependency_ids: issue cannot depend on itself")
        for key in ("labels", "acceptance_gates", "source_refs"):
            _string_list(issue.get(key), f"{loc}.{key}", errors)
        owner = issue.get("owner_session_id")
        if owner is not None and owner not in issued_ids:
            errors.append(f"{loc}.owner_session_id: unknown issued session {owner!r}")
        parse_timestamp(issue.get("created_at"), f"{loc}.created_at", errors)
        parse_timestamp(issue.get("updated_at"), f"{loc}.updated_at", errors)

    _validate_cycle(
        issue_ids,
        lambda issue_id: issue_by_id.get(issue_id, {}).get("dependency_ids", []),
        "issue dependencies",
        errors,
    )
    _validate_cycle(
        issue_ids,
        lambda issue_id: [issue_by_id[issue_id]["parent_id"]]
        if issue_by_id.get(issue_id, {}).get("parent_id") is not None
        else [],
        "issue parent hierarchy",
        errors,
    )

    for issue in issues:
        if not isinstance(issue.get("id"), str):
            continue
        dependencies = issue.get("dependency_ids", [])
        dependencies = (
            dependencies
            if isinstance(dependencies, list) and all(isinstance(item, str) for item in dependencies)
            else []
        )
        if issue.get("status") in {"ready", "in_progress", "review", "done"}:
            unfinished = [
                dependency
                for dependency in dependencies
                if issue_by_id.get(dependency, {}).get("status") != "done"
            ]
            if unfinished:
                errors.append(
                    f"issue {issue['id']!r}: status {issue.get('status')!r} with unfinished dependencies "
                    f"{', '.join(unfinished)}"
                )
    children: dict[str, list[Mapping[str, Any]]] = {issue_id: [] for issue_id in issue_ids}
    for issue in issues:
        parent = issue.get("parent_id")
        if parent in children:
            children[parent].append(issue)
    for issue in issues:
        if issue.get("kind") == "tracking" and issue.get("status") == "done":
            direct_children = children.get(issue.get("id"), [])
            if not direct_children:
                errors.append(f"tracking issue {issue.get('id')!r}: done tracker has no children")
            elif any(child.get("status") != "done" for child in direct_children):
                errors.append(f"tracking issue {issue.get('id')!r}: all direct children must be done before closure")

    pr_required = (
        "id",
        "title",
        "status",
        "issue_ids",
        "base",
        "head",
        "base_sha",
        "head_sha",
        "implementer_session_ids",
        "checks",
        "reviews",
        "findings",
        "integration_sha",
        "merged_at",
        "created_at",
        "updated_at",
    )
    for index, pull_request in enumerate(prs):
        loc = f"prs.json.pull_requests[{index}]"
        _require_keys(pull_request, pr_required, loc, errors)
        for key in ("title", "base", "head"):
            _nonempty_string(pull_request.get(key), f"{loc}.{key}", errors)
        status = pull_request.get("status")
        if status not in PR_STATUSES:
            errors.append(f"{loc}.status: invalid PR status {status!r}")
        linked_issues = pull_request.get("issue_ids")
        if not isinstance(linked_issues, list) or any(not isinstance(item, str) for item in linked_issues):
            errors.append(f"{loc}.issue_ids: expected a list of issue ids")
            linked_issues = []
        elif not linked_issues:
            errors.append(f"{loc}.issue_ids: local PR must link at least one issue")
        elif len(linked_issues) != len(set(linked_issues)):
            errors.append(f"{loc}.issue_ids: duplicate issue")
        for issue_id in linked_issues:
            if issue_id not in issue_ids:
                errors.append(f"{loc}.issue_ids: unknown issue {issue_id!r}")
        for key in ("base_sha", "head_sha"):
            _validate_sha(pull_request.get(key), f"{loc}.{key}", errors, nullable=True)
        parse_timestamp(pull_request.get("created_at"), f"{loc}.created_at", errors)
        parse_timestamp(pull_request.get("updated_at"), f"{loc}.updated_at", errors)
        _validate_pr_evidence(
            pull_request,
            loc,
            errors,
            issue_by_id=issue_by_id,
            issued_by_id=issued_by_id,
        )

    planned_required = ("id", "role", "issue_id")
    planned_names: set[str] = set()
    for index, session in enumerate(planned):
        loc = f"sessions.json.planned[{index}]"
        _require_keys(session, planned_required, loc, errors)
        _nonempty_string(session.get("role"), f"{loc}.role", errors)
        issue_id = session.get("issue_id")
        if issue_id not in issue_ids:
            errors.append(f"{loc}.issue_id: unknown issue {issue_id!r}")
        if "status" in session and session.get("status") != "planned":
            errors.append(f"{loc}.status: planned records may only use 'planned'")
        if "attempt" in session and (not _is_int(session.get("attempt")) or session["attempt"] < 1):
            errors.append(f"{loc}.attempt: expected a positive integer")
        name = session.get("name")
        if name is not None:
            if not isinstance(name, str) or not SESSION_NAME_RE.fullmatch(name):
                errors.append(f"{loc}.name: does not match {SESSION_NAME_RE.pattern!r}")
            elif name in planned_names:
                errors.append(f"sessions.json.planned: duplicate name {name!r}")
            planned_names.add(name)
        parent = session.get("parent_session_id")
        if parent is not None and parent not in all_session_ids:
            errors.append(f"{loc}.parent_session_id: unknown session {parent!r}")

    issued_required = (
        "id",
        "name",
        "backend",
        "role",
        "status",
        "issue_id",
        "pr_id",
        "parent_session_id",
        "external_id",
        "attempt",
        "read_only",
        "base_revision",
        "worktree",
        "owned_paths",
        "validation_command",
        "result_envelope_path",
        "started_at",
        "ended_at",
        "elapsed_seconds",
        "token_usage",
        "archive_status",
        "outcome_path",
    )
    issued_names: set[str] = set()
    external_ids: set[str] = set()
    for index, session in enumerate(issued):
        loc = f"sessions.json.issued[{index}]"
        _require_keys(session, issued_required, loc, errors)
        for key in ("name", "backend", "role", "archive_status"):
            _nonempty_string(session.get(key), f"{loc}.{key}", errors)
        name = session.get("name")
        if isinstance(name, str):
            if not SESSION_NAME_RE.fullmatch(name):
                errors.append(f"{loc}.name: does not match {SESSION_NAME_RE.pattern!r}")
            elif name in issued_names:
                errors.append(f"sessions.json.issued: duplicate name {name!r}")
            issued_names.add(name)
        if name in planned_names:
            errors.append(f"sessions.json: name {name!r} appears in both planned and issued")
        if session.get("status") not in SESSION_STATUSES:
            errors.append(f"{loc}.status: invalid session status {session.get('status')!r}")
        session_issue_id = session.get("issue_id")
        if session_issue_id not in issue_ids:
            errors.append(f"{loc}.issue_id: unknown issue {session_issue_id!r}")
        pr_id = session.get("pr_id")
        if pr_id is not None and pr_id not in pr_ids:
            errors.append(f"{loc}.pr_id: unknown PR {pr_id!r}")
        parent = session.get("parent_session_id")
        if parent is not None and parent not in all_session_ids:
            errors.append(f"{loc}.parent_session_id: unknown session {parent!r}")
        if parent == session.get("id"):
            errors.append(f"{loc}.parent_session_id: session cannot parent itself")
        external_id = session.get("external_id")
        if external_id is not None and (not isinstance(external_id, str) or not external_id):
            errors.append(f"{loc}.external_id: expected null or a non-empty string")
        elif isinstance(external_id, str):
            if external_id in external_ids:
                errors.append(f"sessions.json.issued: duplicate external_id {external_id!r}")
            external_ids.add(external_id)
        attempt = session.get("attempt")
        if not _is_int(attempt) or attempt < 1:
            errors.append(f"{loc}.attempt: expected a positive integer")
        read_only = session.get("read_only")
        if not isinstance(read_only, bool):
            errors.append(f"{loc}.read_only: expected a boolean")
        base_revision = session.get("base_revision")
        if base_revision is None:
            _nonempty_string(session.get("base_revision_reason"), f"{loc}.base_revision_reason", errors)
            issue = issue_by_id.get(session_issue_id, {})
            if _issue_execution_category(issue) == "implementation":
                errors.append(f"{loc}.base_revision: implementation sessions require an immutable Git SHA")
        else:
            _validate_sha(base_revision, f"{loc}.base_revision", errors)
        worktree = session.get("worktree")
        _nonempty_string(worktree, f"{loc}.worktree", errors)
        if isinstance(worktree, str) and worktree.strip() and not Path(worktree).is_absolute():
            errors.append(f"{loc}.worktree: expected an absolute path")
        owned_paths = _unique_string_list(session.get("owned_paths"), f"{loc}.owned_paths", errors)
        normalized_claims: list[tuple[str, ...]] = []
        if isinstance(worktree, str):
            for owned_index, owned_path in enumerate(owned_paths):
                normalized = _owned_path_parts(worktree, owned_path)
                if normalized is None:
                    errors.append(f"{loc}.owned_paths[{owned_index}]: invalid or repository-wide ownership path")
                    continue
                if any(_paths_overlap(normalized, existing) for existing in normalized_claims):
                    errors.append(f"{loc}.owned_paths[{owned_index}]: redundant overlapping ownership claim")
                normalized_claims.append(normalized)
        if read_only is True and owned_paths:
            errors.append(f"{loc}.owned_paths: read-only sessions cannot own writable paths")
        if read_only is False and not owned_paths:
            errors.append(f"{loc}.owned_paths: writable sessions must own at least one path")
        _nonempty_string(session.get("validation_command"), f"{loc}.validation_command", errors)
        _nonempty_string(session.get("result_envelope_path"), f"{loc}.result_envelope_path", errors)
        parse_timestamp(session.get("started_at"), f"{loc}.started_at", errors, nullable=True)
        parse_timestamp(session.get("ended_at"), f"{loc}.ended_at", errors, nullable=True)
        elapsed = session.get("elapsed_seconds")
        if elapsed is not None and (not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0):
            errors.append(f"{loc}.elapsed_seconds: expected null or a non-negative number")
        _validate_token_usage(session.get("token_usage"), f"{loc}.token_usage", errors)
        outcome = session.get("outcome_path")
        if outcome is not None and (not isinstance(outcome, str) or not outcome):
            errors.append(f"{loc}.outcome_path: expected null or a non-empty string")
        session_status = session.get("status")
        started_at = session.get("started_at")
        ended_at = session.get("ended_at")
        archive_status = session.get("archive_status")
        if archive_status not in ARCHIVE_STATUSES:
            errors.append(f"{loc}.archive_status: invalid archive status {archive_status!r}")
        timing_quality = session.get("timing_quality")
        if timing_quality is not None:
            _nonempty_string(timing_quality, f"{loc}.timing_quality", errors)
            if timing_quality not in TIMING_QUALITIES:
                errors.append(f"{loc}.timing_quality: unknown timing provenance {timing_quality!r}")
        timing_bounds = session.get("timing_bounds")
        bounded_timing = timing_quality == BOUNDED_TIMING_QUALITY
        if bounded_timing:
            if session_status not in {"finished", "failed", "archived"}:
                errors.append(f"{loc}.timing_quality: bounded timing is only valid for terminal sessions")
            if not isinstance(parent, str) or parent not in issued_by_id:
                errors.append(f"{loc}.timing_quality: parent-window timing requires an issued parent session")
            if not isinstance(timing_bounds, dict):
                errors.append(f"{loc}.timing_bounds: bounded timing requires an object")
            else:
                _require_keys(timing_bounds, ("not_before", "not_after"), f"{loc}.timing_bounds", errors)
                parse_timestamp(timing_bounds.get("not_before"), f"{loc}.timing_bounds.not_before", errors)
                parse_timestamp(timing_bounds.get("not_after"), f"{loc}.timing_bounds.not_after", errors)
                lower = _timestamp_value(timing_bounds.get("not_before"))
                upper = _timestamp_value(timing_bounds.get("not_after"))
                if lower is not None and upper is not None and upper < lower:
                    errors.append(f"{loc}.timing_bounds: not_after precedes not_before")
                parent_record = issued_by_id.get(parent) if isinstance(parent, str) else None
                if parent_record is not None:
                    parent_start = _timestamp_value(parent_record.get("started_at"))
                    parent_end = _timestamp_value(parent_record.get("ended_at"))
                    if lower is not None and parent_start is not None and lower < parent_start:
                        errors.append(f"{loc}.timing_bounds.not_before: precedes parent session start")
                    if upper is not None and parent_end is not None and upper > parent_end:
                        errors.append(f"{loc}.timing_bounds.not_after: exceeds parent session end")
            if started_at is not None or ended_at is not None or elapsed is not None:
                errors.append(f"{loc}: bounded timing must not invent point timestamps or elapsed duration")
        elif timing_bounds is not None:
            errors.append(
                f"{loc}.timing_bounds: only allowed with timing_quality {BOUNDED_TIMING_QUALITY!r}"
            )
        if session_status == "issued":
            if started_at is not None or ended_at is not None or elapsed is not None:
                errors.append(f"{loc}: issued session cannot have lifecycle timing yet")
        elif session_status == "running":
            if started_at is None:
                errors.append(f"{loc}.started_at: required for running session")
            if ended_at is not None or elapsed is not None:
                errors.append(f"{loc}: running session cannot have terminal timing")
        elif session_status in {"finished", "failed", "archived"}:
            if not bounded_timing and (started_at is None or ended_at is None or elapsed is None):
                errors.append(f"{loc}: terminal session requires started_at, ended_at, and elapsed_seconds")
        start_time = _timestamp_value(started_at)
        end_time = _timestamp_value(ended_at)
        if start_time is not None and end_time is not None and end_time < start_time:
            errors.append(f"{loc}: ended_at precedes started_at")
        if (
            start_time is not None
            and end_time is not None
            and isinstance(elapsed, (int, float))
            and not isinstance(elapsed, bool)
            and timing_quality in {None, "runtime-exact"}
            and abs((end_time - start_time).total_seconds() - elapsed) > 0.01
        ):
            errors.append(f"{loc}.timing_quality: non-exact timing must be labeled approximate or derived")
        if session_status in ACTIVE_SESSION_STATUSES and archive_status not in {"active", "not_requested"}:
            errors.append(f"{loc}.archive_status: active session must be active or not_requested")
        if session_status == "archived":
            if archive_status not in {"archived", "retired-locally-no-cli-session"}:
                errors.append(f"{loc}.archive_status: archived session lacks completed archive evidence")
            if outcome is None:
                errors.append(f"{loc}.outcome_path: required for archived session")

    session_by_id = {
        session["id"]: session
        for session in [*planned, *issued]
        if isinstance(session.get("id"), str)
    }
    _validate_cycle(
        all_session_ids,
        lambda session_id: [session_by_id[session_id]["parent_session_id"]]
        if session_by_id.get(session_id, {}).get("parent_session_id") is not None
        else [],
        "session parent hierarchy",
        errors,
    )

    active_writable_claims: list[tuple[str, str, str, tuple[str, ...]]] = []
    for session in issued:
        if session.get("status") not in ACTIVE_SESSION_STATUSES or session.get("read_only") is not False:
            continue
        worktree = session.get("worktree")
        owned_paths = session.get("owned_paths")
        if not isinstance(worktree, str) or not isinstance(owned_paths, list):
            continue
        for owned_path in owned_paths:
            if not isinstance(owned_path, str):
                continue
            normalized = _owned_path_parts(worktree, owned_path)
            if normalized is not None:
                active_writable_claims.append(
                    (
                        str(session.get("id")),
                        owned_path,
                        _ownership_scope(worktree, owned_path),
                        normalized,
                    )
                )
    for left_index, (left_id, left_path, left_scope, left_parts) in enumerate(active_writable_claims):
        for right_id, right_path, right_scope, right_parts in active_writable_claims[left_index + 1 :]:
            if (
                left_id != right_id
                and left_scope == right_scope
                and _paths_overlap(left_parts, right_parts)
            ):
                errors.append(
                    "active writable ownership overlap: "
                    f"session {left_id!r} path {left_path!r} overlaps session {right_id!r} path {right_path!r}"
                )

    for issue in issues:
        if issue.get("status") != "in_progress" or _issue_execution_category(issue) != "implementation":
            continue
        issue_id = issue.get("id")
        orchestrators = [
            session
            for session in issued
            if session.get("issue_id") == issue_id
            and session.get("role") == "orchestrator"
            and session.get("status") in ACTIVE_SESSION_STATUSES
        ]
        if len(orchestrators) != 1:
            errors.append(
                f"implementation issue {issue_id!r}: in_progress requires exactly one active orchestrator; "
                f"found {len(orchestrators)}"
            )
            continue
        orchestrator = orchestrators[0]
        if issue.get("owner_session_id") != orchestrator.get("id"):
            errors.append(
                f"implementation issue {issue_id!r}: owner_session_id must name its active orchestrator"
            )
        if orchestrator.get("read_only") is not False:
            errors.append(f"implementation issue {issue_id!r}: active orchestrator must be writable")

    stage_required = (
        "id",
        "name",
        "status",
        "issue_ids",
        "started_at",
        "ended_at",
        "elapsed_seconds",
        "token_usage",
        "subagents_issued",
        "max_concurrency",
        "outputs",
        "incident_ids",
    )
    for index, stage in enumerate(stages):
        loc = f"stages.json.stages[{index}]"
        _require_keys(stage, stage_required, loc, errors)
        _nonempty_string(stage.get("name"), f"{loc}.name", errors)
        if stage.get("status") not in STAGE_STATUSES:
            errors.append(f"{loc}.status: invalid stage status {stage.get('status')!r}")
        refs = stage.get("issue_ids")
        if not isinstance(refs, list) or any(not isinstance(item, str) for item in refs):
            errors.append(f"{loc}.issue_ids: expected a list of issue ids")
        else:
            for issue_id in refs:
                if issue_id not in issue_ids:
                    errors.append(f"{loc}.issue_ids: unknown issue {issue_id!r}")
        # Incidents live in research/metrics/incidents.jsonl, outside this
        # state store's transaction boundary.  Reconciliation belongs to the
        # aggregate checker; this ledger validates only the reference shape.
        _string_list(stage.get("incident_ids"), f"{loc}.incident_ids", errors)
        parse_timestamp(stage.get("started_at"), f"{loc}.started_at", errors, nullable=True)
        parse_timestamp(stage.get("ended_at"), f"{loc}.ended_at", errors, nullable=True)
        elapsed = stage.get("elapsed_seconds")
        if elapsed is not None and (not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0):
            errors.append(f"{loc}.elapsed_seconds: expected null or a non-negative number")
        _validate_token_usage(stage.get("token_usage"), f"{loc}.token_usage", errors)
        for key in ("subagents_issued", "max_concurrency"):
            if not _is_int(stage.get(key)) or stage[key] < 0:
                errors.append(f"{loc}.{key}: expected a non-negative integer")
        if not isinstance(stage.get("outputs"), list):
            errors.append(f"{loc}.outputs: expected a list")

    active_revision = protocols_doc.get("active_revision")
    _nonempty_string(active_revision, "protocols.json.active_revision", errors, nullable=True)
    revision_names: set[str] = set()
    active_names: list[str] = []
    for index, revision in enumerate(revisions):
        loc = f"protocols.json.revisions[{index}]"
        _require_keys(
            revision,
            (
                "revision",
                "status",
                "effective_at",
                "cause",
                "evidence_ids",
                "review_pr_id",
                "retirement_condition",
            ),
            loc,
            errors,
        )
        revision_name = revision.get("revision")
        _nonempty_string(revision_name, f"{loc}.revision", errors)
        if isinstance(revision_name, str):
            if revision_name in revision_names:
                errors.append(f"{loc}.revision: duplicate {revision_name!r}")
            revision_names.add(revision_name)
        status = revision.get("status")
        if status not in {"active", "superseded", "retired"}:
            errors.append(f"{loc}.status: invalid protocol status {status!r}")
        elif status == "active" and isinstance(revision_name, str):
            active_names.append(revision_name)
        parse_timestamp(revision.get("effective_at"), f"{loc}.effective_at", errors)
        _nonempty_string(revision.get("cause"), f"{loc}.cause", errors)
        _unique_string_list(revision.get("evidence_ids"), f"{loc}.evidence_ids", errors)
        review_pr_id = revision.get("review_pr_id")
        if review_pr_id is not None and review_pr_id not in pr_ids:
            errors.append(f"{loc}.review_pr_id: unknown PR {review_pr_id!r}")
        _nonempty_string(
            revision.get("retirement_condition"),
            f"{loc}.retirement_condition",
            errors,
        )
    if active_revision is None and revisions:
        errors.append("protocols.json.active_revision: required when revisions exist")
    if active_revision is not None and active_revision not in revision_names:
        errors.append(f"protocols.json.active_revision: unknown revision {active_revision!r}")
    if active_revision is not None and active_names != [active_revision]:
        errors.append("protocols.json: exactly the named active_revision must have status 'active'")

    if errors:
        raise ValidationError(errors)


def validate_event_log(
    path: Path,
    documents: Mapping[str, Any] | None = None,
) -> None:
    """Validate canonical envelopes, chronology, and issued-session lifecycle."""

    if not path.exists():
        return
    errors: list[str] = []
    events: list[tuple[int, dict[str, Any], dt.datetime]] = []
    previous_timestamp: dt.datetime | None = None
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{path}:{line_number}: invalid JSON: {error.msg}")
                continue
            if not isinstance(value, dict):
                errors.append(f"{path}:{line_number}: event must be an object")
                continue
            location = f"{path}:{line_number}"
            _require_keys(
                value,
                ("schema_version", "timestamp", "event", "actor", "pid", "payload"),
                location,
                errors,
            )
            if value.get("schema_version") != SCHEMA_VERSION:
                errors.append(f"{location}.schema_version: expected {SCHEMA_VERSION}")
            parse_timestamp(value.get("timestamp"), f"{location}.timestamp", errors)
            timestamp = _timestamp_value(value.get("timestamp"))
            _nonempty_string(value.get("event"), f"{location}.event", errors)
            _nonempty_string(value.get("actor"), f"{location}.actor", errors)
            pid = value.get("pid")
            if pid is None:
                _nonempty_string(
                    value.get("pid_unavailable_reason"),
                    f"{location}.pid_unavailable_reason",
                    errors,
                )
            elif not _is_int(pid) or pid <= 0:
                errors.append(f"{location}.pid: expected a positive integer or null")
            if not isinstance(value.get("payload"), dict):
                errors.append(f"{location}.payload: expected an object")
            if timestamp is not None:
                if previous_timestamp is not None and timestamp < previous_timestamp:
                    errors.append(f"{location}.timestamp: event log is not chronological")
                previous_timestamp = timestamp
                events.append((line_number, value, timestamp))

    if documents is not None:
        sessions_document = documents.get("sessions.json", {})
        issued_sessions = sessions_document.get("issued", []) if isinstance(sessions_document, dict) else []
        sessions = {
            item.get("id"): item
            for item in issued_sessions
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        lifecycle: dict[str, list[tuple[str, dt.datetime, int]]] = {
            session_id: [] for session_id in sessions
        }
        for line_number, event_value, timestamp in events:
            payload = event_value.get("payload")
            if not isinstance(payload, dict):
                continue
            session_id = payload.get("session_id")
            # Schema-v1 issuance originally used payload.id. Keep that narrow
            # append-only-history fallback; all new lifecycle writers use session_id.
            if session_id is None and event_value.get("event") == "session.issued":
                session_id = payload.get("id")
            if session_id is None:
                continue
            if not isinstance(session_id, str) or session_id not in sessions:
                errors.append(
                    f"{path}:{line_number}.payload: references unknown issued session {session_id!r}"
                )
                continue
            event_name = event_value.get("event")
            phase: str | None = None
            if event_name == "session.issued":
                phase = "issued"
            elif event_name in {"session.finished", "session.failed"}:
                phase = "terminal"
            elif event_name == "session.archived":
                phase = "archived"
            elif event_name == "record.transitioned" and payload.get("kind") in {
                "session",
                "issued-session",
            }:
                status = payload.get("status")
                if status == "issued":
                    phase = "issued"
                elif status in {"finished", "failed"}:
                    phase = "terminal"
                elif status == "archived":
                    phase = "archived"
            if phase is not None:
                lifecycle[session_id].append((phase, timestamp, line_number))

        for session_id, session in sessions.items():
            phases = lifecycle[session_id]
            issued = [item for item in phases if item[0] == "issued"]
            terminal = [item for item in phases if item[0] == "terminal"]
            archived = [item for item in phases if item[0] == "archived"]
            location = f"events[{session_id}]"
            if len(issued) != 1:
                errors.append(f"{location}: expected exactly one session issuance event")
            status = session.get("status")
            if status == "archived":
                if len(terminal) != 1:
                    errors.append(f"{location}: archived session needs exactly one terminal event")
                if len(archived) != 1:
                    errors.append(f"{location}: archived session needs exactly one archive event")
                if terminal and archived and terminal[0][1] > archived[0][1]:
                    errors.append(f"{location}: archive event precedes terminal event")
            elif status in ACTIVE_SESSION_STATUSES and (terminal or archived):
                errors.append(f"{location}: active session has terminal lifecycle events")
    if errors:
        raise ValidationError(errors)


def atomic_write_json(path: Path, value: Any) -> None:
    """Write canonical JSON through a same-directory temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=True, sort_keys=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


class WorkflowStore:
    """Concurrency-safe access to the local workflow ledgers."""

    def __init__(self, state_dir: Path, runtime_dir: Path, events_path: Path):
        self.state_dir = state_dir
        self.runtime_dir = runtime_dir
        self.events_path = events_path

    @contextmanager
    def _lock(self, *, exclusive: bool) -> Any:
        # A directory fd supports flock on the Linux hosts used by this
        # project.  Read-only validation therefore takes the same lock as a
        # writer without creating an ignored runtime file.
        if exclusive:
            self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.state_dir, os.O_RDONLY | os.O_DIRECTORY)
        except OSError as error:
            raise WorkflowError(f"could not open state directory {self.state_dir}: {error}") from error
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            yield descriptor
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def load(self) -> dict[str, Any]:
        documents: dict[str, Any] = {}
        errors: list[str] = []
        for filename in DEFAULT_DOCUMENTS:
            path = self.state_dir / filename
            try:
                with path.open("r", encoding="utf-8") as stream:
                    documents[filename] = json.load(stream)
            except FileNotFoundError:
                errors.append(f"missing state file: {path}")
            except json.JSONDecodeError as error:
                errors.append(f"{path}:{error.lineno}:{error.colno}: invalid JSON: {error.msg}")
        if errors:
            raise ValidationError(errors)
        return documents

    def validate(self, *, include_events: bool = True) -> dict[str, Any]:
        with self._lock(exclusive=False):
            documents = self.load()
            validate_documents(documents)
            if include_events:
                validate_event_log(self.events_path, documents)
            return documents

    def initialize(self, *, missing_only: bool = False) -> list[str]:
        created: list[str] = []
        with self._lock(exclusive=True):
            existing = [name for name in DEFAULT_DOCUMENTS if (self.state_dir / name).exists()]
            if existing and not missing_only:
                raise WorkflowError(
                    "refusing to overwrite existing state files: " + ", ".join(existing)
                )
            for filename, document in DEFAULT_DOCUMENTS.items():
                path = self.state_dir / filename
                if path.exists():
                    continue
                atomic_write_json(path, copy.deepcopy(document))
                created.append(filename)
            self.append_event("workflow.initialized", {"created": created}, lock_held=True)
        return created

    def append_event(self, event: str, payload: Mapping[str, Any], *, lock_held: bool = False) -> None:
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "timestamp": utc_now(),
            "event": event,
            "actor": os.environ.get("WORKFLOW_ACTOR", "local"),
            "pid": os.getpid(),
            "payload": payload,
        }
        encoded = (json.dumps(envelope, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")

        def write() -> None:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(self.events_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                os.write(descriptor, encoded)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

        if lock_held:
            write()
        else:
            with self._lock(exclusive=True):
                write()

    def mutate(
        self,
        filename: str,
        event: str,
        payload: Mapping[str, Any],
        mutation: Callable[[MutableMapping[str, Any]], Any],
    ) -> Any:
        if filename not in DEFAULT_DOCUMENTS:
            raise WorkflowError(f"unknown state document {filename!r}")
        with self._lock(exclusive=True):
            documents = self.load()
            changed_document = copy.deepcopy(documents[filename])
            result = mutation(changed_document)
            documents[filename] = changed_document
            validate_documents(documents)
            atomic_write_json(self.state_dir / filename, changed_document)
            self.append_event(event, payload, lock_held=True)
            return result


def dependency_ready_issues(documents: Mapping[str, Any], *, stage_id: str | None = None) -> list[dict[str, Any]]:
    """Return planned/ready issues whose dependencies are all exactly done."""

    validate_documents(documents)
    issues = documents["issues.json"]["issues"]
    issue_by_id = {issue["id"]: issue for issue in issues}
    allowed_ids: set[str] | None = None
    if stage_id is not None:
        stage = next(
            (item for item in documents["stages.json"]["stages"] if item["id"] == stage_id),
            None,
        )
        if stage is None:
            raise WorkflowError(f"unknown stage {stage_id!r}")
        allowed_ids = set(stage["issue_ids"])
    ready = []
    for issue in issues:
        if issue["status"] not in {"planned", "ready"}:
            continue
        if allowed_ids is not None and issue["id"] not in allowed_ids:
            continue
        if all(issue_by_id[dependency]["status"] == "done" for dependency in issue["dependency_ids"]):
            ready.append(copy.deepcopy(issue))
    return sorted(ready, key=lambda issue: issue["id"])


def _find_record(document: MutableMapping[str, Any], collection: str, record_id: str) -> MutableMapping[str, Any]:
    for record in document[collection]:
        if record.get("id") == record_id:
            return record
    raise WorkflowError(f"unknown record {record_id!r} in {collection}")


def _parse_assignment(assignment: str) -> tuple[list[str], Any]:
    if "=" not in assignment:
        raise WorkflowError(f"invalid assignment {assignment!r}; expected FIELD=JSON")
    path, raw_value = assignment.split("=", 1)
    keys = path.split(".")
    if any(not key for key in keys):
        raise WorkflowError(f"invalid dotted field {path!r}")
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value
    return keys, value


def _set_nested(record: MutableMapping[str, Any], keys: Sequence[str], value: Any) -> None:
    target = record
    for key in keys[:-1]:
        child = target.get(key)
        if child is None:
            child = {}
            target[key] = child
        if not isinstance(child, dict):
            raise WorkflowError(f"cannot descend through non-object field {key!r}")
        target = child
    target[keys[-1]] = value


def _require_append_only(old: Any, new: Any, field: str) -> None:
    if not isinstance(old, list) or not isinstance(new, list) or new[: len(old)] != old:
        raise WorkflowError(f"PR field {field!r} is append-only")


def _require_findings_update(old: Any, new: Any) -> None:
    if not isinstance(old, list) or not isinstance(new, list) or len(new) < len(old):
        raise WorkflowError("PR field 'findings' cannot remove evidence")
    mutable_resolution_fields = {
        "status",
        "disposition",
        "disposition_evidence",
        "resolved_by_review_id",
    }
    for index, old_finding in enumerate(old):
        new_finding = new[index]
        if not isinstance(old_finding, dict) or not isinstance(new_finding, dict):
            raise WorkflowError("PR finding evidence must remain structured objects")
        old_immutable = {key: value for key, value in old_finding.items() if key not in mutable_resolution_fields}
        new_immutable = {key: value for key, value in new_finding.items() if key not in mutable_resolution_fields}
        if old_immutable != new_immutable:
            raise WorkflowError("PR finding identity and introduction evidence are immutable")
        if old_finding.get("status") == "resolved" and new_finding != old_finding:
            raise WorkflowError("resolved PR finding dispositions are immutable")
        if old_finding.get("status") == "open" and new_finding.get("status") not in {"open", "resolved"}:
            raise WorkflowError("PR findings may only transition from open to resolved")


def _check_pr_update(record: Mapping[str, Any], assignments: Sequence[tuple[list[str], Any]]) -> None:
    for keys, value in assignments:
        field = keys[0]
        if field in {"checks", "reviews", "implementer_session_ids"}:
            if len(keys) != 1:
                raise WorkflowError(f"PR field {field!r} must be replaced as one append-only list")
            _require_append_only(record.get(field), value, field)
        elif field == "findings":
            if len(keys) != 1:
                raise WorkflowError("PR findings must be replaced as one disposition-aware list")
            _require_findings_update(record.get("findings"), value)
        elif field == "integration_sha":
            old = record.get(field)
            if old is not None and value != old:
                raise WorkflowError("PR integration_sha is immutable once recorded")


def _check_session_update(record: Mapping[str, Any], assignments: Sequence[tuple[list[str], Any]]) -> None:
    immutable = {
        "name",
        "backend",
        "role",
        "issue_id",
        "pr_id",
        "parent_session_id",
        "attempt",
        "read_only",
        "base_revision",
        "base_revision_reason",
        "worktree",
        "owned_paths",
        "validation_command",
        "result_envelope_path",
    }
    set_once = {
        "external_id",
        "started_at",
        "ended_at",
        "elapsed_seconds",
        "timing_quality",
        "timing_bounds",
        "outcome_path",
    }
    for keys, value in assignments:
        field = keys[0]
        if field in immutable:
            raise WorkflowError(f"issued-session authority field {field!r} is immutable")
        if field in set_once:
            old = record.get(field)
            if old is not None and value != old:
                raise WorkflowError(f"issued-session provenance field {field!r} is immutable once recorded")


def _record_spec(kind: str) -> tuple[str, str]:
    try:
        return STATE_FILES[kind]
    except KeyError as error:
        raise WorkflowError(f"unknown record kind {kind!r}") from error


def _load_json_argument(raw: str | None, file_path: str | None) -> dict[str, Any]:
    if (raw is None) == (file_path is None):
        raise WorkflowError("provide exactly one of --json or --file")
    try:
        if raw is not None:
            value = json.loads(raw)
        else:
            with Path(file_path).open("r", encoding="utf-8") as stream:  # type: ignore[arg-type]
                value = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f"could not load record JSON: {error}") from error
    if not isinstance(value, dict):
        raise WorkflowError("record JSON must be an object")
    return value


def _elapsed_seconds(started_at: Any, ended_at: str) -> float | None:
    if not isinstance(started_at, str):
        return None
    try:
        start = dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round(max(0.0, (end - start).total_seconds()), 3)


def _transition_record(kind: str, record: MutableMapping[str, Any], new_status: str) -> None:
    transitions = {
        "issue": ISSUE_TRANSITIONS,
        "pr": PR_TRANSITIONS,
        "issued-session": SESSION_TRANSITIONS,
        "stage": STAGE_TRANSITIONS,
    }
    if kind not in transitions:
        raise WorkflowError(f"status transitions are not supported for {kind!r}")
    old_status = record.get("status")
    if old_status == new_status:
        return
    if old_status not in transitions[kind] or new_status not in transitions[kind][old_status]:
        raise WorkflowError(f"invalid {kind} transition {old_status!r} -> {new_status!r}")
    now = utc_now()
    record["status"] = new_status
    if kind in {"issue", "pr"}:
        record["updated_at"] = now
        if kind == "pr" and new_status == "merged":
            record["merged_at"] = now
    elif kind == "issued-session":
        if new_status == "running" and record.get("started_at") is None:
            record["started_at"] = now
        if new_status == "failed" and record.get("started_at") is None:
            record["started_at"] = now
        if new_status in {"finished", "failed", "archived"} and record.get("ended_at") is None:
            record["ended_at"] = now
            record["elapsed_seconds"] = _elapsed_seconds(record.get("started_at"), now)
        if new_status == "archived":
            record["archive_status"] = "archived"
    elif kind == "stage":
        if new_status == "in_progress" and record.get("started_at") is None:
            record["started_at"] = now
        if new_status == "completed" and record.get("ended_at") is None:
            record["ended_at"] = now
            record["elapsed_seconds"] = _elapsed_seconds(record.get("started_at"), now)


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="repository root")
    parser.add_argument("--state-dir", default="workflow/state", help="state directory, relative to root")
    parser.add_argument("--runtime-dir", default=".workflow-runtime", help="ignored runtime directory")
    parser.add_argument("--events", default="workflow/events.jsonl", help="append-only event log")
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init", help="create empty v1 state files")
    initialize.add_argument("--missing-only", action="store_true")

    validate = subparsers.add_parser("validate", help="validate all state files and references")
    validate.add_argument("--skip-events", action="store_true")
    validate.add_argument("--json", action="store_true", dest="json_output")

    ready = subparsers.add_parser("ready", help="list issues whose dependencies are done")
    ready.add_argument("--stage")
    ready.add_argument("--ids-only", action="store_true")

    show = subparsers.add_parser("show", help="show a collection or one record")
    show.add_argument("kind", choices=sorted(STATE_FILES))
    show.add_argument("id", nargs="?")

    add = subparsers.add_parser("add", help="atomically append and validate one record")
    add.add_argument("kind", choices=sorted(STATE_FILES))
    add.add_argument("--json")
    add.add_argument("--file")

    update = subparsers.add_parser("update", help="atomically update fields on one record")
    update.add_argument("kind", choices=sorted(STATE_FILES))
    update.add_argument("id")
    update.add_argument("--set", action="append", required=True, dest="assignments")

    transition = subparsers.add_parser("transition", help="perform a checked lifecycle transition")
    transition.add_argument("kind", choices=("issue", "pr", "issued-session", "stage"))
    transition.add_argument("id")
    transition.add_argument("status")

    issue_session = subparsers.add_parser(
        "issue-session", help="atomically move a planned session into the issued ledger"
    )
    issue_session.add_argument("id", help="planned session id")
    issue_session.add_argument("--json")
    issue_session.add_argument("--file")
    return parser


def run_cli(arguments: argparse.Namespace) -> Any:
    root = Path(arguments.root).resolve()
    store = WorkflowStore(
        _resolve(root, arguments.state_dir),
        _resolve(root, arguments.runtime_dir),
        _resolve(root, arguments.events),
    )
    if arguments.command == "init":
        return {"created": store.initialize(missing_only=arguments.missing_only)}
    if arguments.command == "validate":
        documents = store.validate(include_events=not arguments.skip_events)
        counts = {
            "issues": len(documents["issues.json"]["issues"]),
            "pull_requests": len(documents["prs.json"]["pull_requests"]),
            "planned_sessions": len(documents["sessions.json"]["planned"]),
            "issued_sessions": len(documents["sessions.json"]["issued"]),
            "stages": len(documents["stages.json"]["stages"]),
        }
        return {"valid": True, "counts": counts}
    if arguments.command == "ready":
        documents = store.validate()
        ready = dependency_ready_issues(documents, stage_id=arguments.stage)
        return [item["id"] for item in ready] if arguments.ids_only else ready
    if arguments.command == "show":
        documents = store.validate()
        filename, collection = _record_spec(arguments.kind)
        records = documents[filename][collection]
        if arguments.id is None:
            return records
        record = next((item for item in records if item.get("id") == arguments.id), None)
        if record is None:
            raise WorkflowError(f"unknown record {arguments.id!r} in {collection}")
        return record
    if arguments.command == "add":
        filename, collection = _record_spec(arguments.kind)
        record = _load_json_argument(arguments.json, arguments.file)

        def append(document: MutableMapping[str, Any]) -> dict[str, Any]:
            document[collection].append(record)
            return record

        return store.mutate(
            filename,
            "record.added",
            {"kind": arguments.kind, "id": record.get("id")},
            append,
        )
    if arguments.command == "update":
        filename, collection = _record_spec(arguments.kind)
        assignments = [_parse_assignment(item) for item in arguments.assignments]
        immutable = {"id", "created_at", "status"}
        if arguments.kind == "issue":
            immutable.update({"kind", "execution_category"})
        if arguments.kind == "pr":
            immutable.update({"base", "base_sha", "head", "issue_ids", "merged_at"})
        attempted_immutable = sorted({keys[0] for keys, _ in assignments} & immutable)
        if attempted_immutable:
            raise WorkflowError("immutable field(s) cannot be updated: " + ", ".join(attempted_immutable))

        def update_record(document: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
            record = _find_record(document, collection, arguments.id)
            old_head = record.get("head_sha") if arguments.kind == "pr" else None
            if arguments.kind == "pr" and record.get("status") in {"merged", "closed"}:
                raise WorkflowError("merged or closed PR records cannot be updated")
            if arguments.kind == "pr":
                _check_pr_update(record, assignments)
            elif arguments.kind == "issued-session":
                _check_session_update(record, assignments)
            for keys, value in assignments:
                _set_nested(record, keys, value)
            if (
                arguments.kind == "pr"
                and old_head != record.get("head_sha")
                and record.get("status") in {"ready", "approved"}
            ):
                record["status"] = "changes_requested"
                record["integration_sha"] = None
                record["merged_at"] = None
            if arguments.kind in {"issue", "pr"} and not any(keys == ["updated_at"] for keys, _ in assignments):
                record["updated_at"] = utc_now()
            return record

        return store.mutate(
            filename,
            "record.updated",
            {
                "kind": arguments.kind,
                "id": arguments.id,
                "fields": [".".join(keys) for keys, _ in assignments],
            },
            update_record,
        )
    if arguments.command == "transition":
        filename, collection = _record_spec(arguments.kind)

        def transition_record(document: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
            record = _find_record(document, collection, arguments.id)
            _transition_record(arguments.kind, record, arguments.status)
            return record

        event_payload = {"kind": arguments.kind, "status": arguments.status}
        event_payload[
            "session_id" if arguments.kind == "issued-session" else "id"
        ] = arguments.id
        return store.mutate(
            filename,
            "record.transitioned",
            event_payload,
            transition_record,
        )
    if arguments.command == "issue-session":
        additions = _load_json_argument(arguments.json, arguments.file)

        def issue_planned(document: MutableMapping[str, Any]) -> dict[str, Any]:
            planned_record = _find_record(document, "planned", arguments.id)
            issued_record = copy.deepcopy(planned_record)
            issued_record.update(additions)
            if issued_record.get("id") != arguments.id:
                raise WorkflowError("issued session id must match the planned session id")
            issued_record["status"] = "issued"
            document["planned"] = [item for item in document["planned"] if item.get("id") != arguments.id]
            document["issued"].append(issued_record)
            return issued_record

        return store.mutate(
            "sessions.json",
            "session.issued",
            {"session_id": arguments.id},
            issue_planned,
        )
    raise WorkflowError(f"unsupported command {arguments.command!r}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        result = run_cli(arguments)
    except ValidationError as error:
        print(json.dumps({"valid": False, "errors": list(error.errors)}, indent=2), file=sys.stderr)
        return 2
    except WorkflowError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
