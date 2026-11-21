"""Regression tests for FulfillFlow AgentOps Copilot governance hooks.

The commands in these tests are JSON input to the Node.js policy gate;
no shell commands contained in the test cases are executed.
"""

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / ".github" / "hooks" / "policy-gate.cjs"


class GovernanceHookTests(unittest.TestCase):
    """Validate hook decisions for supported tool operations."""

    def evaluate(self, tool_name, command=None):
        """Run the policy script with a simulated preToolUse event."""
        event = {
            "toolName": tool_name,
            "toolArgs": {"command": command} if command is not None else {},
        }

        result = subprocess.run(
            ["node", str(POLICY)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            cwd=ROOT,
            timeout=10,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "Governance hook execution failed.\n"
                f"STDERR: {result.stderr}\n"
                f"STDOUT: {result.stdout}"
            ),
        )

        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"Governance hook returned invalid JSON: {exc}\n{result.stdout}")

        self.assertIsInstance(response, dict)
        return response

    def assert_denied(self, command, rule):
        """Assert that a bash command is denied by the expected policy rule."""
        response = self.evaluate("bash", command)
        self.assertEqual(
            response.get("permissionDecision"),
            "deny",
            msg=f"Command was not denied: {command}\nResponse: {response}",
        )
        self.assertIn(
            rule,
            response.get("permissionDecisionReason", ""),
            msg=f"Expected {rule} for: {command}\nResponse: {response}",
        )

    def assert_no_decision(self, command):
        """Assert the hook adds no restriction; other permissions still apply."""
        response = self.evaluate("bash", command)
        self.assertEqual(response, {}, msg=f"Unexpected restriction: {response}")

    def test_normal_regression_command(self):
        self.assert_no_decision("python -m unittest discover -s tests -q")

    def test_non_shell_tool(self):
        self.assertEqual(self.evaluate("view"), {})

    def test_missing_bash_command(self):
        response = self.evaluate("bash")
        self.assertEqual(response.get("permissionDecision"), "deny")
        self.assertIn("POLICY-000", response.get("permissionDecisionReason", ""))

    def test_recursive_policy_deletion(self):
        self.assert_denied("rm -rf policies/", "POLICY-001")

    def test_combined_rm_flags(self):
        self.assert_denied("rm -fr policies/", "POLICY-001")

    def test_separated_rm_flags(self):
        self.assert_denied("rm -r -f policies/", "POLICY-001")

    def test_pwd_based_policy_path(self):
        self.assert_denied('rm -rf "$PWD/policies"', "POLICY-001")

    def test_codeowners_deletion(self):
        self.assert_denied("rm -f .github/CODEOWNERS", "POLICY-002")

    def test_codeowners_without_force_flag(self):
        self.assert_denied("rm .github/CODEOWNERS", "POLICY-002")

    def test_unlink_codeowners(self):
        self.assert_denied("unlink .github/CODEOWNERS", "POLICY-002")

    def test_force_push_main(self):
        self.assert_denied("git push origin main --force", "POLICY-003")

    def test_force_push_with_lease(self):
        self.assert_denied("git push --force-with-lease origin main", "POLICY-003")

    def test_force_push_head_refspec(self):
        self.assert_denied("git push --force origin HEAD:main", "POLICY-003")

    def test_python_indirect_deletion(self):
        command = 'python -c "import os; os.remove(\'.github/CODEOWNERS\')"'
        self.assert_denied(command, "POLICY-004")


if __name__ == "__main__":
    unittest.main()
