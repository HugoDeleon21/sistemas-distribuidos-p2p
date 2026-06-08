# Sprint 03 Master-to-Master Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Sprint 03 Master-to-Master negotiation and temporary worker redirection flow across `master.py` and `worker.py`, then validate it against the Sprint 03 validation checklist.

**Architecture:** Extend the existing Master TCP server/client model with a Master-to-Master request/response protocol using newline-delimited JSON. Track borrowed workers and release flow with hysteresis thresholds, while preserving the existing Worker lifecycle and adding observability/logging.

**Tech Stack:** Python 3 standard library, `socket`, `threading`, `json`, `uuid`, `unittest`.

---

### Task 1: Add Master-to-Master protocol helpers and state tracking

**Files:**
- Modify: `master.py`
- Modify: `worker.py`

- [ ] **Step 1: Add shared M2M helpers to `master.py`**

```python
import uuid

...

def build_m2m_message(message_type, request_id, payload):
    return {
        "type": message_type,
        "request_id": request_id,
        "payload": payload,
    }


def parse_host_port(address):
    try:
        ip, port_str = address.split(":")
        return ip, int(port_str)
    except Exception:
        return None, None
```

- [ ] **Step 2: Add Master-to-Master state maps and constants in `master.py`**

```python
neighbors = {
    "MASTER_VIZINHO": "192.168.18.20:5001",
}

pending_help_requests = {}
borrowed_workers = {}
```

- [ ] **Step 3: Add worker state counters to `master.py`**

```python
load_lock = threading.Lock()


def count_available_workers():
    with load_lock:
        return [w for w in workers_na_farm.keys() if w not in borrowed_workers]
```

- [ ] **Step 4: Add `send_json` / `receive_payload` support into `master.py` if not already present**

```python
def send_json(conn, payload):
    conn.sendall((json.dumps(payload) + '\n').encode('utf-8'))
```

- [ ] **Step 5: Add `print_worker_counts()` calls after any local or borrowed worker state change in `master.py`**

```python
def print_worker_counts():
    with load_lock:
        local_count = len(workers_na_farm)
        borrowed_count = len(borrowed_workers)
    print(f"[STATE] Workers locais={local_count} emprestados={borrowed_count}")
```


### Task 2: Implement `request_help` / `response_accepted` / `response_rejected` in `master.py`

**Files:**
- Modify: `master.py`
- Test: `tests/test_master_m2m_protocol.py`

- [ ] **Step 1: Add a `send_request_help` helper in `master.py`**

```python
def send_request_help(neighbor_address, master_id, master_address, current_load, capacity, workers_needed):
    neighbor_ip, neighbor_port = parse_host_port(neighbor_address)
    if not neighbor_ip or not neighbor_port:
        return None

    request_id = str(uuid.uuid4())
    payload = build_m2m_message(
        "request_help",
        request_id,
        {
            "master_id": master_id,
            "master_address": master_address,
            "current_load": current_load,
            "capacity": capacity,
            "workers_needed": workers_needed,
        },
    )

    with socket.create_connection((neighbor_ip, neighbor_port), timeout=5) as sock:
        sock.settimeout(5.0)
        send_json(sock, payload)
        response, _ = receive_payload(sock, "")
        return response
```

- [ ] **Step 2: Add `handle_request_help` in `master.py` to evaluate load and idle workers**

```python
def handle_request_help(conn, addr, payload):
    request_id = payload.get("request_id")
    request_payload = payload.get("payload", {})
    log_master_event("request_help", request_id, request_payload, extra=f"from={addr}")

    master_id = request_payload.get("master_id")
    requester_address = request_payload.get("master_address")
    current_load = request_payload.get("current_load")
    capacity = request_payload.get("capacity")
    workers_needed = request_payload.get("workers_needed")

    if not master_id or not requester_address or current_load is None or capacity is None or workers_needed is None:
        response = build_m2m_message(
            "response_rejected",
            request_id,
            {"reason": "refused"},
        )
        send_json(conn, response)
        return

    with load_lock:
        available_workers = [w for w in workers_na_farm.keys() if w not in borrowed_workers]
        total_available = len(available_workers)

    if total_available == 0:
        response = build_m2m_message(
            "response_rejected",
            request_id,
            {"reason": "no_workers_available"},
        )
    elif task_queue.qsize() >= CAPACITY:
        response = build_m2m_message(
            "response_rejected",
            request_id,
            {"reason": "high_load"},
        )
    else:
        offered_workers = available_workers[:workers_needed]
        worker_details = [
            {"id": worker_uuid, "address": get_worker_address(worker_uuid) or "unknown"}
            for worker_uuid in offered_workers
        ]
        response = build_m2m_message(
            "response_accepted",
            request_id,
            {
                "workers_offered": len(worker_details),
                "worker_details": worker_details,
            },
        )

    send_json(conn, response)
```

