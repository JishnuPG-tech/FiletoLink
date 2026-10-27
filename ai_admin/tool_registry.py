"""Tool registry with strict schema, risk, confirmation, and policy metadata."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDefinition:
    name: str
    purpose: str
    json_schema: Dict[str, Any]
    read_only: bool
    mutates: bool
    risk: str  # "low" | "medium" | "high"
    requires_confirmation: str  # "never" | "if_ambiguous" | "always"
    permission: str  # "read" | "write" | "bulk"
    timeout_seconds: int
    max_output_chars: int
    validators: List[Callable[[Dict[str, Any]], bool]] = field(default_factory=list)
    verification: str = ""
    handler: Optional[Callable[..., Any]] = None

    def validate_declaration(self) -> None:
        """Fail registration if any mandatory field is missing or invalid."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Tool declaration missing valid 'name'")
        if not self.purpose or not isinstance(self.purpose, str):
            raise ValueError(f"Tool '{self.name}' missing valid 'purpose'")
        if not isinstance(self.json_schema, dict):
            raise ValueError(f"Tool '{self.name}' missing valid 'json_schema'")
        if not isinstance(self.read_only, bool):
            raise ValueError(f"Tool '{self.name}' missing boolean 'read_only'")
        if not isinstance(self.mutates, bool):
            raise ValueError(f"Tool '{self.name}' missing boolean 'mutates'")
        if self.read_only and self.mutates:
            raise ValueError(f"Tool '{self.name}' cannot be both read_only and mutates")
        if self.risk not in ("low", "medium", "high"):
            raise ValueError(f"Tool '{self.name}' has invalid risk level '{self.risk}'")
        if self.requires_confirmation not in ("never", "if_ambiguous", "always"):
            raise ValueError(f"Tool '{self.name}' has invalid requires_confirmation '{self.requires_confirmation}'")
        if self.permission not in ("read", "write", "bulk"):
            raise ValueError(f"Tool '{self.name}' has invalid permission '{self.permission}'")
        if not isinstance(self.timeout_seconds, (int, float)) or self.timeout_seconds <= 0:
            raise ValueError(f"Tool '{self.name}' has invalid timeout_seconds")
        if not isinstance(self.max_output_chars, int) or self.max_output_chars <= 0:
            raise ValueError(f"Tool '{self.name}' has invalid max_output_chars")


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register tool definition after strict validation."""
        tool.validate_declaration()
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool registration: '{tool.name}'")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_schemas_for_planner(self) -> List[Dict[str, Any]]:
        """Return schema definitions formatted for OpenAI-compatible function calling."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.purpose,
                    "parameters": tool.json_schema,
                },
            })
        return schemas


# Global registry instance
registry = ToolRegistry()

# Stage 1 Test Tool (Safe echo tool for testing the tool runner without side effects)
def _echo_health_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    msg = params.get("message", "ok")
    return {"status": "healthy", "echo": str(msg)}


registry.register(
    ToolDefinition(
        name="echo_health",
        purpose="Harmless echo and health probe for tool runner test validation",
        json_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "maxLength": 100},
            },
            "additionalProperties": False,
        },
        read_only=True,
        mutates=False,
        risk="low",
        requires_confirmation="never",
        permission="read",
        timeout_seconds=5,
        max_output_chars=500,
        verification="none",
        handler=_echo_health_handler,
    )
)
