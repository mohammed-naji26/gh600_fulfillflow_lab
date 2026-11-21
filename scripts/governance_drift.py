
"""Detect governance-sensitive changes between Git revisions."""

import argparse
import json
import subprocess
from datetime import datetime, timezone

from scripts.risk_gate import classify_path


STATUS_NAMES = {
    "A": "ADDED",
    "M": "MODIFIED",
    "D": "DELETED",
    "T": "TYPE_CHANGED",
}


def parse_git_changes(output):
    """Parse null-delimited Git name/status output."""

    if not output:
        return []

    fields = output.split(b"\0")

    if fields[-1] == b"":
        fields.pop()

    if len(fields) % 2:
        raise ValueError("Malformed Git diff output")

    changes = []

    for index in range(0, len(fields), 2):
        status = fields[index].decode("ascii")
        path = fields[index + 1].decode(
            "utf-8", errors="surrogateescape"
        )

        changes.append({
            "path": path,
            "change": STATUS_NAMES.get(status, status),
            "risk": classify_path(path),
        })

    return changes


def evaluate_drift(changes, baseline_sha, target_sha):
    """Assess governance-sensitive changes."""

    high_risk = [
        change
        for change in changes
        if change["risk"] == "HIGH"
    ]

    return {
        "baseline_sha": baseline_sha,
        "target_sha": target_sha,
        "timestamp_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "changes": changes,
        "high_risk_changes": high_risk,
        "drift_detected": bool(high_risk),
        "decision": (
            "REVIEW_REQUIRED"
            if high_risk
            else "CLEAR"
        ),
        "note": (
            "Differences require review when classified "
            "HIGH. Detection does not establish "
            "unauthorized activity or approval status."
        ),
    }


def git(*arguments):
    return subprocess.check_output(
        ["git", *arguments]
    )


def resolve_commit(reference):
    return git(
        "rev-parse",
        "--verify",
        f"{reference}^{{commit}}",
    ).decode().strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("target", nargs="?", default="HEAD")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        baseline_sha = resolve_commit(args.baseline)
        target_sha = resolve_commit(args.target)

        raw = git(
            "diff",
            "--name-status",
            "--no-renames",
            "-z",
            baseline_sha,
            target_sha,
        )

        changes = parse_git_changes(raw)

        report = evaluate_drift(
            changes,
            baseline_sha,
            target_sha,
        )

    except (
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        parser.exit(
            2,
            f"Governance drift evaluation failed: {error}\n",
        )

    payload = json.dumps(report, indent=2) + "\n"

    if args.output:
        from pathlib import Path

        output = Path(args.output)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output.write_text(payload)

    print(payload, end="")

    return (
        1
        if report["drift_detected"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