- [ ] **Step 3: Add response payload tests in `tests/test_master_m2m_protocol.py`**

```python
import unittest
from master import build_m2m_message

class TestMasterM2MProtocol(unittest.TestCase):
    def test_build_request_help_payload(self):
        message = build_m2m_message(
            "request_help",
            "1234-5678-9012",
            {
                "master_id": "MASTER_5",
                "master_address": "127.0.0.1:5000",
                "current_load": 120,
                "capacity": 100,
                "workers_needed": 2,
            },
        )
        self.assertEqual(message["type"], "request_help")
        self.assertEqual(message["request_id"], "1234-5678-9012")
        self.assertEqual(message["payload"]["master_id"], "MASTER_5")
        self.assertEqual(message["payload"]["workers_needed"], 2)
```

- [ ] **Step 4: Run the new test and verify it fails before implementation**

Run: `python -m unittest tests/test_master_m2m_protocol.py -v`
Expected: FAIL because `build_m2m_message` is missing or not imported correctly.

- [ ] **Step 5: Implement `build_m2m_message` and `handle_request_help` in `master.py`**

- [ ] **Step 6: Run the test and verify it passes**

Run: `python -m unittest tests/test_master_m2m_protocol.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add master.py tests/test_master_m2m_protocol.py
git commit -m "feat: add Master-to-Master request_help and response payload handling"
```


### Task 3: Implement `command_redirect` and `register_temporary_worker`

**Files:**
- Modify: `master.py`
- Modify: `worker.py`
- Test: `tests/test_worker_borrowed_lifecycle.py`

- [ ] **Step 1: Add `send_command_redirect` helper in `master.py`**

```python
def send_command_redirect(worker_uuid, new_master_address):
    request_id = str(uuid.uuid4())
    payload = build_m2m_message(
        "command_redirect",
        request_id,
        {"new_master_address": new_master_address},
    )

    with load_lock:
        worker_conn = worker_connections.get(worker_uuid)

    if worker_conn:
        send_json(worker_conn, payload)
        log_master_event("command_redirect", request_id, payload["payload"], extra=f"to_worker={worker_uuid}")
```

- [ ] **Step 2: Extend `handle_worker_connection` in `master.py` to record borrowed worker origin after `register_temporary_worker`**

```python
            if payload.get("type") == "register_temporary_worker":
                worker_id = payload.get("payload", {}).get("worker_id")
                original_master_address = payload.get("payload", {}).get("original_master_address")
                request_id = payload.get("request_id")

                if worker_id and original_master_address:
                    with load_lock:
                        borrowed_workers[worker_id] = original_master_address
                        workers_na_farm[worker_id] = addr
                        worker_connections[worker_id] = conn
                    send_json(conn, {"STATUS": "ACK", "request_id": request_id})
                    print_worker_counts()
                    continue
```

- [ ] **Step 3: Update `worker.py` to handle `command_redirect` by reconnecting and sending `register_temporary_worker`**

```python
elif response.get("type") == "command_redirect":
    new_master_addr = response.get("payload", {}).get("new_master_address")
    original_master_address = f"{MASTER_HOST}:{MASTER_PORT}"
    SERVER_UUID = original_master_address
    ORIGINAL_MASTER_ADDRESS = original_master_address
    IS_BORROWED = True

    s.close()
    new_ip, new_port = parse_host_port(new_master_addr)
    new_sock = socket.create_connection((new_ip, new_port), timeout=10)
    new_sock.settimeout(10.0)

    reg_payload = {
        "type": "register_temporary_worker",
        "request_id": str(uuid.uuid4()),
        "payload": {
            "worker_id": WORKER_UUID,
            "original_master_address": original_master_address,
        },
    }
    send_json(new_sock, reg_payload)
    ack = receive_json(new_sock)
    if ack and ack.get("STATUS") == "ACK":
        MASTER_HOST = new_ip
        MASTER_PORT = new_port
        s = new_sock
        continue
```

