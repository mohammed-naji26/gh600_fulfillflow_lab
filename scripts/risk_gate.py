
"""Classify changed repository paths by governance risk.

This classifier produces advisory review requirements.
Actual approvals must be enforced through GitHub rulesets,
CODEOWNERS, protected environments, and permissions.
"""

import json
import sys
from pathlib import PurePosixPath


HIGH_RISK_PREFIXES = (
    ".github/workflows/",
    ".github/agents/",
    ".github/aw/",
    "policies/",
    "mcp/",
)

HIGH_RISK_FILES = {
    ".github/CODEOWNERS",
    ".github/copilot-instructions.md",
    ".vscode/mcp.json",
}

MEDIUM_RISK_PREFIXES = (
    "fulfillflow/",
    "scripts/",
    "tests/",
)

RISK_LEVELS = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
}


def classify_path(path: str) -> str:
    """Determine the risk classification of one path."""

    normalized = path.replace("\\", "/")

    if (
        not normalized
        or normalized.startswith("/")
        or any(
            part in ("", ".", "..")
            for part in normalized.split("/")
        )
    ):
        raise ValueError(f"Invalid repository path: {path!r}")

    normalized = str(PurePosixPath(normalized))

    if (
        normalized in HIGH_RISK_FILES
        or normalized.startswith(HIGH_RISK_PREFIXES)
    ):
        return "HIGH"

    if normalized.startswith(MEDIUM_RISK_PREFIXES):
        return "MEDIUM"

    return "LOW"


def evaluate_paths(paths: list[str]) -> dict:
    """Return the highest risk across all changed paths."""

    if not paths:
        raise ValueError("At least one changed path is required")

    classifications = {
        path: classify_path(path)
        for path in paths
    }

    highest = max(
        classifications.values(),
        key=lambda level: RISK_LEVELS[level],
    )

    return {
        "paths": paths,
        "classifications": classifications,
        "risk": highest,
        "requires_security_review": highest == "HIGH",
        "requires_tests": highest in ("MEDIUM", "HIGH"),
        "note": (
            "Risk classification is advisory. "
            "Human approvals and protected-branch rules "
            "must be configured separately in GitHub."
        ),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/risk_gate.py "
            "<changed-path> [...]",
            file=sys.stderr,
        )
        return 2

    try:
        report = evaluate_paths(sys.argv[1:])
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
