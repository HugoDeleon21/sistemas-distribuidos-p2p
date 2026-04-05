import socket
import json
import time
import random

MASTER_HOST = '127.0.0.1'
MASTER_PORT = 5000

WORKER_UUID = "W-123"
SERVER_UUID = None  # None significa que é um Worker Local. Para testar o CT02, mude None para "Master-B"

def start_worker():
    while True:
        print("\n[*] Tentando conectar ao Master...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((MASTER_HOST, MASTER_PORT))
                s.settimeout(5.0) # Timeout rigoroso de 5 segundos estipulado pelo projeto
                print("[+] Conectado ao Master.")
                
                while True:
                    # 1. Apresentação e Pedido de Tarefa
                    payload = {
                        "WORKER": "ALIVE",
                        "WORKER_UUID": WORKER_UUID
                    }
                    # Adiciona campo opcional se for emprestado (Pylance aprova)
                    if SERVER_UUID is not None:
                         payload["SERVER_UUID"] = SERVER_UUID
                         
                    s.sendall((json.dumps(payload) + '\n').encode('utf-8'))

                    # 2. Recebendo Tarefa do Master
                    data = s.recv(1024)
                    if not data: raise ConnectionResetError()
                    response = json.loads(data.decode('utf-8').strip())

                    # Processando a tarefa
                    if response.get("TASK") == "QUERY":
                        user = response.get("USER")
                        print(f"[*] Tarefa recebida: QUERY para o usuário '{user}'. Processando...")
                        
                        time.sleep(random.uniform(1, 3)) # Simula o processamento
                        
                        status_result = "OK" # Altere para "NOK" temporariamente para testar o CT05
                        
                        # 3. Reporte de Status
                        status_payload = {
                            "STATUS": status_result,
                            "TASK": "QUERY",
                            "WORKER_UUID": WORKER_UUID
                        }
                        s.sendall((json.dumps(status_payload) + '\n').encode('utf-8'))
                        
                        # 4. Confirmação Final (ACK)
                        ack_data = s.recv(1024)
                        if not ack_data: raise ConnectionResetError()
                        ack_response = json.loads(ack_data.decode('utf-8').strip())
                        
                        if ack_response.get("STATUS") == "ACK":
                            print("[+] ACK recebido do Master. Ciclo concluído com sucesso.")

                    elif response.get("TASK") == "NO_TASK":
                        print("[-] Fila vazia (NO_TASK). Aguardando próximo ciclo...")
                    
                    time.sleep(4) # Pausa antes de pedir outra tarefa para não floodar o terminal

        except socket.timeout:
            print("[!] Timeout: O Master demorou mais de 5 segundos. Reconectando...")
            time.sleep(2)
        except (ConnectionRefusedError, ConnectionResetError):
            print("[!] Status: OFFLINE - Tentando Reconectar...")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()