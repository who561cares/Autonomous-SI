# Autonomous SI Agent (Termux-ready)

A self-modifying conversational agent that runs entirely in a local terminal using Python standard library only.

## Features

- Continuous control loop in terminal
- Local persistent memory and runtime state in SQLite (`data/agent.sqlite3`)
- Local emotional/intimacy state persisted in SQLite
- Autonomous self-modification of Python source code
- Automated test gate after each code modification
- Automatic rollback on test failure
- Change logging (`logs/changes.log`)
- No confirmation gates in self-modification flow

## Run

```bash
python3 run_agent.py
```

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Termux notes

- Works with default Python package in Termux.
- Uses only `python3`, `sqlite3`, and standard library modules.
