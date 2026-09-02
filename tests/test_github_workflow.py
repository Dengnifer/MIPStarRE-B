from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import github_workflow as github  # noqa: E402


REPOSITORY = {
    "owner": github.EXPECTED_OWNER,
    "name": github.EXPECTED_REPOSITORY,
    "database_id": 880001,
    "node_id": "R_repoNode01",
}
CUTOVER_SHA = "a" * 40
BASE_SHA = "b" * 40
HEAD_SHA = "c" * 40


def label_names(*names: str) -> list[dict[str, str]]:
    return [{"name": name} for name in names]


def repository_fixture(*, with_base_sha: bool = False) -> dict[str, object]:
    value: dict[str, object] = {
        "full_name": github.EXPECTED_FULL_NAME,
        "id": REPOSITORY["database_id"],
        "node_id": REPOSITORY["node_id"],
        "base_ref": github.EXPECTED_BASE_REF,
        "default_branch": github.EXPECTED_BASE_REF,
    }
    if with_base_sha:
        value["default_branch_sha"] = BASE_SHA
    return value


def repository_preflight_responses() -> dict[tuple[str, ...], object]:
    return {
        github._api_command(f"repos/{github.EXPECTED_FULL_NAME}"): repository_fixture(),
        github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/commits/main"
        ): {"sha": BASE_SHA},
        github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/commits/{CUTOVER_SHA}"
        ): {"sha": CUTOVER_SHA},
        github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/compare/{CUTOVER_SHA}...{BASE_SHA}"
        ): {
            "status": "ahead",
            "base_commit": {"sha": CUTOVER_SHA},
            "merge_base_commit": {"sha": CUTOVER_SHA},
            "head_commit": {"sha": BASE_SHA},
        },
    }


def manifest_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "repository": copy.deepcopy(REPOSITORY),
        "base_ref": "main",
        "cutover_main_sha": CUTOVER_SHA,
        "issues": [
            {
                "legacy_id": "QPBT-001",
                "number": 11,
                "database_id": 101,
                "node_id": "I_issueNode01",
                "marker": github.issue_marker("QPBT-001"),
            },
            {
                "legacy_id": "QPBT-002",
                "number": 12,
                "database_id": 102,
                "node_id": "I_issueNode02",
                "marker": github.issue_marker("QPBT-002"),
            },
        ],
        "pull_requests": [
            {
                "legacy_id": "LPR-001",
                "number": 21,
                "database_id": 201,
                "node_id": "PR_pullNode01",
                "marker": github.pull_request_marker("LPR-001"),
                "base_ref": "main",
                "base_sha": BASE_SHA,
                "head_ref": "issue/qpbt-001",
                "head_sha": HEAD_SHA,
            }
        ],
    }


def issue_fixture(
    legacy_id: str = "QPBT-002",
    *,
    state: str = "open",
    status_label: str | None = "status:ready",
    dependency_ids: tuple[str, ...] = ("QPBT-001",),
) -> dict[str, object]:
    facts = {
        "QPBT-001": (11, 101, "I_issueNode01"),
        "QPBT-002": (12, 102, "I_issueNode02"),
    }
    number, database_id, node_id = facts[legacy_id]
    body_lines = [github.issue_marker(legacy_id)]
    labels = [github.MIGRATION_LABEL, "kind:implementation"]
    if status_label is not None:
        labels.append(status_label)
    blocked_by = [
        {
            "number": facts[item][0],
            "database_id": facts[item][1],
            "id": facts[item][2],
        }
        for item in dependency_ids
    ]
    return {
        "repository": repository_fixture(),
        "issue": {
            "number": number,
            "id": database_id,
            "node_id": node_id,
            "state": state,
            "state_reason": "completed" if state.lower() == "closed" else None,
            "title": f"Issue {legacy_id}",
            "body": "\n".join(body_lines) + "\n",
            "labels": label_names(*labels),
            "parent": None,
            "subIssues": [],
            "blockedBy": blocked_by,
        },
    }


def pull_request_fixture(*, state: str = "open", merged_at: str | None = None) -> dict[str, object]:
    repo = repository_fixture()
    return {
        "repository": copy.deepcopy(repo),
        "pull_request": {
            "number": 21,
            "id": 201,
            "node_id": "PR_pullNode01",
            "state": state,
            "merged_at": merged_at,
            "title": "feat(QPBT): fixture",
            "body": github.pull_request_marker("LPR-001") + "\n",
            "labels": label_names(github.MIGRATION_LABEL, "review:required"),
            "base": {"ref": "main", "sha": BASE_SHA, "repo": copy.deepcopy(repo)},
            "head": {
                "ref": "issue/qpbt-001",
                "sha": HEAD_SHA,
                "repo": copy.deepcopy(repo),
            },
        },
    }


def canonical_issue_fixture() -> dict[str, object]:
    return {
        "repository": repository_fixture(),
        "issue": {
            "number": 31,
            "id": 301,
            "node_id": "I_canonicalIssue31",
            "state": "open",
            "state_reason": None,
            "title": "Canonical issue 31",
            "body": "No migration provenance.\n",
            "labels": label_names("kind:formalization", "status:planned"),
            "parent": {
                "number": 30,
                "id": 300,
                "node_id": "I_canonicalIssue30",
            },
            "subIssues": [],
            "blockedBy": [
                {"number": 11, "database_id": 101, "id": "I_issueNode01"},
                {
                    "number": 30,
                    "database_id": 300,
                    "id": "I_canonicalIssue30",
                },
            ],
        },
    }


def canonical_pull_request_fixture() -> tuple[dict[str, object], github.PullRequestExpectation]:
    repo = repository_fixture()
    expectation = github.PullRequestExpectation(
        number=32,
        base_ref="main",
        base_sha=BASE_SHA,
        head_ref="feature/canonical-32",
        head_sha="d" * 40,
    )
    fixture = {
        "repository": copy.deepcopy(repo),
        "pull_request": {
            "number": 32,
            "id": 302,
            "node_id": "PR_canonicalPull32",
            "state": "open",
            "merged_at": None,
            "title": "feat(QPBT): canonical PR 32",
            "body": "Closes #31\n",
            "labels": label_names("review:required"),
            "base": {"ref": "main", "sha": BASE_SHA, "repo": copy.deepcopy(repo)},
            "head": {
                "ref": expectation.head_ref,
                "sha": expectation.head_sha,
                "repo": copy.deepcopy(repo),
            },
        },
    }
    return fixture, expectation


