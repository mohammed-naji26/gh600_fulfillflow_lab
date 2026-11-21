
"""Generate auditable decisions for proposed agent handoffs."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.state_check import (
    PHASE_OWNERS,
    validate_handoff,
    validate_state,
)


def evaluate_handoff(state, next_phase, current_sha, now=None):
    """Evaluate a proposed handoff without changing task state."""

    now = now or datetime.now(timezone.utc)

    errors = validate_state(
        state,
        current_sha,
        now=now,
    )

    if not errors:
        errors.extend(
            validate_handoff(
                state["current_phase"],
                next_phase,
                state["human_approval"],
            )
        )

    allowed = not errors

    return {
        "task_id": state.get("task_id"),
        "commit_sha": current_sha,
        "timestamp_utc": now.isoformat(),
        "current_phase": state.get("current_phase"),
        "requested_phase": next_phase,
        "requested_owner": PHASE_OWNERS.get(next_phase),
        "decision": "ALLOW" if allowed else "BLOCK",
        "reasons": errors,
        "note": (
            "Advisory evaluation only; no task-state "
            "mutation or GitHub approval is performed."
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate an AgentOps handoff"
    )
    parser.add_argument("state_file")
    parser.add_argument("next_phase")
    parser.add_argument(
        "--output",
        default="docs/evidence/handoff.json",
    )

    args = parser.parse_args()

    state = json.loads(
        Path(args.state_file).read_text()
    )

    current_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()

    report = evaluate_handoff(
        state,
        args.next_phase,
        current_sha,
    )

    output = Path(args.output)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.write_text(
        json.dumps(report, indent=2) + "\n"
    )

    print(json.dumps(report, indent=2))

    return 0 if report["decision"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
