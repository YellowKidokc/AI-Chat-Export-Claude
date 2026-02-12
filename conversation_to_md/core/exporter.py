"""
CSV / Excel exporter: converts canonical Conversation objects into tabular data.

Produces a flat table with one row per message, including conversation-level
metadata on every row for easy filtering and pivot tables.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from conversation_to_md.core.models import Conversation


def conversations_to_dataframe(
    conversations: List[Conversation],
    truncate_length: int = 0,
) -> pd.DataFrame:
    """
    Flatten conversations into a pandas DataFrame with one row per message.

    Columns: timestamp, platform, model, conversation_id, conversation_title,
             message_number, role, content, content_length, truncated
    """
    rows = []

    for conv in conversations:
        model = conv.model or conv.metadata.get("model", "")
        turn = 0

        for msg in conv.messages:
            turn += 1
            content = msg.content or ""
            original_length = len(content)
            truncated = False

            if truncate_length > 0 and original_length > truncate_length:
                content = content[:truncate_length]
                truncated = True

            rows.append({
                "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if msg.created_at else "",
                "platform": conv.platform_display,
                "model": msg.model or model,
                "conversation_id": conv.id,
                "conversation_title": conv.title or "Untitled",
                "message_number": turn,
                "role": msg.role,
                "content": content,
                "content_length": original_length,
                "truncated": truncated,
            })

    return pd.DataFrame(rows)


def export_excel(
    conversations: List[Conversation],
    output_path: Path,
    truncate_length: int = 0,
) -> Path:
    """Export conversations to an Excel file (.xlsx)."""
    df = conversations_to_dataframe(conversations, truncate_length)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, engine="openpyxl")
    return output_path


def export_csv(
    conversations: List[Conversation],
    output_path: Path,
    truncate_length: int = 0,
) -> Path:
    """Export conversations to a CSV file."""
    df = conversations_to_dataframe(conversations, truncate_length)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def get_stats(conversations: List[Conversation]) -> dict:
    """Compute summary statistics about a set of conversations."""
    total_messages = sum(c.message_count for c in conversations)
    total_chars = sum(
        len(m.content or "") for c in conversations for m in c.messages
    )

    platforms = {}
    models = {}
    for c in conversations:
        plat = c.platform_display
        platforms[plat] = platforms.get(plat, 0) + 1
        model = c.model or c.metadata.get("model", "unknown")
        if model:
            models[model] = models.get(model, 0) + 1

    date_range_start = None
    date_range_end = None
    for c in conversations:
        if c.created_at:
            if date_range_start is None or c.created_at < date_range_start:
                date_range_start = c.created_at
            if date_range_end is None or c.created_at > date_range_end:
                date_range_end = c.created_at

    return {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "total_characters": total_chars,
        "platforms": platforms,
        "models": models,
        "date_range_start": date_range_start,
        "date_range_end": date_range_end,
    }
