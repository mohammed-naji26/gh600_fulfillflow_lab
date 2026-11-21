
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
