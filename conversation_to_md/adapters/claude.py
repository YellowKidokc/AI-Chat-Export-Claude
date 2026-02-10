"""
Claude export adapter.

Handles Claude conversation exports which typically contain JSON with:
  - A list of conversation objects
  - Each conversation has: uuid, name, created_at, updated_at, chat_messages
  - Each chat_message has: uuid, text, sender ("human"/"assistant"), created_at, attachments

Supports streaming for large files (50-200+ MB) via ijson.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List, Optional

from conversation_to_md.core.models import Attachment, Conversation, Message
from conversation_to_md.utils.normalize import (
    clean_content,
    iso_to_datetime,
    sanitize_id,
)
from conversation_to_md.utils.streaming import iter_json_array


def parse(
    extracted_dir: Path,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> List[Conversation]:
    """Parse Claude export files into canonical conversations."""
    json_files = _find_claude_json_files(extracted_dir)
    conversations: List[Conversation] = []
    log = progress_callback or (lambda _: None)

    for json_file in json_files:
        log(f"Parsing {json_file.name}...")
        count = 0
        for raw_conv in iter_json_array(json_file, progress_callback):
            conv = _parse_conversation(raw_conv)
            if conv is not None:
                conversations.append(conv)
            count += 1
            if count % 50 == 0:
                log(f"Parsed {count} Claude conversations...")

    return conversations


def _find_claude_json_files(directory: Path) -> List[Path]:
    """Find JSON files that contain Claude conversation data."""
    candidates = []
    for path in directory.rglob("*.json"):
        if _is_claude_json(path):
            candidates.append(path)
    return candidates


def _is_claude_json(filepath: Path) -> bool:
    """Quick check if a JSON file looks like Claude export data."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            raw = fh.read(50_000)
        data = json.loads(raw)
        items = data if isinstance(data, list) else [data]
        for item in items[:3]:
            if isinstance(item, dict):
                if "chat_messages" in item:
                    return True
                if "uuid" in item and "name" in item:
                    return True
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        pass
    return False


def _parse_conversation(raw: dict) -> Optional[Conversation]:
    """Convert a single Claude conversation dict into the canonical model."""
    if not isinstance(raw, dict):
        return None

    conv_id = sanitize_id(raw.get("uuid") or raw.get("id"))
    title = raw.get("name") or raw.get("title") or "Untitled"
    created_at = iso_to_datetime(raw.get("created_at"))

    raw_messages = raw.get("chat_messages", [])
    messages = []
    for raw_msg in raw_messages:
        msg = _parse_message(raw_msg)
        if msg is not None:
            messages.append(msg)

    # Extract model info
    model = raw.get("model") or ""

    # Try to extract model from message metadata if not at conversation level
    if not model:
        for raw_msg in raw_messages:
            if isinstance(raw_msg, dict):
                msg_model = raw_msg.get("model") or ""
                if msg_model:
                    model = msg_model
                    break

    metadata = {}
    if model:
        metadata["model"] = model
    project = raw.get("project")
    if project and isinstance(project, dict):
        metadata["project"] = project.get("name", "")

    return Conversation(
        id=conv_id,
        source="claude",
        title=title,
        created_at=created_at,
        model=model,
        messages=messages,
        metadata=metadata,
    )


def _parse_message(raw_msg: dict) -> Optional[Message]:
    """Convert a single Claude message into the canonical Message."""
    if not isinstance(raw_msg, dict):
        return None

    sender = raw_msg.get("sender", "")
    role_map = {
        "human": "user",
        "assistant": "assistant",
        "system": "system",
    }
    role = role_map.get(sender, "assistant")

    # Claude messages can have text directly or content array
    text = ""
    if "text" in raw_msg:
        text = clean_content(raw_msg["text"])
    elif "content" in raw_msg:
        content = raw_msg["content"]
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        parts.append(f"[Tool call: {block.get('name', 'unknown')}]")
                    elif block.get("type") == "tool_result":
                        parts.append("[Tool result]")
                elif isinstance(block, str):
                    parts.append(block)
            text = "\n".join(parts).strip()
        else:
            text = clean_content(content)

    if not text:
        return None

    created_at = iso_to_datetime(raw_msg.get("created_at"))
    model = raw_msg.get("model") or None

    attachments = _extract_attachments(raw_msg)

    return Message(
        role=role,
        content=text,
        created_at=created_at,
        model=model,
        attachments=attachments,
    )


def _extract_attachments(raw_msg: dict) -> List[Attachment]:
    """Extract attachment references from a Claude message."""
    attachments: List[Attachment] = []

    for att in raw_msg.get("attachments", []):
        if isinstance(att, dict):
            name = att.get("file_name") or att.get("name", "attachment")
            file_type = att.get("file_type", "unknown")
            att_type = "image" if file_type.startswith("image/") else "file"
            ref = att.get("id", name)
            attachments.append(Attachment(type=att_type, name=name, reference=ref))

    for att in raw_msg.get("files", []):
        if isinstance(att, dict):
            name = att.get("file_name") or att.get("name", "file")
            attachments.append(
                Attachment(type="file", name=name, reference=att.get("id", name))
            )

    return attachments
