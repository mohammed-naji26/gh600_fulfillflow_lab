
"""Regression tests for AgentOps failure recovery."""

import unittest
from datetime import datetime, timezone

from scripts.failure_recovery import evaluate_failure


class FailureRecoveryTests(unittest.TestCase):

    def setUp(self):
        self.timestamp = datetime(
            2026, 11, 20, 12, 0,
            tzinfo=timezone.utc,
        )
        self.sha = "a" * 40

    def evaluate(self, category):
        return evaluate_failure(
            category=category,
            incident_id="INC-001",
            commit_sha=self.sha,
            timestamp=self.timestamp,
        )

    def test_stale_context_requires_refresh(self):
        result = self.evaluate("stale_context")

        self.assertEqual(
            result["action"],
            "REFRESH_AND_REVALIDATE",
        )
        self.assertFalse(result["automatic_retry"])
        self.assertEqual(result["decision"], "BLOCK")

    def test_permission_failure_requires_escalation(self):
        result = self.evaluate("permission")

        self.assertEqual(
            result["action"],
            "STOP_AND_ESCALATE",
        )
        self.assertTrue(result["requires_human_review"])
        self.assertFalse(result["automatic_retry"])

    def test_policy_drift_blocks_execution(self):
        result = self.evaluate("policy_drift")

        self.assertEqual(
            result["action"],
            "BLOCK_AND_REVIEW",
        )
        self.assertEqual(result["decision"], "BLOCK")

    def test_transient_tool_failure_is_conditional(self):
        result = self.evaluate("tool_failure")

        self.assertEqual(
            result["action"],
            "RETRY_WITH_LIMITS",
        )
        self.assertEqual(
            result["decision"],
            "CONDITIONAL",
        )

    def test_reasoning_failure_requires_review(self):
        result = self.evaluate("reasoning")

        self.assertTrue(
            result["requires_human_review"]
        )
        self.assertEqual(
            result["action"],
            "REPLAN_AND_VALIDATE",
        )

    def test_unknown_failure_is_blocked(self):
        result = self.evaluate("unrecognized_failure")

        self.assertEqual(result["decision"], "BLOCK")
        self.assertTrue(result["requires_human_review"])

    def test_missing_incident_id_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_failure(
                "permission",
                "",
                self.sha,
                self.timestamp,
            )

    def test_missing_commit_sha_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_failure(
                "permission",
                "INC-001",
                "",
                self.timestamp,
            )

    def test_report_preserves_commit_reference(self):
        result = self.evaluate("permission")

        self.assertEqual(result["commit_sha"], self.sha)
        self.assertEqual(result["incident_id"], "INC-001")


if __name__ == "__main__":
    unittest.main()