def review_comment_contract(
    expectation: github.PullRequestExpectation,
    *,
    session_name: str = "i032-reviewer-a01-canonical",
    external_id: str = "01234567-89ab-cdef-0123-456789abcdef",
    verdict: str = "approve",
) -> tuple[github.PullRequestExpectation, dict[str, object], str]:
    report = {
        "review_identity": {
            "repository": github.EXPECTED_FULL_NAME,
            "pull_request": expectation.number,
            "session_name": session_name,
            "external_id": external_id,
            "base_sha": expectation.base_sha,
            "head_sha": expectation.head_sha,
        },
        "verdict": verdict,
        "summary": "exact review",
        "checked": ["base/head and owned diff"],
        "findings": [],
        "residual_risk": "none",
    }
    body = json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    comment_expectation = github.ReviewCommentExpectation(
        comment_database_id=401,
        comment_node_id="IC_reviewComment401",
        body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        reviewer_session_name=session_name,
        reviewer_external_id=external_id,
        verdict=verdict,
        disallowed_session_names=("i032-orchestrator-a01-canonical",),
        disallowed_external_ids=("11111111-1111-1111-1111-111111111111",),
    )
    bound = github.PullRequestExpectation(
        expectation.number,
        expectation.base_ref,
        expectation.base_sha,
        expectation.head_ref,
        expectation.head_sha,
        comment_expectation,
    )
    comment = {
        "id": 401,
        "node_id": "IC_reviewComment401",
        "issue_url": (
            f"https://api.github.com/repos/{github.EXPECTED_FULL_NAME}/issues/"
            f"{expectation.number}"
        ),
        "body": body,
    }
    return bound, comment, body


def integration_review_document(
    expectation: github.PullRequestExpectation,
) -> dict[str, object]:
    review = expectation.review_comment
    if review is None:
        raise AssertionError("test expectation must carry review-comment authority")
    return {
        "schema_version": 1,
        "pull_requests": [
            {
                "number": expectation.number,
                "review_comment": {
                    "comment_database_id": review.comment_database_id,
                    "comment_node_id": review.comment_node_id,
                    "body_sha256": review.body_sha256,
                    "reviewer_session_name": review.reviewer_session_name,
                    "reviewer_external_id": review.reviewer_external_id,
                    "verdict": review.verdict,
                    "disallowed_session_names": list(
                        review.disallowed_session_names
                    ),
                    "disallowed_external_ids": list(review.disallowed_external_ids),
                },
            }
        ],
    }


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], object]):
        self.responses = responses
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, command: object) -> subprocess.CompletedProcess[str]:
        argv = tuple(command)  # type: ignore[arg-type]
        self.calls.append(argv)
        response = self.responses[argv]
        if isinstance(response, subprocess.CompletedProcess):
            return response
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(response, ensure_ascii=True),
            stderr="",
        )


class GitHubWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config_path = self.root / "authority.json"
        self.manifest_path = self.root / "cutover.json"
        self.config = {
            "schema_version": 1,
            "repository": copy.deepcopy(REPOSITORY),
            "base_ref": "main",
            "cutover_manifest": "cutover.json",
        }
        self.manifest = manifest_document()
        self.write_contracts()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_contracts(self) -> None:
        self.config_path.write_text(
            json.dumps(self.config, indent=2) + "\n", encoding="utf-8"
        )
        self.manifest_path.write_text(
            json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
        )

    def authority(self) -> github.GitHubAuthority:
        self.write_contracts()
        return github.load_authority(self.config_path)

    def test_offline_contract_binds_exact_repo_base_and_deterministic_markers(self) -> None:
        authority = self.authority()
        self.assertEqual(github.EXPECTED_FULL_NAME, authority.repository.full_name)
        self.assertEqual("main", authority.base_ref)
        self.assertEqual(CUTOVER_SHA, authority.cutover_main_sha)
        self.assertEqual(
            ["QPBT-001", "QPBT-002"],
            [item.legacy_id for item in authority.issues],
        )
        self.assertEqual(
            "<!-- mipstarre-workflow:v1:pull-request:LPR-001 -->",
            authority.pull_requests[0].marker,
        )
        self.assertNotIn("base_sha", self.config)

    def test_config_rejects_unknown_mutable_base_and_schema_fields(self) -> None:
        for field, value in (("base_sha", BASE_SHA), ("token_env", "GH_TOKEN")):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.config)
                candidate[field] = value
                self.config_path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaisesRegex(
                    github.GitHubWorkflowError, "unexpected field set"
                ):
                    github.load_authority(self.config_path)

    def test_schema_version_rejects_boolean_and_float_aliases_for_one(self) -> None:
        for target, value in (("config", True), ("config", 1.0), ("manifest", True)):
            with self.subTest(target=target, value=value):
                self.config = {
                    "schema_version": 1,
                    "repository": copy.deepcopy(REPOSITORY),
                    "base_ref": "main",
                    "cutover_manifest": "cutover.json",
                }
                self.manifest = manifest_document()
                if target == "config":
                    self.config["schema_version"] = value
                else:
                    self.manifest["schema_version"] = value
                self.write_contracts()
                with self.assertRaisesRegex(github.GitHubWorkflowError, "schema"):
                    github.load_authority(self.config_path)

    def test_owner_repo_database_node_and_base_mismatches_fail_closed(self) -> None:
        mutations = (
            ("config owner", lambda: self.config["repository"].__setitem__("owner", "dengnifer")),
            ("config repo", lambda: self.config["repository"].__setitem__("name", "MIPStarRE")),
            (
                "manifest database",
                lambda: self.manifest["repository"].__setitem__("database_id", 9),
            ),
            (
                "manifest node",
                lambda: self.manifest["repository"].__setitem__(
                    "node_id", "R_otherNode01"
                ),
            ),
            ("config base", lambda: self.config.__setitem__("base_ref", "develop")),
            ("manifest base", lambda: self.manifest.__setitem__("base_ref", "develop")),
        )
        for name, mutate in mutations:
            with self.subTest(name=name):
                self.config = {
                    "schema_version": 1,
                    "repository": copy.deepcopy(REPOSITORY),
                    "base_ref": "main",
                    "cutover_manifest": "cutover.json",
                }
                self.manifest = manifest_document()
                mutate()
                self.write_contracts()
                with self.assertRaises(github.GitHubWorkflowError):
                    github.load_authority(self.config_path)

    def test_manifest_rejects_bad_identity_order_marker_sha_and_shared_number(self) -> None:
        def reverse_issues() -> None:
            self.manifest["issues"].reverse()

        def wrong_marker() -> None:
            self.manifest["issues"][0]["marker"] = github.issue_marker("QPBT-002")

        def short_sha() -> None:
            self.manifest["cutover_main_sha"] = "a" * 39

        def duplicate_number() -> None:
            self.manifest["pull_requests"][0]["number"] = 11

        for name, mutate in (
            ("order", reverse_issues),
            ("marker", wrong_marker),
            ("sha", short_sha),
            ("number", duplicate_number),
        ):
            with self.subTest(name=name):
                self.manifest = manifest_document()
                mutate()
                self.write_contracts()
                with self.assertRaises(github.GitHubWorkflowError):
                    github.load_authority(self.config_path)

    def test_duplicate_json_keys_and_symlink_contracts_are_rejected(self) -> None:
        self.config_path.write_text(
            '{"schema_version":1,"schema_version":1}', encoding="utf-8"
        )
        with self.assertRaisesRegex(github.GitHubWorkflowError, "duplicate JSON key"):
            github.load_authority(self.config_path)

        self.config_path.unlink()
        target = self.root / "real-config.json"
        target.write_text(json.dumps(self.config), encoding="utf-8")
        self.config_path.symlink_to(target)
        with self.assertRaisesRegex(github.GitHubWorkflowError, "non-symlink"):
            github.load_authority(self.config_path)

    def test_issue_fixture_parses_state_status_kind_and_dependencies(self) -> None:
        snapshot = github.parse_issue_fixture(self.authority(), issue_fixture())
        self.assertEqual("QPBT-002", snapshot.legacy_id)
        self.assertEqual("OPEN", snapshot.state)
        self.assertEqual("ready", snapshot.status)
        self.assertEqual("implementation", snapshot.kind)
        self.assertEqual(("QPBT-001",), snapshot.dependency_legacy_ids)

        closed = github.parse_issue_fixture(
            self.authority(),
            issue_fixture(
                "QPBT-001", state="closed", status_label=None, dependency_ids=()
            ),
        )
        self.assertEqual(("CLOSED", "done"), (closed.state, closed.status))

    def test_post_cutover_issue_uses_github_number_without_migration_metadata(self) -> None:
        authority = self.authority()
        snapshot = github.parse_issue_fixture(
            authority, canonical_issue_fixture(), expected_number=31
        )
        self.assertIsNone(snapshot.legacy_id)
        self.assertEqual(30, snapshot.parent_number)
        self.assertEqual("I_canonicalIssue30", snapshot.parent_node_id)
        self.assertEqual((11, 30), snapshot.dependency_numbers)
        self.assertEqual(("QPBT-001",), snapshot.dependency_legacy_ids)

        fake_migration = canonical_issue_fixture()
        fake_migration["issue"]["labels"].append({"name": github.MIGRATION_LABEL})
        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "migration provenance"
        ):
            github.parse_issue_fixture(authority, fake_migration)

        missing_migration = issue_fixture()
        missing_migration["issue"]["labels"] = label_names(
            "kind:implementation", "status:ready"
        )
        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "migration provenance"
        ):
            github.parse_issue_fixture(authority, missing_migration)

        wrong_parent = canonical_issue_fixture()
        wrong_parent["issue"]["parent"]["node_id"] = "I_otherParent30"
        parsed = github.parse_issue_fixture(authority, wrong_parent)
        self.assertEqual("I_otherParent30", parsed.parent_node_id)

        bound_parent = canonical_issue_fixture()
        bound_parent["issue"]["parent"] = {
            "number": 11,
            "id": 101,
            "node_id": "I_wrongIssue01",
        }
        with self.assertRaisesRegex(github.GitHubWorkflowError, "parent legacy"):
            github.parse_issue_fixture(authority, bound_parent)

    def test_closed_issue_reason_distinguishes_completion_from_cancellation(self) -> None:
        cancelled = issue_fixture(
            "QPBT-001", state="closed", status_label=None, dependency_ids=()
        )
        cancelled["issue"]["state_reason"] = "not_planned"
        snapshot = github.parse_issue_fixture(self.authority(), cancelled)
        self.assertEqual(("NOT_PLANNED", "not-planned"), (snapshot.state_reason, snapshot.status))

    def test_closed_tracking_issue_requires_completed_native_children(self) -> None:
        tracker = issue_fixture(
            "QPBT-001", state="closed", status_label=None, dependency_ids=()
        )
        tracker["issue"]["labels"] = label_names(
            github.MIGRATION_LABEL, "kind:tracking"
        )
        with self.assertRaisesRegex(github.GitHubWorkflowError, "no native children"):
            github.parse_issue_fixture(self.authority(), tracker)

        child = {
            "number": 12,
            "id": 102,
            "node_id": "I_issueNode02",
            "state": "closed",
            "state_reason": "completed",
        }
        tracker["issue"]["subIssues"] = [child]
        snapshot = github.parse_issue_fixture(self.authority(), tracker)
        self.assertEqual((12,), snapshot.child_numbers)
        self.assertEqual(("QPBT-002",), snapshot.child_legacy_ids)

        child["state"] = "open"
        child["state_reason"] = None
        with self.assertRaisesRegex(github.GitHubWorkflowError, "incomplete native child"):
            github.parse_issue_fixture(self.authority(), tracker)

    def test_each_open_issue_status_label_is_accepted_exactly(self) -> None:
        authority = self.authority()
        for label in sorted(github.ISSUE_STATUSES):
            with self.subTest(label=label):
                snapshot = github.parse_issue_fixture(
                    authority,
                    issue_fixture(
                        "QPBT-001",
                        status_label=label,
                        dependency_ids=(),
                    ),
                )
                self.assertEqual(label.removeprefix("status:"), snapshot.status)

    def test_issue_repository_and_legacy_identity_mismatches_are_rejected(self) -> None:
        mutations = (
            lambda value: value["repository"].__setitem__("full_name", "Dengnifer/Other"),
            lambda value: value["repository"].__setitem__("id", 999),
            lambda value: value["repository"].__setitem__("node_id", "R_wrongNode01"),
            lambda value: value["repository"].__setitem__("base_ref", "dev"),
            lambda value: value["issue"].__setitem__("number", 11),
            lambda value: value["issue"].__setitem__("id", 999),
            lambda value: value["issue"].__setitem__("node_id", "I_wrongNode02"),
        )
        authority = self.authority()
        for mutate in mutations:
            value = issue_fixture()
            mutate(value)
            with self.assertRaises(github.GitHubWorkflowError):
                github.parse_issue_fixture(authority, value)

    def test_issue_labels_markers_and_dependencies_are_fail_closed(self) -> None:
        cases: list[dict[str, object]] = []

        missing_migration = issue_fixture()
        missing_migration["issue"]["labels"] = label_names(
            "kind:implementation", "status:ready"
        )
        cases.append(missing_migration)

        duplicate_status = issue_fixture()
        duplicate_status["issue"]["labels"].append({"name": "status:blocked"})
        cases.append(duplicate_status)

        closed_active = issue_fixture(state="closed")
        cases.append(closed_active)

        malformed_marker = issue_fixture()
        malformed_marker["issue"]["body"] = malformed_marker["issue"]["body"].replace(
            "mipstarre-workflow:v1", "mipstarre-workflow:v2"
        )
        cases.append(malformed_marker)

        parallel_dependency_marker = issue_fixture()
        parallel_dependency_marker["issue"]["body"] += (
            "<!-- mipstarre-workflow:v1:depends-on:QPBT-001 -->\n"
        )
        cases.append(parallel_dependency_marker)

        wrong_dependency_node = issue_fixture()
        wrong_dependency_node["issue"]["blockedBy"][0]["id"] = "I_wrongNode01"
        cases.append(wrong_dependency_node)

        for index, value in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(
                github.GitHubWorkflowError
            ):
                github.parse_issue_fixture(self.authority(), value)

    def test_pull_request_fixture_parses_review_and_immutable_refs(self) -> None:
        snapshot = github.parse_pull_request_fixture(
            self.authority(), pull_request_fixture()
        )
        self.assertEqual("LPR-001", snapshot.legacy_id)
        self.assertEqual("required", snapshot.review_label)
        self.assertEqual(("main", BASE_SHA), (snapshot.base_ref, snapshot.base_sha))
        self.assertEqual(
            ("issue/qpbt-001", HEAD_SHA), (snapshot.head_ref, snapshot.head_sha)
        )

        merged = pull_request_fixture(state="closed", merged_at="2026-09-02T00:00:00Z")
        self.assertEqual(
            "MERGED", github.parse_pull_request_fixture(self.authority(), merged).state
        )

    def test_post_cutover_pr_requires_exact_caller_base_and_head(self) -> None:
        authority = self.authority()
        fixture, expectation = canonical_pull_request_fixture()
        snapshot = github.parse_pull_request_fixture(
            authority, fixture, expected=expectation
        )
        self.assertIsNone(snapshot.legacy_id)
        self.assertEqual(32, snapshot.number)
        self.assertEqual(expectation.head_sha, snapshot.head_sha)

        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "requires exact base/head"
        ):
            github.parse_pull_request_fixture(authority, fixture)

        stale = copy.copy(expectation)
        stale = github.PullRequestExpectation(
            stale.number, stale.base_ref, stale.base_sha, stale.head_ref, "e" * 40
        )
        with self.assertRaisesRegex(github.GitHubWorkflowError, "base/head mismatch"):
            github.parse_pull_request_fixture(authority, fixture, expected=stale)

        fake_migration = copy.deepcopy(fixture)
        fake_migration["pull_request"]["labels"].append(
            {"name": github.MIGRATION_LABEL}
        )
        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "migration provenance"
        ):
            github.parse_pull_request_fixture(
                authority, fake_migration, expected=expectation
            )

    def test_exact_review_comment_binds_identity_body_and_base_head(self) -> None:
        fixture, expectation = canonical_pull_request_fixture()
        fixture["pull_request"]["labels"] = label_names("review:approved")
        bound, comment, _body = review_comment_contract(expectation)
        responses = repository_preflight_responses()
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/pulls/32")
        ] = fixture["pull_request"]
        responses[
            github._api_command(
                f"repos/{github.EXPECTED_FULL_NAME}/issues/comments/401"
            )
        ] = comment
        snapshot = github.live_preflight(
            self.config_path,
            runner=FakeRunner(responses),
            issue_numbers=[],
            pull_request_expectations=[bound],
        )
        review = snapshot.pull_requests[0].review_comment
        self.assertIsNotNone(review)
        self.assertEqual("approve", review.verdict)
        self.assertEqual(
            bound.review_comment.reviewer_session_name,
            review.reviewer_session_name,
        )

    def test_review_label_alone_never_proves_identity_or_approval(self) -> None:
        runner = FakeRunner(self.live_responses())
        snapshot = github.live_preflight(self.config_path, runner=runner)
        pull_request = snapshot.pull_requests[0]
        self.assertEqual("required", pull_request.review_label)
        self.assertIsNone(pull_request.review_comment)

    def test_review_comment_rejects_digest_identity_binding_and_role_conflicts(self) -> None:
        fixture, expectation = canonical_pull_request_fixture()
        fixture["pull_request"]["labels"] = label_names("review:approved")
        bound, comment, body = review_comment_contract(expectation)

        def run(candidate: github.PullRequestExpectation, payload: dict[str, object]) -> None:
            responses = repository_preflight_responses()
            responses[
                github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/pulls/32")
            ] = fixture["pull_request"]
            responses[
                github._api_command(
                    f"repos/{github.EXPECTED_FULL_NAME}/issues/comments/401"
                )
            ] = payload
            github.live_preflight(
                self.config_path,
                runner=FakeRunner(responses),
                issue_numbers=[],
                pull_request_expectations=[candidate],
            )

        wrong_digest = copy.deepcopy(comment)
        wrong_digest["body"] = body + " "
        with self.assertRaisesRegex(github.GitHubWorkflowError, "digest mismatch"):
            run(bound, wrong_digest)

        wrong_identity = copy.deepcopy(comment)
        report = json.loads(body)
        report["review_identity"]["session_name"] = "i032-reviewer-a99-other"
        wrong_body = json.dumps(
            report, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        wrong_identity["body"] = wrong_body
        exact_wrong_digest = replace(
            bound.review_comment,
            body_sha256=hashlib.sha256(wrong_body.encode("utf-8")).hexdigest(),
        )
        with self.assertRaisesRegex(github.GitHubWorkflowError, "session identity"):
            run(replace(bound, review_comment=exact_wrong_digest), wrong_identity)

        wrong_pr = copy.deepcopy(comment)
        wrong_pr["issue_url"] = wrong_pr["issue_url"].replace("/32", "/31")
        with self.assertRaisesRegex(github.GitHubWorkflowError, "PR binding"):
            run(bound, wrong_pr)

        disallowed = replace(
            bound.review_comment,
            disallowed_session_names=(bound.review_comment.reviewer_session_name,),
        )
        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "implementer or orchestrator"
        ):
            run(replace(bound, review_comment=disallowed), comment)

        missing_role_evidence = replace(
            bound.review_comment,
            disallowed_session_names=(),
            disallowed_external_ids=(),
        )
        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "exclusion identities"
        ):
            run(replace(bound, review_comment=missing_role_evidence), comment)

    def test_pull_request_rejects_every_base_head_or_repository_mismatch(self) -> None:
        mutations = (
            lambda value: value["pull_request"]["base"].__setitem__("ref", "dev"),
            lambda value: value["pull_request"]["base"].__setitem__("sha", "d" * 40),
            lambda value: value["pull_request"]["head"].__setitem__("ref", "other"),
            lambda value: value["pull_request"]["head"].__setitem__("sha", "e" * 40),
            lambda value: value["pull_request"]["base"]["repo"].__setitem__("id", 999),
            lambda value: value["pull_request"]["head"].pop("repo"),
            lambda value: value["pull_request"].__setitem__("node_id", "PR_wrongNode01"),
        )
        authority = self.authority()
        for mutate in mutations:
            value = pull_request_fixture()
            mutate(value)
            with self.assertRaises(github.GitHubWorkflowError):
                github.parse_pull_request_fixture(authority, value)

    def test_pull_request_review_label_and_state_are_strict(self) -> None:
        no_review = pull_request_fixture()
        no_review["pull_request"]["labels"] = label_names(github.MIGRATION_LABEL)
        open_merged = pull_request_fixture(merged_at="2026-09-02T00:00:00Z")
        issue_status = pull_request_fixture()
        issue_status["pull_request"]["labels"].append({"name": "status:review"})
        malformed_merge = pull_request_fixture(state="closed", merged_at="not-a-time")
        for value in (no_review, open_merged, issue_status, malformed_merge):
            with self.assertRaises(github.GitHubWorkflowError):
                github.parse_pull_request_fixture(self.authority(), value)

    def live_responses(self) -> dict[tuple[str, ...], object]:
        responses = repository_preflight_responses()
        for legacy_id in ("QPBT-001", "QPBT-002"):
            dependencies = () if legacy_id == "QPBT-001" else ("QPBT-001",)
            envelope = issue_fixture(
                legacy_id,
                state="closed" if legacy_id == "QPBT-001" else "open",
                status_label=None if legacy_id == "QPBT-001" else "status:ready",
                dependency_ids=dependencies,
            )
            rest = copy.deepcopy(envelope["issue"])
            blocked_by = rest.pop("blockedBy")
            number = rest["number"]
            responses[
                github._api_command(
                    f"repos/{github.EXPECTED_FULL_NAME}/issues/{number}"
                )
            ] = rest
            responses[
                (
                    "gh",
                    "issue",
                    "view",
                    str(number),
                    "--repo",
                    github.EXPECTED_FULL_NAME,
                    "--json",
                    "blockedBy,body,id,labels,number,parent,state,stateReason,subIssues,title",
                )
            ] = {
                "blockedBy": {
                    "nodes": blocked_by,
                    "totalCount": len(blocked_by),
                },
                "body": rest["body"],
                "id": rest["node_id"],
                "labels": rest["labels"],
                "number": number,
                "parent": rest["parent"],
                "subIssues": {
                    "nodes": rest["subIssues"],
                    "totalCount": len(rest["subIssues"]),
                },
                "state": rest["state"],
                "stateReason": rest["state_reason"],
                "title": rest["title"],
            }
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/pulls/21")
        ] = pull_request_fixture()["pull_request"]
        return responses

    def test_live_preflight_is_injected_read_only_and_explicitly_scoped(self) -> None:
        runner = FakeRunner(self.live_responses())
        snapshot = github.live_preflight(self.config_path, runner=runner)
        self.assertEqual(BASE_SHA, snapshot.repository.base_sha)
        self.assertEqual(2, len(snapshot.issues))
        self.assertEqual(1, len(snapshot.pull_requests))
        self.assertEqual((), snapshot.issues[0].dependency_numbers)
        self.assertEqual((11,), snapshot.issues[1].dependency_numbers)
        self.assertEqual(10, len(runner.calls))

        forbidden = {"POST", "PATCH", "PUT", "DELETE", "create", "edit", "close", "merge"}
        for command in runner.calls:
            self.assertEqual("gh", command[0])
            self.assertTrue(forbidden.isdisjoint(command))
            if command[1] == "api":
                self.assertIn("--hostname", command)
                self.assertIn(github.EXPECTED_HOST, command)
                self.assertEqual("GET", command[command.index("--method") + 1])
                self.assertIn(github.EXPECTED_FULL_NAME, command[-1])
            else:
                self.assertEqual(("issue", "view"), command[1:3])
                self.assertEqual(
                    github.EXPECTED_FULL_NAME, command[command.index("--repo") + 1]
                )

    def test_live_preflight_normalizes_nonempty_sub_issues_connection(self) -> None:
        responses = self.live_responses()
        issue_view = next(
            command
            for command in responses
            if command[:4] == ("gh", "issue", "view", "11")
        )
        responses[issue_view]["subIssues"] = {
            "nodes": [
                {
                    "number": 31,
                    "id": "I_canonicalIssue31",
                }
            ],
            "totalCount": 1,
        }
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/issues/31")
        ] = {
            "number": 31,
            "id": 301,
            "node_id": "I_canonicalIssue31",
            "state": "closed",
            "state_reason": "completed",
        }
        snapshot = github.live_preflight(
            self.config_path, runner=FakeRunner(responses)
        )
        self.assertEqual((31,), snapshot.issues[0].child_numbers)

    def test_live_preflight_rejects_malformed_issue_connections(self) -> None:
        def issue_view(
            responses: dict[tuple[str, ...], object], number: str = "11"
        ) -> dict[str, object]:
            command = next(
                command
                for command in responses
                if command[:4] == ("gh", "issue", "view", number)
            )
            return responses[command]

        mutations = (
            lambda connection: connection.__setitem__("totalCount", 1),
            lambda connection: connection.__setitem__("totalCount", -1),
            lambda connection: connection.__setitem__("totalCount", True),
            lambda connection: connection.__setitem__("nodes", {}),
            lambda connection: connection.pop("totalCount"),
            lambda connection: connection.__setitem__("pageInfo", {}),
        )
        for field in ("blockedBy", "subIssues"):
            for index, mutate in enumerate(mutations):
                responses = self.live_responses()
                connection = issue_view(responses)[field]
                mutate(connection)
                with self.subTest(field=field, index=index), self.assertRaises(
                    github.GitHubWorkflowError
                ):
                    github.live_preflight(
                        self.config_path, runner=FakeRunner(responses)
                    )

            bare_array = self.live_responses()
            issue_view(bare_array)[field] = []
            with self.subTest(field=field), self.assertRaisesRegex(
                github.GitHubWorkflowError, "must be an object"
            ):
                github.live_preflight(
                    self.config_path, runner=FakeRunner(bare_array)
                )

    def test_repository_only_preflight_never_reads_items(self) -> None:
        responses = self.live_responses()
        repository_endpoint = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}"
        )
        responses[repository_endpoint]["default_branch"] = "from-monorepo"
        runner = FakeRunner(responses)
        snapshot = github.live_preflight(
            self.config_path, runner=runner, repository_only=True
        )
        self.assertEqual(4, len(runner.calls))
        self.assertEqual((), snapshot.issues)
        self.assertEqual((), snapshot.pull_requests)
        self.assertEqual("main", snapshot.repository.base_ref)
        self.assertEqual("from-monorepo", snapshot.repository.default_branch)

    def test_live_preflight_proves_cutover_commit_ancestry(self) -> None:
        identical = repository_preflight_responses()
        main = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/commits/main"
        )
        old_comparison = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/compare/{CUTOVER_SHA}...{BASE_SHA}"
        )
        identical[main] = {"sha": CUTOVER_SHA}
        identical.pop(old_comparison)
        identical[
            github._api_command(
                f"repos/{github.EXPECTED_FULL_NAME}/compare/"
                f"{CUTOVER_SHA}...{CUTOVER_SHA}"
            )
        ] = {
            "status": "identical",
            "base_commit": {"sha": CUTOVER_SHA},
            "merge_base_commit": {"sha": CUTOVER_SHA},
        }
        snapshot = github.live_preflight(
            self.config_path,
            runner=FakeRunner(identical),
            repository_only=True,
        )
        self.assertEqual(CUTOVER_SHA, snapshot.repository.base_sha)

        divergent = repository_preflight_responses()
        comparison = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/compare/{CUTOVER_SHA}...{BASE_SHA}"
        )
        divergent[comparison]["status"] = "diverged"
        with self.assertRaisesRegex(github.GitHubWorkflowError, "not an ancestor"):
            github.live_preflight(
                self.config_path,
                runner=FakeRunner(divergent),
                repository_only=True,
            )

        wrong_commit = repository_preflight_responses()
        cutover = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/commits/{CUTOVER_SHA}"
        )
        wrong_commit[cutover]["sha"] = "e" * 40
        with self.assertRaisesRegex(github.GitHubWorkflowError, "commit SHA mismatch"):
            github.live_preflight(
                self.config_path,
                runner=FakeRunner(wrong_commit),
                repository_only=True,
            )

    def test_live_preflight_supports_selected_post_cutover_objects(self) -> None:
        responses = repository_preflight_responses()
        issue = canonical_issue_fixture()["issue"]
        issue_rest = copy.deepcopy(issue)
        blocked_by = issue_rest.pop("blockedBy")
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/issues/31")
        ] = issue_rest
        responses[
            github._api_command(
                f"repos/{github.EXPECTED_FULL_NAME}/issues/31/parent"
            )
        ] = {
            "number": 30,
            "id": 300,
            "node_id": "I_canonicalIssue30",
        }
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/issues/11")
        ] = {"number": 11, "id": 101, "node_id": "I_issueNode01"}
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/issues/30")
        ] = {"number": 30, "id": 300, "node_id": "I_canonicalIssue30"}
        responses[
            (
                "gh",
                "issue",
                "view",
                "31",
                "--repo",
                github.EXPECTED_FULL_NAME,
                "--json",
                "blockedBy,body,id,labels,number,parent,state,stateReason,subIssues,title",
            )
        ] = {
            "blockedBy": {
                "nodes": blocked_by,
                "totalCount": len(blocked_by),
            },
            "body": issue_rest["body"],
            "id": issue_rest["node_id"],
            "labels": issue_rest["labels"],
            "number": 31,
            "parent": {"number": 30, "id": "I_canonicalIssue30"},
            "subIssues": {"nodes": [], "totalCount": 0},
            "state": issue_rest["state"],
            "stateReason": issue_rest["state_reason"],
            "title": issue_rest["title"],
        }
        pr_fixture, expectation = canonical_pull_request_fixture()
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/pulls/32")
        ] = pr_fixture["pull_request"]
        runner = FakeRunner(responses)
        snapshot = github.live_preflight(
            self.config_path,
            runner=runner,
            expected_base_sha=BASE_SHA,
            issue_numbers=[31],
            pull_request_expectations=[expectation],
        )
        self.assertEqual([31], [item.number for item in snapshot.issues])
        self.assertEqual([32], [item.number for item in snapshot.pull_requests])
        self.assertEqual(10, len(runner.calls))

    def test_live_preflight_rejects_ready_issue_with_incomplete_dependency(self) -> None:
        responses = self.live_responses()
        issue_endpoint = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/issues/11"
        )
        issue_view = next(
            command
            for command in responses
            if command[:4] == ("gh", "issue", "view", "11")
        )
        responses[issue_endpoint]["state"] = "open"
        responses[issue_endpoint]["state_reason"] = None
        responses[issue_endpoint]["labels"] = label_names(
            github.MIGRATION_LABEL, "kind:implementation", "status:ready"
        )
        responses[issue_view]["state"] = "open"
        responses[issue_view]["stateReason"] = None
        responses[issue_view]["labels"] = copy.deepcopy(
            responses[issue_endpoint]["labels"]
        )
        with self.assertRaisesRegex(
            github.GitHubWorkflowError, "incomplete dependency"
        ):
            github.live_preflight(self.config_path, runner=FakeRunner(responses))

    def test_live_preflight_distinguishes_missing_parent_from_null_parent(self) -> None:
        responses = self.live_responses()
        issue_view = next(
            command
            for command in responses
            if command[:4] == ("gh", "issue", "view", "11")
        )
        responses[issue_view].pop("parent")
        with self.assertRaisesRegex(github.GitHubWorkflowError, "omitted parent"):
            github.live_preflight(self.config_path, runner=FakeRunner(responses))

        responses = self.live_responses()
        responses[issue_view].pop("subIssues")
        with self.assertRaisesRegex(github.GitHubWorkflowError, "omitted subIssues"):
            github.live_preflight(self.config_path, runner=FakeRunner(responses))

    def test_live_preflight_normalizes_only_open_cli_empty_state_reason(self) -> None:
        responses = self.live_responses()
        open_view = next(
            command
            for command in responses
            if command[:4] == ("gh", "issue", "view", "12")
        )
        responses[open_view]["stateReason"] = ""
        snapshot = github.live_preflight(
            self.config_path, runner=FakeRunner(responses)
        )
        self.assertIsNone(
            next(item for item in snapshot.issues if item.number == 12).state_reason
        )

        responses = self.live_responses()
        closed_view = next(
            command
            for command in responses
            if command[:4] == ("gh", "issue", "view", "11")
        )
        responses[closed_view]["stateReason"] = ""
        with self.assertRaisesRegex(github.GitHubWorkflowError, "non-empty string"):
            github.live_preflight(self.config_path, runner=FakeRunner(responses))

    def test_runner_failures_and_malformed_output_do_not_echo_credentials(self) -> None:
        secret = "ghp_DO_NOT_EXPOSE_THIS_TOKEN"
        first = github._api_command(f"repos/{github.EXPECTED_FULL_NAME}")
        for response in (
            subprocess.CompletedProcess(first, 1, stdout=secret, stderr=secret),
            subprocess.CompletedProcess(first, 0, stdout="{" + secret, stderr=""),
        ):
            runner = FakeRunner({first: response})
            with self.assertRaises(github.GitHubWorkflowError) as captured:
                github.live_preflight(self.config_path, runner=runner)
            self.assertNotIn(secret, str(captured.exception))

        class RaisingRunner:
            def __call__(self, _command: object) -> object:
                raise RuntimeError(secret)

        with self.assertRaises(github.GitHubWorkflowError) as captured:
            github.live_preflight(self.config_path, runner=RaisingRunner())
        rendered = "".join(
            traceback.format_exception(
                type(captured.exception), captured.exception, captured.exception.__traceback__
            )
        )
        self.assertNotIn(secret, rendered)
        self.assertIsNone(captured.exception.__cause__)

    def test_cli_integration_review_file_binds_and_live_validates_comment(self) -> None:
        fixture, expectation = canonical_pull_request_fixture()
        fixture["pull_request"]["labels"] = label_names("review:approved")
        bound, comment, _body = review_comment_contract(expectation)
        integration_path = self.root / "integration-reviews.json"
        integration_path.write_text(
            json.dumps(integration_review_document(bound), indent=2) + "\n",
            encoding="utf-8",
        )
        responses = self.live_responses()
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/pulls/32")
        ] = fixture["pull_request"]
        comment_command = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/issues/comments/401"
        )
        responses[comment_command] = comment
        runner = FakeRunner(responses)
        expectation_argument = ":".join(
            (
                str(expectation.number),
                expectation.base_ref,
                expectation.base_sha,
                expectation.head_ref,
                expectation.head_sha,
            )
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(github, "_default_runner", runner), redirect_stdout(
            stdout
        ), redirect_stderr(stderr):
            result = github.main(
                [
                    "--config",
                    str(self.config_path),
                    "preflight",
                    "--pull-request-expectation",
                    expectation_argument,
                    "--integration-review-expectations-file",
                    str(integration_path),
                ]
            )
        self.assertEqual(0, result)
        self.assertEqual("", stderr.getvalue())
        summary = json.loads(stdout.getvalue())
        review = summary["pull_requests"][0]["review_comment"]
        self.assertEqual(401, review["comment_database_id"])
        self.assertEqual(
            bound.review_comment.reviewer_session_name,
            review["reviewer_session_name"],
        )
        self.assertEqual(
            bound.review_comment.reviewer_external_id,
            review["reviewer_external_id"],
        )
        self.assertIn(comment_command, runner.calls)

    def test_cli_integration_review_file_rejects_invalid_authority_before_live_reads(
        self,
    ) -> None:
        _fixture, expectation = canonical_pull_request_fixture()
        bound, _comment, _body = review_comment_contract(expectation)
        valid = integration_review_document(bound)
        expectation_argument = ":".join(
            (
                str(expectation.number),
                expectation.base_ref,
                expectation.base_sha,
                expectation.head_ref,
                expectation.head_sha,
            )
        )

        wrong_schema = copy.deepcopy(valid)
        wrong_schema["schema_version"] = True
        wrong_number_type = copy.deepcopy(valid)
        wrong_number_type["pull_requests"][0]["number"] = "32"
        wrong_database_id_type = copy.deepcopy(valid)
        wrong_database_id_type["pull_requests"][0]["review_comment"][
            "comment_database_id"
        ] = True
        wrong_digest = copy.deepcopy(valid)
        wrong_digest["pull_requests"][0]["review_comment"]["body_sha256"] = "f" * 63
        wrong_verdict = copy.deepcopy(valid)
        wrong_verdict["pull_requests"][0]["review_comment"]["verdict"] = "approved"
        wrong_exclusion_type = copy.deepcopy(valid)
        wrong_exclusion_type["pull_requests"][0]["review_comment"][
            "disallowed_session_names"
        ] = "not-an-array"
        missing_session_exclusions = copy.deepcopy(valid)
        missing_session_exclusions["pull_requests"][0]["review_comment"][
            "disallowed_session_names"
        ] = []
        missing_external_exclusions = copy.deepcopy(valid)
        missing_external_exclusions["pull_requests"][0]["review_comment"][
            "disallowed_external_ids"
        ] = []
        overlapping_reviewer = copy.deepcopy(valid)
        review = overlapping_reviewer["pull_requests"][0]["review_comment"]
        review["disallowed_external_ids"] = [review["reviewer_external_id"]]
        duplicate_pr = copy.deepcopy(valid)
        duplicate_pr["pull_requests"].append(
            copy.deepcopy(duplicate_pr["pull_requests"][0])
        )
        unexpected_field = copy.deepcopy(valid)
        unexpected_field["pull_requests"][0]["mutable"] = True
        cases = (
            ("schema", wrong_schema, "schema mismatch"),
            ("number-type", wrong_number_type, "positive integer"),
            ("database-id-type", wrong_database_id_type, "positive integer"),
            ("digest", wrong_digest, "SHA-256 digest"),
            ("verdict", wrong_verdict, "verdict is not recognized"),
            ("exclusion-type", wrong_exclusion_type, "must be an array"),
            (
                "missing-session-exclusions",
                missing_session_exclusions,
                "exclusion identities",
            ),
            (
                "missing-external-exclusions",
                missing_external_exclusions,
                "exclusion identities",
            ),
            (
                "reviewer-overlap",
                overlapping_reviewer,
                "implementer or orchestrator",
            ),
            ("duplicate-pr", duplicate_pr, "duplicate integration review"),
            ("unexpected-field", unexpected_field, "unexpected field set"),
        )
        for name, document, expected_error in cases:
            with self.subTest(name=name):
                integration_path = self.root / f"integration-{name}.json"
                integration_path.write_text(
                    json.dumps(document) + "\n", encoding="utf-8"
                )
                runner = FakeRunner({})
                stdout = io.StringIO()
                stderr = io.StringIO()
                with mock.patch.object(
                    github, "_default_runner", runner
                ), redirect_stdout(stdout), redirect_stderr(stderr):
                    result = github.main(
                        [
                            "--config",
                            str(self.config_path),
                            "preflight",
                            "--pull-request-expectation",
                            expectation_argument,
                            "--integration-review-expectations-file",
                            str(integration_path),
                        ]
                    )
                self.assertEqual(2, result)
                self.assertEqual("", stdout.getvalue())
                self.assertIn(expected_error, stderr.getvalue())
                self.assertEqual([], runner.calls)

    def test_cli_integration_review_file_requires_one_to_one_pr_mapping(self) -> None:
        _fixture, expectation = canonical_pull_request_fixture()
        bound, _comment, _body = review_comment_contract(expectation)
        integration_path = self.root / "integration-mapping.json"
        integration_path.write_text(
            json.dumps(integration_review_document(bound)) + "\n",
            encoding="utf-8",
        )
        exact_argument = ":".join(
            (
                str(expectation.number),
                expectation.base_ref,
                expectation.base_sha,
                expectation.head_ref,
                expectation.head_sha,
            )
        )
        mismatched_argument = exact_argument.replace("32:", "21:", 1)
        cases = (
            ("missing", [], "require pull-request expectations"),
            (
                "mismatched",
                ["--pull-request-expectation", mismatched_argument],
                "do not exactly match",
            ),
            (
                "ambiguous",
                [
                    "--pull-request-expectation",
                    exact_argument,
                    "--pull-request-expectation",
                    exact_argument,
                ],
                "mapping is ambiguous",
            ),
        )
        for name, expectation_arguments, expected_error in cases:
            with self.subTest(name=name):
                runner = FakeRunner({})
                stdout = io.StringIO()
                stderr = io.StringIO()
                with mock.patch.object(
                    github, "_default_runner", runner
                ), redirect_stdout(stdout), redirect_stderr(stderr):
                    result = github.main(
                        [
                            "--config",
                            str(self.config_path),
                            "preflight",
                            *expectation_arguments,
                            "--integration-review-expectations-file",
                            str(integration_path),
                        ]
                    )
                self.assertEqual(2, result)
                self.assertEqual("", stdout.getvalue())
                self.assertIn(expected_error, stderr.getvalue())
                self.assertEqual([], runner.calls)

    def test_cli_integration_review_file_rejects_live_comment_digest_mismatch(
        self,
    ) -> None:
        fixture, expectation = canonical_pull_request_fixture()
        fixture["pull_request"]["labels"] = label_names("review:approved")
        bound, comment, _body = review_comment_contract(expectation)
        integration_path = self.root / "integration-live-mismatch.json"
        integration_path.write_text(
            json.dumps(integration_review_document(bound)) + "\n",
            encoding="utf-8",
        )
        comment["body"] = str(comment["body"]) + " "
        responses = self.live_responses()
        responses[
            github._api_command(f"repos/{github.EXPECTED_FULL_NAME}/pulls/32")
        ] = fixture["pull_request"]
        comment_command = github._api_command(
            f"repos/{github.EXPECTED_FULL_NAME}/issues/comments/401"
        )
        responses[comment_command] = comment
        runner = FakeRunner(responses)
        expectation_argument = ":".join(
            (
                str(expectation.number),
                expectation.base_ref,
                expectation.base_sha,
                expectation.head_ref,
                expectation.head_sha,
            )
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(github, "_default_runner", runner), redirect_stdout(
            stdout
        ), redirect_stderr(stderr):
            result = github.main(
                [
                    "--config",
                    str(self.config_path),
                    "preflight",
                    "--pull-request-expectation",
                    expectation_argument,
                    "--integration-review-expectations-file",
                    str(integration_path),
                ]
            )
        self.assertEqual(2, result)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("body digest mismatch", stderr.getvalue())
        self.assertIn(comment_command, runner.calls)

    def test_cli_offline_validation_outputs_only_nonsecret_authority_summary(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = github.main(["--config", str(self.config_path), "validate"])
        self.assertEqual(0, result)
        self.assertEqual("", stderr.getvalue())
        summary = json.loads(stdout.getvalue())
        self.assertEqual(github.EXPECTED_FULL_NAME, summary["repository"])
        self.assertEqual("valid", summary["status"])
        self.assertNotIn("node_id", summary)
        self.assertNotIn("database_id", summary)


if __name__ == "__main__":
    unittest.main()
