import socket
import json
import time

# Configurações de conexão (devem bater com as do Master)
MASTER_HOST = '127.0.0.1'
MASTER_PORT = 5000
SERVER_UUID_TARGET = "Master_A"

def start_worker():
    while True:
        print("\n[*] Tentando conectar ao Master...")
        try:
            # Inicia conexão TCP [cite: 80]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((MASTER_HOST, MASTER_PORT))
                print("[+] Conectado ao Master com sucesso.")
                
                # Loop de Heartbeat enquanto a conexão estiver ativa [cite: 84]
                while True:
                    # Monta o payload do Worker [cite: 70]
                    payload = {
                        "SERVER_UUID": SERVER_UUID_TARGET,
                        "TASK": "HEARTBEAT"
                    }
                    
                    # Envia o JSON com \n no final [cite: 67]
                    message = json.dumps(payload) + '\n'
                    s.sendall(message.encode('utf-8'))
                    
                    # Aguarda a resposta do Master
                    data = s.recv(1024)
                    if not data:
                        # Se não recebeu dados, a conexão caiu
                        raise ConnectionResetError("Conexão fechada pelo servidor")
                    
                    # Faz o parse da resposta
                    response_str = data.decode('utf-8').strip()
                    response_json = json.loads(response_str)
                    
                    # Verifica se o status é ALIVE e faz o log [cite: 82, 95]
                    if response_json.get("RESPONSE") == "ALIVE":
                        print("Status: ALIVE")
                    
                    # Aguarda 10 segundos para o próximo Heartbeat [cite: 77]
                    time.sleep(10)

        except (ConnectionRefusedError, ConnectionResetError, socket.error):
            # Se a conexão falhar, entra no fluxo de reconexão previsto no diagrama [cite: 96, 98]
            print("Status: OFFLINE - Tentando Reconectar")
            time.sleep(10) # Aguarda antes de tentar reconectar [cite: 99]

if __name__ == "__main__":
    start_worker()