import socket
import threading
import json
import queue
import time
import uuid

HOST = '0.0.0.0'
PORT = 5000
MASTER_ID = "MASTER_5"
SERVER_UUID = MASTER_ID
MASTER_ADDRESS = "192.168.18.248:5000" #Coloque aqui o IP do computador que está rodando este arquivo.
CAPACITY = 100
RELEASE_THRESHOLD = 60

# Criando a fila de tarefas do Master
task_queue = queue.Queue()
workers_na_farm = {}
worker_connections = {}  # Mapeia worker_uuid -> socket para envio de comandos
borrowed_workers = {}
pending_help_requests = {}
neighbors = {"MASTER_VIZINHO": "192.168.18.20:5001"} #Coloque aqui o IP e a porta do pc do outro grupo

load_lock = threading.Lock()

# Adicionando 60 tarefas mockadas automaticamente
for i in range(1, 150):
    task_queue.put({"TASK": "QUERY", "USER": f"Hugo{i}"})

def send_json(conn, payload):
    conn.sendall((json.dumps(payload) + '\n').encode('utf-8'))


def current_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def log_master_event(event_type, request_id=None, payload=None, extra=None):
    ts = current_timestamp()
    print(f"[{ts}] [MASTER_MSG] type={event_type} request_id={request_id} payload={payload} {extra or ''}")


def print_worker_counts():
    with load_lock:
        local_count = len(workers_na_farm)
        borrowed_count = len(borrowed_workers)
    print(f"[STATE] Workers locais={local_count} emprestados={borrowed_count}")


def get_worker_address(worker_uuid):
    worker_addr = workers_na_farm.get(worker_uuid)
    if isinstance(worker_addr, tuple) and len(worker_addr) == 2:
        return f"{worker_addr[0]}:{worker_addr[1]}"
    return None


def receive_payload(conn, buffer):
    while True:
        if '\n' in buffer:
            message, buffer = buffer.split('\n', 1)
            if not message.strip():
                continue
            try:
                payload = json.loads(message)
                return payload, buffer
            except json.JSONDecodeError:
                continue  # Ignora JSON malformado

        data = conn.recv(1024)
        if not data:
            return None, buffer
        buffer += data.decode('utf-8')


def handle_connection(conn, addr):
    print(f"[+] Nova conexão de {addr}")
    with conn:
        initial_payload, buffer = receive_payload(conn, "")
        if not initial_payload:
            print(f"[-] Conexão fechada antes da primeira mensagem: {addr}")
            return

        if initial_payload.get("type") == "register_temporary_worker":
            handle_worker_connection(conn, addr, initial_payload, buffer)
        elif initial_payload.get("WORKER") == "ALIVE" or ("WORKER_UUID" in initial_payload and "type" not in initial_payload):
            handle_worker_connection(conn, addr, initial_payload, buffer)
        elif "type" in initial_payload:
            handle_master_connection(conn, addr, initial_payload, buffer)
        else:
            print(f"[-] Tipo de conexão desconhecido de {addr}: {initial_payload}")


