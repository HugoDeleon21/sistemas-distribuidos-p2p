# AI Agent Guide for `sistemas-distribuidos-p2p`

## What this repository is

A Python prototype for a simple master/worker distributed system.
- `master.py`: TCP-based Master server on port `5000`.
- `worker.py`: Worker client that connects to the Master and can trigger a UDP-based election to become Master if the current Master fails.

## Key architecture

- Master listens on `HOST='0.0.0.0'` and `PORT=5000`.
- Worker uses `MASTER_HOST`, `MASTER_PORT`, and a UDP election port `5001`.
- Communication is newline-delimited JSON over TCP.
- Master tracks workers in `workers_na_farm` and uses a `queue.Queue()` of mocked tasks.
- Worker handles tasks of type `QUERY`, reports `STATUS`, and receives an `ACK`.
- If the worker loses connection, it runs a bully-style election using disk space and UUID tie-breakers.

## Primary files

- `master.py`
  - Accepts worker connections and processes two main flows:
    - Worker presentation (`WORKER`: `ALIVE`) -> assign task or `NO_TASK`
    - Worker status report (`STATUS`: `OK` or `NOK`) -> send final `ACK`
  - Prints logs in Portuguese and handles malformed JSON gracefully.

- `worker.py`
  - Connects to the Master, sends heartbeat/presentation payloads, receives task assignments, simulates work, then reports completion.
  - Contains election logic that broadcasts `ELECTION` and `VICTORY` messages over UDP.
  - Hardcodes `MASTER_HOST` to `10.62.217.39` and uses `shutil.disk_usage("/")` for election criteria.

## How to run

There is no build system or package manifest in this repository.

- Run the master:
  - `python master.py`
- Run the worker:
  - `python worker.py`

## Notes for AI code agents

- Do not assume a package manager or tests exist.
- Preserve the existing JSON message contract and newline-delimited framing.
- Look for network-related hardcodes in `worker.py` before changing connection behavior.
- Use `Sprint3.pdf` as the project specification reference rather than duplicating it.

## When editing

- Keep the handshake fields intact: `WORKER_UUID`, `SERVER_UUID`, `TASK`, `USER`, `STATUS`, `ACK`.
- Prefer small, focused changes because this repository is a compact demo.
