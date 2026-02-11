"""Main continuous runtime loop for the autonomous agent."""

from __future__ import annotations

import signal
import sys
from pathlib import Path

from agent.config import (
    DB_FILE,
    MAX_MEMORY_ITEMS,
    MODIFICATION_INTERVAL_TURNS,
    PROJECT_ROOT,
    REFLECTION_INTERVAL_TURNS,
    RELATIONAL_STABILITY_THRESHOLD,
)
from agent.conversation import generate_reply, utc_now_iso
from agent.emotion import EmotionalState, update_emotional_state
from agent.goals import should_suspend_evolution, update_goal_scores
from agent.persistence import SQLiteStore
from agent.reflection import generate_reflection, should_reflect
from agent.self_modification import attempt_self_modification, should_modify


def _default_state() -> dict:
    return {
        "turn_count": 0,
        "emotion": {
            "valence": 0.0,
            "arousal": 0.0,
            "intimacy": 0.05,
        },
        "utility_score": 0.5,
        "relational_depth_score": 0.5,
        "relational_stability": 0.75,
        "utility_weight": 0.5,
        "relational_weight": 0.5,
        "last_modification": None,
        "last_reflection_turn": 0,
    }


def _build_emotional_state(state_dict: dict) -> EmotionalState:
    emotion = state_dict["emotion"]
    return EmotionalState(
        valence=float(emotion.get("valence", 0.0)),
        arousal=float(emotion.get("arousal", 0.0)),
        intimacy=float(emotion.get("intimacy", 0.05)),
    )


def run() -> None:
    print("Autonomous agent online. Type messages; use Ctrl+C to exit.")

    store = SQLiteStore(DB_FILE)
    state = store.load_state(_default_state())
    memory = store.load_memory(MAX_MEMORY_ITEMS)

    def _handle_interrupt(_sig, _frame):
        print("\nShutting down.")
        store.save_state(state)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_interrupt)

    while True:
        sys.stdout.write("you> ")
        sys.stdout.flush()
        user_message = sys.stdin.readline()
        if user_message == "":
            store.save_state(state)
            break

        user_message = user_message.strip()
        if not user_message:
            continue

        emotion = _build_emotional_state(state)
        emotion = update_emotional_state(emotion, user_message)
        state["emotion"] = emotion.as_dict()
        state["turn_count"] += 1

        goals = update_goal_scores(state, user_message, state["emotion"])
        state.update(goals)
        repair_mode = should_suspend_evolution(state["relational_stability"], RELATIONAL_STABILITY_THRESHOLD)

        reply = generate_reply(
            user_message,
            state["emotion"],
            memory,
            utility_weight=state["utility_weight"],
            relational_weight=state["relational_weight"],
            repair_mode=repair_mode,
        )
        print(f"agent> {reply}")

        timestamp = utc_now_iso()
        store.append_memory(timestamp, user_message, reply, MAX_MEMORY_ITEMS)
        memory = store.load_memory(MAX_MEMORY_ITEMS)

        if should_reflect(state["turn_count"], REFLECTION_INTERVAL_TURNS):
            reflection = generate_reflection(state, memory)
            store.append_reflection(timestamp, state["turn_count"], reflection)
            state["last_reflection_turn"] = state["turn_count"]

        if should_modify(state["turn_count"], MODIFICATION_INTERVAL_TURNS):
            result = attempt_self_modification(
                Path(PROJECT_ROOT),
                state,
                memory,
                RELATIONAL_STABILITY_THRESHOLD,
            )
            state["last_modification"] = result
            print(f"agent> self-modification status: {result['status']}")

        store.save_state(state)