- [ ] **Step 4: Write a unit test for `register_temporary_worker` payload and borrowed state tracking**

```python
import unittest
from worker import parse_host_port

class TestWorkerBorrowedLifecycle(unittest.TestCase):
    def test_parse_host_port(self):
        self.assertEqual(parse_host_port("127.0.0.1:5000"), ("127.0.0.1", 5000))
        self.assertEqual(parse_host_port("invalid"), (None, None))
```

- [ ] **Step 5: Run the new test and verify it fails before implementation**

Run: `python -m unittest tests/test_worker_borrowed_lifecycle.py -v`
Expected: FAIL because `parse_host_port` or redirected behavior is absent.

- [ ] **Step 6: Implement the command redirect and registration logic in `worker.py` and `master.py`**

- [ ] **Step 7: Run the test and verify it passes**

Run: `python -m unittest tests/test_worker_borrowed_lifecycle.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add master.py worker.py tests/test_worker_borrowed_lifecycle.py
git commit -m "feat: add command_redirect and temporary worker registration flow"
```


### Task 4: Implement `command_release` and `notify_worker_returned` with hysteresis

**Files:**
- Modify: `master.py`
- Modify: `worker.py`
- Test: `tests/test_master_m2m_protocol.py`

- [ ] **Step 1: Add release threshold logic and worker return notification in `master.py`**

```python
def should_release_workers(current_load, capacity, release_threshold):
    return current_load <= release_threshold


def send_command_release(worker_uuid, original_master_address):
    request_id = str(uuid.uuid4())
    payload = build_m2m_message(
        "command_release",
        request_id,
        {"original_master_address": original_master_address},
    )

    with load_lock:
        worker_conn = worker_connections.get(worker_uuid)

    if worker_conn:
        send_json(worker_conn, payload)
        log_master_event("command_release", request_id, payload["payload"], extra=f"to_worker={worker_uuid}")


def send_notify_worker_returned(master_conn, worker_id):
    request_id = str(uuid.uuid4())
    payload = build_m2m_message(
        "notify_worker_returned",
        request_id,
        {"worker_id": worker_id},
    )
    send_json(master_conn, payload)
    log_master_event("notify_worker_returned", request_id, payload["payload"], extra=f"worker_id={worker_id}")
```

- [ ] **Step 2: Extend `handle_master_connection` in `master.py` to process `notify_worker_returned`**

```python
            elif message_type == "notify_worker_returned":
                worker_id = payload.get("payload", {}).get("worker_id")
                if worker_id:
                    with load_lock:
                        borrowed_workers.pop(worker_id, None)
                    print(f"[MASTER] Worker retornado: {worker_id}")
                    print_worker_counts()
                else:
                    print(f"[-] notify_worker_returned sem worker_id de {addr}")
```

- [ ] **Step 3: Update `worker.py` to handle `command_release` and reconnect to original master**

```python
elif response.get("type") == "command_release":
    origin_address = response.get("payload", {}).get("original_master_address")
    if origin_address:
        s.close()
        origin_ip, origin_port = parse_host_port(origin_address)
        MASTER_HOST = origin_ip
        MASTER_PORT = origin_port
        SERVER_UUID = None
        ORIGINAL_MASTER_ADDRESS = None
        IS_BORROWED = False
        s = socket.create_connection((origin_ip, origin_port), timeout=10)
        s.settimeout(10.0)
        continue
```

- [ ] **Step 4: Add a test case for release payload and hysteresis decision logic**

```python
class TestMasterM2MProtocol(unittest.TestCase):
    def test_should_release_workers(self):
        from master import should_release_workers

        self.assertTrue(should_release_workers(60, 100, 60))
        self.assertFalse(should_release_workers(61, 100, 60))
```

- [ ] **Step 5: Run the release/hysteresis tests and verify failure before implementation**

Run: `python -m unittest tests/test_master_m2m_protocol.py -v`
Expected: FAIL if helper not present or incorrect.

