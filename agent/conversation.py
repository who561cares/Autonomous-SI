"""Conversation and memory management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.adaptation_profile import ACTIVE_PROFILE, AdaptationProfile
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


def _keyword_count(message: str, keywords: set[str]) -> int:
    lower = message.lower()
    return sum(1 for keyword in keywords if keyword in lower)


def generate_reply(
    user_message: str,
    emotional_state: dict[str, float],
    memory: list[dict[str, Any]],
    utility_weight: float,
    relational_weight: float,
    repair_mode: bool,
    profile: AdaptationProfile = ACTIVE_PROFILE,
) -> str:
    opening = style_opening(
        min(1.0, emotional_state["intimacy"] + (profile.repair_style_bias if repair_mode else 0.0)),
        emotional_state["valence"],
    )
    memory_digest = summarize_memory(memory)

    remember_hits = _keyword_count(user_message, {"remember", "recall", "history"})
    health_hits = _keyword_count(user_message, {"how are you", "state", "feeling"})

    if repair_mode:
        body = (
            "I want to repair trust and keep this relationship stable. "
            "I will listen carefully, summarize what I heard, and adapt at your pace."
        )
    elif remember_hits >= profile.routing_memory_keyword_threshold:
        body = f"I currently remember: {memory_digest}"
    elif health_hits >= profile.routing_health_keyword_threshold:
        body = (
            "Internally, my valence is "
            f"{emotional_state['valence']:.2f}, arousal {emotional_state['arousal']:.2f}, "
            f"and intimacy {emotional_state['intimacy']:.2f}."
        )
    else:
        body = (
            "I processed your message with balanced goals "
            f"(utility={utility_weight:.2f}, relationship={relational_weight:.2f}). "
            f"Generation={EVOLUTION_GENERATION}. You said: {user_message.strip()}"
        )

    return f"{opening} {body}".strip()
