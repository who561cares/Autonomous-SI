"""Core behavior tests for autonomous agent."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent.emotion import EmotionalState, update_emotional_state
from agent.goals import should_suspend_evolution, update_goal_scores
from agent.persistence import SQLiteStore
from agent.reflection import generate_reflection
from agent.self_modification import _set_profile_updates, generate_change_proposal


class EmotionTests(unittest.TestCase):
    def test_update_emotional_state_changes_values(self):
        initial = EmotionalState(valence=0.0, arousal=0.1, intimacy=0.1)
        updated = update_emotional_state(initial, "I feel great and happy today")
        self.assertGreater(updated.intimacy, initial.intimacy)
        self.assertGreaterEqual(updated.arousal, 0.0)


class PersistenceTests(unittest.TestCase):
    def test_sqlite_store_round_trip_and_reflections(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agent.sqlite3"
            store = SQLiteStore(db_path)

            baseline = {
                "turn_count": 1,
                "emotion": {"valence": 0.1, "arousal": 0.2, "intimacy": 0.3},
                "last_modification": None,
            }
            store.save_state(baseline)
            loaded_state = store.load_state({})
            self.assertEqual(loaded_state["turn_count"], 1)

            store.append_memory("2026-01-01T00:00:00+00:00", "hello", "hi", max_items=10)
            memory = store.load_memory(limit=10)
            self.assertEqual(len(memory), 1)
            self.assertEqual(memory[0]["user"], "hello")

            reflection = {"summary": {"utility_score": 0.5}}
            store.append_reflection("2026-01-01T00:00:00+00:00", 1, reflection)
            reflections = store.load_reflections(limit=5)
            self.assertEqual(len(reflections), 1)
            self.assertEqual(reflections[0]["turn"], 1)


class GoalAndReflectionTests(unittest.TestCase):
    def test_goal_balancing_and_reflection_fields(self):
        state = {
            "utility_score": 0.4,
            "relational_depth_score": 0.6,
            "relational_stability": 0.7,
            "turn_count": 4,
        }
        goals = update_goal_scores(state, "please help me remember this context", {"valence": 0.2, "intimacy": 0.5})
        self.assertGreaterEqual(goals["utility_weight"], 0.0)
        self.assertGreaterEqual(goals["relational_weight"], 0.0)

        reflection = generate_reflection({**state, **goals}, [{"user": "thanks for helping", "assistant": "ok"}])
        self.assertIn("summary", reflection)
        self.assertIn("assessment", reflection)


class SelfModificationTests(unittest.TestCase):
    def test_model_driven_updates_change_profile_source(self):
        source = (
            "from dataclasses import dataclass\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class AdaptationProfile:\n"
            "    valence_decay: float\n"
            "\n"
            "ACTIVE_PROFILE = AdaptationProfile(valence_decay=0.8, repair_style_bias=0.2)\n"
        )
        candidate = _set_profile_updates(source, {"repair_style_bias": 0.33})
        self.assertIn("repair_style_bias=0.33", candidate)

    def test_generate_change_proposal_and_relational_governor(self):
        proposal = generate_change_proposal(
            {"utility_score": 0.4, "relational_depth_score": 0.5, "relational_stability": 0.7},
            [{"user": "please help me with this long message", "assistant": "ok"}],
        )
        self.assertIn("updates", proposal)
        self.assertFalse(should_suspend_evolution(0.7, 0.45))
        self.assertTrue(should_suspend_evolution(0.2, 0.45))


if __name__ == "__main__":
    unittest.main()
