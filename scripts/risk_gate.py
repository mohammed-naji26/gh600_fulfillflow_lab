"""Demonstration risk gate: reads changed paths and outputs review classification.
Not a substitute for server-side branch protection or human judgment.
"""
import json
import sys

paths = sys.argv[1:]
if not paths:
    raise SystemExit("Usage: python scripts/risk_gate.py <changed-path> [...]")
high = (".github/workflows/", ".github/CODEOWNERS", "policies/", ".github/agents/", ".github/aw/")
medium = ("fulfillflow/", "mcp/", "scripts/")
severity = "LOW"
for path in paths:
    if path.startswith(high) or path == ".github/CODEOWNERS":
        severity = "HIGH"
        break
    if path.startswith(medium):
        severity = "MEDIUM"
report = {"paths": paths, "risk": severity,
          "requires_security_review": severity == "HIGH",
          "requires_tests": severity in ("MEDIUM", "HIGH"),
          "note": "Human review and repository rules remain the enforcement boundary."}
print(json.dumps(report, indent=2))