def handle_worker_connection(conn, addr, initial_payload, buffer):
    print(f"[+] Worker conectado: {addr}")
    payload = initial_payload
    is_borrowed_worker = False
    borrowed_worker_origin = None

    while payload is not None:
        try:
            if payload.get("type") == "register_temporary_worker":
                worker_id = payload.get("payload", {}).get("worker_id")
                original_master_address = payload.get("payload", {}).get("original_master_address")
                
                print(f"[BORROW] Recebido register_temporary_worker: worker_id={worker_id}, origin={original_master_address}")
                
                if not worker_id or not original_master_address:
                    print("[-] Erro: worker_id ou original_master_address ausente no register_temporary_worker.")
                else:
                    with load_lock:
                        borrowed_workers[worker_id] = original_master_address
                        print(f"[BORROW] Worker {worker_id} registrado como emprestado de {original_master_address}")
        
                    print_worker_counts() # <- Movi para fora (alinhei com a margem esquerda do with)
        
                    is_borrowed_worker = True
                    borrowed_worker_origin = original_master_address
                    
                    # Enviar ACK
                    ack_payload = {
                        "STATUS": "ACK",
                        "request_id": payload.get("request_id")
                    }
                    send_json(conn, ack_payload)

            elif payload.get("WORKER") == "ALIVE":
                worker_uuid = payload.get("WORKER_UUID")
                if not worker_uuid:
                    print("[-] Erro: WORKER_UUID ausente na apresentação.")
                else:
                    server_uuid_origem = payload.get("SERVER_UUID", "Local")
                    print(f"[*] Apresentação recebida do Worker {worker_uuid} (Origem: {server_uuid_origem})")
                    with load_lock:
                        workers_na_farm[worker_uuid] = addr
                        worker_connections[worker_uuid] = conn  # Registrar conexão para comandos
                        print(f"[FARM] Lista de Workers ativos no momento: {list(workers_na_farm.keys())}")
        
                    print_worker_counts() # <- Movi para fora do cadeado (alinhado com o 'with')

                    if not task_queue.empty():
                        task = task_queue.get()
                        response = task
                    else:
                        response = {"TASK": "NO_TASK"}

                    send_json(conn, response)

            elif "STATUS" in payload and payload.get("STATUS") in ["OK", "NOK"]:
                worker_uuid = payload.get("WORKER_UUID")
                task_type = payload.get("TASK")
                status = payload.get("STATUS")

                if not worker_uuid or not task_type:
                    print("[-] Erro: Campos obrigatórios ausentes no reporte de status.")
                else:
                    print(f"[+] Log: Worker {worker_uuid} finalizou a tarefa {task_type} com status {status}")
                    ack_payload = {
                        "STATUS": "ACK",
                        "WORKER_UUID": worker_uuid
                    }
                    send_json(conn, ack_payload)

            else:
                print(f"[!] Mensagem desconhecida de Worker {addr}: {payload}")

            payload, buffer = receive_payload(conn, buffer)
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"[!] Erro inesperado com {addr}: {e}")
            break

    print(f"[-] Conexão encerrada com Worker {addr}")


