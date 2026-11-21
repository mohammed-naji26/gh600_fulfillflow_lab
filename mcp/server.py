
"""FulfillFlow read-only MCP tool server."""

import sys
from pathlib import Path

# Ensure the FulfillFlow package is importable when the
# MCP server is launched directly by VS Code.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer

server = MCPServer("fulfillflow-agentops")


@server.tool()
def list_shipment_statuses() -> list[str]:
    """List the shipment statuses supported by FulfillFlow."""
    from fulfillflow.core import Status

    return [status.value for status in Status]


@server.tool()
def get_allowed_transitions(status: str) -> dict:
    """Return permitted next states for a shipment status."""
    from fulfillflow.core import Status, ALLOWED

    try:
        current = Status(status)
    except ValueError:
        return {
            "error": "Unknown shipment status",
            "status": status,
        }

    return {
        "status": current.value,
        "allowed_transitions": sorted(
            next_status.value
            for next_status in ALLOWED[current]
        ),
    }


@server.tool()
def validate_transition(
    current_status: str,
    target_status: str,
) -> dict:
    """Validate a transition without modifying shipment data."""
    from fulfillflow.core import Status, ALLOWED

    try:
        current = Status(current_status)
        target = Status(target_status)
    except ValueError:
        return {
            "valid": False,
            "reason": "Unknown shipment status",
        }

    allowed = target in ALLOWED[current]

    return {
        "current_status": current.value,
        "target_status": target.value,
        "valid": allowed,
        "reason": (
            "Transition permitted"
            if allowed
            else "Transition forbidden"
        ),
    }


if __name__ == "__main__":
    server.run(transport="stdio")
