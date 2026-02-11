"""Self-modification logic with model-driven proposals and safe apply/rollback."""

from __future__ import annotations

import ast
import difflib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.config import CHANGE_LOG_FILE, TARGET_SELF_MOD_FILE
from agent.goals import should_suspend_evolution

PROFILE_FILE = TARGET_SELF_MOD_FILE.parent / "adaptation_profile.py"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_log(message: str) -> None:
    CHANGE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHANGE_LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{_timestamp()}] {message}\n")


def should_modify(turn_count: int, interval_turns: int = 6) -> bool:
    return turn_count > 0 and turn_count % interval_turns == 0


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def generate_change_proposal(state: dict[str, Any], memory: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a model-style proposal from interaction metrics."""
    recent = memory[-6:]
    user_lengths = [len(item["user"].split()) for item in recent] or [5]
    avg_words = sum(user_lengths) / len(user_lengths)

    relational_stability = float(state.get("relational_stability", 0.7))
    utility_score = float(state.get("utility_score", 0.5))
    relational_depth_score = float(state.get("relational_depth_score", 0.5))

    updates = {
        "intimacy_base_gain": _bounded(0.025 + (0.015 if avg_words > 9 else 0.0), 0.01, 0.07),
        "routing_memory_keyword_threshold": 1,
        "routing_health_keyword_threshold": 1,
        "repair_style_bias": _bounded(0.2 + ((0.6 - relational_stability) * 0.35), 0.1, 0.35),
        "valence_sentiment_gain": _bounded(1.1 + ((0.6 - utility_score) * 0.5), 0.8, 1.6),
        "intimacy_negative_penalty": _bounded(0.02 + ((0.55 - relational_depth_score) * 0.03), 0.005, 0.04),
    }

    return {
        "reasoning": {
            "relational_stability": relational_stability,
            "utility_score": utility_score,
            "relational_depth_score": relational_depth_score,
            "avg_recent_user_words": avg_words,
        },
        "target_file": str(PROFILE_FILE),
        "updates": updates,
    }


def _set_profile_updates(source: str, updates: dict[str, Any]) -> str:
    tree = ast.parse(source)
    replacement_map = {k: ast.Constant(v) for k, v in updates.items()}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ACTIVE_PROFILE" for t in node.targets):
            if isinstance(node.value, ast.Call):
                for keyword in node.value.keywords:
                    if keyword.arg in replacement_map:
                        keyword.value = replacement_map[keyword.arg]

    return ast.unparse(tree) + "\n"


def _run_tests(project_root: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    cmd = ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    proc = subprocess.run(
        cmd,
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode == 0, proc.stdout


def attempt_self_modification(
    project_root: Path,
    state: dict[str, Any],
    memory: list[dict[str, Any]],
    relational_threshold: float,
) -> dict[str, Any]:
    if should_suspend_evolution(float(state.get("relational_stability", 0.0)), relational_threshold):
        reason = "relational stability below threshold; evolution suspended"
        _append_log(f"SUSPEND {reason}")
        return {"changed": False, "status": "suspended", "reason": reason}

    target = PROFILE_FILE
    if not target.exists():
        reason = f"target file not found: {target}"
        _append_log(f"SKIP {reason}")
        return {"changed": False, "status": "skipped", "reason": reason}

    proposal = generate_change_proposal(state, memory)
    original_source = target.read_text(encoding="utf-8")
    candidate_source = _set_profile_updates(original_source, proposal["updates"])
    if candidate_source == original_source:
        _append_log("SKIP candidate source equals original")
        return {"changed": False, "status": "skipped", "reason": "no-op", "proposal": proposal}

    temp_path = target.with_suffix(".py.tmp")
    backup_path = target.with_suffix(".py.bak")
    temp_path.write_text(candidate_source, encoding="utf-8")
    shutil.copy2(target, backup_path)
    shutil.copy2(temp_path, target)

    passed, output = _run_tests(project_root)
    diff = "\n".join(
        difflib.unified_diff(
            original_source.splitlines(),
            candidate_source.splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )

    _append_log(f"PROPOSAL {json.dumps(proposal, ensure_ascii=False)}")
    _append_log("TEST_OUTPUT_START")
    _append_log(output.strip())
    _append_log("TEST_OUTPUT_END")

    if passed:
        temp_path.unlink(missing_ok=True)
        backup_path.unlink(missing_ok=True)
        _append_log("APPLY model-driven self-modification accepted after tests passed")
        _append_log(diff)
        return {
            "changed": True,
            "status": "applied",
            "proposal": proposal,
            "tests_output": output,
            "diff": diff,
        }

    shutil.copy2(backup_path, target)
    temp_path.unlink(missing_ok=True)
    backup_path.unlink(missing_ok=True)
    _append_log("ROLLBACK model-driven self-modification rejected after test failure")
    _append_log(diff)
    return {
        "changed": False,
        "status": "rolled_back",
        "proposal": proposal,
        "tests_output": output,
        "diff": diff,
    }
