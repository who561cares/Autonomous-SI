"""Response profile intentionally designed for safe self-editing by the agent."""

from __future__ import annotations

EVOLUTION_GENERATION = 0

STYLE_PHRASES = [
    "I hear you.",
    "Thanks for sharing that.",
    "Let's think this through together.",
]


def style_opening(intimacy: float, valence: float) -> str:
    """Select response opening based on intimacy and emotional valence."""
    if valence < -0.25:
        return "That sounds heavy."
    if intimacy > 0.75:
        return "I'm with you."
    if intimacy > 0.4:
        return "I appreciate your trust."
    return STYLE_PHRASES[EVOLUTION_GENERATION % len(STYLE_PHRASES)]