def handle_master_connection(conn, addr, initial_payload, buffer):
    print(f"[+] Master conectado: {addr}")
    payload = initial_payload

    while payload is not None:
        try:
            message_type = payload.get("type")
            request_id = payload.get("request_id")

            if message_type == "request_help":
                    request_payload = payload.get("payload", {})
                    log_master_event("request_help", request_id, request_payload, extra=f"from={addr}")

                    requesting_master = request_payload.get("master_id")
                    requester_address = request_payload.get("master_address")
                    current_load = request_payload.get("current_load")
                    capacity = request_payload.get("capacity")
                    workers_needed = request_payload.get("workers_needed")

                    if not requesting_master or not requester_address or current_load is None or capacity is None or workers_needed is None:
                        print(f"[-] request_help inválido de {addr}: campos obrigatórios ausentes {request_payload}")
                        response = {
                            "type": "response_rejected",
                            "request_id": request_id,
                            "payload": {"reason": "refused"}
                        }
                        send_json(conn, response)
                        payload, buffer = receive_payload(conn, buffer)
                        continue

                    with load_lock:
                        actual_load = task_queue.qsize()
                        available_workers = [w for w in workers_na_farm.keys() if w not in borrowed_workers]

                    if actual_load >= CAPACITY:
                        print(f"[MASTER] Rejeitando request_help de {requesting_master}: current_load={actual_load} >= capacity={CAPACITY}")
                        response = {
                            "type": "response_rejected",
                            "request_id": request_id,
                            "payload": {"reason": "high_load"}
                        }
                    elif not available_workers:
                        print(f"[MASTER] Rejeitando request_help de {requesting_master}: nenhum worker disponível")
                        response = {
                            "type": "response_rejected",
                            "request_id": request_id,
                            "payload": {"reason": "no_workers_available"}
                        }
                    else:
                        selected_workers = available_workers[:workers_needed]
                        offered_workers_details = []
                        print(f"[MASTER] Aceitando request_help de {requesting_master}: current_load={actual_load} < capacity={CAPACITY}")

                        for worker_uuid in selected_workers:
                            try:
                                with load_lock:
                                    worker_conn = worker_connections.get(worker_uuid)
                                    worker_addr = workers_na_farm.get(worker_uuid)

                                if worker_conn:
                                    redirect_payload = {
                                        "type": "command_redirect",
                                        "request_id": str(uuid.uuid4()),
                                        "payload": {
                                            "new_master_address": requester_address
                                        }
                                    }
                                    print(f"[REDIRECT] Enviando command_redirect ao Worker {worker_uuid}")
                                    send_json(worker_conn, redirect_payload)

                                    offered_workers_details.append({
                                        "id": worker_uuid,
                                        "address": get_worker_address(worker_uuid) or "unknown"
                                    })
                                else:
                                    print(f"[ERRO] Conexão do Worker {worker_uuid} não encontrada")
                            except Exception as e:
                                print(f"[ERRO] Falha ao enviar command_redirect ao Worker {worker_uuid}: {e}")

                        if not offered_workers_details:
                            response = {
                                "type": "response_rejected",
                                "request_id": request_id,
                                "payload": {"reason": "no_workers_available"}
                            }
                        else:
                            response = {
                                "type": "response_accepted",
                                "request_id": request_id,
                                "payload": {
                                    "workers_offered": len(offered_workers_details),
                                    "worker_details": offered_workers_details
                                }
                            }

                    log_master_event(response["type"], request_id, response.get("payload"), extra=f"to={addr}")
                    send_json(conn, response)
            elif message_type == "notify_worker_returned":
                notify_payload = payload.get('payload', {})
                log_master_event("notify_worker_returned", request_id, notify_payload, extra=f"from={addr}")
                returned_worker_id = notify_payload.get('worker_id')
                if returned_worker_id:
                    with load_lock:
                        if returned_worker_id in borrowed_workers:
                            borrowed_workers.pop(returned_worker_id, None)
                            worker_connections.pop(returned_worker_id, None)
                            print(f"[MASTER] Worker devolvido com sucesso: {returned_worker_id}")
                            print_worker_counts()
                        else:
                            print(f"[MASTER] notify_worker_returned recebido para worker desconhecido: {returned_worker_id}")
                else:
                    print(f"[MASTER] notify_worker_returned recebido sem worker_id: {payload}")
            elif message_type in ["response_accepted", "response_rejected"]:
                log_master_event(message_type, request_id, payload.get('payload'), extra=f"from={addr}")
                print(f"[MASTER] Mensagem {message_type} recebida de {addr} request_id={request_id} payload={payload.get('payload')}")
            else:
                print(f"[MASTER] Tipo desconhecido recebido de {addr}: {payload}")

            payload, buffer = receive_payload(conn, buffer)
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"[!] Erro inesperado na conexão Master {addr}: {e}")
            break

    print(f"[-] Conexão encerrada com Master {addr}")


