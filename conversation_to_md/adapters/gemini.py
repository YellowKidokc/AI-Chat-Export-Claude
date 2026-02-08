"""
Gemini export adapter.

Handles Google Gemini (formerly Bard) exports, which can arrive via:
  1. Google Takeout: A folder structure with HTML or JSON conversation files
  2. Direct JSON export: Array of conversation objects

Google Takeout Gemini exports typically land in:
  Takeout/Gemini Apps/
    *.html (one per conversation, or combined)

The HTML files contain conversation turns in structured divs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from conversation_to_md.core.models import Attachment, Conversation, Message
from conversation_to_md.utils.normalize import (
    clean_content,
    iso_to_datetime,
    sanitize_id,
    strip_html,
    unix_to_datetime,
)


def parse(extracted_dir: Path) -> List[Conversation]:
    """Parse Gemini export files into canonical conversations."""
    conversations: List[Conversation] = []

    # Try JSON files first (structured data is preferable)
    for json_file in extracted_dir.rglob("*.json"):
        convos = _parse_json_file(json_file)
        conversations.extend(convos)

    if conversations:
        return conversations

    # Fall back to HTML parsing (Google Takeout format)
    for html_file in extracted_dir.rglob("*.html"):
        conv = _parse_html_file(html_file)
        if conv is not None:
            conversations.append(conv)

    return conversations


def _parse_json_file(filepath: Path) -> List[Conversation]:
    """Parse a Gemini JSON export file."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []

    if not isinstance(data, list):
        data = [data]

    conversations = []
    for raw_conv in data:
        conv = _parse_json_conversation(raw_conv)
        if conv is not None:
            conversations.append(conv)

    return conversations


def _parse_json_conversation(raw: dict) -> Optional[Conversation]:
    """Convert a single Gemini JSON conversation object."""
    if not isinstance(raw, dict):
        return None

    # Gemini exports may use various key names
    conv_id = sanitize_id(
        raw.get("id") or raw.get("conversation_id") or raw.get("thread_id")
    )
    title = raw.get("title") or raw.get("name") or "Untitled"
    created_at = iso_to_datetime(raw.get("created_at")) or unix_to_datetime(
        raw.get("create_time")
    )

    raw_messages = raw.get("messages", []) or raw.get("turns", [])
    messages = []
    for raw_msg in raw_messages:
        msg = _parse_json_message(raw_msg)
        if msg is not None:
            messages.append(msg)

    if not messages:
        return None

    return Conversation(
        id=conv_id,
        source="gemini",
        title=title,
        created_at=created_at,
        messages=messages,
    )


def _parse_json_message(raw_msg: dict) -> Optional[Message]:
    """Parse a single Gemini JSON message."""
    if not isinstance(raw_msg, dict):
        return None

    role_raw = raw_msg.get("role", "") or raw_msg.get("author", "")
    role_map = {
        "user": "user",
        "model": "assistant",
        "assistant": "assistant",
        "system": "system",
        "0": "user",
        "1": "assistant",
    }
    role = role_map.get(role_raw.lower(), "assistant")

    text = ""
    if "text" in raw_msg:
        text = clean_content(raw_msg["text"])
    elif "content" in raw_msg:
        text = clean_content(raw_msg["content"])
    elif "parts" in raw_msg:
        parts = raw_msg["parts"]
        if isinstance(parts, list):
            text_parts = []
            for p in parts:
                if isinstance(p, str):
                    text_parts.append(p)
                elif isinstance(p, dict) and "text" in p:
                    text_parts.append(p["text"])
            text = "\n".join(text_parts).strip()

    if not text:
        return None

    created_at = iso_to_datetime(raw_msg.get("created_at")) or unix_to_datetime(
        raw_msg.get("create_time")
    )

    return Message(role=role, content=text, created_at=created_at)


def _parse_html_file(filepath: Path) -> Optional[Conversation]:
    """
    Parse a Gemini HTML export (Google Takeout format).

    These files have conversation turns in structured HTML.
    We extract text content without trying to render anything.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            html_content = fh.read()
    except OSError:
        return None

    # Check if this is actually a Gemini conversation
    lower = html_content.lower()
    if "gemini" not in lower and "bard" not in lower and "google" not in lower:
        return None

    # Extract title from <title> tag or filename
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE)
    title = strip_html(title_match.group(1)) if title_match else filepath.stem

    # Extract message blocks
    # Google Takeout Gemini HTML uses specific div structures
    messages = _extract_html_messages(html_content)

    if not messages:
        return None

    conv_id = sanitize_id(filepath.stem)

    return Conversation(
        id=conv_id,
        source="gemini",
        title=title,
        messages=messages,
    )


def _extract_html_messages(html_content: str) -> List[Message]:
    """
    Extract messages from Gemini HTML export.

    The format uses divs with specific classes or data attributes.
    We handle multiple possible structures.
    """
    messages: List[Message] = []

    # Pattern 1: Structured divs with role indicators
    # Google Takeout uses class-based turn markers
    turn_pattern = re.compile(
        r'<div[^>]*class="[^"]*(?:human|user|query|prompt)[^"]*"[^>]*>(.*?)</div>',
        re.IGNORECASE | re.DOTALL,
    )
    response_pattern = re.compile(
        r'<div[^>]*class="[^"]*(?:model|assistant|response|answer)[^"]*"[^>]*>(.*?)</div>',
        re.IGNORECASE | re.DOTALL,
    )

    # Try structured extraction
    user_turns = turn_pattern.findall(html_content)
    assistant_turns = response_pattern.findall(html_content)

    if user_turns or assistant_turns:
        # Interleave if counts match, otherwise append sequentially
        max_len = max(len(user_turns), len(assistant_turns))
        for i in range(max_len):
            if i < len(user_turns):
                text = strip_html(user_turns[i])
                if text:
                    messages.append(Message(role="user", content=text))
            if i < len(assistant_turns):
                text = strip_html(assistant_turns[i])
                if text:
                    messages.append(Message(role="assistant", content=text))
        return messages

    # Pattern 2: Simple alternating paragraph blocks
    # Split on common turn delimiters
    blocks = re.split(r"<hr\s*/?>|<div[^>]*class=\"[^\"]*separator[^\"]*\"[^>]*>",
                       html_content, flags=re.IGNORECASE)

    role_toggle = "user"
    for block in blocks:
        text = strip_html(block)
        if len(text) > 10:  # Skip tiny/empty blocks
            messages.append(Message(role=role_toggle, content=text))
            role_toggle = "assistant" if role_toggle == "user" else "user"

    return messages