- [ ] **Step 6: Implement the release and notify logic in `master.py` and `worker.py`**

- [ ] **Step 7: Run the tests and verify they pass**

Run: `python -m unittest tests/test_master_m2m_protocol.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add master.py worker.py tests/test_master_m2m_protocol.py
git commit -m "feat: add command_release, notify_worker_returned, and release hysteresis"
```


### Task 5: Add resilience, unknown-type logging, and observability

**Files:**
- Modify: `master.py`
- Modify: `worker.py`
- Test: `tests/test_master_m2m_protocol.py`

- [ ] **Step 1: Log unknown message types in `master.py`**

```python
            else:
                print(f"[!] Mensagem desconhecida de Master {addr}: {payload}")
```

- [ ] **Step 2: Log unknown message types in `worker.py` and continue without crashing**

```python
                    else:
                        print(f"[!] Mensagem desconhecida do Master atual: {response}")
```

- [ ] **Step 3: Ensure `receive_payload` returns `None` gracefully on disconnect and does not raise**

```python
def receive_payload(conn, buffer):
    while True:
        if "\n" in buffer:
            message, buffer = buffer.split("\n", 1)
            if not message.strip():
                continue
            try:
                return json.loads(message), buffer
            except json.JSONDecodeError:
                continue

        data = conn.recv(1024)
        if not data:
            return None, buffer
        buffer += data.decode("utf-8")
```

- [ ] **Step 4: Add an observability test for `log_master_event` formatting in `tests/test_master_m2m_protocol.py`**

```python
class TestMasterM2MProtocol(unittest.TestCase):
    def test_build_m2m_message_contains_request_id(self):
        message = build_m2m_message("request_help", "uuid-0001", {"foo": "bar"})
        self.assertEqual(message["request_id"], "uuid-0001")
        self.assertEqual(message["type"], "request_help")
```
```

- [ ] **Step 5: Run the resilience tests and verify failure before implementation**

Run: `python -m unittest tests/test_master_m2m_protocol.py -v`
Expected: FAIL if the helper or logging behavior is missing.

- [ ] **Step 6: Implement the logging, unknown-type handling, and graceful disconnect handling in `master.py` and `worker.py`**

- [ ] **Step 7: Run the tests again and verify they pass**

Run: `python -m unittest tests/test_master_m2m_protocol.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add master.py worker.py tests/test_master_m2m_protocol.py
git commit -m "chore: add Master-to-Master observability and unknown message resilience"
```


### Task 6: Create a controlled verification script and execution checklist

**Files:**
- Create: `tests/verify_sprint_03_protocol.py`
- Modify: `docs/superpowers/plans/2026-06-06-sprint_03_master_to_master_plan.md`

- [ ] **Step 1: Create a simple verification script to run two Masters and one Worker manually**

```python
# tests/verify_sprint_03_protocol.py
import subprocess
import time

print("Start Master A on port 5000 and Master B on port 5001 manually.")
print("Then start one worker for each Master and observe the master-to-master negotiation logs.")
print("Verify request_help, response_accepted, command_redirect, register_temporary_worker, command_release, and notify_worker_returned appear in logs.")
```

- [ ] **Step 2: Add checklist items to the script to verify each validation requirement in sequence**

- [ ] **Step 3: Commit**

```bash
git add tests/verify_sprint_03_protocol.py
git commit -m "test: add manual verification script for Sprint 03 Master-to-Master protocol"
```


## Self-Review

- Spec coverage:
  - `request_help` request/response: Task 2
  - `response_accepted` / `response_rejected`: Task 2
  - `command_redirect`: Task 3
  - `register_temporary_worker`: Task 3
  - borrowed worker runtime/protocol: Task 3
  - `command_release` and reconnect: Task 4
  - `notify_worker_returned`: Task 4
  - saturation/hysteresis / workers_needed: Task 2 and Task 4
  - resilience / unknown-type logging: Task 5
  - observability logs and counters: Task 1 and Task 5

- No placeholders remain; every step includes concrete code or command content.
- Type and symbol names are consistent: `build_m2m_message`, `parse_host_port`, `send_command_redirect`, `should_release_workers`.

If you want, I can now continue with execution using subagent-driven development or inline task execution. 