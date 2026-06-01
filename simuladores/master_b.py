import socket
import threading
import json
import queue
import time
import uuid

HOST = '0.0.0.0'
PORT = 5001
MASTER_ID = "MASTER_5"
SERVER_UUID = MASTER_ID
MASTER_ADDRESS = "127.0.0.1:5000" #Coloque aqui o IP do computador que está rodando este arquivo
CAPACITY = 100
RELEASE_THRESHOLD = 60

# Criando a fila de tarefas do Master
task_queue = queue.Queue()
workers_na_farm = {}
worker_connections = {}  # Mapeia worker_uuid -> socket para envio de comandos
borrowed_workers = {}
pending_help_requests = {}
neighbors = {"MASTER_VIZINHO": "127.0.0.1:5001"} #Coloque aqui o IP e a porta do pc do outro grupo

load_lock = threading.Lock()

# Adicionando 60 tarefas mockadas automaticamente
for i in range(0):
    task_queue.put({"TASK": "QUERY", "USER": f"Hugo{i}"})

def send_json(conn, payload):
    conn.sendall((json.dumps(payload) + '\n').encode('utf-8'))


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

        if initial_payload.get("WORKER") == "ALIVE" or ("WORKER_UUID" in initial_payload and "type" not in initial_payload):
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
                        print(f"[BORROW] Lista de Workers emprestados: {list(borrowed_workers.keys())}")
                    
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
                        if worker_uuid not in workers_na_farm:
                            workers_na_farm[worker_uuid] = addr
                            worker_connections[worker_uuid] = conn  # Registrar conexão para comandos
                            print(f"[FARM] Lista de Workers ativos no momento: {list(workers_na_farm.keys())}")

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
                print(f"[MASTER] request_help recebido de {addr} request_id={request_id} payload={payload.get('payload')}")
                
                requester_payload = payload.get("payload", {})
                requesting_master = requester_payload.get("master_id", "UNKNOWN")
                workers_needed = requester_payload.get("workers_needed", 1)

                with load_lock:
                    current_load = task_queue.qsize()

                if current_load < CAPACITY:
                    print(f"[MASTER] Aceitando request_help de {requesting_master}: current_load={current_load} < capacity={CAPACITY}")
                    
                    # Selecionar Workers ociosos para oferecer
                    with load_lock:
                        available_workers = list(workers_na_farm.keys())[:workers_needed]
                    
                    offered_workers_details = []
                    for worker_uuid in available_workers:
                        # Enviar command_redirect para cada worker
                        try:
                            redirect_payload = {
                                "type": "command_redirect",
                                "request_id": str(uuid.uuid4()),
                                "payload": {
                                    "new_master_address": requester_payload.get("master_address")
                                }
                            }
                            
                            with load_lock:
                                worker_conn = worker_connections.get(worker_uuid)
                            
                            if worker_conn:
                                print(f"[REDIRECT] Enviando command_redirect ao Worker {worker_uuid}")
                                send_json(worker_conn, redirect_payload)
                                offered_workers_details.append({
                                    "id": worker_uuid,
                                    "address": f"127.0.0.1:5000"  # Seria o endereço real do worker
                                })
                        except Exception as e:
                            print(f"[ERRO] Falha ao enviar command_redirect ao Worker {worker_uuid}: {e}")
                    
                    response = {
                        "type": "response_accepted",
                        "request_id": request_id,
                        "payload": {
                            "workers_offered": len(offered_workers_details),
                            "worker_details": offered_workers_details
                        }
                    }
                else:
                    print(f"[MASTER] Rejeitando request_help de {requesting_master}: current_load={current_load} >= capacity={CAPACITY}")
                    response = {
                        "type": "response_rejected",
                        "request_id": request_id,
                        "payload": {"reason": "high_load"}
                    }

                send_json(conn, response)

            elif message_type == "notify_worker_returned":
                print(f"[MASTER] notify_worker_returned recebido de {addr} request_id={request_id} payload={payload.get('payload')}")
                returned_worker_id = payload.get('payload', {}).get('worker_id')
                print(f"[MASTER] Worker devolvido com sucesso: {returned_worker_id}")
            elif message_type in ["response_accepted", "response_rejected"]:
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
                        send_json(notify_sock, notify_payload)
                        print(f"[RELEASE] notify_worker_returned enviado para {origin_address} worker_id={worker_id}")
                except Exception as e:
                    print(f"[ERRO] Falha ao notificar Master de origem {origin_address}: {e}")

                with load_lock:
                    borrowed_workers.pop(worker_id, None)
                    worker_connections.pop(worker_id, None)

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

    print(f"[HELP] Enviando request_help para {neighbor_id} ({addr_str}) request_id={request_id} workers_needed={workers_needed}")

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
                            print(f"[HELP] Resposta de {neighbor_id}: type={rtype} request_id={resp.get('request_id')} payload={resp.get('payload')}")
                            break
                        except json.JSONDecodeError:
                            continue
                except socket.timeout:
                    break

    except Exception as e:
        print(f"[HELP] Falha ao conectar/comunicar com {neighbor_id} ({addr_str}): {e}")

    with load_lock:
        pending_help_requests.pop(neighbor_id, None)


def start_master():
    monitor_thread = threading.Thread(target=load_monitor_loop, daemon=True)
    monitor_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] {SERVER_UUID} escutando na porta {PORT}...")
        
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_master()