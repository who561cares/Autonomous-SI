"""Emotional and intimacy state updates."""

from __future__ import annotations

from dataclasses import dataclass

from agent.adaptation_profile import ACTIVE_PROFILE, AdaptationProfile

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


def update_emotional_state(
    state: EmotionalState,
    message: str,
    profile: AdaptationProfile = ACTIVE_PROFILE,
) -> EmotionalState:
    sentiment = score_sentiment(message)
    length_factor = min(len(message) / 140.0, 1.0)

    next_valence = _clamp((state.valence * profile.valence_decay) + (sentiment * profile.valence_sentiment_gain))
    next_arousal = _clamp(
        (state.arousal * profile.arousal_decay) + (length_factor * profile.arousal_length_gain),
        0.0,
        1.0,
    )

    intimacy_delta = profile.intimacy_base_gain
    if len(message.split()) > 6:
        intimacy_delta += profile.intimacy_long_message_bonus
    if sentiment < -0.2:
        intimacy_delta -= profile.intimacy_negative_penalty
    next_intimacy = _clamp(state.intimacy + intimacy_delta, 0.0, 1.0)

    return EmotionalState(next_valence, next_arousal, next_intimacy)
