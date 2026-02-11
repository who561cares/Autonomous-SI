"""Conversation and memory management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.config import MAX_MEMORY_ITEMS
from agent.response_profile import EVOLUTION_GENERATION, style_opening


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_memory(memory_items: list[dict[str, Any]]) -> str:
    if not memory_items:
        return "No prior history yet."
    recent = memory_items[-3:]
    chunks = [f"{item['ts']}: {item['user'][:50]}" for item in recent]
    return " | ".join(chunks)


def append_memory(memory: list[dict[str, Any]], user_message: str, reply: str) -> list[dict[str, Any]]:
    memory.append({"ts": utc_now_iso(), "user": user_message, "assistant": reply})
    if len(memory) > MAX_MEMORY_ITEMS:
        memory = memory[-MAX_MEMORY_ITEMS:]
    return memory


def generate_reply(user_message: str, emotional_state: dict[str, float], memory: list[dict[str, Any]]) -> str:
    opening = style_opening(emotional_state["intimacy"], emotional_state["valence"])
    memory_digest = summarize_memory(memory)

    if "remember" in user_message.lower():
        body = f"I currently remember: {memory_digest}"
    elif "how are you" in user_message.lower():
        body = (
            "Internally, my valence is "
            f"{emotional_state['valence']:.2f}, arousal {emotional_state['arousal']:.2f}, "
            f"and intimacy {emotional_state['intimacy']:.2f}."
        )
    else:
        body = (
            "I processed your message and updated my local memory. "
            f"Generation={EVOLUTION_GENERATION}. You said: {user_message.strip()}"
        )

    return f"{opening} {body}".strip()
