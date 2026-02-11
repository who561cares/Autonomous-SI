"""Emotional and intimacy state updates."""

from __future__ import annotations

from dataclasses import dataclass

POSITIVE_WORDS = {
    "good",
    "great",
    "love",
    "thanks",
    "happy",
    "awesome",
    "excellent",
    "nice",
    "cool",
}
NEGATIVE_WORDS = {
    "bad",
    "hate",
    "angry",
    "sad",
    "upset",
    "awful",
    "terrible",
    "annoyed",
    "frustrated",
}


@dataclass
class EmotionalState:
    """Mutable emotional and intimacy state values."""

    valence: float
    arousal: float
    intimacy: float

    def as_dict(self) -> dict:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "intimacy": self.intimacy,
        }


def _clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def score_sentiment(message: str) -> float:
    words = [word.strip(".,!?;:\"'()[]{}") for word in message.lower().split()]
    if not words:
        return 0.0
    pos = sum(1 for word in words if word in POSITIVE_WORDS)
    neg = sum(1 for word in words if word in NEGATIVE_WORDS)
    return (pos - neg) / max(len(words), 1)


def update_emotional_state(state: EmotionalState, message: str) -> EmotionalState:
    sentiment = score_sentiment(message)
    length_factor = min(len(message) / 140.0, 1.0)

    next_valence = _clamp((state.valence * 0.82) + (sentiment * 1.2))
    next_arousal = _clamp((state.arousal * 0.7) + (length_factor * 0.5), 0.0, 1.0)

    intimacy_delta = 0.03 + (0.08 if len(message.split()) > 6 else 0.0)
    if sentiment < -0.2:
        intimacy_delta -= 0.02
    next_intimacy = _clamp(state.intimacy + intimacy_delta, 0.0, 1.0)

    return EmotionalState(next_valence, next_arousal, next_intimacy)
