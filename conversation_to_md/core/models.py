"""
Canonical data model for normalized conversations.

Every provider adapter converts into these structures.
The renderer consumes only these structures.
No provider-specific logic belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Attachment:
    """A file, image, or code block attached to a message."""

    type: str  # "image" | "file" | "code" | "unknown"
    name: str
    reference: str  # path, URL, or inline content hint


@dataclass
class Message:
    """A single message within a conversation."""

    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    created_at: Optional[datetime] = None
    model: Optional[str] = None
    attachments: List[Attachment] = field(default_factory=list)


@dataclass
class Conversation:
    """
    A complete conversation thread, provider-agnostic.

    This is the central data structure of the entire pipeline.
    Everything upstream produces these; everything downstream consumes them.
    """

    id: str
    source: str  # "chatgpt" | "claude" | "gemini" | "grok" | "unknown"
    title: str
    created_at: Optional[datetime] = None
    model: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def platform_display(self) -> str:
        """Human-friendly platform name."""
        names = {
            "chatgpt": "ChatGPT",
            "claude": "Claude",
            "gemini": "Gemini",
            "grok": "Grok",
            "unknown": "Unknown",
        }
        return names.get(self.source, self.source.title())

    @property
    def first_user_message(self) -> Optional[str]:
        """Return the first user message content, if any."""
        for msg in self.messages:
            if msg.role == "user" and msg.content:
                return msg.content[:200]
        return None
