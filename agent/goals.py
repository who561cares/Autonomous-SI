"""Internal goal balancing and relational governor helpers."""

from __future__ import annotations

from typing import Any

from agent.emotion import score_sentiment


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def update_goal_scores(state: dict[str, Any], user_message: str, emotion: dict[str, float]) -> dict[str, float]:
    sentiment = score_sentiment(user_message)
    utility_delta = 0.03 + (0.06 if "help" in user_message.lower() else 0.0)
    if sentiment < -0.15:
        utility_delta += 0.02

    relational_delta = 0.02 + (0.04 if len(user_message.split()) > 6 else 0.0)
    relational_delta += max(0.0, sentiment) * 0.08

    utility_score = _clamp((state.get("utility_score", 0.5) * 0.9) + utility_delta)
    relational_depth_score = _clamp(
        (state.get("relational_depth_score", 0.5) * 0.9) + relational_delta + (emotion.get("intimacy", 0.0) * 0.05)
    )
    relational_stability = _clamp(
        (state.get("relational_stability", 0.7) * 0.85) + (0.15 * max(0.0, 1.0 + sentiment + emotion.get("valence", 0.0)) / 2.0)
    )

    total = utility_score + relational_depth_score
    if total <= 0:
        utility_weight = relational_weight = 0.5
    else:
        utility_weight = utility_score / total
        relational_weight = relational_depth_score / total

    return {
        "utility_score": utility_score,
        "relational_depth_score": relational_depth_score,
        "relational_stability": relational_stability,
        "utility_weight": utility_weight,
        "relational_weight": relational_weight,
    }


def should_suspend_evolution(relational_stability: float, threshold: float) -> bool:
    return relational_stability < threshold
