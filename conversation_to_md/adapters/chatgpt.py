"""
ChatGPT export adapter.

Handles the standard ChatGPT data export ZIP which contains:
  - conversations.json: Array of conversation objects
  - Each conversation has a `mapping` dict (tree of message nodes)

This adapter walks the tree to reconstruct linear message order.
Supports streaming for large files via ijson.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from conversation_to_md.core.models import Attachment, Conversation, Message
from conversation_to_md.utils.normalize import (
    clean_content,
    sanitize_id,
    unix_to_datetime,
)
from conversation_to_md.utils.streaming import iter_json_array


def parse(
    extracted_dir: Path,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> List[Conversation]:
    """Parse ChatGPT export files into canonical conversations."""
    conversations_file = _find_conversations_json(extracted_dir)
    if conversations_file is None:
        return []

    log = progress_callback or (lambda _: None)
    conversations: List[Conversation] = []
    count = 0

    for raw_conv in iter_json_array(conversations_file, progress_callback):
        conv = _parse_conversation(raw_conv)
        if conv is not None:
            conversations.append(conv)
        count += 1
        if count % 50 == 0:
            log(f"Parsed {count} ChatGPT conversations...")

    return conversations


def _find_conversations_json(directory: Path) -> Optional[Path]:
    """Locate conversations.json in the extracted directory."""
    candidate = directory / "conversations.json"
    if candidate.exists():
        return candidate

    for child in directory.iterdir():
        if child.is_dir():
            candidate = child / "conversations.json"
            if candidate.exists():
                return candidate

    return None


def _parse_conversation(raw: dict) -> Optional[Conversation]:
    """Convert a single raw ChatGPT conversation dict into the canonical model."""
    if not isinstance(raw, dict):
        return None

    mapping: Dict[str, dict] = raw.get("mapping", {})
    if not mapping:
        return None

    conv_id = sanitize_id(raw.get("id") or raw.get("conversation_id"))
    title = raw.get("title") or "Untitled"
    created_at = unix_to_datetime(raw.get("create_time"))

    # Extract model from conversation-level or first assistant message
    model = raw.get("default_model_slug") or raw.get("model_slug") or ""

    messages = _walk_mapping(mapping)

    # If no conversation-level model, try to get it from messages
    if not model:
        for node in mapping.values():
            msg_obj = node.get("message")
            if msg_obj and isinstance(msg_obj, dict):
                meta = msg_obj.get("metadata", {})
                if meta.get("model_slug"):
                    model = meta["model_slug"]
                    break

    # Set model on all assistant messages if they don't have one
    for msg in messages:
        if msg.role == "assistant" and not msg.model and model:
            msg.model = model

    metadata = {}
    if model:
        metadata["model"] = model
    if raw.get("plugin_ids"):
        metadata["plugins"] = ", ".join(raw["plugin_ids"])

    return Conversation(
        id=conv_id,
        source="chatgpt",
        title=title,
        created_at=created_at,
        model=model,
        messages=messages,
        metadata=metadata,
    )


def _walk_mapping(mapping: Dict[str, dict]) -> List[Message]:
    """
    Walk the ChatGPT mapping tree and produce a linear message list.

    The mapping is a dict of node_id -> node. Each node has:
      - parent: node_id or None
      - children: list of node_ids
      - message: the message object or None

    We find the root (no parent), then walk depth-first following the
    first child at each level (ChatGPT linear conversations).
    """
    if not mapping:
        return []

    root_id = None
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent is None or parent not in mapping:
            root_id = node_id
            break

    if root_id is None:
        return _extract_messages_flat(mapping)

    messages: List[Message] = []
    current_id = root_id
    visited = set()

    while current_id and current_id not in visited:
        visited.add(current_id)
        node = mapping.get(current_id)
        if node is None:
            break

        msg = _extract_message(node)
        if msg is not None:
            messages.append(msg)

        children = node.get("children", [])
        current_id = children[0] if children else None

    return messages


def _extract_messages_flat(mapping: Dict[str, dict]) -> List[Message]:
    """Fallback: extract messages without tree walking."""
    messages = []
    for node in mapping.values():
        msg = _extract_message(node)
        if msg is not None:
            messages.append(msg)

    messages.sort(key=lambda m: m.created_at or 0)
    return messages


def _extract_message(node: dict) -> Optional[Message]:
    """Extract a Message from a mapping node, or None if no real message."""
    raw_msg = node.get("message")
    if raw_msg is None:
        return None

    author = raw_msg.get("author", {})
    role = author.get("role", "unknown")

    content_obj = raw_msg.get("content", {})
    content_type = content_obj.get("content_type", "text")
    parts = content_obj.get("parts", [])

    text = _extract_text(parts, content_type)
    if not text:
        return None

    role_map = {
        "user": "user",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
    }
    normalized_role = role_map.get(role, "assistant")

    created_at = unix_to_datetime(raw_msg.get("create_time"))

    # Extract per-message model
    meta = raw_msg.get("metadata", {})
    model = meta.get("model_slug") or None

    attachments = _extract_attachments(raw_msg)

    return Message(
        role=normalized_role,
        content=text,
        created_at=created_at,
        model=model,
        attachments=attachments,
    )


def _extract_text(parts: list, content_type: str) -> str:
    """Extract readable text from ChatGPT message parts."""
    if content_type == "code" and parts:
        return "```\n" + clean_content(parts) + "\n```"

    return clean_content(parts)


def _extract_attachments(raw_msg: dict) -> List[Attachment]:
    """Pull out attachment references from a ChatGPT message."""
    attachments: List[Attachment] = []
    metadata = raw_msg.get("metadata", {})

    for att in metadata.get("attachments", []):
        name = att.get("name", "attachment")
        att_type = "file"
        mime = att.get("mimeType", "")
        if mime.startswith("image/"):
            att_type = "image"
        ref = att.get("id", name)
        attachments.append(Attachment(type=att_type, name=name, reference=ref))

    return attachments
