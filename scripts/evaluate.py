"""Write current-SHA-aware evaluation evidence without calling an AI model."""
import json
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
head = sha.stdout.strip() if sha.returncode == 0 else "uncommitted"
suite = unittest.defaultTestLoader.discover(str(root / "tests"), top_level_dir=str(root))
result = unittest.TestResult()
suite.run(result)
report = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "commit_sha": head,
    "tests_run": result.testsRun,
    "passed": result.testsRun - len(result.failures) - len(result.errors),
    "failures": len(result.failures),
    "errors": len(result.errors),
    "success": result.wasSuccessful(),
    "failure_details": [str(test) + ": " + output[-1000:] for test, output in result.failures + result.errors],
    "quality_gate": "PASS" if result.wasSuccessful() else "BLOCK",
}
out = root / "docs" / "evidence" / "evaluation.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
raise SystemExit(0 if result.wasSuccessful() else 1)
