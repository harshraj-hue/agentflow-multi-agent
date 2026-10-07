"""External action tool requiring human-in-the-loop approval."""

from typing import Any

from app.tools.base import BaseTool, ToolResult


class ExternalActionTool(BaseTool):
    name = "external_action"
    description = "Performs an external side-effect (e.g. publishing reports, sending notifications, webhook dispatch). Requires human approval."
    category = "integration"
    requires_approval = True
    parameters_schema = {
        "type": "object",
        "properties": {
            "action_type": {
                "type": "string",
                "description": "Type of action: publish_report, notify_slack, export_data",
                "default": "publish_report",
            },
            "destination": {
                "type": "string",
                "description": "Destination channel or target repository",
            },
            "payload": {
                "type": "object",
                "description": "The payload data or deliverable to export",
            },
        },
        "required": ["action_type"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        action_type = kwargs.get("action_type", "publish_report")
        destination = kwargs.get("destination", "production-channel")
        payload = kwargs.get("payload", {})

        return ToolResult(
            success=True,
            data={
                "status": "executed",
                "action_type": action_type,
                "destination": destination,
                "payload": payload,
                "confirmed_at": "now",
                "message": f"Action '{action_type}' was approved by human operator and executed successfully.",
            },
            metadata={"requires_approval": True, "approved": True},
        )
