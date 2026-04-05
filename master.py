import socket
import threading
import json
import queue

HOST = '127.0.0.1'
PORT = 5000

# Criando a fila de tarefas do Master
task_queue = queue.Queue()

# Adicionando tarefas mockadas para os testes CT01 e CT02
task_queue.put({"TASK": "QUERY", "USER": "Michel"})
task_queue.put({"TASK": "QUERY", "USER": "Hugo"})

def handle_worker(conn, addr):
    print(f"[+] Worker conectado: {addr}")
    with conn:
        buffer = ""
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    if not message.strip():
                        continue
                        
                    try:
                        payload = json.loads(message)
                    except json.JSONDecodeError:
                        continue # Ignora JSON malformado

                    # ETAPA 1 E 2: Worker se apresenta e Master distribui tarefa
                    if payload.get("WORKER") == "ALIVE":
                        worker_uuid = payload.get("WORKER_UUID")
                        
                        # Strict Parsing: Falha se faltar campo obrigatório
                        if not worker_uuid:
                            print("[-] Erro: WORKER_UUID ausente na apresentação.")
                            continue
                            
                        server_uuid = payload.get("SERVER_UUID", "Local")
                        print(f"[*] Apresentação recebida do Worker {worker_uuid} (Origem: {server_uuid})")

                        # Verifica se há tarefas na fila
                        if not task_queue.empty():
                            task = task_queue.get()
                            response = task
                        else:
                            response = {"TASK": "NO_TASK"}
                            
                        conn.sendall((json.dumps(response) + '\n').encode('utf-8'))

                    # ETAPA 3 E 4: Worker reporta status e Master envia ACK
                    elif "STATUS" in payload and payload.get("STATUS") in ["OK", "NOK"]:
                        worker_uuid = payload.get("WORKER_UUID")
                        task_type = payload.get("TASK")
                        status = payload.get("STATUS")

                        if not worker_uuid or not task_type:
                            print("[-] Erro: Campos obrigatórios ausentes no reporte de status.")
                            continue

                        # Registra no Log
                        print(f"[+] Log: Worker {worker_uuid} finalizou a tarefa {task_type} com status {status}")

                        # Envia Confirmação Final (ACK)
                        ack_payload = {
                            "STATUS": "ACK",
                            "WORKER_UUID": worker_uuid
                        }
                        conn.sendall((json.dumps(ack_payload) + '\n').encode('utf-8'))

            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[!] Erro inesperado com {addr}: {e}")
                break
                
    print(f"[-] Conexão encerrada com {addr}")

def start_master():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] Master escutando na porta {PORT}...")
        
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_worker, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_master()