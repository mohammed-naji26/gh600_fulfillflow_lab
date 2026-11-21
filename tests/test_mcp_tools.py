
"""Regression tests for FulfillFlow MCP tools."""

import asyncio
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))

from mcp import Client
from server import server


async def invoke_tool(name, arguments):
    async with Client(server) as client:
        result = await client.call_tool(name, arguments)

        if result.is_error:
            raise AssertionError(
                f"MCP tool failed: {result.content}"
            )

        if result.structured_content is not None:
            return result.structured_content

        for block in result.content:
            if block.type == "text":
                return json.loads(block.text)

        raise AssertionError("No usable MCP response")


class MCPToolTests(unittest.TestCase):

    def call(self, name, arguments):
        return asyncio.run(invoke_tool(name, arguments))

    def test_shipped_cannot_be_cancelled(self):
        result = self.call(
            "validate_transition",
            {
                "current_status": "shipped",
                "target_status": "cancelled",
            },
        )
        self.assertFalse(result["valid"])

    def test_shipped_can_be_delivered(self):
        result = self.call(
            "validate_transition",
            {
                "current_status": "shipped",
                "target_status": "delivered",
            },
        )
        self.assertTrue(result["valid"])

    def test_shipped_can_be_returned(self):
        result = self.call(
            "validate_transition",
            {
                "current_status": "shipped",
                "target_status": "return_to_sender",
            },
        )
        self.assertTrue(result["valid"])

    def test_invalid_status_is_rejected(self):
        result = self.call(
            "validate_transition",
            {
                "current_status": "invalid",
                "target_status": "delivered",
            },
        )
        self.assertFalse(result["valid"])
        self.assertEqual(
            result["reason"],
            "Unknown shipment status",
        )

    def test_allowed_transitions(self):
        result = self.call(
            "get_allowed_transitions",
            {"status": "shipped"},
        )
        self.assertEqual(
            result["allowed_transitions"],
            ["delivered", "return_to_sender"],
        )

    def test_only_approved_tools_are_exposed(self):
        """The MCP server must expose only approved tools."""

        async def check_tools():
            async with Client(server) as client:
                result = await client.list_tools()
                return {tool.name for tool in result.tools}

        actual = asyncio.run(check_tools())

        expected = {
            "list_shipment_statuses",
            "get_allowed_transitions",
            "validate_transition",
        }

        self.assertEqual(actual, expected)

    def test_unauthorized_tool_is_rejected(self):
        """Unregistered shipment-modification tools must fail."""

        async def attempt_unauthorized_call():
            async with Client(server) as client:
                return await client.call_tool(
                    "cancel_shipment",
                    {"shipment_id": "SHP-1042"},
                )

        result = asyncio.run(attempt_unauthorized_call())

        self.assertTrue(result.is_error)
        self.assertIn(
            "Unknown tool",
            str(result.content),
        )