def load_monitor_loop():
    while True:
        with load_lock:
            current_load = task_queue.qsize()
            borrowed_list = list(borrowed_workers.items())

        if current_load > CAPACITY:
            print(f"[LOAD] Saturação detectada: current_load={current_load} > capacity={CAPACITY}")
            workers_needed = max(1, current_load - CAPACITY)

            with load_lock:
                if not pending_help_requests:
                    for nid, addr in neighbors.items():
                        t = threading.Thread(target=request_help_to_neighbor, args=(nid, addr, workers_needed))
                        t.daemon = True
                        t.start()
                        pending_help_requests[nid] = "pending"

        elif current_load <= RELEASE_THRESHOLD and borrowed_list:
            print(f"[LOAD] Carga normalizada: current_load={current_load} <= release_threshold={RELEASE_THRESHOLD}")
            for worker_id, origin_address in borrowed_list:
                with load_lock:
                    worker_conn = worker_connections.get(worker_id)

                release_payload = {
                    "type": "command_release",
                    "request_id": str(uuid.uuid4()),
                    "payload": {
                        "original_master_address": origin_address
                    }
                }

                if worker_conn:
                    try:
                        print(f"[RELEASE] Enviando command_release para Worker {worker_id}")
                        send_json(worker_conn, release_payload)
                    except Exception as e:
                        print(f"[ERRO] Falha ao enviar command_release para {worker_id}: {e}")
                else:
                    print(f"[RELEASE] Conexão do Worker {worker_id} não encontrada")

                try:
                    origin_ip, origin_port_s = origin_address.split(":")
                    origin_port = int(origin_port_s)
                    with socket.create_connection((origin_ip, origin_port), timeout=5) as notify_sock:
                        notify_payload = {
                            "type": "notify_worker_returned",
                            "request_id": str(uuid.uuid4()),
                            "payload": {"worker_id": worker_id}
                        }
                        log_master_event("notify_worker_returned", notify_payload["request_id"], notify_payload["payload"], extra=f"to={origin_address}")
                        send_json(notify_sock, notify_payload)
                        print(f"[RELEASE] notify_worker_returned enviado para {origin_address} worker_id={worker_id}")

                    with load_lock:
                        borrowed_workers.pop(worker_id, None)
                        worker_connections.pop(worker_id, None)
                        print_worker_counts()
                except Exception as e:
                    print(f"[ERRO] Falha ao notificar Master de origem {origin_address}: {e}")
                    print(f"[RELEASE] Worker {worker_id} permanecerá listado como emprestado até confirmação")

        else:
            print(f"[LOAD] Carga estável: current_load={current_load}")

        time.sleep(2)


def request_help_to_neighbor(neighbor_id, addr_str, workers_needed):
    """Abre conexão com o Master vizinho e envia request_help, aguardando resposta até 5s."""
    try:
        ip, port_s = addr_str.split(":")
        port = int(port_s)
    except Exception as e:
        print(f"[HELP] Endereço de vizinho inválido {addr_str}: {e}")
        with load_lock:
            pending_help_requests.pop(neighbor_id, None)
        return

    request_id = str(uuid.uuid4())
    payload = {
        "type": "request_help",
        "request_id": request_id,
        "payload": {
            "master_id": MASTER_ID,
            "master_address": MASTER_ADDRESS,
            "current_load": task_queue.qsize(),
            "capacity": CAPACITY,
            "workers_needed": workers_needed
        }
    }

    log_master_event("request_help", request_id, payload["payload"], extra=f"to={neighbor_id}")
    print(f"[HELP] Enviando request_help para {neighbor_id} ({addr_str}) request_id={request_id} workers_needed={workers_needed}")

    response_received = False
    try:
        with socket.create_connection((ip, port), timeout=5) as s:
            s.settimeout(5.0)
            send_json(s, payload)

            buffer = ""
            start = time.time()
            while time.time() - start < 5.0:
                try:
                    data = s.recv(1024)
                    if not data:
                        break
                    buffer += data.decode('utf-8')
                    if '\n' in buffer:
                        message, _ = buffer.split('\n', 1)
                        try:
                            resp = json.loads(message)
                            rtype = resp.get('type')
                            log_master_event(rtype, resp.get('request_id'), resp.get('payload'), extra=f"from={neighbor_id}")
                            print(f"[HELP] Resposta de {neighbor_id}: type={rtype} request_id={resp.get('request_id')} payload={resp.get('payload')}")
                            response_received = True
                            break
                        except json.JSONDecodeError:
                            continue
                except socket.timeout:
                    break

    except Exception as e:
        print(f"[HELP] Falha ao conectar/comunicar com {neighbor_id} ({addr_str}): {e}")

    if not response_received:
        print(f"[HELP] Timeout de 5s aguardando resposta de {neighbor_id} ({addr_str})")

    with load_lock:
        pending_help_requests.pop(neighbor_id, None)


def start_master():
    monitor_thread = threading.Thread(target=load_monitor_loop, daemon=True)
    monitor_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, 5000))
        server.listen()
        print(f"[*] {SERVER_UUID} escutando na porta {PORT}...")
        
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_master()