
"""Tests for AgentOps task-state validation."""

import copy
import unittest
from datetime import datetime, timedelta, timezone

from scripts.state_check import validate_state


class TaskStateTests(unittest.TestCase):

    def setUp(self):
        self.now = datetime(
            2026, 11, 20, 12, 0,
            tzinfo=timezone.utc,
        )

        self.sha = "a" * 40

        self.valid_state = {
            "issue": 1,
            "task_id": "FF-001",
            "goal": "Validate shipment transitions",
            "current_phase": "plan",
            "owner_role": "planner",
            "commit_sha": self.sha,
            "approved_paths": [
                "fulfillflow/core.py",
                "tests/test_core.py",
            ],
            "risk_level": "MEDIUM",
            "last_updated_utc": (
                self.now - timedelta(hours=1)
            ).isoformat(),
            "expires_at_utc": (
                self.now + timedelta(hours=24)
            ).isoformat(),
            "human_approval": False,
        }

    def check(self, state):
        return validate_state(
            state,
            self.sha,
            now=self.now,
        )

    def test_valid_planning_state(self):
        self.assertEqual(
            self.check(self.valid_state),
            [],
        )

    def test_stale_commit_is_rejected(self):
        state = copy.deepcopy(self.valid_state)
        state["commit_sha"] = "b" * 40

        errors = self.check(state)

        self.assertTrue(
            any("STALE STATE" in e for e in errors)
        )

    def test_expired_state_is_rejected(self):
        state = copy.deepcopy(self.valid_state)
        state["expires_at_utc"] = (
            self.now - timedelta(minutes=1)
        ).isoformat()

        errors = self.check(state)

        self.assertTrue(
            any("expired" in e.lower() for e in errors)
        )

    def test_wrong_phase_owner_is_rejected(self):
        state = copy.deepcopy(self.valid_state)
        state["owner_role"] = "implementer"

        errors = self.check(state)

        self.assertTrue(
            any("Invalid owner" in e for e in errors)
        )

    def test_implementation_requires_approval(self):
        state = copy.deepcopy(self.valid_state)
        state["current_phase"] = "implement"
        state["owner_role"] = "implementer"

        errors = self.check(state)

        self.assertTrue(
            any("Human approval required" in e
                for e in errors)
        )

    def test_approved_implementation_state(self):
        state = copy.deepcopy(self.valid_state)
        state["current_phase"] = "implement"
        state["owner_role"] = "implementer"
        state["human_approval"] = True

        self.assertEqual(self.check(state), [])

    def test_unknown_phase_is_rejected(self):
        state = copy.deepcopy(self.valid_state)
        state["current_phase"] = "deploy"

        errors = self.check(state)

        self.assertTrue(
            any("Unknown phase" in e for e in errors)
        )

    def test_naive_timestamp_is_rejected(self):
        state = copy.deepcopy(self.valid_state)
        state["expires_at_utc"] = (
            "2026-11-22T12:00:00"
        )

        errors = self.check(state)

        self.assertTrue(
            any("timezone" in e.lower() for e in errors)
        )

    def test_missing_required_field_is_rejected(self):
        state = copy.deepcopy(self.valid_state)
        del state["commit_sha"]

        errors = self.check(state)

        self.assertTrue(
            any("Missing required fields" in e
                for e in errors)
        )


if __name__ == "__main__":
    unittest.main()
