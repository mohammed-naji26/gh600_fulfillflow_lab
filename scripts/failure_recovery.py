
"""Advisory failure-recovery policy for FulfillFlow agents."""

import json
import sys
from datetime import datetime, timezone


RECOVERY_POLICY = {
    "stale_context": {
        "action": "REFRESH_AND_REVALIDATE",
        "requires_human_review": False,
        "automatic_retry": False,
        "explanation": (
            "Refresh repository context and task state. "
            "Revalidate before continuing."
        ),
    },
    "tool_failure": {
        "action": "RETRY_WITH_LIMITS",
        "requires_human_review": False,
        "automatic_retry": True,
        "explanation": (
            "Retry only confirmed transient failures "
            "within the approved retry budget."
        ),
    },
    "permission": {
        "action": "STOP_AND_ESCALATE",
        "requires_human_review": True,
        "automatic_retry": False,
        "explanation": (
            "Do not bypass access restrictions. "
            "Escalate to an authorized human."
        ),
    },
    "policy_drift": {
        "action": "BLOCK_AND_REVIEW",
        "requires_human_review": True,
        "automatic_retry": False,
        "explanation": (
            "Suspend affected operations until "
            "the governance change is reviewed."
        ),
    },
    "reasoning": {
        "action": "REPLAN_AND_VALIDATE",
        "requires_human_review": True,
        "automatic_retry": False,
        "explanation": (
            "Reassess assumptions and obtain review "
            "before continuing."
        ),
    },
}


def evaluate_failure(
    category,
    incident_id,
    commit_sha,
    timestamp=None,
):
    """Return an advisory decision without executing recovery."""

    timestamp = timestamp or datetime.now(timezone.utc)

    if not isinstance(category, str):
        raise ValueError("Failure category must be a string")

    if not isinstance(incident_id, str) or not incident_id.strip():
        raise ValueError("Incident ID is required")

    if not isinstance(commit_sha, str) or not commit_sha.strip():
        raise ValueError("Commit SHA is required")

    policy = RECOVERY_POLICY.get(category)

    if policy is None:
        return {
            "incident_id": incident_id,
            "commit_sha": commit_sha,
            "timestamp_utc": timestamp.isoformat(),
            "category": category,
            "action": "STOP_AND_ESCALATE",
            "requires_human_review": True,
            "automatic_retry": False,
            "explanation": "Unknown failure category.",
            "decision": "BLOCK",
        }

    return {
        "incident_id": incident_id,
        "commit_sha": commit_sha,
        "timestamp_utc": timestamp.isoformat(),
        "category": category,
        **policy,
        "decision": (
            "CONDITIONAL"
            if policy["automatic_retry"]
            else "BLOCK"
        ),
    }


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python -m scripts.failure_recovery "
            "<category> <incident_id> <commit_sha>",
            file=sys.stderr,
        )
        return 2

    report = evaluate_failure(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
    )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
