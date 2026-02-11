"""Self-modification logic with test-and-rollback safety."""

from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from agent.config import CHANGE_LOG_FILE, MAX_CODE_REVISIONS, TARGET_SELF_MOD_FILE


GEN_RE = re.compile(r"^EVOLUTION_GENERATION\s*=\s*(\d+)\s*$", re.MULTILINE)
PHRASE_BLOCK_RE = re.compile(r"STYLE_PHRASES\s*=\s*\[(?P<body>.*?)\]\n", re.DOTALL)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_log(message: str) -> None:
    CHANGE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHANGE_LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{_timestamp()}] {message}\n")


def should_modify(turn_count: int, emotional_state: dict[str, float], interval_turns: int = 6) -> bool:
    if turn_count <= 0:
        return False
    if turn_count % interval_turns == 0:
        return True
    if emotional_state["valence"] < -0.45:
        return True
    return False


def _next_phrase(generation: int) -> str:
    phrase_bank = [
        "I want to become more helpful each turn.",
        "Your feedback informs my next revision.",
        "I can evolve safely through testing.",
        "I keep improving while preserving stability.",
        "I adapt to you with deliberate care.",
    ]
    return phrase_bank[generation % len(phrase_bank)]


def build_candidate_source(existing_source: str) -> str:
    match = GEN_RE.search(existing_source)
    if not match:
        raise ValueError("Missing EVOLUTION_GENERATION constant in response profile.")

    current_generation = int(match.group(1))
    next_generation = min(current_generation + 1, MAX_CODE_REVISIONS)
    updated = GEN_RE.sub(f"EVOLUTION_GENERATION = {next_generation}", existing_source, count=1)

    phrase_match = PHRASE_BLOCK_RE.search(updated)
    if not phrase_match:
        raise ValueError("Missing STYLE_PHRASES block in response profile.")

    candidate_phrase = _next_phrase(next_generation)
    body = phrase_match.group("body")
    if candidate_phrase not in body:
        insertion = f'    "{candidate_phrase}",\n'
        new_body = body + insertion
        updated = (
            updated[: phrase_match.start("body")]
            + new_body
            + updated[phrase_match.end("body") :]
        )

    return updated


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


def attempt_self_modification(project_root: Path) -> dict:
    target = TARGET_SELF_MOD_FILE
    if not target.exists():
        reason = f"target file not found: {target}"
        _append_log(f"SKIP {reason}")
        return {"changed": False, "status": "skipped", "reason": reason}

    original_source = target.read_text(encoding="utf-8")
    candidate_source = build_candidate_source(original_source)
    if candidate_source == original_source:
        _append_log("SKIP candidate source equals original")
        return {"changed": False, "status": "skipped", "reason": "no-op"}

    backup_path = target.with_suffix(".py.bak")
    shutil.copy2(target, backup_path)
    target.write_text(candidate_source, encoding="utf-8")

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

    if passed:
        backup_path.unlink(missing_ok=True)
        _append_log("APPLY self-modification accepted after tests passed")
        _append_log(diff)
        _append_log(output.strip())
        return {
            "changed": True,
            "status": "applied",
            "tests_output": output,
            "diff": diff,
        }

    shutil.copy2(backup_path, target)
    backup_path.unlink(missing_ok=True)
    _append_log("ROLLBACK self-modification rejected after test failure")
    _append_log(diff)
    _append_log(output.strip())
    return {
        "changed": False,
        "status": "rolled_back",
        "tests_output": output,
        "diff": diff,
    }
