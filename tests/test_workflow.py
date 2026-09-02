from __future__ import annotations

import copy
from contextlib import contextmanager
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import workflow  # noqa: E402
import check_workflow  # noqa: E402
import github_workflow  # noqa: E402


NOW = "2026-08-30T00:00:00Z"
CHECKED = "2026-08-30T00:01:00Z"
REVIEW_STARTED = "2026-08-30T00:02:00Z"
REVIEW_ENDED = "2026-08-30T00:03:00Z"
REVIEW2_STARTED = "2026-08-30T00:04:00Z"
REVIEW2_ENDED = "2026-08-30T00:05:00Z"
CHECKED3 = "2026-08-30T00:06:00Z"
REVIEW3_STARTED = "2026-08-30T00:07:00Z"
REVIEW3_ENDED = "2026-08-30T00:08:00Z"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40
RESOLUTION_HEAD_SHA = "c" * 40
ADVANCED_HEAD_SHA = "d" * 40


def unavailable_tokens() -> dict[str, object]:
    return {
        "input": None,
        "output": None,
        "total": None,
        "availability_reason": "not exposed",
    }


def issue(issue_id: str, status: str, dependencies: list[str] | None = None, **extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": issue_id,
        "title": issue_id,
        "kind": "formalization",
        "status": status,
        "parent_id": None,
        "dependency_ids": dependencies or [],
        "labels": [],
        "acceptance_gates": [],
        "owner_session_id": None,
        "source_refs": [],
        "created_at": NOW,
        "updated_at": NOW,
    }
    value.update(extra)
    return value


def issued_session(
    session_id: str,
    *,
    issue_id: str = "QPBT-002",
    pr_id: str | None = None,
    role: str = "prover",
    status: str = "archived",
    read_only: bool = False,
    owned_paths: list[str] | None = None,
    started_at: str | None = REVIEW_STARTED,
    ended_at: str | None = REVIEW_ENDED,
    elapsed_seconds: float | None = 60.0,
) -> dict[str, object]:
    if owned_paths is None:
        owned_paths = [] if read_only else ["MIPStarRE/QPBT/Test.lean"]
    archived = status == "archived"
    return {
        "id": session_id,
        "name": session_id,
        "backend": "codex-cli",
        "role": role,
        "status": status,
        "issue_id": issue_id,
        "pr_id": pr_id,
        "parent_session_id": None,
        "external_id": f"thread-{session_id}",
        "attempt": 1,
        "read_only": read_only,
        "base_revision": BASE_SHA,
        "worktree": "/tmp/qpbt-worktree",
        "owned_paths": owned_paths,
        "validation_command": "lake env lean MIPStarRE/QPBT/Test.lean",
        "result_envelope_path": f".workflow-runtime/runs/{session_id}/result.json",
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_seconds": elapsed_seconds,
        "token_usage": unavailable_tokens(),
        "archive_status": "archived" if archived else "active",
        "outcome_path": f".workflow-runtime/runs/{session_id}/result.json" if archived else None,
    }


def planned_session(
    session_id: str,
    *,
    issue_id: str = "QPBT-002",
    role: str = "reviewer",
    read_only: bool = True,
    worktree: str = "/tmp/qpbt-worktree",
    owned_paths: list[str] | None = None,
) -> dict[str, object]:
    """Build a complete planned row suitable for dispatch materialization."""

    if owned_paths is None:
        owned_paths = [] if read_only else ["MIPStarRE/QPBT/Test.lean"]
    record = issued_session(
        session_id,
        issue_id=issue_id,
        role=role,
        status="issued",
        read_only=read_only,
        owned_paths=owned_paths,
        started_at=None,
        ended_at=None,
        elapsed_seconds=None,
    )
    record["worktree"] = worktree
    record["status"] = "planned"
    record["external_id"] = None
    record["archive_status"] = "not_requested"
    record["outcome_path"] = None
    return record


def launch_confirmations(*sessions: dict[str, object]) -> dict[str, str]:
    return {
        str(session["id"]): f"launched-{session['id']}"
        for session in sessions
    }


def collaboration_planned_session(
    session_id: str,
    **arguments: object,
) -> dict[str, object]:
    record = planned_session(session_id, **arguments)  # type: ignore[arg-type]
    record["backend"] = "codex-collaboration"
    return record


def check_evidence(
    *,
    check_id: str = "check-full-build",
    head_sha: str = HEAD_SHA,
    status: str = "passed",
    completed_at: str = CHECKED,
) -> dict[str, object]:
    return {
        "id": check_id,
        "name": "full build",
        "command": "lake build",
        "status": status,
        "base_sha": BASE_SHA,
        "head_sha": head_sha,
        "completed_at": completed_at,
        "result_path": ".workflow-runtime/checks/full-build.log",
    }


def review_evidence(
    reviewer_id: str = "i002-reviewer-a01-source",
    *,
    review_id: str = "review-001",
    head_sha: str = HEAD_SHA,
    verdict: str = "approve",
    finding_ids: list[str] | None = None,
    started_at: str = REVIEW_STARTED,
    completed_at: str = REVIEW_ENDED,
) -> dict[str, object]:
    return {
        "id": review_id,
        "reviewer_session_id": reviewer_id,
        "verdict": verdict,
        "base_sha": BASE_SHA,
        "head_sha": head_sha,
        "started_at": started_at,
        "completed_at": completed_at,
        "result_path": f".workflow-runtime/reviews/{review_id}.json",
        "finding_ids": finding_ids or [],
    }


