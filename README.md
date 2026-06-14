Supervisor metrics emitter

This project adds a TLS-over-TCP supervisor client that periodically sends a JSON payload (Sprint 4 format) to the external supervisor endpoint `nuted-ia.dev:443`. The sender does not wait for a response.

Quick run (development):

- Run unit tests:

```bash
python -m unittest
```

- To run the master (it will start emitting metrics every 10s):

```bash
python master.py
```

Configuration:

- Supervisor host/port can be changed by editing `supervisor_client.send_periodic` call in `master.py`.
- TLS is used by default; for local testing the client supports `use_tls=False` in tests.

Notes:

- The implementation avoids new runtime dependencies and uses the Python standard library for TLS and system metrics collection.
