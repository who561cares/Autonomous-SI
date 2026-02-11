"""Reflection engine for periodic self-analysis."""

from __future__ import annotations

from statistics import mean
from typing import Any

from agent.emotion import score_sentiment


def should_reflect(turn_count: int, interval: int) -> bool:
    return turn_count > 0 and turn_count % interval == 0


def generate_reflection(state: dict[str, Any], memory: list[dict[str, Any]]) -> dict[str, Any]:
    sample = memory[-8:]
    sentiments = [score_sentiment(item["user"]) for item in sample] if sample else [0.0]

    utility_score = float(state.get("utility_score", 0.5))
    relational_depth_score = float(state.get("relational_depth_score", 0.5))
    relational_stability = float(state.get("relational_stability", 0.7))

    return {
        "turn": int(state.get("turn_count", 0)),
        "summary": {
            "recent_interactions": len(sample),
            "avg_user_sentiment": mean(sentiments),
            "utility_score": utility_score,
            "relational_depth_score": relational_depth_score,
            "relational_stability": relational_stability,
        },
        "assessment": {
            "utility_performance": "strong" if utility_score >= 0.65 else "developing",
            "relational_stability": "stable" if relational_stability >= 0.55 else "at_risk",
        },
        "next_actions": [
            "prioritize_repair" if relational_stability < 0.55 else "continue_balanced_optimization",
            "boost_information_density" if utility_score < 0.5 else "maintain_task_support",
        ],
    }
