
"""Tests for controlled AgentOps handoffs."""

import unittest

from scripts.state_check import validate_handoff


class HandoffTests(unittest.TestCase):

    def test_approved_plan_to_implementation(self):
        self.assertEqual(
            validate_handoff("plan", "implement", True),
            [],
        )

    def test_unapproved_implementation_is_blocked(self):
        errors = validate_handoff(
            "plan", "implement", False
        )
        self.assertTrue(
            any("Human approval required" in e for e in errors)
        )

    def test_implementation_to_validation(self):
        self.assertEqual(
            validate_handoff("implement", "validate", True),
            [],
        )

    def test_validation_to_security_review(self):
        self.assertEqual(
            validate_handoff("validate", "security_review", True),
            [],
        )

    def test_security_review_to_human_review(self):
        self.assertEqual(
            validate_handoff("security_review", "human_review", True),
            [],
        )

    def test_human_review_to_completion(self):
        self.assertEqual(
            validate_handoff("human_review", "complete", True),
            [],
        )

    def test_skip_validation_is_rejected(self):
        errors = validate_handoff(
            "implement", "security_review", True
        )
        self.assertTrue(
            any("Forbidden handoff" in e for e in errors)
        )

    def test_direct_completion_is_rejected(self):
        errors = validate_handoff(
            "implement", "complete", True
        )
        self.assertTrue(
            any("Forbidden handoff" in e for e in errors)
        )

    def test_completed_task_is_terminal(self):
        errors = validate_handoff(
            "complete", "implement", True
        )
        self.assertTrue(
            any("Forbidden handoff" in e for e in errors)
        )

    def test_validator_can_return_to_implementation(self):
        self.assertEqual(
            validate_handoff("validate", "implement", True),
            [],
        )

    def test_unknown_phase_is_rejected(self):
        errors = validate_handoff(
            "unknown", "implement", True
        )
        self.assertTrue(
            any("Unknown current phase" in e for e in errors)
        )


if __name__ == "__main__":
    unittest.main()
