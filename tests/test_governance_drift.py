
"""Regression tests for governance drift detection."""

import unittest

from scripts.governance_drift import (
    evaluate_drift,
    parse_git_changes,
)


class GovernanceDriftTests(unittest.TestCase):

    def test_high_risk_workflow_change(self):
        raw = (
            b"M\x00"
            b".github/workflows/ci.yml\x00"
        )
        changes = parse_git_changes(raw)
        report = evaluate_drift(changes, "a" * 40, "b" * 40)

        self.assertTrue(report["drift_detected"])
        self.assertEqual(
            report["decision"], "REVIEW_REQUIRED"
        )

    def test_mcp_configuration_change(self):
        raw = b"M\x00.vscode/mcp.json\x00"
        changes = parse_git_changes(raw)

        self.assertEqual(changes[0]["risk"], "HIGH")

    def test_codeowners_deletion(self):
        raw = b"D\x00.github/CODEOWNERS\x00"
        changes = parse_git_changes(raw)

        self.assertEqual(
            changes[0]["change"], "DELETED"
        )
        self.assertEqual(changes[0]["risk"], "HIGH")

    def test_medium_risk_change_is_clear(self):
        raw = b"M\x00scripts/failure_recovery.py\x00"
        changes = parse_git_changes(raw)
        report = evaluate_drift(changes, "a" * 40, "b" * 40)

        self.assertFalse(report["drift_detected"])
        self.assertEqual(report["decision"], "CLEAR")

    def test_no_changes_is_clear(self):
        changes = parse_git_changes(b"")
        report = evaluate_drift(changes, "a" * 40, "a" * 40)

        self.assertEqual(changes, [])
        self.assertEqual(report["decision"], "CLEAR")

    def test_malformed_git_output_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_git_changes(b"M\x00")

    def test_added_governance_file_is_detected(self):
        raw = b"A\x00policies/new_policy.md\x00"
        changes = parse_git_changes(raw)

        self.assertEqual(changes[0]["change"], "ADDED")
        self.assertEqual(changes[0]["risk"], "HIGH")

    def test_multiple_changes_preserve_severity(self):
        raw = (
            b"M\x00docs/README.md\x00"
            b"M\x00fulfillflow/core.py\x00"
            b"M\x00.github/workflows/ci.yml\x00"
        )
        changes = parse_git_changes(raw)
        report = evaluate_drift(changes, "a" * 40, "b" * 40)

        self.assertEqual(len(changes), 3)
        self.assertEqual(len(report["high_risk_changes"]), 1)
        self.assertEqual(
            report["decision"], "REVIEW_REQUIRED"
        )

    def test_rename_represented_as_delete_and_add(self):
        raw = (
            b"D\x00.github/CODEOWNERS\x00"
            b"A\x00docs/old_codeowners.md\x00"
        )
        changes = parse_git_changes(raw)

        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0]["risk"], "HIGH")
        self.assertEqual(changes[1]["risk"], "LOW")


if __name__ == "__main__":
    unittest.main()
