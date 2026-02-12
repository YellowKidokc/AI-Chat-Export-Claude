"""Tests for the CSV/Excel exporter and statistics."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from conversation_to_md.core.exporter import (
    conversations_to_dataframe,
    export_csv,
    export_excel,
    get_stats,
)
from conversation_to_md.core.models import Conversation, Message


def _make_conversations():
    return [
        Conversation(
            id="conv-1",
            source="chatgpt",
            title="Math Chat",
            created_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            model="gpt-4o",
            messages=[
                Message(
                    role="user",
                    content="What is 2+2?",
                    created_at=datetime(2025, 1, 15, 10, 0, 1, tzinfo=timezone.utc),
                ),
                Message(
                    role="assistant",
                    content="4",
                    created_at=datetime(2025, 1, 15, 10, 0, 5, tzinfo=timezone.utc),
                    model="gpt-4o",
                ),
            ],
        ),
        Conversation(
            id="conv-2",
            source="claude",
            title="Python Help",
            created_at=datetime(2025, 2, 10, 14, 0, 0, tzinfo=timezone.utc),
            model="claude-3-opus",
            messages=[
                Message(role="user", content="How to read a file?"),
                Message(role="assistant", content="Use open() with a context manager."),
            ],
        ),
    ]


def test_conversations_to_dataframe():
    convos = _make_conversations()
    df = conversations_to_dataframe(convos)

    assert len(df) == 4  # 2 + 2 messages
    assert list(df.columns) == [
        "timestamp", "platform", "model", "conversation_id",
        "conversation_title", "message_number", "role", "content",
        "content_length", "truncated",
    ]
    assert df.iloc[0]["platform"] == "ChatGPT"
    assert df.iloc[0]["role"] == "user"
    assert df.iloc[0]["content"] == "What is 2+2?"
    assert df.iloc[2]["platform"] == "Claude"


def test_dataframe_truncation():
    convos = [
        Conversation(
            id="1",
            source="chatgpt",
            title="T",
            messages=[Message(role="user", content="A" * 10000)],
        )
    ]
    df = conversations_to_dataframe(convos, truncate_length=100)
    assert len(df) == 1
    assert len(df.iloc[0]["content"]) == 100
    assert df.iloc[0]["truncated"] == True
    assert df.iloc[0]["content_length"] == 10000


def test_export_csv():
    convos = _make_conversations()
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "test.csv"
        result = export_csv(convos, csv_path)
        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "Math Chat" in content
        assert "Python Help" in content


def test_export_excel():
    convos = _make_conversations()
    with tempfile.TemporaryDirectory() as tmp:
        xlsx_path = Path(tmp) / "test.xlsx"
        result = export_excel(convos, xlsx_path)
        assert result.exists()
        assert result.stat().st_size > 0


def test_get_stats():
    convos = _make_conversations()
    stats = get_stats(convos)

    assert stats["total_conversations"] == 2
    assert stats["total_messages"] == 4
    assert stats["total_characters"] > 0
    assert "ChatGPT" in stats["platforms"]
    assert "Claude" in stats["platforms"]
    assert stats["platforms"]["ChatGPT"] == 1
    assert stats["platforms"]["Claude"] == 1
    assert "gpt-4o" in stats["models"]
    assert "claude-3-opus" in stats["models"]
    assert stats["date_range_start"].year == 2025
    assert stats["date_range_start"].month == 1
    assert stats["date_range_end"].month == 2