def pull_request(
    *,
    status: str = "approved",
    head_sha: str = HEAD_SHA,
    checks: list[dict[str, object]] | None = None,
    reviews: list[dict[str, object]] | None = None,
    findings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id": "LPR-001",
        "title": "feat(QPBT/Test): test",
        "status": status,
        "issue_ids": ["QPBT-002"],
        "base": "main",
        "head": "issue/qpbt-002",
        "base_sha": BASE_SHA,
        "head_sha": head_sha,
        "implementer_session_ids": ["i002-prover-a01-implementation"],
        "checks": [check_evidence(head_sha=head_sha)] if checks is None else checks,
        "reviews": [review_evidence(head_sha=head_sha)] if reviews is None else reviews,
        "findings": [] if findings is None else findings,
        "integration_sha": None,
        "merged_at": None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def add_pr_sessions(state: dict[str, object]) -> None:
    state["sessions.json"]["issued"] = [
        issued_session("i002-prover-a01-implementation", pr_id="LPR-001"),
        issued_session(
            "i002-reviewer-a01-source",
            pr_id="LPR-001",
            role="reviewer",
            read_only=True,
        ),
    ]


def documents() -> dict[str, object]:
    return {
        "issues.json": {
            "schema_version": 1,
            "next_sequence": 3,
            "issues": [issue("QPBT-001", "done"), issue("QPBT-002", "planned", ["QPBT-001"], note="keep")],
        },
        "prs.json": {"schema_version": 1, "next_sequence": 1, "pull_requests": []},
        "sessions.json": {"schema_version": 1, "planned": [], "issued": []},
        "stages.json": {
            "schema_version": 1,
            "stages": [
                {
                    "id": "STAGE-01",
                    "name": "test",
                    "status": "in_progress",
                    "issue_ids": ["QPBT-002"],
                    "started_at": NOW,
                    "ended_at": None,
                    "elapsed_seconds": None,
                    "token_usage": unavailable_tokens(),
                    "subagents_issued": 0,
                    "max_concurrency": 1,
                    "outputs": [],
                    "incident_ids": ["INC-001"],
                }
            ],
        },
        "protocols.json": {
            "schema_version": 1,
            "active_revision": "0.1.0",
            "revisions": [
                {
                    "revision": "0.1.0",
                    "status": "active",
                    "effective_at": NOW,
                    "cause": "test protocol",
                    "evidence_ids": [],
                    "review_pr_id": None,
                    "retirement_condition": "re-evaluate after three uses",
                }
            ],
        },
    }


def finding_reconfirmation_documents(
    *,
    confirmation_ids: list[str] | None = None,
    confirmation_head_sha: str = ADVANCED_HEAD_SHA,
    confirmation_verdict: str = "approve",
) -> dict[str, object]:
    """Build an approved PR whose finding resolution predates its current head."""

    state = documents()
    finding = {
        "id": "F-001",
        "introduced_review_id": "review-001",
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "severity": "high",
        "status": "resolved",
        "disposition": "fixed",
        "disposition_evidence": "review-002 confirmed the repair",
        "resolved_by_review_id": "review-002",
        "confirmation_review_ids": ["review-003"] if confirmation_ids is None else confirmation_ids,
    }
    later_finding = {
        "id": "F-002",
        "introduced_review_id": "review-002",
        "base_sha": BASE_SHA,
        "head_sha": RESOLUTION_HEAD_SHA,
        "severity": "high",
        "status": "resolved",
        "disposition": "fixed",
        "disposition_evidence": "review-003 confirmed the later repair",
        "resolved_by_review_id": "review-003",
    }
    reviews = [
        review_evidence(verdict="request_changes", finding_ids=["F-001"]),
        review_evidence(
            "i002-reviewer-a02-resolution",
            review_id="review-002",
            head_sha=RESOLUTION_HEAD_SHA,
            verdict="request_changes",
            finding_ids=["F-002"],
            started_at=REVIEW2_STARTED,
            completed_at=REVIEW2_ENDED,
        ),
        review_evidence(
            "i002-reviewer-a03-confirmation",
            review_id="review-003",
            head_sha=confirmation_head_sha,
            verdict=confirmation_verdict,
            started_at=REVIEW3_STARTED,
            completed_at=REVIEW3_ENDED,
        ),
    ]
    checks = [
        check_evidence(),
        check_evidence(
            check_id="check-resolution-head",
            head_sha=RESOLUTION_HEAD_SHA,
            completed_at="2026-08-30T00:03:30Z",
        ),
        check_evidence(
            check_id="check-current-head",
            head_sha=ADVANCED_HEAD_SHA,
            completed_at=CHECKED3,
        ),
    ]
    state["prs.json"]["pull_requests"] = [
        pull_request(
            head_sha=ADVANCED_HEAD_SHA,
            checks=checks,
            reviews=reviews,
            findings=[finding, later_finding],
        )
    ]
    add_pr_sessions(state)
    state["sessions.json"]["issued"].extend(
        [
            issued_session(
                "i002-reviewer-a02-resolution",
                pr_id="LPR-001",
                role="reviewer",
                read_only=True,
                started_at=REVIEW2_STARTED,
                ended_at=REVIEW2_ENDED,
            ),
            issued_session(
                "i002-reviewer-a03-confirmation",
                pr_id="LPR-001",
                role="reviewer",
                read_only=True,
                started_at=REVIEW3_STARTED,
                ended_at=REVIEW3_ENDED,
            ),
        ]
    )
    return state


class WorkflowValidationTests(unittest.TestCase):
    def test_valid_documents_and_dependency_ready(self) -> None:
        state = documents()
        workflow.validate_documents(state)
        self.assertEqual(["QPBT-002"], [item["id"] for item in workflow.dependency_ready_issues(state)])

    def test_active_non_coordinator_count_excludes_coordinator_and_terminal_sessions(self) -> None:
        state = documents()
        coordinator = issued_session(
            "i001-coordinator-a01-active",
            issue_id="QPBT-001",
            role="coordinator",
            status="running",
            read_only=False,
            owned_paths=["workflow/"],
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        active = issued_session(
            "i002-prover-a01-active",
            status="running",
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        terminal = issued_session("i002-reviewer-a01-terminal", read_only=True)
        state["sessions.json"]["issued"] = [coordinator, active, terminal]
        self.assertEqual(1, workflow.active_non_coordinator_count(state))
        self.assertEqual(1, workflow.active_non_coordinator_count(state, stage_id="STAGE-01"))

    def test_active_count_is_conservative_across_backends(self) -> None:
        state = documents()
        cli_session = issued_session(
            "i002-prover-a01-cli-active",
            status="running",
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        collaboration_session = issued_session(
            "i002-reviewer-a01-collaboration-active",
            role="reviewer",
            read_only=True,
            status="issued",
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        collaboration_session["backend"] = "codex-collaboration"
        state["sessions.json"]["issued"] = [cli_session, collaboration_session]
        self.assertEqual(2, workflow.active_non_coordinator_count(state))
        result = workflow.plan_dispatch(state, capacity=2, stage_id="STAGE-01")
        self.assertEqual("stage", result["capacity_scope"])
        self.assertEqual("all", result["backend_scope"])

    def test_active_count_includes_each_nested_non_coordinator_session(self) -> None:
        state = documents()
        coordinator = issued_session(
            "i001-coordinator-a01-nested-root",
            issue_id="QPBT-001",
            role="coordinator",
            status="running",
            read_only=False,
            owned_paths=["workflow/"],
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        parent = issued_session(
            "i002-reviewer-a01-nested-parent",
            role="reviewer",
            status="running",
            read_only=True,
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        child = issued_session(
            "i002-reviewer-a02-nested-child",
            role="reviewer",
            status="issued",
            read_only=True,
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        parent["parent_session_id"] = coordinator["id"]
        child["parent_session_id"] = parent["id"]
        candidate = planned_session("i002-reviewer-a03-nested-queued")
        state["sessions.json"]["issued"] = [coordinator, parent, child]
        state["sessions.json"]["planned"] = [candidate]

        self.assertEqual(
            2,
            workflow.active_non_coordinator_count(state, stage_id="STAGE-01"),
        )
        result = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[candidate["id"]],
        )
        self.assertEqual([], result["dispatchable"])
        self.assertEqual(
            [{"id": candidate["id"], "reason": "capacity-exhausted"}],
            result["queued"],
        )

    def test_active_issued_session_requires_external_thread_identity(self) -> None:
        state = documents()
        active = issued_session(
            "i002-reviewer-a01-unconfirmed-active",
            role="reviewer",
            status="issued",
            read_only=True,
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        active["backend"] = "codex-collaboration"
        active["external_id"] = None
        state["sessions.json"]["issued"] = [active]
        with self.assertRaisesRegex(
            workflow.ValidationError,
            "active sessions require a non-empty immutable external thread identity",
        ):
            workflow.validate_documents(state)

        active["status"] = "archived"
        active["started_at"] = REVIEW_STARTED
        active["ended_at"] = REVIEW_ENDED
        active["elapsed_seconds"] = 60.0
        active["archive_status"] = "archived"
        active["outcome_path"] = ".workflow-runtime/runs/legacy/result.json"
        workflow.validate_documents(state)

    def test_stage_count_ignores_active_issue_without_stage_mapping(self) -> None:
        state = documents()
        unrelated = issued_session(
            "i001-reviewer-a01-unmapped-active",
            issue_id="QPBT-001",
            role="reviewer",
            read_only=True,
            status="running",
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        state["sessions.json"]["issued"] = [unrelated]
        self.assertEqual(1, workflow.active_non_coordinator_count(state))
        self.assertEqual(0, workflow.active_non_coordinator_count(state, stage_id="STAGE-01"))

    def test_stage_count_fails_closed_on_any_ambiguous_active_mapping(self) -> None:
        state = documents()
        duplicate_stage = copy.deepcopy(state["stages.json"]["stages"][0])
        duplicate_stage["id"] = "STAGE-02"
        duplicate_stage["issue_ids"] = ["QPBT-001"]
        state["stages.json"]["stages"][0]["issue_ids"].append("QPBT-001")
        state["stages.json"]["stages"].append(duplicate_stage)
        active = issued_session(
            "i001-reviewer-a01-ambiguous-active",
            issue_id="QPBT-001",
            role="reviewer",
            read_only=True,
            status="running",
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        state["sessions.json"]["issued"] = [active]
        with self.assertRaisesRegex(workflow.WorkflowError, "ambiguous stage mapping"):
            workflow.active_non_coordinator_count(state, stage_id="STAGE-01")

    def test_dispatch_requires_explicit_capacity_and_rejects_invalid_values(self) -> None:
        state = documents()
        for capacity in (None, -1, True, 1.5):
            with self.assertRaises(workflow.WorkflowError):
                workflow.plan_dispatch(state, capacity=capacity)  # type: ignore[arg-type]

    def test_unknown_capacity_does_not_mask_dag_diagnostics(self) -> None:
        state = documents()
        state["issues.json"]["issues"][0]["status"] = "planned"
        state["issues.json"]["issues"][0]["dependency_ids"] = ["QPBT-002"]
        state["issues.json"]["issues"][1]["dependency_ids"] = ["QPBT-001"]
        with self.assertRaisesRegex(workflow.ValidationError, "issue dependencies: cycle detected"):
            workflow.plan_dispatch(state, capacity=None)

    def test_unknown_capacity_preserves_dag_and_ownership_diagnostics(self) -> None:
        state = documents()
        blocked_issue = issue("QPBT-003", "planned", ["QPBT-002"])
        state["issues.json"]["issues"].append(blocked_issue)
        state["stages.json"]["stages"][0]["issue_ids"].append("QPBT-003")
        active = issued_session(
            "i002-prover-a01-unknown-capacity-owner",
            role="prover",
            status="running",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Conflict.lean"],
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        conflicting = planned_session(
            "i002-prover-a02-unknown-capacity-conflict",
            role="prover",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Conflict.lean"],
        )
        dependency_blocked = planned_session(
            "i003-reviewer-a01-unknown-capacity-blocked",
            issue_id="QPBT-003",
        )
        state["sessions.json"]["issued"] = [active]
        state["sessions.json"]["planned"] = [conflicting, dependency_blocked]
        with self.assertRaisesRegex(workflow.WorkflowError, "capacity is unknown") as caught:
            workflow.plan_dispatch(
                state,
                capacity=None,
                stage_id="STAGE-01",
                session_ids=[conflicting["id"], dependency_blocked["id"]],
            )
        message = str(caught.exception)
        self.assertIn("ownership-conflict", message)
        self.assertIn("dependencies-not-done", message)

    def test_dispatch_plan_reports_sorted_queue_and_dependency_block(self) -> None:
        state = documents()
        blocked_issue = issue("QPBT-003", "planned", ["QPBT-002"])
        state["issues.json"]["issues"].append(blocked_issue)
        state["stages.json"]["stages"][0]["issue_ids"].append("QPBT-003")
        state["sessions.json"]["planned"] = [
            planned_session("i003-reviewer-a01-blocked", issue_id="QPBT-003"),
            planned_session("i002-reviewer-a02-queued"),
            planned_session("i002-reviewer-a01-queued"),
        ]
        result = workflow.plan_dispatch(
            state,
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[
                "i003-reviewer-a01-blocked",
                "i002-reviewer-a02-queued",
                "i002-reviewer-a01-queued",
            ],
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual(["i002-reviewer-a01-queued"], result["dispatchable"])
        self.assertEqual(
            [{"id": "i002-reviewer-a02-queued", "reason": "capacity-exhausted"}],
            result["queued"],
        )
        self.assertEqual("dependencies-not-done", result["blocked"][0]["reason"])

    def test_dispatch_plan_reports_writable_ownership_conflict(self) -> None:
        state = documents()
        active = issued_session(
            "i002-prover-a01-active-owner",
            status="running",
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
            owned_paths=["MIPStarRE/QPBT/Test.lean"],
        )
        state["sessions.json"]["issued"] = [active]
        state["sessions.json"]["planned"] = [
            planned_session(
                "i002-prover-a02-conflict",
                role="prover",
                read_only=False,
                owned_paths=["MIPStarRE/QPBT/Test.lean"],
            )
        ]
        result = workflow.plan_dispatch(state, capacity=2, stage_id="STAGE-01")
        self.assertEqual("blocked", result["status"])
        self.assertEqual("ownership-conflict", result["blocked"][0]["reason"])
        self.assertEqual("i002-prover-a01-active-owner", result["blocked"][0]["with_session_id"])

    def test_dispatch_rejects_duplicate_planned_orchestrators_for_one_issue(self) -> None:
        state = documents()
        first = planned_session(
            "i002-orchestrator-a01-duplicate",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/First.lean"],
        )
        second = planned_session(
            "i002-orchestrator-a02-duplicate",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Second.lean"],
        )
        state["sessions.json"]["planned"] = [first, second]
        result = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[first["id"], second["id"]],
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual(
            [first["id"], second["id"]],
            [entry["id"] for entry in result["blocked"]],
        )
        self.assertTrue(
            all(entry["reason"] == "duplicate-orchestrator" for entry in result["blocked"])
        )

    def test_github_only_formalization_delegates_require_one_active_orchestrator(self) -> None:
        state = documents()
        prover = planned_session(
            "i028-prover-a01-github-only-formalization",
            role="prover",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/GitHubOnlyProof.lean"],
        )
        prover["issue_id"] = None
        prover["github_issue_number"] = 28
        prover["stage_id"] = "STAGE-01"
        state["sessions.json"]["planned"] = [prover]
        projection = {
            28: {
                "status": "ready",
                "kind": "formalization",
                "execution_category": "implementation",
                "dependency_numbers": [],
                "incomplete_dependency_numbers": [],
            }
        }

        blocked = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[prover["id"]],
            canonical_issue_projection=projection,
            canonical_issue_bindings={},
        )
        self.assertEqual("blocked", blocked["status"])
        self.assertEqual(
            "implementation-orchestrator-required",
            blocked["blocked"][0]["reason"],
        )

        scout = planned_session(
            "i028-scout-a01-github-only-formalization",
            role="scout",
            read_only=True,
        )
        scout["issue_id"] = None
        scout["github_issue_number"] = 28
        scout["stage_id"] = "STAGE-01"
        state["sessions.json"]["planned"].append(scout)
        blocked_scout = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[scout["id"]],
            canonical_issue_projection=projection,
            canonical_issue_bindings={},
        )
        self.assertEqual("blocked", blocked_scout["status"])
        self.assertEqual(
            "implementation-orchestrator-required",
            blocked_scout["blocked"][0]["reason"],
        )

        orchestrator = issued_session(
            "i028-orchestrator-a01-github-only-formalization",
            role="orchestrator",
            status="issued",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/GitHubOnlyOrchestration.md"],
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        orchestrator["issue_id"] = None
        orchestrator["github_issue_number"] = 28
        orchestrator["stage_id"] = "STAGE-01"
        state["sessions.json"]["issued"] = [orchestrator]

        admitted = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[prover["id"]],
            canonical_issue_projection=projection,
            canonical_issue_bindings={},
        )
        self.assertEqual("ready", admitted["status"])
        self.assertEqual([prover["id"]], admitted["dispatchable"])

    def test_dispatch_rejects_orchestrator_when_active_attempt_exists(self) -> None:
        state = documents()
        active = issued_session(
            "i002-orchestrator-a01-active",
            role="orchestrator",
            status="running",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Existing.lean"],
            started_at=REVIEW_STARTED,
            ended_at=None,
            elapsed_seconds=None,
        )
        candidate = planned_session(
            "i002-orchestrator-a02-active-duplicate",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Candidate.lean"],
        )
        state["sessions.json"]["issued"] = [active]
        state["sessions.json"]["planned"] = [candidate]
        result = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[candidate["id"]],
        )
        self.assertEqual("duplicate-orchestrator", result["blocked"][0]["reason"])
        self.assertEqual([active["id"]], result["blocked"][0]["with_session_ids"])

    def test_dispatch_rejects_cross_domain_orchestrator_identity(self) -> None:
        state = documents()
        migrated = planned_session(
            "i002-orchestrator-a03-migrated-identity",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Migrated.lean"],
        )
        migrated["github_issue_number"] = 2
        github_only = planned_session(
            "i002-orchestrator-a04-github-only-identity",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/GitHubOnly.lean"],
        )
        github_only["issue_id"] = None
        github_only["github_issue_number"] = 2
        github_only["stage_id"] = "STAGE-01"
        state["sessions.json"]["planned"] = [migrated, github_only]
        result = workflow.plan_dispatch(
            state,
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[migrated["id"], github_only["id"]],
            canonical_issue_projection={
                2: {
                    "status": "ready",
                    "kind": "formalization",
                    "execution_category": "implementation",
                    "dependency_numbers": [],
                    "incomplete_dependency_numbers": [],
                }
            },
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual(
            [migrated["id"], github_only["id"]],
            [entry["id"] for entry in result["blocked"]],
        )
        self.assertTrue(
            all(entry["reason"] == "duplicate-orchestrator" for entry in result["blocked"])
        )

    def test_dispatch_plan_rejects_cross_candidate_batch_conflict(self) -> None:
        state = documents()
        first = planned_session("i002-reviewer-a01-batch-conflict")
        second = planned_session("i002-reviewer-a02-batch-conflict")
        state["sessions.json"]["planned"] = [first, second]
        result = workflow.plan_dispatch(
            state,
            capacity=2,
            session_ids=[first["id"], second["id"]],
            session_overrides={
                first["id"]: {"external_id": "shared-external-id"},
                second["id"]: {"external_id": "shared-external-id"},
            },
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual(
            [first["id"], second["id"]],
            [entry["id"] for entry in result["blocked"]],
        )
        self.assertTrue(all(entry["reason"] == "batch-validation-failure" for entry in result["blocked"]))

    def test_queued_cross_candidate_conflict_is_deferred_until_admission(self) -> None:
        state = documents()
        first = planned_session("i002-reviewer-a01-queued-conflict")
        second = planned_session("i002-reviewer-a02-queued-conflict")
        state["sessions.json"]["planned"] = [first, second]
        result = workflow.plan_dispatch(
            state,
            capacity=1,
            session_ids=[first["id"], second["id"]],
            session_overrides={
                first["id"]: {"external_id": "shared-queued-external-id"},
                second["id"]: {"external_id": "shared-queued-external-id"},
            },
        )
        self.assertEqual("queued", result["status"])
        self.assertEqual([first["id"]], result["dispatchable"])
        self.assertEqual(
            [{"id": second["id"], "reason": "capacity-exhausted"}],
            result["queued"],
        )
        self.assertEqual([], result["blocked"])
        self.assertTrue(result["request_atomic"])
        self.assertFalse(result["all_or_nothing"])

    def test_dispatch_override_cannot_change_planned_authority(self) -> None:
        state = documents()
        candidate = planned_session("i002-reviewer-a01-authority")
        state["sessions.json"]["planned"] = [candidate]
        result = workflow.plan_dispatch(
            state,
            capacity=1,
            session_ids=[candidate["id"]],
            session_overrides={candidate["id"]: {"issue_id": "QPBT-001"}},
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual("invalid-dispatch-override", result["blocked"][0]["reason"])
        self.assertIn("issue_id", result["blocked"][0]["detail"])

    def test_dispatch_override_cannot_retarget_pr_or_rewrite_external_id(self) -> None:
        state = documents()
        candidate = planned_session("i002-reviewer-a01-provenance")
        candidate["pr_id"] = "LPR-001"
        candidate["external_id"] = "thread-original"
        state["sessions.json"]["planned"] = [candidate]
        cases = [
            ({"pr_id": "LPR-002"}, "pr_id", candidate),
            (
                {"external_id": "thread-new"},
                "external_id",
                {**candidate, "pr_id": None},
            ),
        ]
        for override, expected, row in cases:
            state["sessions.json"]["planned"] = [row]
            result = workflow.plan_dispatch(
                state,
                capacity=1,
                session_ids=[row["id"]],
                session_overrides={row["id"]: override},
            )
            self.assertEqual("blocked", result["status"])
            self.assertIn(expected, result["blocked"][0]["detail"])

    def test_dispatch_rejects_mixed_shape_override_object(self) -> None:
        session_id = "i002-reviewer-a01-mixed-override"
        mixed = json.dumps(
            {
                "id": session_id,
                "external_id": "thread-materialized",
                "another-session": {"external_id": "thread-other"},
            }
        )
        with self.assertRaisesRegex(
            workflow.WorkflowError,
            "cannot mix single-record and keyed shapes",
        ):
            workflow._load_dispatch_overrides(mixed, None)

        with self.assertRaisesRegex(
            workflow.WorkflowError,
            "cannot mix single-record and keyed shapes",
        ):
            workflow._load_dispatch_overrides(
                json.dumps({"id": 17, "external_id": "thread-materialized"}),
                None,
            )

    def test_protocol_ledger_requires_the_named_unique_active_revision(self) -> None:
        state = documents()
        state["protocols.json"]["active_revision"] = "0.2.0"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("unknown revision '0.2.0'", str(caught.exception))

        state = documents()
        duplicate = copy.deepcopy(state["protocols.json"]["revisions"][0])
        state["protocols.json"]["revisions"].append(duplicate)
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("duplicate '0.1.0'", str(caught.exception))

    def test_rejects_dependency_and_parent_cycles(self) -> None:
        state = documents()
        issues = state["issues.json"]["issues"]
        issues[0]["status"] = "planned"
        issues[0]["dependency_ids"] = ["QPBT-002"]
        issues[0]["parent_id"] = "QPBT-002"
        issues[1]["parent_id"] = "QPBT-001"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        message = str(caught.exception)
        self.assertIn("issue dependencies: cycle detected", message)
        self.assertIn("issue parent hierarchy: cycle detected", message)

    def test_malformed_dependency_reports_validation_error_instead_of_crashing(self) -> None:
        state = documents()
        state["issues.json"]["issues"][1]["dependency_ids"] = [{}]
        state["issues.json"]["issues"][1]["status"] = "ready"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("expected a list of issue ids", str(caught.exception))

    def test_rejects_invalid_status_and_reference(self) -> None:
        state = documents()
        state["issues.json"]["issues"][1]["status"] = "almost_done"
        state["stages.json"]["stages"][0]["issue_ids"] = ["QPBT-999"]
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("invalid issue status", str(caught.exception))
        self.assertIn("unknown issue 'QPBT-999'", str(caught.exception))

    def test_rejects_cross_bucket_session_duplicate_and_cycle(self) -> None:
        state = documents()
        planned = {
            "id": "S1",
            "name": "i002-prover-a01-one",
            "role": "prover",
            "issue_id": "QPBT-002",
            "status": "planned",
            "parent_session_id": "S2",
        }
        issued = {
            "id": "S2",
            "name": "i002-reviewer-a01-two",
            "backend": "codex-cli",
            "role": "reviewer",
            "status": "issued",
            "issue_id": "QPBT-002",
            "pr_id": None,
            "parent_session_id": "S1",
            "external_id": None,
            "attempt": 1,
            "started_at": None,
            "ended_at": None,
            "elapsed_seconds": None,
            "token_usage": unavailable_tokens(),
            "archive_status": "not_requested",
            "outcome_path": None,
        }
        state["sessions.json"]["planned"] = [planned]
        state["sessions.json"]["issued"] = [issued]
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("session parent hierarchy: cycle detected", str(caught.exception))
        issued["id"] = "S1"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("ids appear in both planned and issued", str(caught.exception))

    def test_done_tracker_requires_done_child(self) -> None:
        state = documents()
        tracker = issue("QPBT-000", "done", kind="tracking")
        state["issues.json"]["issues"].insert(0, tracker)
        state["issues.json"]["issues"][2]["parent_id"] = "QPBT-000"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("all direct children must be done", str(caught.exception))

    def test_valid_approved_pr_has_sha_bound_checks_and_independent_review(self) -> None:
        state = documents()
        state["prs.json"]["pull_requests"] = [pull_request()]
        add_pr_sessions(state)
        workflow.validate_documents(state)

    def test_rejects_stale_or_failed_pr_evidence(self) -> None:
        state = documents()
        stale_review = review_evidence(head_sha="c" * 40)
        state["prs.json"]["pull_requests"] = [
            pull_request(
                checks=[check_evidence(status="failed")],
                reviews=[stale_review],
            )
        ]
        add_pr_sessions(state)
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        message = str(caught.exception)
        self.assertIn("all current checks must pass", message)
        self.assertIn("requires a current approving review", message)

    def test_rejects_non_independent_reviewer(self) -> None:
        state = documents()
        implementer_id = "i002-prover-a01-implementation"
        state["prs.json"]["pull_requests"] = [
            pull_request(reviews=[review_evidence(implementer_id)])
        ]
        add_pr_sessions(state)
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        message = str(caught.exception)
        self.assertIn("reviewer must be a read-only reviewer session", message)
        self.assertIn("reviewer is not independent", message)

    def test_reviewer_identity_is_unique_and_bound_to_pr_base(self) -> None:
        state = documents()
        state["prs.json"]["pull_requests"] = [pull_request()]
        add_pr_sessions(state)
        implementer, reviewer = state["sessions.json"]["issued"]
        reviewer["external_id"] = implementer["external_id"]
        reviewer["base_revision"] = "c" * 40
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        message = str(caught.exception)
        self.assertIn("duplicate external_id", message)
        self.assertIn("base_revision differs from PR base_sha", message)

    def test_approved_pr_requires_a_linked_issue(self) -> None:
        state = documents()
        pr = pull_request()
        pr["issue_ids"] = []
        state["prs.json"]["pull_requests"] = [pr]
        add_pr_sessions(state)
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("must link at least one issue", str(caught.exception))

    def test_rejects_unresolved_finding_and_accepts_review_confirmed_disposition(self) -> None:
        finding = {
            "id": "F-001",
            "introduced_review_id": "review-001",
            "base_sha": BASE_SHA,
            "head_sha": HEAD_SHA,
            "severity": "high",
            "status": "open",
            "disposition": "pending",
            "disposition_evidence": None,
            "resolved_by_review_id": None,
        }
        state = documents()
        first_review = review_evidence(verdict="request_changes", finding_ids=["F-001"])
        second_reviewer = "i002-reviewer-a02-resolution"
        second_review = review_evidence(
            second_reviewer,
            review_id="review-002",
            started_at=REVIEW2_STARTED,
            completed_at=REVIEW2_ENDED,
        )
        state["prs.json"]["pull_requests"] = [
            pull_request(
                reviews=[first_review, second_review],
                findings=[finding],
            )
        ]
        add_pr_sessions(state)
        state["sessions.json"]["issued"].append(
            issued_session(
                second_reviewer,
                pr_id="LPR-001",
                role="reviewer",
                read_only=True,
                started_at=REVIEW2_STARTED,
                ended_at=REVIEW2_ENDED,
            )
        )
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("requires every finding to be resolved", str(caught.exception))

        finding["status"] = "resolved"
        finding["disposition"] = "rejected"
        finding["disposition_evidence"] = "second reviewer confirmed the report was inapplicable"
        finding["resolved_by_review_id"] = "review-002"
        workflow.validate_documents(state)

    def test_approved_pr_accepts_append_only_current_head_reconfirmation(self) -> None:
        state = finding_reconfirmation_documents()

        workflow.validate_documents(state)

    def test_approved_pr_rejects_stale_resolution_without_reconfirmation(self) -> None:
        state = finding_reconfirmation_documents(confirmation_ids=[])

        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)

        self.assertIn("resolution is not confirmed on current base/head", str(caught.exception))

    def test_finding_reconfirmation_rejects_malformed_or_unknown_review_ids(self) -> None:
        cases: list[tuple[str, list[object], str]] = [
            ("duplicate", ["review-003", "review-003"], "duplicate entries"),
            ("non-string", [3], "expected a list of strings"),
            ("unknown", ["review-unknown"], "unknown review 'review-unknown'"),
        ]
        for name, confirmation_ids, expected in cases:
            with self.subTest(name=name):
                state = finding_reconfirmation_documents(
                    confirmation_ids=confirmation_ids,  # type: ignore[arg-type]
                )
                with self.assertRaises(workflow.ValidationError) as caught:
                    workflow.validate_documents(state)
                self.assertIn(expected, str(caught.exception))

    def test_finding_reconfirmation_adjacent_malformed_values_report_validation_errors(self) -> None:
        cases = [
            ("checks", 2, "status", [], "invalid check status"),
            ("reviews", 2, "verdict", [], "invalid review verdict"),
            ("findings", 0, "introduced_review_id", [], "unknown review []"),
            ("findings", 0, "severity", [], "invalid finding severity"),
            ("findings", 0, "status", [], "invalid finding status"),
            ("findings", 0, "disposition", [], "invalid finding disposition"),
            ("findings", 0, "resolved_by_review_id", [], "unknown review []"),
        ]
        for collection, index, field, value, expected in cases:
            with self.subTest(collection=collection, field=field):
                state = finding_reconfirmation_documents()
                state["prs.json"]["pull_requests"][0][collection][index][field] = value
                with self.assertRaises(workflow.ValidationError) as caught:
                    workflow.validate_documents(state)
                self.assertIn(expected, str(caught.exception))

        state = finding_reconfirmation_documents()
        confirmation_reviewer = next(
            session
            for session in state["sessions.json"]["issued"]
            if session["id"] == "i002-reviewer-a03-confirmation"
        )
        confirmation_reviewer["status"] = []
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        message = str(caught.exception)
        self.assertIn("reviewer session has not finished", message)
        self.assertIn("invalid session status", message)

        for field, value, expected in (
            ("pr_id", [], "unknown PR []"),
            ("issue_id", [], "unknown issue []"),
            ("parent_session_id", [], "unknown session []"),
            ("archive_status", [], "invalid archive status []"),
            ("timing_quality", [], "unknown timing provenance []"),
        ):
            with self.subTest(reviewer_session_field=field):
                state = finding_reconfirmation_documents()
                confirmation_reviewer = next(
                    session
                    for session in state["sessions.json"]["issued"]
                    if session["id"] == "i002-reviewer-a03-confirmation"
                )
                confirmation_reviewer[field] = value
                with self.assertRaises(workflow.ValidationError) as caught:
                    workflow.validate_documents(state)
                self.assertIn(expected, str(caught.exception))

        state = finding_reconfirmation_documents()
        state["prs.json"]["pull_requests"][0]["status"] = []
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("invalid PR status []", str(caught.exception))

    def test_approved_pr_rejects_wrong_head_or_nonapproving_reconfirmation(self) -> None:
        wrong_head = finding_reconfirmation_documents(
            confirmation_head_sha=RESOLUTION_HEAD_SHA,
        )
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(wrong_head)
        self.assertIn("resolution is not confirmed on current base/head", str(caught.exception))

        nonapproving = finding_reconfirmation_documents(
            confirmation_verdict="request_changes",
        )
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(nonapproving)
        self.assertIn("confirmation review 'review-003' must approve", str(caught.exception))

    def test_finding_reconfirmation_requires_a_fresh_later_review_round(self) -> None:
        state = finding_reconfirmation_documents()
        pr = state["prs.json"]["pull_requests"][0]
        confirmation = pr["reviews"][2]
        confirmation["started_at"] = "2026-08-30T00:04:30Z"
        confirmation["completed_at"] = "2026-08-30T00:05:30Z"
        pr["checks"][2]["completed_at"] = "2026-08-30T00:04:15Z"
        reviewer_session = next(
            session
            for session in state["sessions.json"]["issued"]
            if session["id"] == "i002-reviewer-a03-confirmation"
        )
        reviewer_session["started_at"] = confirmation["started_at"]
        reviewer_session["ended_at"] = confirmation["completed_at"]

        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)

        self.assertIn("review 'review-003' started before 'review-002' completed", str(caught.exception))

    def test_finding_reconfirmation_requires_independent_same_pr_reviewer(self) -> None:
        wrong_role = finding_reconfirmation_documents()
        confirmation_review = wrong_role["prs.json"]["pull_requests"][0]["reviews"][2]
        confirmation_review["reviewer_session_id"] = "i002-prover-a01-implementation"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(wrong_role)
        message = str(caught.exception)
        self.assertIn("reviewer must be a read-only reviewer session", message)
        self.assertIn("reviewer is not independent of implementation", message)

        wrong_pr = finding_reconfirmation_documents()
        confirmation_reviewer = next(
            session
            for session in wrong_pr["sessions.json"]["issued"]
            if session["id"] == "i002-reviewer-a03-confirmation"
        )
        confirmation_reviewer["pr_id"] = None
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(wrong_pr)
        self.assertIn("reviewer session is not bound to PR 'LPR-001'", str(caught.exception))

    def test_finding_confirmation_update_is_append_only_and_preserves_resolution(self) -> None:
        state = finding_reconfirmation_documents()
        resolved = state["prs.json"]["pull_requests"][0]["findings"][0]
        original = copy.deepcopy(resolved)
        original.pop("confirmation_review_ids")
        appended = copy.deepcopy(original)
        appended["confirmation_review_ids"] = ["review-003"]

        workflow._require_findings_update([original], [appended])

        for field, value in (
            ("id", "F-rewritten"),
            ("status", "open"),
            ("disposition", "rejected"),
            ("disposition_evidence", "rewritten evidence"),
            ("resolved_by_review_id", "review-003"),
        ):
            with self.subTest(mutation=field):
                mutated = copy.deepcopy(appended)
                mutated[field] = value
                with self.assertRaises(workflow.WorkflowError):
                    workflow._require_findings_update([appended], [mutated])

        removed = copy.deepcopy(appended)
        removed["confirmation_review_ids"] = []
        with self.assertRaisesRegex(workflow.WorkflowError, "confirmation_review_ids are append-only"):
            workflow._require_findings_update([appended], [removed])

        replaced = copy.deepcopy(appended)
        replaced["confirmation_review_ids"] = ["review-004"]
        with self.assertRaisesRegex(workflow.WorkflowError, "confirmation_review_ids are append-only"):
            workflow._require_findings_update([appended], [replaced])

        open_finding = copy.deepcopy(original)
        open_finding["status"] = "open"
        open_finding["disposition"] = "pending"
        open_finding["disposition_evidence"] = None
        open_finding["resolved_by_review_id"] = None
        malformed_transition = copy.deepcopy(open_finding)
        malformed_transition["status"] = []
        with self.assertRaisesRegex(workflow.WorkflowError, "only transition from open to resolved"):
            workflow._require_findings_update([open_finding], [malformed_transition])

    def test_pr_update_guard_authorizes_only_new_current_confirmations(self) -> None:
        state = finding_reconfirmation_documents(confirmation_ids=[])
        old = state["prs.json"]["pull_requests"][0]
        confirmation_review = old["reviews"].pop()
        candidate = copy.deepcopy(old)
        candidate["reviews"].append(confirmation_review)
        candidate["findings"][0]["confirmation_review_ids"] = ["review-003"]
        workflow._check_pr_update(old, candidate)

        appended_finding = copy.deepcopy(candidate)
        appended_finding["head_sha"] = "e" * 40
        new_finding = copy.deepcopy(appended_finding["findings"][0])
        new_finding["id"] = "F-003"
        new_finding["confirmation_review_ids"] = ["review-003"]
        appended_finding["findings"].append(new_finding)
        with self.assertRaisesRegex(workflow.WorkflowError, "wrong head SHA"):
            workflow._check_pr_update(candidate, appended_finding)

        cases = [
            ("missing", lambda pr, docs: pr["reviews"].pop(), "candidate review list"),
            (
                "duplicate",
                lambda pr, docs: pr["findings"][0].update(
                    confirmation_review_ids=["review-003", "review-003"]
                ),
                "duplicated",
            ),
            ("wrong-head", lambda pr, docs: pr.update(head_sha="e" * 40), "wrong head SHA"),
            ("wrong-base", lambda pr, docs: pr["reviews"][2].update(base_sha="e" * 40), "wrong base SHA"),
            (
                "non-approve",
                lambda pr, docs: pr["reviews"][2].update(verdict="request_changes"),
                "must approve",
            ),
            (
                "malformed",
                lambda pr, docs: pr["reviews"][2].update(completed_at=[]),
                "malformed chronology",
            ),
            (
                "out-of-order",
                lambda pr, docs: pr["reviews"][2].update(started_at=REVIEW2_STARTED),
                "out of order",
            ),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                changed = copy.deepcopy(candidate)
                changed_state = copy.deepcopy(state)
                mutate(changed, changed_state)
                with self.assertRaisesRegex(workflow.WorkflowError, expected):
                    workflow._check_pr_update(old, changed)

    def test_issued_session_contract_and_lifecycle_are_required(self) -> None:
        state = documents()
        session = issued_session(
            "i002-prover-a01-lifecycle",
            status="running",
            started_at=None,
            ended_at=REVIEW_ENDED,
            elapsed_seconds=1.0,
        )
        session.pop("result_envelope_path")
        state["sessions.json"]["issued"] = [session]
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        message = str(caught.exception)
        self.assertIn("missing required field 'result_envelope_path'", message)
        self.assertIn("started_at: required for running session", message)
        self.assertIn("running session cannot have terminal timing", message)

    def test_terminal_session_accepts_explicit_parent_window_without_fabricated_timing(self) -> None:
        state = documents()
        session = issued_session(
            "i002-auditor-a01-interrupted",
            role="auditor",
            read_only=True,
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        session["timing_quality"] = "bounded-by-parent-window"
        session["timing_bounds"] = {
            "not_before": REVIEW_STARTED,
            "not_after": REVIEW_ENDED,
        }
        parent = issued_session("i002-auditor-a02-parent", role="auditor", read_only=True)
        session["parent_session_id"] = parent["id"]
        state["sessions.json"]["issued"] = [parent, session]
        workflow.validate_documents(state)

        session["timing_bounds"]["not_before"] = "2026-08-30T00:04:00Z"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("not_after precedes not_before", str(caught.exception))

    def test_approximate_terminal_timing_must_be_labeled(self) -> None:
        state = documents()
        session = issued_session("i002-auditor-a01-approximate", role="auditor", read_only=True)
        session["elapsed_seconds"] = 55.0
        state["sessions.json"]["issued"] = [session]
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("non-exact timing must be labeled", str(caught.exception))

        session["timing_quality"] = "agent-reported-approximate"
        workflow.validate_documents(state)

    def test_rejects_overlapping_active_writable_ownership(self) -> None:
        state = documents()
        first = issued_session(
            "i002-prover-a01-left",
            status="running",
            owned_paths=["MIPStarRE/QPBT/"],
            ended_at=None,
            elapsed_seconds=None,
        )
        second = issued_session(
            "i002-prover-a02-right",
            status="running",
            owned_paths=["MIPStarRE/QPBT/Test.lean"],
            ended_at=None,
            elapsed_seconds=None,
        )
        state["sessions.json"]["issued"] = [first, second]
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("active writable ownership overlap", str(caught.exception))

        second["worktree"] = "/tmp/qpbt-other-worktree"
        workflow.validate_documents(state)

    def test_in_progress_implementation_requires_one_matching_orchestrator(self) -> None:
        state = documents()
        implementation = state["issues.json"]["issues"][1]
        implementation["status"] = "in_progress"
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("requires exactly one active orchestrator", str(caught.exception))

        orchestrator = issued_session(
            "i002-orchestrator-a01-delivery",
            role="orchestrator",
            status="running",
            owned_paths=["MIPStarRE/QPBT/"],
            ended_at=None,
            elapsed_seconds=None,
        )
        state["sessions.json"]["issued"] = [orchestrator]
        implementation["owner_session_id"] = orchestrator["id"]
        workflow.validate_documents(state)

        implementation["execution_category"] = "preflight"
        state["sessions.json"]["issued"] = []
        implementation["owner_session_id"] = None
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.validate_documents(state)
        self.assertIn("cannot bypass implementation gates", str(caught.exception))

    def test_workflow_bootstrap_category_does_not_require_orchestrator(self) -> None:
        state = documents()
        bootstrap = state["issues.json"]["issues"][1]
        bootstrap["kind"] = "workflow"
        bootstrap["status"] = "in_progress"
        workflow.validate_documents(state)


    def test_postcutover_session_uses_canonical_github_identity(self) -> None:
        state = documents()
        session = issued_session(
            "i001-writer-a01-github-cutover",
            role="writer",
            read_only=True,
        )
        session["issue_id"] = None
        session["github_issue_number"] = 1
        session["github_pull_request_number"] = 26
        session["stage_id"] = "STAGE-01"
        state["sessions.json"]["issued"] = [session]
        workflow.validate_documents(state)

        for field, value, expected in (
            ("github_issue_number", None, "required positive integer"),
            ("github_issue_number", True, "expected a positive integer"),
            ("github_pull_request_number", 0, "expected a positive integer"),
            ("stage_id", "STAGE-404", "requires a known explicit stage"),
        ):
            with self.subTest(field=field, value=value):
                invalid = copy.deepcopy(state)
                invalid["sessions.json"]["issued"][0][field] = value
                with self.assertRaisesRegex(workflow.ValidationError, expected):
                    workflow.validate_documents(invalid)


class WorkflowStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state_dir = self.root / "workflow" / "state"
        self.state_dir.mkdir(parents=True)
        for filename, value in documents().items():
            (self.state_dir / filename).write_text(json.dumps(value), encoding="utf-8")
        self.events = self.root / "workflow" / "events.jsonl"
        self.events.write_text(
            "\n"
            + json.dumps(
                {
                    "schema_version": 1,
                    "timestamp": NOW,
                    "event": "bootstrap",
                    "actor": "test",
                    "pid": 1,
                    "payload": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.runtime = self.root / ".workflow-runtime"
        self.store = workflow.WorkflowStore(self.state_dir, self.runtime, self.events)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def activate_github_cutover(self) -> Path:
        """Create the exact valid config/manifest pair used by cutover tests."""

        repository = {
            "owner": "Dengnifer",
            "name": "MIPStarRE-B",
            "database_id": 1352436168,
            "node_id": "R_kgDOUJyJyA",
        }
        config = self.root / "workflow" / "github.json"
        config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repository": repository,
                    "base_ref": "main",
                    "cutover_manifest": "github-cutover.json",
                }
            ),
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 1,
            "repository": repository,
            "base_ref": "main",
            "cutover_main_sha": BASE_SHA,
            "issues": [
                {
                    "legacy_id": legacy_id,
                    "number": number,
                    "database_id": 100 + number,
                    "node_id": f"I_issueNode0{number}",
                    "marker": github_workflow.issue_marker(legacy_id),
                }
                for legacy_id, number in (("QPBT-001", 1), ("QPBT-002", 2))
            ],
            "pull_requests": [
                {
                    "legacy_id": "LPR-001",
                    "number": 26,
                    "database_id": 226,
                    "node_id": "PR_pullRequestNode026",
                    "marker": github_workflow.pull_request_marker("LPR-001"),
                    "base_ref": "main",
                    "base_sha": BASE_SHA,
                    "head_ref": "issue/qpbt-002",
                    "head_sha": HEAD_SHA,
                }
            ],
        }
        (self.root / "workflow" / "github-cutover.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return config

    def test_read_only_validation_creates_no_runtime_files(self) -> None:
        self.store.validate()
        self.assertFalse(self.runtime.exists())

    def test_github_cutover_disables_legacy_issue_and_pr_authority_commands(self) -> None:
        self.activate_github_cutover()
        parser = workflow.build_parser()
        issue_payload = json.dumps(issue("QPBT-003", "planned"))
        commands = [
            ["init", "--missing-only"],
            ["ready"],
            ["add", "issue", "--json", issue_payload],
            [
                "add",
                "issued-session",
                "--json",
                json.dumps(issued_session("i002-reviewer-a01-direct-add")),
            ],
            [
                "update",
                "issued-session",
                "i002-reviewer-a01-direct-update",
                "--set",
                'external_id="invented-thread"',
            ],
            [
                "transition",
                "issued-session",
                "i002-reviewer-a01-direct-transition",
                "running",
            ],
            ["update", "issue", "QPBT-002", "--set", 'title="stale"'],
            ["transition", "pr", "LPR-001", "closed"],
        ]
        state_before = {
            path.name: path.read_bytes() for path in sorted(self.state_dir.iterdir())
        }
        events_before = self.events.read_bytes()

        for command in commands:
            with self.subTest(command=command), self.assertRaisesRegex(
                workflow.WorkflowError,
                "GitHub Issues and pull requests.*canonical",
            ):
                workflow.run_cli(
                    parser.parse_args(["--root", str(self.root), *command])
                )

        self.assertEqual(
            state_before,
            {path.name: path.read_bytes() for path in sorted(self.state_dir.iterdir())},
        )
        self.assertEqual(events_before, self.events.read_bytes())

        with self.assertRaisesRegex(
            workflow.WorkflowError, "generic local API"
        ):
            self.store.mutate(
                "sessions.json",
                "record.updated",
                {"kind": "issued-session"},
                lambda document: document.update({"tampered": True}),
            )
        with self.assertRaisesRegex(
            workflow.WorkflowError, "cannot be initialized"
        ):
            self.store.initialize(missing_only=True)
        with self.assertRaisesRegex(
            workflow.WorkflowError, "require a guarded dispatch"
        ):
            self.store.append_event(
                "record.transitioned",
                {"kind": "issued-session", "session_id": "forged"},
            )

    def test_github_cutover_dispatch_requires_exact_explicit_config(self) -> None:
        self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a01-github-config")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        parser = workflow.build_parser()
        before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()

        with self.assertRaisesRegex(
            workflow.WorkflowError, "requires --github-config workflow/github.json"
        ):
            workflow.run_cli(
                parser.parse_args(
                    [
                        "--root",
                        str(self.root),
                        "dispatch",
                        "--capacity",
                        "1",
                        "--session-id",
                        str(candidate["id"]),
                        "--dry-run",
                    ]
                )
            )
        with self.assertRaisesRegex(
            workflow.WorkflowError, "must be exactly workflow/github.json"
        ):
            workflow.run_cli(
                parser.parse_args(
                    [
                        "--root",
                        str(self.root),
                        "dispatch",
                        "--capacity",
                        "1",
                        "--session-id",
                        str(candidate["id"]),
                        "--dry-run",
                        "--github-config",
                        "other.json",
                    ]
                )
            )

        self.assertEqual(before, (self.state_dir / "sessions.json").read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_store_rejects_alternate_authority_config(self) -> None:
        self.activate_github_cutover()
        alternate = self.root / "alternate-github.json"
        alternate.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(
            workflow.WorkflowError, "exactly workflow/github.json"
        ):
            workflow.WorkflowStore(
                self.state_dir,
                self.runtime,
                self.events,
                github_authority_config=alternate,
            )

    def test_github_cutover_rejects_symlinked_authority_config(self) -> None:
        config = self.root / "workflow" / "github.json"
        target = self.root / "evil.json"
        target.write_text("{}\n", encoding="utf-8")
        config.symlink_to(target)
        parser = workflow.build_parser()
        with self.assertRaisesRegex(
            workflow.WorkflowError, "regular, non-symlink"
        ):
            workflow.run_cli(
                parser.parse_args(
                    [
                        "--root",
                        str(self.root),
                        "dispatch",
                        "--capacity",
                        "1",
                        "--dry-run",
                        "--github-config",
                        "workflow/github.json",
                    ]
                )
            )

    def test_github_cutover_blocks_store_issue_and_pr_mutations(self) -> None:
        self.activate_github_cutover()
        before = {
            name: (self.state_dir / name).read_bytes()
            for name in ("issues.json", "prs.json")
        }
        for filename in ("issues.json", "prs.json"):
            with self.subTest(filename=filename), self.assertRaisesRegex(
                workflow.WorkflowError, "local issue/PR mutation is disabled"
            ):
                self.store.mutate(
                    filename,
                    "record.updated",
                    {"kind": filename},
                    lambda document: document.update({"tampered": True}),
                )
        self.assertEqual(
            before,
            {
                name: (self.state_dir / name).read_bytes()
                for name in ("issues.json", "prs.json")
            },
        )

    def test_github_cutover_plans_migrated_session_with_manifest_number(self) -> None:
        self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a01-plan-migrated")
        candidate.pop("github_issue_number", None)
        parser = workflow.build_parser()

        result = workflow.run_cli(
            parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "add",
                    "planned-session",
                    "--json",
                    json.dumps(candidate),
                ]
            )
        )

        self.assertEqual(2, result["github_issue_number"])
        planned = self.store.validate()["sessions.json"]["planned"]
        self.assertEqual([result], planned)

    def test_github_cutover_plans_github_only_session_without_shadow_issue(self) -> None:
        self.activate_github_cutover()
        candidate = planned_session("i028-reviewer-a01-plan-github-only")
        candidate["issue_id"] = None
        candidate["github_issue_number"] = 28
        candidate["pr_id"] = None
        candidate["github_pull_request_number"] = 29
        candidate["github_pull_request_base_ref"] = "main"
        candidate["github_pull_request_base_sha"] = BASE_SHA
        candidate["github_pull_request_head_ref"] = "workflow/qpbt-053"
        candidate["github_pull_request_head_sha"] = HEAD_SHA
        candidate["stage_id"] = "STAGE-01"
        issues_before = (self.state_dir / "issues.json").read_bytes()

        result = self.store.plan_session(candidate)

        self.assertIsNone(result["issue_id"])
        self.assertEqual(28, result["github_issue_number"])
        self.assertEqual(29, result["github_pull_request_number"])
        self.assertEqual("STAGE-01", result["stage_id"])
        self.assertEqual(issues_before, (self.state_dir / "issues.json").read_bytes())
        self.assertEqual(
            [result], self.store.validate()["sessions.json"]["planned"]
        )

    def test_github_cutover_plan_identity_failures_roll_back_exact_bytes(self) -> None:
        self.activate_github_cutover()
        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()
        mismatched = planned_session("i002-reviewer-a02-plan-mismatch")
        mismatched["github_issue_number"] = 999
        github_only_migrated = planned_session(
            "i002-reviewer-a03-plan-migrated-as-github-only"
        )
        github_only_migrated["issue_id"] = None
        github_only_migrated["github_issue_number"] = 2
        github_only_migrated["stage_id"] = "STAGE-01"

        for candidate, message in (
            (mismatched, "binding disagrees"),
            (github_only_migrated, "targets migrated issue #2"),
        ):
            with self.subTest(session_id=candidate["id"]), self.assertRaisesRegex(
                workflow.WorkflowError, message
            ):
                self.store.plan_session(candidate)
            self.assertEqual(
                sessions_before, (self.state_dir / "sessions.json").read_bytes()
            )
            self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_symlinked_state_dir_cannot_bypass_authority(self) -> None:
        self.activate_github_cutover()
        alias = self.root / "state-alias"
        alias.symlink_to(self.state_dir, target_is_directory=True)
        store = workflow.WorkflowStore(alias, self.runtime, self.events)
        issues_before = (self.state_dir / "issues.json").read_bytes()
        events_before = self.events.read_bytes()

        with self.assertRaisesRegex(
            workflow.WorkflowError, "must not use a symlink or lexical alias"
        ):
            store.mutate(
                "issues.json",
                "record.updated",
                {"kind": "issue"},
                lambda document: document.update({"tampered": True}),
            )

        self.assertEqual(issues_before, (self.state_dir / "issues.json").read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_plan_rejects_issued_record_dead_ends(self) -> None:
        self.activate_github_cutover()
        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()
        unknown_pr = planned_session("i002-reviewer-a05-unknown-pr")
        unknown_pr["pr_id"] = "LPR-404"
        missing_backend = planned_session("i002-reviewer-a06-missing-backend")
        missing_backend.pop("backend")
        unbound_pr_without_identity = planned_session(
            "i002-reviewer-a09-unbound-pr-without-identity"
        )
        unbound_pr_without_identity["pr_id"] = None
        unbound_pr_without_identity["github_pull_request_number"] = 999

        for candidate, message in (
            (unknown_pr, "unmigrated legacy pull request 'LPR-404'"),
            (missing_backend, "cannot materialize as an issued record.*backend"),
            (
                unbound_pr_without_identity,
                "pull-request base ref must match canonical main",
            ),
        ):
            with self.subTest(session_id=candidate["id"]), self.assertRaisesRegex(
                workflow.WorkflowError, message
            ):
                self.store.plan_session(candidate)
            self.assertEqual(
                sessions_before, (self.state_dir / "sessions.json").read_bytes()
            )
            self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_plan_binds_migrated_pull_request_identity(self) -> None:
        self.activate_github_cutover()
        state = documents()
        draft = pull_request(status="draft", checks=[], reviews=[], findings=[])
        draft["implementer_session_ids"] = []
        state["prs.json"]["pull_requests"] = [draft]
        (self.state_dir / "prs.json").write_text(
            json.dumps(state["prs.json"]), encoding="utf-8"
        )
        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()

        mismatch = planned_session("i002-reviewer-a07-pr-mismatch")
        mismatch["pr_id"] = "LPR-001"
        mismatch["github_pull_request_number"] = 999
        with self.assertRaisesRegex(
            workflow.WorkflowError, "pull-request binding disagrees"
        ):
            self.store.plan_session(mismatch)
        self.assertEqual(sessions_before, (self.state_dir / "sessions.json").read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

        migrated = planned_session("i002-reviewer-a08-pr-materialized")
        migrated["pr_id"] = "LPR-001"
        migrated.pop("github_pull_request_number", None)
        result = self.store.plan_session(migrated)
        self.assertEqual(26, result["github_pull_request_number"])
        self.assertEqual("main", result["github_pull_request_base_ref"])
        self.assertEqual(HEAD_SHA, result["github_pull_request_head_sha"])

    def test_github_cutover_dispatch_reaudits_migrated_pr_manifest_binding(self) -> None:
        config = self.activate_github_cutover()
        state = documents()
        draft = pull_request(status="draft", checks=[], reviews=[], findings=[])
        draft["implementer_session_ids"] = []
        state["prs.json"]["pull_requests"] = [draft]
        (self.state_dir / "prs.json").write_text(
            json.dumps(state["prs.json"]), encoding="utf-8"
        )
        candidate = planned_session("i002-reviewer-a10-pr-remapped")
        candidate["pr_id"] = "LPR-001"
        candidate = self.store.plan_session(candidate)
        manifest_path = self.root / "workflow" / "github-cutover.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["pull_requests"][0]["number"] = 27
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()

        with mock.patch.object(github_workflow, "live_preflight") as preflight, \
             self.assertRaisesRegex(
                 workflow.WorkflowError,
                 "mismatched migrated GitHub pull-request binding",
             ):
            workflow._github_dispatch_preflight(
                self.store, config.resolve(), [candidate["id"]]
            )
        preflight.assert_not_called()
        self.assertEqual(sessions_before, (self.state_dir / "sessions.json").read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_plan_rejects_duplicate_orchestrator_dead_end(self) -> None:
        self.activate_github_cutover()
        first = planned_session(
            "i002-orchestrator-a01-cutover-plan",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/First.lean"],
        )
        second = planned_session(
            "i002-orchestrator-a02-cutover-plan",
            role="orchestrator",
            read_only=False,
            owned_paths=["MIPStarRE/QPBT/Second.lean"],
        )
        self.store.plan_session(first)
        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()
        with self.assertRaisesRegex(
            workflow.WorkflowError, "duplicate orchestrator"
        ):
            self.store.plan_session(second)
        self.assertEqual(sessions_before, (self.state_dir / "sessions.json").read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_manifest_without_config_fails_closed(self) -> None:
        config = self.activate_github_cutover()
        config.unlink()
        store = workflow.WorkflowStore(self.state_dir, self.runtime, self.events)
        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()

        with self.assertRaisesRegex(
            workflow.WorkflowError,
            "authority config is missing while the irreversible cutover manifest remains",
        ):
            store.plan_session(planned_session("i002-reviewer-a04-missing-config"))

        self.assertEqual(
            sessions_before, (self.state_dir / "sessions.json").read_bytes()
        )
        self.assertEqual(events_before, self.events.read_bytes())

    def test_long_lived_store_rechecks_cutover_marker_before_dispatch(self) -> None:
        candidate = planned_session("i002-reviewer-a01-late-cutover")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        self.activate_github_cutover()
        with self.assertRaisesRegex(
            workflow.WorkflowError, "requires an opaque live preflight proof"
        ):
            self.store.dispatch_sessions(
                capacity=1,
                session_ids=[candidate["id"]],
                dry_run=True,
                issue_projection={},
                canonical_issue_projection={},
            )

    def test_cutover_marker_created_before_dispatch_lock_fails_closed(self) -> None:
        candidate = planned_session("i002-reviewer-a02-cutover-race")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        original_refresh = self.store._refresh_github_authority
        calls = 0

        def create_marker_on_second_refresh() -> Path | None:
            nonlocal calls
            calls += 1
            if calls == 2:
                (self.root / "workflow" / "github.json").write_text(
                    "{}\n", encoding="utf-8"
                )
            return original_refresh()

        self.store._refresh_github_authority = create_marker_on_second_refresh  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                workflow.WorkflowError, "appeared or disappeared during dispatch"
            ):
                self.store.dispatch_sessions(
                    capacity=1,
                    session_ids=[candidate["id"]],
                    dry_run=True,
                    issue_projection={
                        "QPBT-002": {
                            "status": "ready",
                            "parent_id": None,
                            "dependency_ids": [],
                        }
                    },
                    canonical_issue_projection={},
                )
        finally:
            self.store._refresh_github_authority = original_refresh  # type: ignore[method-assign]

    def test_cutover_marker_created_during_session_mutation_fails_closed(self) -> None:
        sessions_path = self.state_dir / "sessions.json"
        before_sessions = sessions_path.read_bytes()
        before_events = self.events.read_bytes()

        def create_marker(document: dict[str, object]) -> None:
            document["mutation_marker"] = True
            (self.root / "workflow" / "github.json").write_text(
                "{}\n", encoding="utf-8"
            )

        with self.assertRaisesRegex(
            workflow.WorkflowError, "authority appeared during generic local mutation"
        ):
            self.store.mutate(
                "sessions.json",
                "record.updated",
                {"kind": "issued-session"},
                create_marker,
            )
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

    def test_cutover_marker_created_after_session_write_rolls_back(self) -> None:
        sessions_path = self.state_dir / "sessions.json"
        before_sessions = sessions_path.read_bytes()
        before_events = self.events.read_bytes()
        original_write = workflow.atomic_write_json

        def create_marker_after_write(path: Path, value: object) -> None:
            original_write(path, value)
            if path == sessions_path:
                (self.root / "workflow" / "github.json").write_text(
                    "{}\n", encoding="utf-8"
                )

        with mock.patch.object(
            workflow, "atomic_write_json", side_effect=create_marker_after_write
        ), self.assertRaisesRegex(
            workflow.WorkflowError, "authority appeared during generic local mutation"
        ):
            self.store.mutate(
                "sessions.json",
                "record.updated",
                {"kind": "issued-session"},
                lambda document: document.update({"mutation_marker": True}),
            )
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

    def test_cutover_marker_created_during_initialize_rolls_back(self) -> None:
        root = self.root / "initialize-race"
        state_dir = root / "workflow" / "state"
        state_dir.mkdir(parents=True)
        events = root / "workflow" / "events.jsonl"
        store = workflow.WorkflowStore(
            state_dir, root / ".workflow-runtime", events
        )
        original_write = workflow.atomic_write_json

        def create_marker_after_first_write(path: Path, value: object) -> None:
            original_write(path, value)
            if path.name == "issues.json":
                (root / "workflow" / "github.json").write_text(
                    "{}\n", encoding="utf-8"
                )

        with mock.patch.object(
            workflow, "atomic_write_json", side_effect=create_marker_after_first_write
        ), self.assertRaisesRegex(
            workflow.WorkflowError, "appeared during workflow initialization"
        ):
            store.initialize()
        self.assertEqual([], list(state_dir.iterdir()))
        self.assertFalse(events.exists())

    def test_initialize_rolls_back_interrupt_after_first_publication(self) -> None:
        root = self.root / "initialize-interrupt"
        state_dir = root / "workflow" / "state"
        state_dir.mkdir(parents=True)
        events = root / "workflow" / "events.jsonl"
        store = workflow.WorkflowStore(
            state_dir, root / ".workflow-runtime", events
        )
        original_write = workflow.atomic_write_json
        interrupted = False

        def interrupt_after_write(path: Path, value: object) -> None:
            nonlocal interrupted
            original_write(path, value)
            if not interrupted:
                interrupted = True
                raise KeyboardInterrupt

        with mock.patch.object(
            workflow, "atomic_write_json", side_effect=interrupt_after_write
        ), self.assertRaises(KeyboardInterrupt):
            store.initialize()
        self.assertEqual([], list(state_dir.iterdir()))
        self.assertFalse(events.exists())

    def test_cutover_marker_created_on_event_lock_fails_closed(self) -> None:
        before_events = self.events.read_bytes()
        original_lock = self.store._lock

        @contextmanager
        def create_marker_on_lock(*, exclusive: bool):
            with original_lock(exclusive=exclusive) as descriptor:
                (self.root / "workflow" / "github.json").write_text(
                    "{}\n", encoding="utf-8"
                )
                yield descriptor

        self.store._lock = create_marker_on_lock  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                workflow.WorkflowError, "appeared during generic event append"
            ):
                self.store.append_event("record.updated", {"kind": "stage"})
        finally:
            self.store._lock = original_lock  # type: ignore[method-assign]
        self.assertEqual(before_events, self.events.read_bytes())

    def test_github_cutover_dispatch_uses_live_canonical_issue_projection(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a01-github-preflight")
        candidate["github_issue_number"] = 2
        state = documents()
        state["issues.json"]["issues"][1]["kind"] = "workflow"
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "issues.json").write_text(
            json.dumps(state["issues.json"]), encoding="utf-8"
        )
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        bindings = (
            github_workflow.IssueBinding("QPBT-001", 1, 101, "ISSUE1", "marker1"),
            github_workflow.IssueBinding("QPBT-002", 2, 102, "ISSUE2", "marker2"),
        )
        authority = mock.Mock()
        authority.issues = bindings
        authority.pull_requests = ()
        authority.issue_by_legacy_id.side_effect = lambda value: {
            item.legacy_id: item for item in bindings
        }[value]
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            "QPBT-002",
            2,
            102,
            "ISSUE2",
            "OPEN",
            None,
            "ready",
            "workflow",
            "QPBT-002",
            ("kind:workflow", "status:ready"),
            None,
            None,
            None,
            None,
            (),
            (),
            (1,),
            ("QPBT-001",),
        )
        dependency = github_workflow.IssueSnapshot(
            "QPBT-001",
            1,
            101,
            "ISSUE1",
            "CLOSED",
            "COMPLETED",
            "done",
            "formalization",
            "QPBT-001",
            ("kind:formalization",),
            None,
            None,
            None,
            None,
            (),
            (),
            (),
            (),
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository,
            BASE_SHA,
            (selected, dependency),
            (),
        )
        parser = workflow.build_parser()
        arguments = parser.parse_args(
            [
                "--root",
                str(self.root),
                "dispatch",
                "--capacity",
                "1",
                "--session-id",
                str(candidate["id"]),
                "--dry-run",
                "--github-config",
                "workflow/github.json",
            ]
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ) as preflight:
            result = workflow.run_cli(arguments)

        self.assertEqual("ready", result["status"])
        self.assertEqual([2], result["github_preflight"]["selected_issue_numbers"])
        preflight.assert_has_calls([
            mock.call(
                config.resolve(),
                issue_numbers=[2],
                pull_request_expectations=[],
            ),
            mock.call(
                config.resolve(),
                issue_numbers=[2],
                pull_request_expectations=[],
            ),
        ])
        self.assertEqual(2, preflight.call_count)
        self.assertEqual([], self.store.validate()["sessions.json"]["issued"])

        guarded_store = workflow.WorkflowStore(
            self.state_dir,
            self.runtime,
            self.events,
        )
        with self.assertRaisesRegex(
            workflow.WorkflowError, "requires an opaque live preflight proof"
        ):
            guarded_store.dispatch_sessions(
                capacity=1,
                session_ids=[str(candidate["id"])],
                dry_run=True,
            )

    def test_github_cutover_dispatch_live_checks_exact_github_only_pr_twice(self) -> None:
        config = self.activate_github_cutover()
        state = documents()
        state["issues.json"]["issues"][1]["kind"] = "workflow"
        (self.state_dir / "issues.json").write_text(
            json.dumps(state["issues.json"]), encoding="utf-8"
        )
        candidate = planned_session("i002-reviewer-a09-github-only-pr")
        candidate.update(
            {
                "pr_id": None,
                "github_pull_request_number": 29,
                "github_pull_request_base_ref": "main",
                "github_pull_request_base_sha": BASE_SHA,
                "github_pull_request_head_ref": "workflow/qpbt-053",
                "github_pull_request_head_sha": HEAD_SHA,
            }
        )
        candidate = self.store.plan_session(candidate)
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected_issue = github_workflow.IssueSnapshot(
            "QPBT-002", 2, 102, "ISSUE2", "OPEN", None, "ready",
            "workflow", "QPBT-002", ("kind:workflow", "status:ready"),
            None, None, None, None, (), (), (), ()
        )
        selected_pr = github_workflow.PullRequestSnapshot(
            None,
            29,
            229,
            "PR_pullNode029",
            "OPEN",
            "required",
            "GitHub canonical cutover",
            ("review:required",),
            "main",
            BASE_SHA,
            "workflow/qpbt-053",
            HEAD_SHA,
            None,
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (selected_issue,), (selected_pr,)
        )
        expectation = github_workflow.PullRequestExpectation(
            29, "main", BASE_SHA, "workflow/qpbt-053", HEAD_SHA
        )
        with mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ) as preflight:
            _, _, evidence, proof = workflow._github_dispatch_preflight(
                self.store, config.resolve(), [candidate["id"]]
            )
            result = self.store.dispatch_sessions(
                capacity=1,
                session_ids=[candidate["id"]],
                dry_run=True,
                github_preflight_proof=proof,
            )

        self.assertEqual("ready", result["status"])
        self.assertEqual([29], evidence["selected_pull_request_numbers"])
        preflight.assert_has_calls(
            [
                mock.call(
                    config.resolve(),
                    issue_numbers=[2],
                    pull_request_expectations=[expectation],
                ),
                mock.call(
                    config.resolve(),
                    issue_numbers=[2],
                    pull_request_expectations=[expectation],
                ),
            ]
        )

        sessions_before = (self.state_dir / "sessions.json").read_bytes()
        events_before = self.events.read_bytes()
        missing_pr = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (selected_issue,), ()
        )
        with mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            _, _, _, proof = workflow._github_dispatch_preflight(
                self.store, config.resolve(), [candidate["id"]]
            )
        with mock.patch.object(
            github_workflow, "live_preflight", return_value=missing_pr
        ), self.assertRaisesRegex(
            workflow.WorkflowError, "omitted selected pull requests: 29"
        ):
            self.store.dispatch_sessions(
                capacity=1,
                session_ids=[candidate["id"]],
                github_preflight_proof=proof,
            )
        self.assertEqual(sessions_before, (self.state_dir / "sessions.json").read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_locked_live_state_change_blocks_publication(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a10-locked-live-state")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        sessions_before = sessions_path.read_bytes()
        events_before = self.events.read_bytes()
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )

        def selected(status: str) -> github_workflow.IssueSnapshot:
            return github_workflow.IssueSnapshot(
                legacy_id="QPBT-002",
                number=2,
                database_id=102,
                node_id="I_issueNode02",
                state="OPEN",
                state_reason=None,
                status=status,
                kind="formalization",
                title="QPBT-002",
                labels=("kind:formalization", f"status:{status}"),
                parent_number=None,
                parent_database_id=None,
                parent_node_id=None,
                parent_legacy_id=None,
                child_numbers=(),
                child_legacy_ids=(),
                dependency_numbers=(1,),
                dependency_legacy_ids=("QPBT-001",),
            )

        dependency = github_workflow.IssueSnapshot(
            legacy_id="QPBT-001",
            number=1,
            database_id=101,
            node_id="I_issueNode01",
            state="CLOSED",
            state_reason="COMPLETED",
            status="done",
            kind="formalization",
            title="QPBT-001",
            labels=("kind:formalization",),
            parent_number=None,
            parent_database_id=None,
            parent_node_id=None,
            parent_legacy_id=None,
            child_numbers=(),
            child_legacy_ids=(),
            dependency_numbers=(),
            dependency_legacy_ids=(),
        )
        snapshots = [
            github_workflow.PreflightSnapshot(
                repository, BASE_SHA, (selected("ready"), dependency), ()
            ),
            github_workflow.PreflightSnapshot(
                repository, BASE_SHA, (selected("blocked"), dependency), ()
            ),
        ]
        arguments = workflow.build_parser().parse_args(
            [
                "--root",
                str(self.root),
                "dispatch",
                "--capacity",
                "1",
                "--session-id",
                str(candidate["id"]),
                "--github-config",
                "workflow/github.json",
            ]
        )

        with mock.patch.object(
            github_workflow, "live_preflight", side_effect=snapshots
        ) as preflight, self.assertRaisesRegex(
            workflow.WorkflowError, "not dispatchable from status 'blocked'"
        ):
            workflow.run_cli(arguments)

        self.assertEqual(2, preflight.call_count)
        self.assertEqual(sessions_before, sessions_path.read_bytes())
        self.assertEqual(events_before, self.events.read_bytes())

    def test_github_cutover_dispatches_github_only_issue_without_shadow_row(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i028-reviewer-a01-live-contract")
        candidate["issue_id"] = None
        candidate["github_issue_number"] = 28
        candidate["stage_id"] = "STAGE-01"
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        frozen_issues = (self.state_dir / "issues.json").read_bytes()
        authority = mock.Mock()
        authority.issues = ()
        authority.pull_requests = ()
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            legacy_id=None,
            number=28,
            database_id=128,
            node_id="ISSUE28",
            state="OPEN",
            state_reason=None,
            status="ready",
            kind="workflow",
            title="live contract",
            labels=("kind:workflow", "status:ready"),
            parent_number=1,
            parent_database_id=101,
            parent_node_id="ISSUE1",
            parent_legacy_id="QPBT-053",
            child_numbers=(),
            child_legacy_ids=(),
            dependency_numbers=(),
            dependency_legacy_ids=(),
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository,
            BASE_SHA,
            (selected,),
            (),
        )
        parser = workflow.build_parser()
        arguments = parser.parse_args(
            [
                "--root",
                str(self.root),
                "dispatch",
                "--capacity",
                "1",
                "--stage",
                "STAGE-01",
                "--session-id",
                str(candidate["id"]),
                "--github-config",
                "workflow/github.json",
            ]
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ) as preflight:
            result = workflow.run_cli(arguments)

        self.assertEqual("issued", result["status"])
        self.assertEqual([28], result["github_preflight"]["selected_issue_numbers"])
        preflight.assert_has_calls([
            mock.call(
                config.resolve(),
                issue_numbers=[28],
                pull_request_expectations=[],
            ),
            mock.call(
                config.resolve(),
                issue_numbers=[28],
                pull_request_expectations=[],
            ),
        ])
        self.assertEqual(2, preflight.call_count)
        issued = self.store.validate()["sessions.json"]["issued"][-1]
        self.assertIsNone(issued["issue_id"])
        self.assertEqual(28, issued["github_issue_number"])
        self.assertEqual("STAGE-01", issued["stage_id"])
        self.assertEqual(frozen_issues, (self.state_dir / "issues.json").read_bytes())

    def test_github_cutover_materializes_resolved_number_for_migrated_session(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a01-materialize-number")
        candidate.pop("github_issue_number", None)
        state = documents()
        state["issues.json"]["issues"][1]["kind"] = "workflow"
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "issues.json").write_text(
            json.dumps(state["issues.json"]), encoding="utf-8"
        )
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        binding = github_workflow.IssueBinding(
            "QPBT-002", 2, 102, "ISSUE2", "marker2"
        )
        authority = mock.Mock()
        authority.issues = (binding,)
        authority.pull_requests = ()
        authority.issue_by_legacy_id.side_effect = lambda value: binding
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            "QPBT-002", 2, 102, "ISSUE2", "OPEN", None, "ready",
            "workflow", "QPBT-002", ("kind:workflow", "status:ready"), None, None,
            None, None, (), (), (), ()
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (selected,), ()
        )
        parser = workflow.build_parser()
        arguments = parser.parse_args(
            [
                "--root", str(self.root), "dispatch", "--capacity", "1",
                "--session-id", candidate["id"], "--github-config",
                "workflow/github.json",
            ]
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            result = workflow.run_cli(arguments)
        self.assertEqual("issued", result["status"])
        issued = self.store.validate()["sessions.json"]["issued"][-1]
        self.assertEqual("QPBT-002", issued["issue_id"])
        self.assertEqual(2, issued["github_issue_number"])

    def test_github_cutover_manifest_digest_is_checked_before_publication(self) -> None:
        config = self.activate_github_cutover()
        manifest = self.root / "workflow" / "github-cutover.json"
        manifest.write_text("manifest-A\n", encoding="utf-8")
        candidate = planned_session("i002-reviewer-a02-manifest-race")
        candidate.pop("github_issue_number", None)
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        binding = github_workflow.IssueBinding(
            "QPBT-002", 2, 102, "ISSUE2", "marker2"
        )
        authority = mock.Mock()
        authority.issues = (binding,)
        authority.pull_requests = ()
        authority.manifest_path = manifest
        authority.issue_by_legacy_id.side_effect = lambda value: binding
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main", BASE_SHA, "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            "QPBT-002", 2, 102, "ISSUE2", "OPEN", None, "ready",
            "formalization", "QPBT-002", ("status:ready",), None, None,
            None, None, (), (), (), ()
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (selected,), ()
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            _, _, _, proof = workflow._github_dispatch_preflight(
                self.store, config.resolve(), [candidate["id"]]
            )
        self.assertIsNotNone(proof)
        original_lock = self.store._lock

        @contextmanager
        def rewrite_manifest_on_lock(*, exclusive: bool):
            with original_lock(exclusive=exclusive) as descriptor:
                if exclusive:
                    manifest.write_text("manifest-B\n", encoding="utf-8")
                yield descriptor

        self.store._lock = rewrite_manifest_on_lock  # type: ignore[method-assign]
        try:
            with mock.patch.object(
                github_workflow, "load_authority", return_value=authority
            ), mock.patch.object(
                github_workflow, "live_preflight", return_value=snapshot
            ):
                with self.assertRaisesRegex(
                    workflow.WorkflowError,
                    "cutover manifest changed during dispatch|"
                    "does not match a fresh live preflight under the publication lock",
                ):
                    self.store.dispatch_sessions(
                        capacity=1,
                        session_ids=[candidate["id"]],
                        github_preflight_proof=proof,
                    )
        finally:
            self.store._lock = original_lock  # type: ignore[method-assign]

    def test_github_cutover_direct_empty_projection_cannot_bypass_preflight(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a02-empty-proof")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        guarded_store = workflow.WorkflowStore(
            self.state_dir, self.runtime, self.events
        )
        before_sessions = (self.state_dir / "sessions.json").read_bytes()
        with self.assertRaisesRegex(
            workflow.WorkflowError, "opaque live preflight proof"
        ):
            guarded_store.dispatch_sessions(
                capacity=1,
                session_ids=[str(candidate["id"])],
                dry_run=False,
                issue_projection={},
                canonical_issue_projection={},
            )
        forged = workflow._GitHubDispatchProof(
            store_token=object(),
            config_path=config.resolve(),
            selected_session_ids=(str(candidate["id"]),),
            planned_rows_digest="forged",
            issue_projection={},
            canonical_issue_projection={},
            canonical_issue_bindings={},
            canonical_pull_request_bindings={},
        )
        with self.assertRaisesRegex(
            workflow.WorkflowError, "belongs to another store"
        ):
            guarded_store.dispatch_sessions(
                capacity=1,
                session_ids=[str(candidate["id"])],
                dry_run=True,
                github_preflight_proof=forged,
            )
        self.assertEqual(before_sessions, (self.state_dir / "sessions.json").read_bytes())

    def test_github_cutover_dispatch_rejects_stale_planned_snapshot(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a03-stale-proof")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        guarded_store = workflow.WorkflowStore(
            self.state_dir, self.runtime, self.events
        )
        binding = github_workflow.IssueBinding(
            "QPBT-002", 2, 102, "ISSUE2", "marker2"
        )
        authority = mock.Mock()
        authority.issues = (binding,)
        authority.pull_requests = ()
        authority.issue_by_legacy_id.side_effect = lambda value: binding
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            "QPBT-002",
            2,
            102,
            "ISSUE2",
            "OPEN",
            None,
            "ready",
            "formalization",
            "QPBT-002",
            ("kind:formalization", "status:ready"),
            None,
            None,
            None,
            None,
            (),
            (),
            (),
            (),
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (selected,), ()
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            _, _, _, proof = workflow._github_dispatch_preflight(
                guarded_store, config.resolve(), [str(candidate["id"])]
            )
        self.assertIsNotNone(proof)
        other_store = workflow.WorkflowStore(self.state_dir, self.runtime, self.events)
        with self.assertRaisesRegex(
            workflow.WorkflowError, "belongs to another store"
        ):
            other_store.dispatch_sessions(
                capacity=1,
                session_ids=[str(candidate["id"])],
                dry_run=True,
                github_preflight_proof=proof,
            )
        changed = copy.deepcopy(candidate)
        changed["role"] = "scout"
        (self.state_dir / "sessions.json").write_text(
            json.dumps({"schema_version": 1, "planned": [changed], "issued": []}),
            encoding="utf-8",
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            with self.assertRaisesRegex(
                workflow.WorkflowError, "does not match a fresh live preflight"
            ):
                guarded_store.dispatch_sessions(
                    capacity=1,
                    session_ids=[str(candidate["id"])],
                    dry_run=True,
                    github_preflight_proof=proof,
                )

    def test_github_cutover_rejects_migrated_issue_as_github_only(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i002-reviewer-a04-migrated-number")
        candidate["issue_id"] = None
        candidate["github_issue_number"] = 2
        candidate["stage_id"] = "STAGE-01"
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        authority = mock.Mock()
        authority.issues = (
            github_workflow.IssueBinding("QPBT-002", 2, 102, "ISSUE2", "marker2"),
        )
        authority.pull_requests = ()
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            "QPBT-002",
            2,
            102,
            "ISSUE2",
            "OPEN",
            None,
            "ready",
            "formalization",
            "QPBT-002",
            ("kind:formalization", "status:ready"),
            None,
            None,
            None,
            None,
            (),
            (),
            (),
            (),
        )
        snapshot = github_workflow.PreflightSnapshot(repository, BASE_SHA, (selected,), ())
        parser = workflow.build_parser()
        arguments = parser.parse_args(
            [
                "--root",
                str(self.root),
                "dispatch",
                "--capacity",
                "1",
                "--session-id",
                str(candidate["id"]),
                "--github-config",
                "workflow/github.json",
            ]
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            with self.assertRaisesRegex(
                workflow.WorkflowError, "targets migrated issue"
            ):
                workflow.run_cli(arguments)

    def test_github_cutover_rejects_unselected_migrated_number_reservation(self) -> None:
        config = self.activate_github_cutover()
        selected = planned_session("i002-orchestrator-a05-selected-migrated", role="orchestrator")
        stale = planned_session("i002-orchestrator-a06-stale-github-only", role="orchestrator")
        stale["issue_id"] = None
        stale["github_issue_number"] = 2
        stale["stage_id"] = "STAGE-01"
        state = documents()
        state["sessions.json"]["planned"] = [selected, stale]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        binding = github_workflow.IssueBinding(
            "QPBT-002", 2, 102, "ISSUE2", "marker2"
        )
        authority = mock.Mock()
        authority.issues = (binding,)
        authority.pull_requests = ()
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(github_workflow, "live_preflight") as preflight:
            with self.assertRaisesRegex(
                workflow.WorkflowError, "stale-github-only.*targets migrated issue"
            ):
                workflow._github_dispatch_preflight(
                    workflow.WorkflowStore(self.state_dir, self.runtime, self.events),
                    config.resolve(),
                    [str(selected["id"])],
                )
        preflight.assert_not_called()

    def test_github_cutover_preflight_respects_stage_scope(self) -> None:
        config = self.activate_github_cutover()
        state = documents()
        state["issues.json"]["issues"].append(issue("QPBT-003", "planned"))
        state["stages.json"]["stages"].append(
            {
                "id": "STAGE-02",
                "name": "other",
                "status": "in_progress",
                "issue_ids": ["QPBT-003"],
                "started_at": NOW,
                "ended_at": None,
                "elapsed_seconds": None,
                "token_usage": unavailable_tokens(),
                "subagents_issued": 0,
                "max_concurrency": 1,
                "outputs": [],
                "incident_ids": ["INC-001"],
            }
        )
        first = planned_session("i002-reviewer-a07-stage-one")
        second = planned_session("i003-reviewer-a08-stage-two", issue_id="QPBT-003")
        state["sessions.json"]["planned"] = [first, second]
        (self.state_dir / "issues.json").write_text(
            json.dumps(state["issues.json"]), encoding="utf-8"
        )
        (self.state_dir / "stages.json").write_text(
            json.dumps(state["stages.json"]), encoding="utf-8"
        )
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        bindings = (
            github_workflow.IssueBinding("QPBT-002", 2, 102, "ISSUE2", "marker2"),
            github_workflow.IssueBinding("QPBT-003", 3, 103, "ISSUE3", "marker3"),
        )
        authority = mock.Mock()
        authority.issues = bindings
        authority.pull_requests = ()
        authority.issue_by_legacy_id.side_effect = lambda value: {
            item.legacy_id: item for item in bindings
        }[value]
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        selected = github_workflow.IssueSnapshot(
            "QPBT-002", 2, 102, "ISSUE2", "OPEN", None, "ready",
            "formalization", "QPBT-002", ("status:ready",), None, None,
            None, None, (), (), (), ()
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (selected,), ()
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ) as preflight:
            workflow._github_dispatch_preflight(
                workflow.WorkflowStore(self.state_dir, self.runtime, self.events),
                config.resolve(),
                None,
                "STAGE-01",
            )
        preflight.assert_called_once_with(
            config.resolve(), issue_numbers=[2], pull_request_expectations=[]
        )

    def test_github_cutover_preflight_rejects_unhashable_dependencies(self) -> None:
        config = self.activate_github_cutover()
        candidate = planned_session("i028-reviewer-a09-malformed-dependencies")
        candidate["issue_id"] = None
        candidate["github_issue_number"] = 28
        candidate["stage_id"] = "STAGE-01"
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        authority = mock.Mock()
        authority.issues = ()
        authority.pull_requests = ()
        repository = github_workflow.RepositorySnapshot(
            github_workflow.RepositoryIdentity(
                "Dengnifer", "MIPStarRE-B", 1352436168, "R_kgDOUJyJyA"
            ),
            "main",
            BASE_SHA,
            "from-monorepo",
        )
        malformed = github_workflow.IssueSnapshot(
            legacy_id=None,
            number=28,
            database_id=128,
            node_id="ISSUE28",
            state="OPEN",
            state_reason=None,
            status="ready",
            kind="workflow",
            title="malformed",
            labels=("status:ready",),
            parent_number=None,
            parent_database_id=None,
            parent_node_id=None,
            parent_legacy_id=None,
            child_numbers=(),
            child_legacy_ids=(),
            dependency_numbers=([[]],),  # type: ignore[arg-type]
            dependency_legacy_ids=(),
        )
        snapshot = github_workflow.PreflightSnapshot(
            repository, BASE_SHA, (malformed,), ()
        )
        with mock.patch.object(
            github_workflow, "load_authority", return_value=authority
        ), mock.patch.object(
            github_workflow, "live_preflight", return_value=snapshot
        ):
            with self.assertRaisesRegex(
                workflow.WorkflowError, "invalid dependencies"
            ):
                workflow._github_dispatch_preflight(
                    workflow.WorkflowStore(self.state_dir, self.runtime, self.events),
                    config.resolve(),
                    [str(candidate["id"])],
                )

    def test_plan_dispatch_rejects_malformed_canonical_projection(self) -> None:
        state = documents()
        candidate = planned_session("i002-reviewer-a05-malformed-projection")
        candidate["issue_id"] = None
        candidate["github_issue_number"] = 22
        candidate["stage_id"] = "STAGE-01"
        state["sessions.json"]["planned"] = [candidate]
        with self.assertRaisesRegex(
            workflow.WorkflowError, "canonical issue projection must be an object"
        ):
            workflow.plan_dispatch(
                state,
                capacity=1,
                session_ids=[str(candidate["id"])],
                canonical_issue_projection=[],  # type: ignore[arg-type]
            )

    def test_github_cutover_override_cannot_add_canonical_issue_number(self) -> None:
        state = documents()
        candidate = planned_session("i002-reviewer-a10-identity-override")
        candidate.pop("github_issue_number", None)
        state["sessions.json"]["planned"] = [candidate]
        result = workflow.plan_dispatch(
            state,
            capacity=1,
            session_ids=[candidate["id"]],
            session_overrides={candidate["id"]: {"github_issue_number": 999}},
            canonical_issue_projection={
                2: {
                    "status": "ready",
                    "kind": "formalization",
                    "execution_category": "implementation",
                    "dependency_numbers": [],
                    "incomplete_dependency_numbers": [],
                }
            },
            canonical_issue_bindings={"QPBT-002": 2},
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual("invalid-dispatch-override", result["blocked"][0]["reason"])
        self.assertIn("github_issue_number", result["blocked"][0]["detail"])

    def test_dispatch_batch_issues_available_prefix_when_capacity_is_exhausted(self) -> None:
        first = collaboration_planned_session("i002-reviewer-a01-batch")
        second = collaboration_planned_session("i002-reviewer-a02-batch")
        state = documents()
        state["sessions.json"]["planned"] = [second, first]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )

        queued = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[second["id"], first["id"]],
            launch_confirmations=launch_confirmations(first),
        )
        self.assertEqual("issued", queued["status"])
        self.assertEqual([first["id"]], queued["issued"])
        self.assertEqual([first["id"]], queued["dispatchable"])
        self.assertEqual(
            [{"id": second["id"], "reason": "capacity-exhausted"}],
            queued["queued"],
        )
        unchanged = self.store.validate()
        self.assertEqual([second["id"]], [row["id"] for row in unchanged["sessions.json"]["planned"]])
        self.assertEqual([first["id"]], [row["id"] for row in unchanged["sessions.json"]["issued"]])
        events = [
            json.loads(line)
            for line in self.events.read_text(encoding="utf-8").splitlines()
            if line
        ]
        self.assertFalse(events[-1]["payload"]["all_or_nothing_request"])
        self.assertTrue(events[-1]["payload"]["atomic_batch"])

    def test_dispatch_batch_issues_sorted_candidates_atomically_and_records_events(self) -> None:
        first = collaboration_planned_session("i002-reviewer-a01-batch")
        second = collaboration_planned_session("i002-reviewer-a02-batch")
        state = documents()
        state["sessions.json"]["planned"] = [second, first]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )

        issued = self.store.dispatch_sessions(
            capacity=2,
            stage_id="STAGE-01",
            session_ids=[second["id"], first["id"]],
            launch_confirmations=launch_confirmations(first, second),
        )
        self.assertEqual("issued", issued["status"])
        self.assertEqual([first["id"], second["id"]], issued["issued"])
        loaded = self.store.validate()
        self.assertEqual([], loaded["sessions.json"]["planned"])
        self.assertEqual(
            [first["id"], second["id"]],
            [session["id"] for session in loaded["sessions.json"]["issued"]],
        )
        events = [
            json.loads(line)
            for line in self.events.read_text(encoding="utf-8").splitlines()
            if line
        ]
        self.assertEqual(
            [first["id"], second["id"]],
            [
                event["payload"]["session_id"]
                for event in events
                if event["event"] == "session.issued"
            ],
        )
        issuance_events = [event for event in events if event["event"] == "session.issued"]
        self.assertEqual(1, len({event["timestamp"] for event in issuance_events}))
        self.assertEqual("sessions.dispatched", events[-1]["event"])
        self.assertEqual(issuance_events[0]["timestamp"], events[-1]["timestamp"])
        self.assertTrue(events[-1]["payload"]["all_or_nothing_request"])
        self.assertTrue(events[-1]["payload"]["atomic_batch"])

    def test_dispatch_batch_with_blocked_member_leaves_every_candidate_planned(self) -> None:
        blocked_issue = issue("QPBT-003", "planned", ["QPBT-002"])
        state = documents()
        state["issues.json"]["issues"].append(blocked_issue)
        state["stages.json"]["stages"][0]["issue_ids"].append("QPBT-003")
        eligible = planned_session("i002-reviewer-a01-eligible")
        blocked = planned_session("i003-reviewer-a01-blocked", issue_id="QPBT-003")
        state["sessions.json"]["planned"] = [eligible, blocked]
        (self.state_dir / "issues.json").write_text(
            json.dumps(state["issues.json"]), encoding="utf-8"
        )
        (self.state_dir / "stages.json").write_text(
            json.dumps(state["stages.json"]), encoding="utf-8"
        )
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )

        result = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[blocked["id"], eligible["id"]],
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual([], result["issued"])
        self.assertTrue(result["request_atomic"])
        self.assertTrue(result["blocked_batch_unchanged"])
        loaded = self.store.validate()
        self.assertEqual(
            sorted([blocked["id"], eligible["id"]]),
            sorted(row["id"] for row in loaded["sessions.json"]["planned"]),
        )
        self.assertEqual([], loaded["sessions.json"]["issued"])

    def test_dispatch_dry_run_and_cli_leave_state_unchanged(self) -> None:
        candidate = planned_session("i002-reviewer-a01-dry-run")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        parser = workflow.build_parser()
        result = workflow.run_cli(
            parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "dispatch",
                    "--capacity",
                    "1",
                    "--stage",
                    "STAGE-01",
                    "--session-id",
                    candidate["id"],
                    "--dry-run",
                ]
            )
        )
        self.assertEqual("ready", result["status"])
        self.assertTrue(result["dry_run"])
        self.assertEqual([], self.store.validate()["sessions.json"]["issued"])

    def test_backend_launch_rejection_leaves_exact_bytes_and_retry_deterministic(self) -> None:
        candidate = collaboration_planned_session("i002-reviewer-a01-launch-rejected")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        before_sessions = sessions_path.read_bytes()
        before_events = self.events.read_bytes()

        first = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[candidate["id"]],
            dry_run=True,
        )
        # A backend rejection means no confirmation call exists. Repeating the
        # preflight must select the same planned work without durable effects.
        second = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[candidate["id"]],
            dry_run=True,
        )
        self.assertEqual(first, second)
        self.assertEqual([candidate["id"]], first["dispatchable"])
        self.assertTrue(first["launch_confirmation_required"])
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

        unconfirmed = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[candidate["id"]],
        )
        self.assertEqual("blocked", unconfirmed["status"])
        self.assertEqual("backend-launch-unconfirmed", unconfirmed["blocked"][0]["reason"])
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

        external_id = "collaboration-thread-returned-by-backend"
        issued = workflow.run_cli(
            workflow.build_parser().parse_args(
                [
                    "--root",
                    str(self.root),
                    "dispatch",
                    "--capacity",
                    "1",
                    "--stage",
                    "STAGE-01",
                    "--session-id",
                    str(candidate["id"]),
                    "--confirm-launched",
                    f"{candidate['id']}={external_id}",
                ]
            )
        )
        self.assertEqual("issued", issued["status"])
        loaded = self.store.validate()["sessions.json"]["issued"]
        self.assertEqual(external_id, loaded[0]["external_id"])
        issuance = [
            json.loads(line)
            for line in self.events.read_text(encoding="utf-8").splitlines()
            if line and json.loads(line)["event"] == "session.issued"
        ]
        self.assertEqual(external_id, issuance[-1]["payload"]["external_id"])

    def test_generic_external_id_cannot_bypass_launch_confirmation(self) -> None:
        candidate = collaboration_planned_session("i002-reviewer-a01-fabricated-override")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        before_sessions = sessions_path.read_bytes()
        before_events = self.events.read_bytes()

        result = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[candidate["id"]],
            session_overrides={
                str(candidate["id"]): {"external_id": "unconfirmed-generic-value"}
            },
        )
        self.assertEqual("blocked", result["status"])
        self.assertEqual("backend-launch-unconfirmed", result["blocked"][0]["reason"])
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

    def test_confirmation_for_queued_session_fails_closed_then_admitted_prefix_issues(self) -> None:
        first = collaboration_planned_session("i002-reviewer-a01-confirmed-prefix")
        second = collaboration_planned_session("i002-reviewer-a02-confirmed-queued")
        state = documents()
        state["sessions.json"]["planned"] = [second, first]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        before_sessions = sessions_path.read_bytes()
        before_events = self.events.read_bytes()

        preflight = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[second["id"], first["id"]],
            dry_run=True,
        )
        self.assertEqual([first["id"]], preflight["dispatchable"])
        self.assertEqual(
            [{"id": second["id"], "reason": "capacity-exhausted"}],
            preflight["queued"],
        )

        stale = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[second["id"], first["id"]],
            launch_confirmations=launch_confirmations(second),
        )
        self.assertEqual("blocked", stale["status"])
        self.assertEqual(
            ["backend-launch-unconfirmed", "launch-confirmation-not-admitted"],
            [entry["reason"] for entry in stale["blocked"]],
        )
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

        admitted = self.store.dispatch_sessions(
            capacity=1,
            stage_id="STAGE-01",
            session_ids=[second["id"], first["id"]],
            launch_confirmations=launch_confirmations(first),
        )
        self.assertEqual([first["id"]], admitted["issued"])
        loaded = self.store.validate()["sessions.json"]
        self.assertEqual([second["id"]], [row["id"] for row in loaded["planned"]])
        self.assertIsNone(loaded["planned"][0]["external_id"])

    def test_launch_confirmation_parser_rejects_duplicates_and_malformed_values(self) -> None:
        with self.assertRaisesRegex(workflow.WorkflowError, "duplicate launch confirmation"):
            workflow._parse_launch_confirmation_assignments(["session=one", "session=two"])
        for malformed in ("session", "=external", "session="):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(workflow.WorkflowError, "SESSION_ID=EXTERNAL_ID"):
                    workflow._parse_launch_confirmation_assignments([malformed])

    def test_dispatch_store_rejects_unknown_capacity_without_mutation(self) -> None:
        candidate = planned_session("i002-reviewer-a01-unknown-capacity")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        before_events = self.events.read_text(encoding="utf-8")
        with self.assertRaisesRegex(workflow.WorkflowError, "capacity is unknown"):
            self.store.dispatch_sessions(
                capacity=None,
                stage_id="STAGE-01",
                session_ids=[candidate["id"]],
            )
        loaded = self.store.validate()
        self.assertEqual([candidate["id"]], [row["id"] for row in loaded["sessions.json"]["planned"]])
        self.assertEqual([], loaded["sessions.json"]["issued"])
        self.assertEqual(before_events, self.events.read_text(encoding="utf-8"))

    def test_dispatch_rejects_invalid_existing_event_log_without_mutation(self) -> None:
        candidate = planned_session("i002-reviewer-a01-invalid-history")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        before_sessions = sessions_path.read_bytes()

        self.events.write_text("{bad}\n", encoding="utf-8")
        before_events = self.events.read_bytes()
        with self.assertRaises(workflow.ValidationError):
            self.store.dispatch_sessions(
                capacity=1,
                stage_id="STAGE-01",
                session_ids=[candidate["id"]],
            )
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

        def event(timestamp: str, name: str) -> str:
            return json.dumps(
                {
                    "schema_version": 1,
                    "timestamp": timestamp,
                    "event": name,
                    "actor": "test",
                    "pid": 1,
                    "payload": {},
                }
            )

        self.events.write_text(
            event(REVIEW_ENDED, "later") + "\n" + event(REVIEW_STARTED, "earlier") + "\n",
            encoding="utf-8",
        )
        before_events = self.events.read_bytes()
        with self.assertRaisesRegex(workflow.ValidationError, "chronological"):
            self.store.dispatch_sessions(
                capacity=1,
                stage_id="STAGE-01",
                session_ids=[candidate["id"]],
            )
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())

    def test_dispatch_rolls_back_state_and_events_when_event_append_fails(self) -> None:
        candidate = collaboration_planned_session("i002-reviewer-a01-event-rollback")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        before_sessions = sessions_path.read_bytes()
        before_events = self.events.read_bytes()
        original_append_event = self.store.append_event
        calls = 0

        def fail_on_summary(event: str, payload: object, **kwargs: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected append failure")
            original_append_event(event, payload, **kwargs)

        self.store.append_event = fail_on_summary  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(RuntimeError, "injected append failure"):
                self.store.dispatch_sessions(
                    capacity=1,
                    stage_id="STAGE-01",
                    session_ids=[candidate["id"]],
                    launch_confirmations=launch_confirmations(candidate),
                )
        finally:
            self.store.append_event = original_append_event  # type: ignore[method-assign]
        self.assertEqual(2, calls)
        self.assertEqual(before_sessions, sessions_path.read_bytes())
        self.assertEqual(before_events, self.events.read_bytes())
        loaded = self.store.validate()
        self.assertEqual([candidate["id"]], [row["id"] for row in loaded["sessions.json"]["planned"]])
        self.assertEqual([], loaded["sessions.json"]["issued"])

    def test_generic_mutation_rolls_back_every_state_file_when_event_append_fails(self) -> None:
        original_append_event = self.store.append_event

        def fail_append(event: str, payload: object, **kwargs: object) -> None:
            raise RuntimeError("injected mutation append failure")

        self.store.append_event = fail_append  # type: ignore[method-assign]
        try:
            for filename in workflow.DEFAULT_DOCUMENTS:
                with self.subTest(filename=filename):
                    state = documents()
                    for name, value in state.items():
                        (self.state_dir / name).write_text(
                            json.dumps(value), encoding="utf-8"
                        )
                    before = {
                        path.name: path.read_bytes()
                        for path in sorted(self.state_dir.iterdir())
                    }
                    before_events = self.events.read_bytes()

                    def mutate(document: dict[str, object]) -> None:
                        document["mutation_marker"] = filename

                    with self.assertRaisesRegex(
                        RuntimeError, "injected mutation append failure"
                    ):
                        self.store.mutate(
                            filename,
                            "record.updated",
                            {"kind": filename},
                            mutate,
                        )
                    self.assertEqual(
                        before,
                        {
                            path.name: path.read_bytes()
                            for path in sorted(self.state_dir.iterdir())
                        },
                    )
                    self.assertEqual(
                        before_events,
                        self.events.read_bytes(),
                    )
        finally:
            self.store.append_event = original_append_event  # type: ignore[method-assign]

    def test_dispatch_rolls_back_keyboard_interrupt_at_every_publication_boundary(self) -> None:
        baseline_events = self.events.read_bytes()
        boundaries = (
            "sessions-json",
            "session-issued-1",
            "session-issued-2",
            "sessions-dispatched",
            "post-publication-audit",
        )
        for boundary in boundaries:
            with self.subTest(boundary=boundary):
                first = collaboration_planned_session(
                    "i002-reviewer-a01-interrupt-first"
                )
                second = collaboration_planned_session(
                    "i002-reviewer-a02-interrupt-second"
                )
                state = documents()
                state["sessions.json"]["planned"] = [second, first]
                sessions_path = self.state_dir / "sessions.json"
                sessions_path.write_text(
                    json.dumps(state["sessions.json"]), encoding="utf-8"
                )
                self.events.write_bytes(baseline_events)
                before_sessions = sessions_path.read_bytes()
                before_events = self.events.read_bytes()
                preflight = self.store.dispatch_sessions(
                    capacity=2,
                    stage_id="STAGE-01",
                    session_ids=[second["id"], first["id"]],
                    dry_run=True,
                )

                original_atomic_write = workflow.atomic_write_json
                original_append_event = self.store.append_event
                original_validate_event_log = workflow.validate_event_log
                append_calls = 0

                def interrupt_after_sessions_write(path: Path, value: object) -> None:
                    original_atomic_write(path, value)
                    if path == sessions_path:
                        raise KeyboardInterrupt

                def interrupt_after_event(
                    event: str, payload: object, **kwargs: object
                ) -> None:
                    nonlocal append_calls
                    original_append_event(event, payload, **kwargs)  # type: ignore[arg-type]
                    append_calls += 1
                    expected_call = {
                        "session-issued-1": 1,
                        "session-issued-2": 2,
                        "sessions-dispatched": 3,
                    }.get(boundary)
                    if append_calls == expected_call:
                        raise KeyboardInterrupt

                def interrupt_after_audit(*args: object, **kwargs: object) -> None:
                    original_validate_event_log(*args, **kwargs)  # type: ignore[arg-type]
                    published_events = [
                        json.loads(line)
                        for line in self.events.read_text(encoding="utf-8").splitlines()
                        if line
                    ]
                    if published_events[-1]["event"] == "sessions.dispatched":
                        raise KeyboardInterrupt

                if boundary == "sessions-json":
                    patcher = mock.patch.object(
                        workflow,
                        "atomic_write_json",
                        side_effect=interrupt_after_sessions_write,
                    )
                elif boundary == "post-publication-audit":
                    patcher = mock.patch.object(
                        workflow,
                        "validate_event_log",
                        side_effect=interrupt_after_audit,
                    )
                else:
                    patcher = mock.patch.object(
                        self.store,
                        "append_event",
                        side_effect=interrupt_after_event,
                    )

                with patcher, self.assertRaises(KeyboardInterrupt):
                    self.store.dispatch_sessions(
                        capacity=2,
                        stage_id="STAGE-01",
                        session_ids=[second["id"], first["id"]],
                        launch_confirmations=launch_confirmations(first, second),
                    )

                self.assertEqual(before_sessions, sessions_path.read_bytes())
                self.assertEqual(before_events, self.events.read_bytes())
                self.store.validate()
                retry_preflight = self.store.dispatch_sessions(
                    capacity=2,
                    stage_id="STAGE-01",
                    session_ids=[second["id"], first["id"]],
                    dry_run=True,
                )
                self.assertEqual(preflight, retry_preflight)
                retried = self.store.dispatch_sessions(
                    capacity=2,
                    stage_id="STAGE-01",
                    session_ids=[second["id"], first["id"]],
                    launch_confirmations=launch_confirmations(first, second),
                )
                self.assertEqual([first["id"], second["id"]], retried["issued"])

    def test_issue_session_wrapper_honors_capacity_and_authority_checks(self) -> None:
        candidate = planned_session("i002-reviewer-a01-legacy-wrapper")
        state = documents()
        state["sessions.json"]["planned"] = [candidate]
        sessions_path = self.state_dir / "sessions.json"
        sessions_path.write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        parser = workflow.build_parser()

        queued = workflow.run_cli(
            parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "issue-session",
                    candidate["id"],
                    "--capacity",
                    "0",
                    "--json",
                    "{}",
                ]
            )
        )
        self.assertEqual("queued", queued["status"])
        self.assertEqual([], self.store.validate()["sessions.json"]["issued"])

        blocked = workflow.run_cli(
            parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "issue-session",
                    candidate["id"],
                    "--capacity",
                    "1",
                    "--json",
                    json.dumps({"issue_id": "QPBT-001"}),
                ]
            )
        )
        self.assertEqual("blocked", blocked["status"])
        self.assertEqual([], self.store.validate()["sessions.json"]["issued"])

        issued = workflow.run_cli(
            parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "issue-session",
                    candidate["id"],
                    "--capacity",
                    "1",
                    "--json",
                    "{}",
                ]
            )
        )
        # Successful legacy calls retain the historical single-record shape;
        # admission metadata remains available on the dispatch command.
        self.assertEqual(candidate["id"], issued["id"])
        self.assertEqual("issued", issued["status"])
        self.assertIsNone(issued["external_id"])
        self.assertNotIn("dispatchable", issued)
        self.assertNotIn("queued", issued)
        self.assertEqual(
            [candidate["id"]],
            [row["id"] for row in self.store.validate()["sessions.json"]["issued"]],
        )

    def test_issue_session_parser_requires_explicit_capacity(self) -> None:
        parser = workflow.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "issue-session",
                    "i002-reviewer-a01-parser-capacity",
                    "--json",
                    "{}",
                ]
            )

    def test_atomic_mutation_preserves_metadata_and_appends_event(self) -> None:
        def mutate(document: dict[str, object]) -> None:
            document["issues"][1]["title"] = "updated"

        self.store.mutate("issues.json", "record.updated", {"id": "QPBT-002"}, mutate)
        loaded = self.store.validate()
        self.assertEqual("keep", loaded["issues.json"]["issues"][1]["note"])
        entries = [json.loads(line) for line in self.events.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual("record.updated", entries[-1]["event"])
        leftovers = list(self.state_dir.glob(".*.tmp"))
        self.assertEqual([], leftovers)

    def test_pr_head_change_invalidates_approval_and_id_is_immutable(self) -> None:
        state = documents()
        state["prs.json"]["pull_requests"] = [pull_request()]
        add_pr_sessions(state)
        (self.state_dir / "prs.json").write_text(json.dumps(state["prs.json"]), encoding="utf-8")
        (self.state_dir / "sessions.json").write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        parser = workflow.build_parser()
        arguments = parser.parse_args(
            ["--root", str(self.root), "update", "pr", "LPR-001", "--set", f"head_sha={json.dumps('c' * 40)}"]
        )
        result = workflow.run_cli(arguments)
        self.assertEqual("changes_requested", result["status"])
        arguments = parser.parse_args(
            ["--root", str(self.root), "update", "pr", "LPR-001", "--set", "id=LPR-002"]
        )
        with self.assertRaises(workflow.WorkflowError):
            workflow.run_cli(arguments)

    def test_generic_update_cannot_mutate_status(self) -> None:
        parser = workflow.build_parser()
        arguments = parser.parse_args(
            ["--root", str(self.root), "update", "issue", "QPBT-002", "--set", 'status="done"']
        )
        with self.assertRaisesRegex(workflow.WorkflowError, "immutable field.*status"):
            workflow.run_cli(arguments)

        category = parser.parse_args(
            [
                "--root",
                str(self.root),
                "update",
                "issue",
                "QPBT-002",
                "--set",
                'execution_category="preflight"',
            ]
        )
        with self.assertRaisesRegex(workflow.WorkflowError, "immutable field.*execution_category"):
            workflow.run_cli(category)

    def test_generic_update_cannot_rewrite_attempt_authority_or_pr_evidence(self) -> None:
        state = documents()
        state["prs.json"]["pull_requests"] = [pull_request()]
        add_pr_sessions(state)
        (self.state_dir / "prs.json").write_text(json.dumps(state["prs.json"]), encoding="utf-8")
        (self.state_dir / "sessions.json").write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        parser = workflow.build_parser()

        authority = parser.parse_args(
            [
                "--root",
                str(self.root),
                "update",
                "issued-session",
                "i002-prover-a01-implementation",
                "--set",
                "read_only=true",
            ]
        )
        with self.assertRaisesRegex(workflow.WorkflowError, "authority field 'read_only' is immutable"):
            workflow.run_cli(authority)

        rewritten_reviews = [review_evidence(verdict="request_changes")]
        evidence = parser.parse_args(
            [
                "--root",
                str(self.root),
                "update",
                "pr",
                "LPR-001",
                "--set",
                f"reviews={json.dumps(rewritten_reviews)}",
            ]
        )
        with self.assertRaisesRegex(workflow.WorkflowError, "reviews.*append-only"):
            workflow.run_cli(evidence)

    def test_pr_update_rejects_stale_confirmation_after_all_assignments_atomically(self) -> None:
        state = finding_reconfirmation_documents(confirmation_ids=[])
        pr = state["prs.json"]["pull_requests"][0]
        pr["status"] = "changes_requested"
        (self.state_dir / "prs.json").write_text(json.dumps(state["prs.json"]), encoding="utf-8")
        (self.state_dir / "sessions.json").write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        parser = workflow.build_parser()
        findings = copy.deepcopy(pr["findings"])
        new_finding = copy.deepcopy(findings[0])
        new_finding["id"] = "F-003"
        new_finding["confirmation_review_ids"] = ["review-003"]
        findings.append(new_finding)
        assignments = [
            f"findings={json.dumps(findings)}",
            f"reviews={json.dumps(pr['reviews'])}",
            f"head_sha={json.dumps('e' * 40)}",
        ]
        original_prs = (self.state_dir / "prs.json").read_bytes()
        original_events = self.events.read_bytes()
        for order in itertools.permutations(assignments):
            arguments = ["--root", str(self.root), "update", "pr", "LPR-001"]
            for assignment in order:
                arguments.extend(["--set", assignment])
            with self.subTest(order=order), self.assertRaisesRegex(
                workflow.WorkflowError, "wrong head SHA"
            ):
                workflow.run_cli(parser.parse_args(arguments))
            self.assertEqual(original_prs, (self.state_dir / "prs.json").read_bytes())
            self.assertEqual(original_events, self.events.read_bytes())

    def test_current_confirmation_may_become_a_historical_prefix(self) -> None:
        state = finding_reconfirmation_documents(confirmation_ids=[])
        pr = state["prs.json"]["pull_requests"][0]
        pr["status"] = "changes_requested"
        (self.state_dir / "prs.json").write_text(json.dumps(state["prs.json"]), encoding="utf-8")
        (self.state_dir / "sessions.json").write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        parser = workflow.build_parser()
        findings = copy.deepcopy(pr["findings"])
        findings[0]["confirmation_review_ids"] = ["review-003"]
        append = parser.parse_args(
            [
                "--root", str(self.root), "update", "pr", "LPR-001",
                "--set", f"findings={json.dumps(findings)}",
            ]
        )
        workflow.run_cli(append)
        advance = parser.parse_args(
            [
                "--root", str(self.root), "update", "pr", "LPR-001",
                "--set", f"head_sha={json.dumps('e' * 40)}",
            ]
        )
        result = workflow.run_cli(advance)
        self.assertEqual(["review-003"], result["findings"][0]["confirmation_review_ids"])

    def test_approval_and_merge_transitions_require_current_evidence(self) -> None:
        state = documents()
        state["prs.json"]["pull_requests"] = [pull_request(status="ready", reviews=[])]
        add_pr_sessions(state)
        (self.state_dir / "prs.json").write_text(json.dumps(state["prs.json"]), encoding="utf-8")
        (self.state_dir / "sessions.json").write_text(json.dumps(state["sessions.json"]), encoding="utf-8")
        parser = workflow.build_parser()
        approve = parser.parse_args(
            ["--root", str(self.root), "transition", "pr", "LPR-001", "approved"]
        )
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.run_cli(approve)
        self.assertIn("requires a current approving review", str(caught.exception))

        state["prs.json"]["pull_requests"] = [pull_request()]
        (self.state_dir / "prs.json").write_text(json.dumps(state["prs.json"]), encoding="utf-8")
        merge = parser.parse_args(
            ["--root", str(self.root), "transition", "pr", "LPR-001", "merged"]
        )
        with self.assertRaises(workflow.ValidationError) as caught:
            workflow.run_cli(merge)
        self.assertIn("integration_sha", str(caught.exception))

        integration_sha = "d" * 40
        update = parser.parse_args(
            [
                "--root",
                str(self.root),
                "update",
                "pr",
                "LPR-001",
                "--set",
                f"integration_sha={json.dumps(integration_sha)}",
            ]
        )
        workflow.run_cli(update)
        result = workflow.run_cli(merge)
        self.assertEqual("merged", result["status"])
        self.assertIsNotNone(result["merged_at"])

    def test_issue_and_transition_events_use_canonical_session_id(self) -> None:
        session_id = "i002-reviewer-a01-lifecycle"
        planned = {
            "id": session_id,
            "name": session_id,
            "role": "reviewer",
            "issue_id": "QPBT-002",
            "status": "planned",
            "parent_session_id": None,
        }
        issued = issued_session(
            session_id,
            role="reviewer",
            status="issued",
            read_only=True,
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        issued["outcome_path"] = ".workflow-runtime/runs/lifecycle/result.json"
        state = documents()
        state["sessions.json"]["planned"] = [planned]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        parser = workflow.build_parser()
        issue_arguments = parser.parse_args(
            [
                "--root",
                str(self.root),
                "issue-session",
                session_id,
                "--capacity",
                "1",
                "--json",
                json.dumps(issued),
            ]
        )
        workflow.run_cli(issue_arguments)
        for status in ("running", "finished", "archived"):
            transition = parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "transition",
                    "issued-session",
                    session_id,
                    status,
                ]
            )
            workflow.run_cli(transition)
        self.store.validate()
        events = [
            json.loads(line)
            for line in self.events.read_text(encoding="utf-8").splitlines()
            if line
        ]
        lifecycle = [
            event for event in events if event["event"] in {"session.issued", "record.transitioned"}
        ]
        self.assertEqual(4, len(lifecycle))
        for event in lifecycle:
            self.assertEqual(session_id, event["payload"]["session_id"])
            self.assertNotIn("id", event["payload"])

    def test_failed_session_transition_reconciles_with_canonical_session_id(self) -> None:
        session_id = "i002-reviewer-a02-lifecycle-failure"
        session = issued_session(
            session_id,
            status="issued",
            read_only=True,
            started_at=None,
            ended_at=None,
            elapsed_seconds=None,
        )
        session["outcome_path"] = ".workflow-runtime/runs/lifecycle-failure/result.json"
        state = documents()
        state["sessions.json"]["issued"] = [session]
        (self.state_dir / "sessions.json").write_text(
            json.dumps(state["sessions.json"]), encoding="utf-8"
        )
        self.store.append_event("session.issued", {"session_id": session_id})
        parser = workflow.build_parser()
        for status in ("failed", "archived"):
            transition = parser.parse_args(
                [
                    "--root",
                    str(self.root),
                    "transition",
                    "issued-session",
                    session_id,
                    status,
                ]
            )
            workflow.run_cli(transition)
        self.store.validate()


class ResearchReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state = documents()
        session = issued_session("i002-reviewer-a01-metric", read_only=True)
        self.state["sessions.json"]["issued"] = [session]
        self.state["stages.json"]["stages"][0]["subagents_issued"] = 1
        metrics = self.root / "research" / "metrics"
        metrics.mkdir(parents=True)
        (metrics / "incidents.jsonl").write_text('{"id":"INC-001"}\n', encoding="utf-8")
        (metrics / "protocol_changes.jsonl").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def validate_metric(self, **updates: object) -> None:
        metric = {
            "session_id": "i002-reviewer-a01-metric",
            "issue_id": "QPBT-002",
            "stage_id": "STAGE-01",
        }
        metric.update(updates)
        path = self.root / "research" / "metrics" / "sessions.jsonl"
        path.write_text(json.dumps(metric) + "\n", encoding="utf-8")
        check_workflow.validate_research_ledgers(self.root, self.state)

    def test_exact_metric_and_stage_reconciliation_passes(self) -> None:
        self.validate_metric()

    def test_metric_issue_and_stage_mismatches_are_rejected(self) -> None:
        with self.assertRaisesRegex(workflow.ValidationError, "issue_id: expected"):
            self.validate_metric(issue_id="QPBT-001")
        with self.assertRaisesRegex(workflow.ValidationError, "unknown stage"):
            self.validate_metric(stage_id="STAGE-404")

    def test_duplicate_issue_to_stage_mapping_is_rejected(self) -> None:
        duplicate = copy.deepcopy(self.state["stages.json"]["stages"][0])
        duplicate["id"] = "STAGE-02"
        self.state["stages.json"]["stages"].append(duplicate)
        with self.assertRaisesRegex(workflow.ValidationError, "mapped to multiple stages"):
            self.validate_metric()

    def test_stale_stage_subagent_total_is_rejected(self) -> None:
        self.state["stages.json"]["stages"][0]["subagents_issued"] = 0
        with self.assertRaisesRegex(workflow.ValidationError, "subagents_issued: expected 1"):
            self.validate_metric()

    def test_postcutover_metric_reconciles_canonical_github_identity(self) -> None:
        session = self.state["sessions.json"]["issued"][0]
        session["issue_id"] = None
        session["github_issue_number"] = 1
        session["github_pull_request_number"] = 26
        session["stage_id"] = "STAGE-01"
        metric = {
            "session_id": session["id"],
            "issue_id": None,
            "github_issue_number": 1,
            "github_pull_request_number": 26,
            "stage_id": "STAGE-01",
        }
        path = self.root / "research" / "metrics" / "sessions.jsonl"
        path.write_text(json.dumps(metric) + "\n", encoding="utf-8")
        check_workflow.validate_research_ledgers(self.root, self.state)

        metric["github_issue_number"] = 2
        path.write_text(json.dumps(metric) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            workflow.ValidationError, "github_issue_number: expected 1, got 2"
        ):
            check_workflow.validate_research_ledgers(self.root, self.state)


