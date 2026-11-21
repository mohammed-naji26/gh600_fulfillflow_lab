
"""Validate persisted AgentOps task state and freshness."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PHASE_OWNERS = {
    "plan": "planner",
    "implement": "implementer",
    "validate": "validator",
    "security_review": "security-reviewer",
    "human_review": "human",
    "complete": "human",
}

ALLOWED_HANDOFFS = {
    "plan": {"implement"},
    "implement": {"validate"},
    "validate": {"implement", "security_review"},
    "security_review": {"implement", "human_review"},
    "human_review": {"implement", "complete"},
    "complete": set(),
}


def validate_handoff(current_phase, next_phase, human_approval):
    """Validate a proposed agent-to-agent task handoff."""

    errors = []

    if current_phase not in ALLOWED_HANDOFFS:
        return [f"Unknown current phase: {current_phase}"]

    if next_phase not in PHASE_OWNERS:
        return [f"Unknown target phase: {next_phase}"]

    if next_phase not in ALLOWED_HANDOFFS[current_phase]:
        errors.append(
            f"Forbidden handoff: {current_phase} -> {next_phase}"
        )

    if (
        current_phase == "plan"
        and next_phase == "implement"
        and human_approval is not True
    ):
        errors.append(
            "Human approval required before implementation"
        )

    return errors


REQUIRED_FIELDS = {
    "issue",
    "task_id",
    "goal",
    "current_phase",
    "owner_role",
    "commit_sha",
    "approved_paths",
    "risk_level",
    "last_updated_utc",
    "expires_at_utc",
    "human_approval",
}


def parse_timestamp(value):
    """Parse a timezone-aware ISO 8601 timestamp."""

    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")

    timestamp = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")

    return timestamp.astimezone(timezone.utc)


def validate_state(state, current_sha, now=None):
    """Return validation errors for a persisted task state."""

    now = now or datetime.now(timezone.utc)
    errors = []

    if not isinstance(state, dict):
        return ["Task state must be a JSON object"]

    missing = REQUIRED_FIELDS - state.keys()

    if missing:
        return [
            "Missing required fields: "
            + ", ".join(sorted(missing))
        ]

    phase = state["current_phase"]
    owner = state["owner_role"]

    if phase not in PHASE_OWNERS:
        errors.append(f"Unknown phase: {phase}")

    elif owner != PHASE_OWNERS[phase]:
        errors.append(
            f"Invalid owner '{owner}' for phase '{phase}'"
        )

    if state["commit_sha"] != current_sha:
        errors.append("STALE STATE: commit SHA mismatch")

    if state["risk_level"] not in {
        "LOW", "MEDIUM", "HIGH"
    }:
        errors.append("Invalid risk level")

    if type(state["human_approval"]) is not bool:
        errors.append("human_approval must be boolean")

    if (
        phase in {"implement", "complete"}
        and state["human_approval"] is not True
    ):
        errors.append(
            "Human approval required for this phase"
        )

    paths = state["approved_paths"]

    if (
        not isinstance(paths, list)
        or not paths
        or not all(
            isinstance(path, str) and path.strip()
            for path in paths
        )
    ):
        errors.append(
            "approved_paths must contain valid paths"
        )

    try:
        updated = parse_timestamp(
            state["last_updated_utc"]
        )
        expires = parse_timestamp(
            state["expires_at_utc"]
        )

        if updated > now:
            errors.append(
                "Task state has a future update timestamp"
            )

        if expires <= now:
            errors.append("Task state has expired")

        if expires <= updated:
            errors.append(
                "Expiration must follow last update"
            )

    except (ValueError, TypeError) as error:
        errors.append(
            f"Invalid task-state timestamp: {error}"
        )

    return errors


def current_commit_sha():
    """Read the current repository HEAD."""

    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()


def main():
    path = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "docs/templates/task_state.example.json"
    )

    try:
        state = json.loads(path.read_text())
        errors = validate_state(
            state,
            current_commit_sha(),
        )
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"BLOCK: {error}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"BLOCK: {error}")
        return 1

    print("PASS: task state is valid and current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
