
"""Regression tests for auditable AgentOps handoffs."""

import copy
import unittest
from datetime import datetime, timedelta, timezone

from scripts.handoff_audit import evaluate_handoff


class HandoffAuditTests(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 20, 12, 0,
            tzinfo=timezone.utc,
        )
        self.sha = "a" * 40

        self.state = {
            "issue": 1,
            "task_id": "FF-001",
            "goal": "Validate shipment transitions",
            "current_phase": "plan",
            "owner_role": "planner",
            "commit_sha": self.sha,
            "approved_paths": ["fulfillflow/core.py"],
            "risk_level": "MEDIUM",
            "last_updated_utc": (
                self.now - timedelta(hours=1)
            ).isoformat(),
            "expires_at_utc": (
                self.now + timedelta(hours=24)
            ).isoformat(),
            "human_approval": True,
        }

    def evaluate(self, state, next_phase):
        return evaluate_handoff(
            state,
            next_phase,
            self.sha,
            now=self.now,
        )

    def test_valid_handoff_is_allowed(self):
        result = self.evaluate(self.state, "implement")

        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(
            result["requested_owner"], "implementer"
        )
        self.assertEqual(result["reasons"], [])

    def test_unapproved_handoff_is_blocked(self):
        state = copy.deepcopy(self.state)
        state["human_approval"] = False

        result = self.evaluate(state, "implement")

        self.assertEqual(result["decision"], "BLOCK")
        self.assertTrue(result["reasons"])

    def test_stale_state_is_blocked(self):
        state = copy.deepcopy(self.state)
        state["commit_sha"] = "b" * 40

        result = self.evaluate(state, "implement")

        self.assertEqual(result["decision"], "BLOCK")
        self.assertTrue(
            any(
                "STALE STATE" in reason
                for reason in result["reasons"]
            )
        )

    def test_forbidden_handoff_is_blocked(self):
        result = self.evaluate(self.state, "complete")

        self.assertEqual(result["decision"], "BLOCK")
        self.assertTrue(
            any(
                "Forbidden handoff" in reason
                for reason in result["reasons"]
            )
        )

    def test_evaluation_does_not_mutate_state(self):
        original = copy.deepcopy(self.state)

        self.evaluate(self.state, "implement")

        self.assertEqual(self.state, original)

    def test_report_contains_commit_reference(self):
        result = self.evaluate(self.state, "implement")

        self.assertEqual(result["commit_sha"], self.sha)
        self.assertEqual(result["task_id"], "FF-001")


if __name__ == "__main__":
    unittest.main()