class EventLogTests(unittest.TestCase):
    @staticmethod
    def event(timestamp: str, event: str, payload: dict[str, object] | None = None) -> str:
        return json.dumps(
            {
                "schema_version": 1,
                "timestamp": timestamp,
                "event": event,
                "actor": "test",
                "pid": 1,
                "payload": payload or {},
            }
        )

    def test_blank_lines_are_allowed_but_malformed_json_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text("\n" + self.event(NOW, "ok") + "\n\n", encoding="utf-8")
            workflow.validate_event_log(path)
            path.write_text("{bad}\n", encoding="utf-8")
            with self.assertRaises(workflow.ValidationError):
                workflow.validate_event_log(path)

    def test_legacy_envelope_and_reverse_chronology_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text('{"at":"old","event":"ok"}\n', encoding="utf-8")
            with self.assertRaises(workflow.ValidationError):
                workflow.validate_event_log(path)
            path.write_text(
                self.event(REVIEW_ENDED, "later")
                + "\n"
                + self.event(REVIEW_STARTED, "earlier")
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(workflow.ValidationError, "chronological"):
                workflow.validate_event_log(path)

    def test_archived_session_requires_ordered_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            state = documents()
            session = issued_session("i002-prover-a01-lifecycle")
            state["sessions.json"]["issued"] = [session]
            path.write_text(
                self.event(
                    NOW,
                    "session.issued",
                    {"session_id": session["id"]},
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(workflow.ValidationError, "terminal event"):
                workflow.validate_event_log(path, state)

            path.write_text(
                "\n".join(
                    [
                        self.event(NOW, "session.issued", {"session_id": session["id"]}),
                        self.event(REVIEW_STARTED, "session.finished", {"session_id": session["id"]}),
                        self.event(REVIEW_ENDED, "session.archived", {"session_id": session["id"]}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            workflow.validate_event_log(path, state)


if __name__ == "__main__":
    unittest.main()
