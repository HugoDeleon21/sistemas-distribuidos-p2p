import json
import time
import socket
import os
import shutil

# Prefer psutil for reliable memory metrics; fallback to generic values when unavailable
try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    psutil = None
    _HAS_PSUTIL = False

def current_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def gather_system_metrics():
    # Build a system metrics dictionary that matches the Sprint 4 schema.
    # Use psutil when available for accurate metrics; otherwise fall back to best-effort and safe defaults.
    # Uptime: seconds since epoch is used as a proxy for uptime_seconds in this prototype.
    uptime_seconds = int(time.time())

    # Load averages
    try:
        load1, load5, load15 = os.getloadavg()
    except Exception:
        load1 = load5 = load15 = 0.0

    # CPU
    try:
        count_logical = psutil.cpu_count(logical=True) if _HAS_PSUTIL else (os.cpu_count() or 1)
    except Exception:
        count_logical = os.cpu_count() or 1
    try:
        c_phys = psutil.cpu_count(logical=False) if _HAS_PSUTIL else None
        count_physical = c_phys if c_phys is not None else count_logical
    except Exception:
            count_physical = count_logical
    try:
        cpu_usage = float(psutil.cpu_percent(interval=0.1)) if _HAS_PSUTIL else 0.0
    except Exception:
        cpu_usage = 0.0

    # Disk
    try:
        du = shutil.disk_usage("/")
        disk_total_gb = round(du.total / (1024**3), 2)
        disk_free_gb = round(du.free / (1024**3), 2)
        disk_percent = round((du.used / du.total) * 100, 2)
    except Exception:
        disk_total_gb = disk_free_gb = disk_percent = 0.0

    # Memory
    mem_total = None
    mem_available = None
    mem_used = None
    mem_percent = None
    try:
        if _HAS_PSUTIL:
            vm = psutil.virtual_memory()
            mem_total = int(vm.total / (1024 * 1024))
            mem_available = int(vm.available / (1024 * 1024))
            mem_used = int((vm.total - vm.available) / (1024 * 1024))
            mem_percent = round(vm.percent, 2)
        else:
            # Try /proc parsing
            if os.name == 'posix' and os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo') as f:
                    info = f.read()
                def parse(key):
                    for line in info.splitlines():
                        if line.startswith(key):
                            parts = line.split()
                            return int(parts[1])
                    return None
                mem_total_kb = parse('MemTotal:')
                mem_available_kb = parse('MemAvailable:') or parse('MemFree:')
                if mem_total_kb and mem_available_kb:
                    mem_total = int(mem_total_kb / 1024)
                    mem_available = int(mem_available_kb / 1024)
                    mem_used = mem_total - mem_available
                    mem_percent = round((1 - (mem_available / mem_total)) * 100, 2)
    except Exception:
        pass

    # Final fallbacks to avoid nulls
    if mem_total is None:
        mem_total = 16384
    if mem_available is None:
        mem_available = max(0, int(mem_total * 0.5))
    if mem_used is None:
        mem_used = mem_total - mem_available
    if mem_percent is None:
        try:
            mem_percent = round((mem_used / mem_total) * 100, 2)
        except Exception:
            mem_percent = 0.0

    system = {
        "uptime_seconds": uptime_seconds,
        "load_average_1m": load1,
        "load_average_5m": load5,
        "load_average_15m": load15,
        "cpu": {
            "usage_percent": cpu_usage,
            "count_logical": count_logical,
            "count_physical": count_physical,
        },
        "memory": {
            "total_mb": mem_total,
            "available_mb": mem_available,
            "percent_used": mem_percent,
            "memory_used": mem_used,
        },
        "disk": {
            "total_gb": disk_total_gb,
            "free_gb": disk_free_gb,
            "percent_used": disk_percent,
        },
    }

    # Preenchendo os campos obrigatórios da Sprint 4
    farm_state = {
        "workers": {
            "total_registered": 0,
            "workers_utilization": 0,
            "workers_alive": 0,
            "workers_idle": 0,
            "workers_borrowed": 0,
            "workers_received": 0,
            "workers_failed": 0,
            "workers_home": 0,
            "workers_available_capacity": 0,
            "borrowed_workers": []
        },
        "tasks": {
            "tasks_pending": 0,
            "tasks_running": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "oldest_task_age_s": 0
        }
    }

    config_thresholds = {
        "max_task": 100,
        "warn_cpu_percent": 85,
        "warn_memory_percent": 85,
        "release_task": 60
    }

    return {"system": system, "farm_state": farm_state, "config_thresholds": config_thresholds}

def build_payload(server_uuid, hostname, role, task, performance=None, extra=None):
    perf = performance or gather_system_metrics()
    
    payload = {
        "server_uuid": server_uuid,
        "hostname": hostname,
        "role": role,
        "task": task,
        "timestamp": current_timestamp(),
        "message_id": socket.gethostname() + "-" + str(int(time.time())),
        "payload_version": "sprint4-monitor-v2",
        "neighbors": [],
        "performance": perf
    }

    if extra:
        # INTERCEPTADOR: Puxa os dados reais da raiz e mescla perfeitamente dentro do 'performance'
        if "farm_state" in extra:
            for cat in ["workers", "tasks"]:
                if cat in extra["farm_state"]:
                    payload["performance"]["farm_state"][cat].update(extra["farm_state"][cat])
            del extra["farm_state"]
        
        if "config_thresholds" in extra:
            payload["performance"]["config_thresholds"].update(extra["config_thresholds"])
            del extra["config_thresholds"]
            
        if "neighbors" in extra:
            payload["neighbors"] = extra["neighbors"]
            del extra["neighbors"]

        # O que sobrar (se sobrar) vai para a raiz
        payload.update(extra)

    return payload

def to_json(payload):
    return json.dumps(payload, ensure_ascii=False) + '\n'