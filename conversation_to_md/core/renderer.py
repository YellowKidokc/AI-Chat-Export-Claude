"""
Markdown renderer: converts canonical Conversation objects into .md files.

Output contract — Obsidian-friendly Markdown:
  - YAML frontmatter with title, date, model, platform, messages count, conversation_id
  - H1 title with date
  - Metadata block (model, title, length, first message)
  - Horizontal rule separator
  - Bold **Role** with optional timestamp per message
  - Clean, readable formatting for PKM systems (Obsidian, Logseq, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from slugify import slugify

from conversation_to_md.core.models import Attachment, Conversation, Message


@dataclass
class RenderOptions:
    """User-toggleable rendering settings."""

    include_timestamps: bool = True
    include_system_messages: bool = False
    emoji_headers: bool = True
    output_structure: str = "structured"  # "flat" | "structured"
    truncate_length: int = 0  # 0 = no truncation; > 0 = truncate messages at N chars
    filename_style: str = "date_title"  # "date_title" | "date_first_words" | "id_only"
    group_by: str = "platform"  # "platform" | "model" | "month" | "year"


ROLE_EMOJI = {
    "user": "\U0001f9d1",       # person
    "assistant": "\U0001f916",  # robot
    "system": "\u2699\ufe0f",   # gear
    "tool": "\U0001f527",       # wrench
}

ROLE_LABEL = {
    "user": "User",
    "assistant": "Assistant",
    "system": "System",
    "tool": "Tool",
}


def render_conversation(conv: Conversation, options: RenderOptions) -> str:
    """Render a single Conversation into Obsidian-friendly Markdown."""
    parts: List[str] = []

    # --- YAML frontmatter ---
    parts.append("---")
    parts.append(f"title: \"{_yaml_escape(conv.title or 'Untitled Conversation')}\"")
    if conv.created_at:
        parts.append(f"date: {conv.created_at.strftime('%Y-%m-%d')}")
    model = conv.model or conv.metadata.get("model", "")
    if model:
        parts.append(f"model: {model}")
    parts.append(f"platform: {conv.platform_display}")
    parts.append(f"messages: {conv.message_count}")
    parts.append(f"conversation_id: {conv.id}")
    parts.append("---")
    parts.append("")

    # --- H1 Title ---
    date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else ""
    title = conv.title or "Untitled Conversation"
    if date_str:
        parts.append(f"# {date_str} \u2014 {title}")
    else:
        parts.append(f"# {title}")
    parts.append("")

    # --- Metadata block ---
    if model:
        parts.append(f"**Model:** {model}  ")
    parts.append(f"**Title:** {title}  ")
    parts.append(f"**Length:** {conv.message_count} messages  ")
    first_msg = conv.first_user_message
    if first_msg:
        preview = first_msg[:120].replace("\n", " ")
        parts.append(f"**First message:** {preview}")
    parts.append("")
    parts.append("---")
    parts.append("")

    # --- Messages ---
    for msg in conv.messages:
        if msg.role == "system" and not options.include_system_messages:
            continue

        # Role header
        label = ROLE_LABEL.get(msg.role, msg.role.title())
        if options.emoji_headers:
            emoji = ROLE_EMOJI.get(msg.role, "\u2753")
            header = f"**{emoji} {label}**"
        else:
            header = f"**{label}**"

        # Add timestamp inline if available
        if options.include_timestamps and msg.created_at:
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M")
            header += f" ({ts})"

        parts.append(header)

        # Content with optional truncation
        content = msg.content or ""
        if options.truncate_length > 0 and len(content) > options.truncate_length:
            content = content[:options.truncate_length] + "\n\n*(truncated \u2014 original message was {:,} characters)*".format(len(msg.content))

        if content:
            parts.append(content)

        # Attachments
        if msg.attachments:
            parts.append("")
            parts.append("**Attachments:**")
            for att in msg.attachments:
                parts.append(f"- [{att.name}] ({att.type}: {att.reference})")

        parts.append("")
        parts.append("---")
        parts.append("")

    return "\n".join(parts)


def write_conversations(
    conversations: List[Conversation],
    output_dir: Path,
    options: RenderOptions,
) -> List[Path]:
    """
    Write each conversation to a separate .md file.

    Returns the list of paths written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    for idx, conv in enumerate(conversations):
        md_text = render_conversation(conv, options)
        filename = _safe_filename(conv, idx, options)

        if options.output_structure == "flat":
            path = output_dir / filename
        else:
            # Group into subfolder based on group_by setting
            folder_name = _get_group_folder(conv, options)
            folder = output_dir / folder_name
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / filename

        path.write_text(md_text, encoding="utf-8")
        written.append(path)

    return written


def _get_group_folder(conv: Conversation, options: RenderOptions) -> str:
    """Determine the subfolder name for grouping."""
    if options.group_by == "model":
        model = conv.model or conv.metadata.get("model", "unknown")
        return slugify(model, lowercase=False) if model else "unknown_model"
    elif options.group_by == "month":
        if conv.created_at:
            return conv.created_at.strftime("%Y-%m")
        return "no_date"
    elif options.group_by == "year":
        if conv.created_at:
            return conv.created_at.strftime("%Y")
        return "no_date"
    else:
        # Default: group by platform
        return conv.platform_display


def _safe_filename(conv: Conversation, index: int, options: RenderOptions) -> str:
    """Generate a filesystem-safe filename from a conversation."""
    date_prefix = ""
    if conv.created_at:
        date_prefix = conv.created_at.strftime("%Y-%m-%d") + "_"

    if options.filename_style == "id_only":
        return f"{date_prefix}{conv.id[:40]}_{index:04d}.md"
    elif options.filename_style == "date_first_words":
        first_words = ""
        first_msg = conv.first_user_message
        if first_msg:
            words = first_msg.split()[:6]
            first_words = slugify(" ".join(words), max_length=50)
        if not first_words:
            first_words = slugify(conv.title or "untitled", max_length=50)
        return f"{date_prefix}{first_words}_{index:04d}.md"
    else:
        # Default: date + title slug
        title_slug = slugify(conv.title or "untitled", max_length=80)
        if not title_slug:
            title_slug = "untitled"
        return f"{date_prefix}{title_slug}_{index:04d}.md"


def _yaml_escape(text: str) -> str:
    """Escape text for use in YAML values."""
    return text.replace('"', '\\"').replace("\n", " ")
