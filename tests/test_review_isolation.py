from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import review_isolation  # noqa: E402


class ReviewIsolationTests(unittest.TestCase):
    def test_landlock_child_denies_unmanifested_host_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            projection = root / "projection"
            projection.mkdir()
            (projection / "allowed.txt").write_bytes(b"allowed\n")
            sentinel = root / "host-sentinel"
            sentinel.write_bytes(b"denied\n")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "review_isolation.py"),
                    "--probe-child",
                    str(projection),
                    str(sentinel),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"},
            )
        self.assertEqual(0, completed.returncode, completed.stderr.decode())

    def test_complete_capability_fails_closed_when_tool_egress_is_unavailable(self) -> None:
        capability = review_isolation.probe_production_isolation()
        self.assertTrue(capability["filesystem_enforced"])
        self.assertTrue(capability["sentinel_denied"])
        if capability["available"]:
            self.assertEqual(capability, review_isolation.require_production_isolation(capability))
        else:
            with self.assertRaisesRegex(
                review_isolation.IsolationError, "isolation is unavailable"
            ):
                review_isolation.require_production_isolation(capability)

    def test_capability_schema_and_policy_are_exact(self) -> None:
        capability = review_isolation.probe_production_isolation()
        for field, replacement in (
            ("policy_sha256", "0" * 64),
            ("sentinel_denied", False),
            ("minimal_environment_credential_names_present", True),
        ):
            candidate = {**capability, field: replacement, "available": True}
            with self.subTest(field=field), self.assertRaises(review_isolation.IsolationError):
                review_isolation.require_production_isolation(candidate)
        extra = {**capability, "unexpected": True}
        with self.assertRaisesRegex(review_isolation.IsolationError, "invalid schema"):
            review_isolation.require_production_isolation(extra)

    def test_minimal_environment_has_no_ambient_or_credential_names(self) -> None:
        original = os.environ.copy()
        os.environ["SYNTHETIC_API_KEY"] = "must-not-escape"
        try:
            environment = review_isolation.minimal_reviewer_environment()
        finally:
            os.environ.clear()
            os.environ.update(original)
        self.assertNotIn("SYNTHETIC_API_KEY", environment)
        self.assertFalse(any("TOKEN" in key or "KEY" in key for key in environment))
        self.assertEqual("/nonexistent", environment["HOME"])


if __name__ == "__main__":
    unittest.main()
