from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import workflow  # noqa: E402


NOW = "2026-08-30T00:00:00Z"
CHECKED = "2026-08-30T00:01:00Z"
REVIEW_STARTED = "2026-08-30T00:02:00Z"
REVIEW_ENDED = "2026-08-30T00:03:00Z"
REVIEW2_STARTED = "2026-08-30T00:04:00Z"
REVIEW2_ENDED = "2026-08-30T00:05:00Z"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40


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


def check_evidence(*, head_sha: str = HEAD_SHA, status: str = "passed") -> dict[str, object]:
    return {
        "id": "check-full-build",
        "name": "full build",
        "command": "lake build",
        "status": status,
        "base_sha": BASE_SHA,
        "head_sha": head_sha,
        "completed_at": CHECKED,
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


class WorkflowValidationTests(unittest.TestCase):
    def test_valid_documents_and_dependency_ready(self) -> None:
        state = documents()
        workflow.validate_documents(state)
        self.assertEqual(["QPBT-002"], [item["id"] for item in workflow.dependency_ready_issues(state)])

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

    def test_read_only_validation_creates_no_runtime_files(self) -> None:
        self.store.validate()
        self.assertFalse(self.runtime.exists())

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
