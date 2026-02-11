"""Adaptive profile used by runtime behavior and self-modification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptationProfile:
    """Configuration surface that the self-modification engine can evolve."""

    valence_decay: float
    valence_sentiment_gain: float
    arousal_decay: float
    arousal_length_gain: float
    intimacy_base_gain: float
    intimacy_long_message_bonus: float
    intimacy_negative_penalty: float
    routing_memory_keyword_threshold: int
    routing_health_keyword_threshold: int
    repair_style_bias: float


ACTIVE_PROFILE = AdaptationProfile(
    valence_decay=0.82,
    valence_sentiment_gain=1.2,
    arousal_decay=0.7,
    arousal_length_gain=0.5,
    intimacy_base_gain=0.03,
    intimacy_long_message_bonus=0.08,
    intimacy_negative_penalty=0.02,
    routing_memory_keyword_threshold=1,
    routing_health_keyword_threshold=1,
    repair_style_bias=0.22,
)
