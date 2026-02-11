"""Core behavior tests for autonomous agent."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent.emotion import EmotionalState, update_emotional_state
from agent.persistence import SQLiteStore
from agent.self_modification import build_candidate_source


class EmotionTests(unittest.TestCase):
    def test_update_emotional_state_changes_values(self):
        initial = EmotionalState(valence=0.0, arousal=0.1, intimacy=0.1)
        updated = update_emotional_state(initial, "I feel great and happy today")
        self.assertGreater(updated.intimacy, initial.intimacy)
        self.assertGreaterEqual(updated.arousal, 0.0)


class PersistenceTests(unittest.TestCase):
    def test_sqlite_store_round_trip(self):
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


class SelfModificationTests(unittest.TestCase):
    def test_build_candidate_source_increments_generation(self):
        original = (
            "EVOLUTION_GENERATION = 1\n"
            "STYLE_PHRASES = [\n"
            "    \"a\",\n"
            "]\n"
        )
        candidate = build_candidate_source(original)
        self.assertIn("EVOLUTION_GENERATION = 2", candidate)
        self.assertNotEqual(candidate, original)


if __name__ == "__main__":
    unittest.main()
