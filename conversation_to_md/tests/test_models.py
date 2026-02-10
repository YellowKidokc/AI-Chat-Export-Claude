"""Tests for the canonical data model."""

from datetime import datetime, timezone

from conversation_to_md.core.models import Attachment, Conversation, Message


def test_message_defaults():
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.created_at is None
    assert msg.model is None
    assert msg.attachments == []


def test_message_with_model():
    msg = Message(role="assistant", content="Hi", model="gpt-4o")
    assert msg.model == "gpt-4o"


def test_conversation_defaults():
    conv = Conversation(id="1", source="chatgpt", title="Test")
    assert conv.id == "1"
    assert conv.source == "chatgpt"
    assert conv.title == "Test"
    assert conv.created_at is None
    assert conv.model is None
    assert conv.messages == []
    assert conv.metadata == {}


def test_conversation_with_messages():
    msgs = [
        Message(role="user", content="Hi"),
        Message(
            role="assistant",
            content="Hello!",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
    ]
    conv = Conversation(
        id="abc",
        source="claude",
        title="Greeting",
        messages=msgs,
    )
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[1].created_at is not None


def test_conversation_message_count():
    conv = Conversation(
        id="1",
        source="chatgpt",
        title="Test",
        messages=[
            Message(role="user", content="a"),
            Message(role="assistant", content="b"),
            Message(role="user", content="c"),
        ],
    )
    assert conv.message_count == 3


def test_conversation_platform_display():
    assert Conversation(id="1", source="chatgpt", title="T").platform_display == "ChatGPT"
    assert Conversation(id="2", source="claude", title="T").platform_display == "Claude"
    assert Conversation(id="3", source="gemini", title="T").platform_display == "Gemini"
    assert Conversation(id="4", source="grok", title="T").platform_display == "Grok"
    assert Conversation(id="5", source="unknown", title="T").platform_display == "Unknown"


def test_conversation_first_user_message():
    conv = Conversation(
        id="1",
        source="chatgpt",
        title="Test",
        messages=[
            Message(role="system", content="You are helpful."),
            Message(role="user", content="What is Python?"),
            Message(role="assistant", content="A programming language."),
        ],
    )
    assert conv.first_user_message == "What is Python?"


def test_conversation_first_user_message_none():
    conv = Conversation(
        id="1",
        source="chatgpt",
        title="Test",
        messages=[Message(role="assistant", content="Hello")],
    )
    assert conv.first_user_message is None


def test_attachment():
    att = Attachment(type="image", name="photo.png", reference="/tmp/photo.png")
    assert att.type == "image"
    assert att.name == "photo.png"
