
"""Regression tests for the AgentOps risk classifier."""

import unittest

from scripts.risk_gate import classify_path, evaluate_paths


class RiskGateTests(unittest.TestCase):

    def test_mcp_configuration_is_high_risk(self):
        self.assertEqual(
            classify_path(".vscode/mcp.json"),
            "HIGH",
        )

    def test_mcp_server_is_high_risk(self):
        self.assertEqual(
            classify_path("mcp/server.py"),
            "HIGH",
        )

    def test_github_workflow_is_high_risk(self):
        self.assertEqual(
            classify_path(".github/workflows/ci.yml"),
            "HIGH",
        )

    def test_business_logic_is_medium_risk(self):
        self.assertEqual(
            classify_path("fulfillflow/core.py"),
            "MEDIUM",
        )

    def test_documentation_is_low_risk(self):
        self.assertEqual(
            classify_path("docs/README.md"),
            "LOW",
        )

    def test_highest_risk_takes_precedence(self):
        report = evaluate_paths([
            "docs/README.md",
            "fulfillflow/core.py",
            "mcp/server.py",
        ])

        self.assertEqual(report["risk"], "HIGH")
        self.assertTrue(report["requires_security_review"])
        self.assertTrue(report["requires_tests"])

    def test_medium_risk_requires_tests(self):
        report = evaluate_paths(["fulfillflow/core.py"])

        self.assertEqual(report["risk"], "MEDIUM")
        self.assertTrue(report["requires_tests"])
        self.assertFalse(report["requires_security_review"])

    def test_empty_path_list_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_paths([])

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_path("../policies/autonomy.md")


if __name__ == "__main__":
    unittest.main()
