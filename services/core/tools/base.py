from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ActionOutcome(StrEnum):
    CONFIRMED = "confirmed"
    UNCONFIRMED = "unconfirmed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class ToolResult:
    text: str
    data: dict


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict
    risk_level: RiskLevel = RiskLevel.LOW
    confirmation_required: bool = False
    availability: str = "available"


class Tool(Protocol):
    name: str
    description: str
    parameters: dict
    risk_level: RiskLevel
    confirmation_required: bool

    async def run(self, arguments: dict) -> ToolResult: ...


class CancellationSignal(Protocol):
    @property
    def cancelled(self) -> bool: ...

    @property
    def reason(self) -> str: ...


ALWAYS_MUTATING_TOOLS = frozenset(
    {
        "announcement.send",
        "arrival.mode",
        "camera.lenovo.snapshot",
        "camera.snapshot",
        "communication.send",
        "computer.command.run",
        "device.control",
        "health.repair",
        "homelab.recover",
        "memory.remember",
        "msi.code.run",
        "msi.documents.organize",
        "notification.send",
        "phone.call",
        "presence.appear",
        "presence.hide",
        "reminder.create",
        "reminder.update",
        "routine.execute",
        "security.contain",
        "system.ensure_msi",
        "workspace.create_file",
    }
)

MUTATING_TOOL_ACTIONS: dict[str, frozenset[str]] = {
    "focus.manage": frozenset({"start", "pause", "resume", "cancel"}),
    "automation.manage": frozenset({"create", "delete", "disable", "enable", "update"}),
    "companion.session": frozenset({"start", "stop"}),
    "curiosity.manage": frozenset({"cancel", "enqueue", "lab", "run"}),
    "embodiment.manage": frozenset({"hide", "present", "sync"}),
    "maddy.room": frozenset({"camera", "move"}),
    "maddy.avatar": frozenset({"gaze", "move"}),
    "development.agent": frozenset({"approve", "create", "execute", "start"}),
    "goal.manage": frozenset({"create", "transition", "update"}),
    "learning.acquire": frozenset({"acquire", "correct", "verify"}),
    "live.visual.task": frozenset({"cancel", "start"}),
    "media.control": frozenset(
        {
            "launch_content",
            "media_pause",
            "media_play",
            "select_source",
            "turn_off",
            "turn_on",
            "volume_down",
            "volume_mute",
            "volume_set",
            "volume_up",
            "youtube_latest",
        }
    ),
    "memory.manage": frozenset({"delete", "update"}),
    "pattern.manage": frozenset({"evaluate", "feedback", "observe", "shadow"}),
    "personal.safety": frozenset(
        {"cancel", "escalate", "respond", "start", "stop"}
    ),
    "spatial.memory": frozenset({"forget"}),
    "workspace.profile": frozenset({"deactivate", "save"}),
    "workspace.orchestrate": frozenset({"cancel", "start"}),
    "mobility.state": frozenset({"driving", "update"}),
    "phone.control": frozenset({"find", "ring", "set_dnd"}),
    "privacy.manage": frozenset({"disable", "enable"}),
    "project.manage": frozenset({"create", "save", "update", "activate", "note", "write_note"}),
    "room.control": frozenset({"turn_off"}),
    "skill.manage": frozenset(
        {"confirm", "deactivate", "delete", "execute", "prepare", "update"}
    ),
    "study.coach": frozenset({"grade", "plan", "quiz"}),
    "study.manage": frozenset({"record"}),
    "timer.manage": frozenset({"alarm", "cancel", "create"}),
    "voice.profile": frozenset({"reset", "set", "update"}),
    "vehicle.manage": frozenset({"control"}),
    "work.manage": frozenset({"cancel", "create", "transition", "update"}),
    "world.model": frozenset({"alias", "update"}),
}


def is_tool_mutating(tool_name: str, action: str = "") -> bool:
    if tool_name in ALWAYS_MUTATING_TOOLS:
        return True
    return action.strip().lower() in MUTATING_TOOL_ACTIONS.get(tool_name, frozenset())
