import socket
import threading
import json

# Configurações do Master
HOST = '127.0.0.1' # Localhost
PORT = 5000        # Porta definida para escuta
SERVER_UUID = "Master_A"

def handle_worker(conn, addr):
    """Função que roda em uma Thread separada para cada Worker conectado."""
    print(f"[+] Nova conexão de Worker estabelecida: {addr}")
    
    with conn:
        buffer = ""
        while True:
            try:
                # Recebe os dados do TCP
                data = conn.recv(1024)
                if not data:
                    print(f"[-] Conexão perdida com {addr}")
                    break
                
                # Adiciona ao buffer e processa mensagens separadas por \n
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    
                    if message.strip():
                        # Parsing do JSON recebido [cite: 81]
                        payload = json.loads(message)
                        
                        # Verifica se a Task é HEARTBEAT [cite: 72]
                        if payload.get("TASK") == "HEARTBEAT":
                            # Prepara e envia a resposta [cite: 73]
                            response = {
                                "SERVER_UUID": SERVER_UUID,
                                "TASK": "HEARTBEAT",
                                "RESPONSE": "ALIVE"
                            }
                            # Converte para string JSON e adiciona o \n [cite: 38]
                            response_str = json.dumps(response) + '\n'
                            conn.sendall(response_str.encode('utf-8'))
                            
            except json.JSONDecodeError:
                print(f"[!] Erro ao decodificar JSON de {addr}")
            except Exception as e:
                print(f"[!] Erro na conexão com {addr}: {e}")
                break

def start_master():
    """Inicia o servidor TCP do Master[cite: 65]."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] Master {SERVER_UUID} escutando na porta {PORT}...")
        
        while True:
            # Aceita novas conexões de Workers
            conn, addr = server.accept()
            # Cria uma Thread para lidar com o Worker concorrentemente 
            thread = threading.Thread(target=handle_worker, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_master()