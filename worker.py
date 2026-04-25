import socket
import json
import time
import random
import shutil
import master # Importa o seu código do Master para podermos acioná-lo depois!

# ATENÇÃO: IP do Notebook
MASTER_HOST = '192.168.18.20' 
MASTER_PORT = 5000
ELECTION_PORT = 5001

WORKER_UUID = f"W-{random.randint(100, 999)}"
SERVER_UUID = "MASTER_5" 

def get_free_disk():
    """Retorna o espaço livre no HD atual em bytes"""
    return shutil.disk_usage("/").free

def get_local_ip():
    """Descobre o próprio IP na rede (Versão Blindada para Windows)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((MASTER_HOST, 5000)) # Finge conectar no master só para o Windows decidir a placa de rede
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

def hold_election():
    """Executa o Algoritmo do Valentão via UDP Broadcast (Com Desempate)"""
    print("\n[ELECTION] O Master caiu! Iniciando Eleição do Valentão...")
    my_disk = get_free_disk()
    my_ip = get_local_ip()
    
    print(f"[ELECTION] Meu espaço livre no HD: {my_disk / (1024**3):.2f} GB")

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(('0.0.0.0', ELECTION_PORT))
    udp_sock.settimeout(2.0)

    election_msg = {"TYPE": "ELECTION", "UUID": WORKER_UUID, "DISK": my_disk, "IP": my_ip}
    udp_sock.sendto((json.dumps(election_msg) + '\n').encode('utf-8'), ('255.255.255.255', ELECTION_PORT))

    highest_disk = my_disk
    winner_ip = my_ip
    winner_uuid = WORKER_UUID

    end_time = time.time() + 5.0 
    while time.time() < end_time:
        try:
            data, addr = udp_sock.recvfrom(1024)
            msg = json.loads(data.decode('utf-8').strip())

            if msg.get("TYPE") == "ELECTION" and msg.get("UUID") != WORKER_UUID:
                peer_disk = msg.get("DISK")
                peer_uuid = msg.get("UUID")
                print(f"[ELECTION] Ouvi o Worker {peer_uuid} com {peer_disk / (1024**3):.2f} GB.")
                
                # Regra do Valentão + Desempate por UUID
                if peer_disk > highest_disk or (peer_disk == highest_disk and peer_uuid > winner_uuid):
                    highest_disk = peer_disk
                    winner_ip = msg.get("IP")
                    winner_uuid = peer_uuid
                    
            elif msg.get("TYPE") == "VICTORY":
                winner_ip = msg.get("IP")
                winner_uuid = msg.get("UUID")
                break

        except socket.timeout:
            continue
        except Exception:
            break

    udp_sock.close()

    if winner_uuid == WORKER_UUID:
        print("\n[ELECTION] VITÓRIA! Eu tenho o maior HD (ou venci no desempate). Eu sou o novo Master!")
        vic_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        vic_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        vic_msg = {"TYPE": "VICTORY", "UUID": WORKER_UUID, "IP": my_ip}
        vic_sock.sendto((json.dumps(vic_msg) + '\n').encode('utf-8'), ('255.255.255.255', ELECTION_PORT))
        vic_sock.close()
        return True, my_ip
    else:
        print(f"\n[ELECTION] Fui derrotado. O novo Master é o {winner_uuid} no IP {winner_ip}.")
        return False, winner_ip

def start_worker():
    global MASTER_HOST
    connection_errors = 0

    while True:
        print(f"\n[*] Worker {WORKER_UUID} tentando conectar ao Master em {MASTER_HOST}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((MASTER_HOST, MASTER_PORT))
                s.settimeout(5.0) 
                
                connection_errors = 0 
                print(f"[+] Conectado ao Master!")
                
                while True:
                    payload = {"WORKER": "ALIVE", "WORKER_UUID": WORKER_UUID}
                    if SERVER_UUID is not None:
                         payload["SERVER_UUID"] = SERVER_UUID
                         
                    s.sendall((json.dumps(payload) + '\n').encode('utf-8'))

                    data = s.recv(1024)
                    if not data: raise ConnectionResetError()
                    response = json.loads(data.decode('utf-8').strip())

                    if response.get("TASK") == "QUERY":
                        user = response.get("USER")
                        print(f"[*] Tarefa recebida: QUERY para o usuário '{user}'. Processando...")
                        time.sleep(random.uniform(1, 3)) 
                        
                        status_payload = {"STATUS": "OK", "TASK": "QUERY", "WORKER_UUID": WORKER_UUID}
                        s.sendall((json.dumps(status_payload) + '\n').encode('utf-8'))
                        
                        ack_data = s.recv(1024)
                        if not ack_data: raise ConnectionResetError()
                        ack_response = json.loads(ack_data.decode('utf-8').strip())
                        
                        if ack_response.get("STATUS") == "ACK":
                            print("[+] ACK recebido. Ciclo concluído.")

                    elif response.get("TASK") == "NO_TASK":
                        print("[-] Fila vazia (NO_TASK). Aguardando próximo ciclo...")
                    
                    time.sleep(4) 

        # AGORA ELE CAPTURA QUALQUER ERRO DO WINDOWS (Sem escape!)
        except Exception as e:
            connection_errors += 1
            print(f"[!] Falha de conexão. Erro {connection_errors}/4. ({type(e).__name__})")
            
            if connection_errors >= 4:
                is_master, new_master_ip = hold_election()
                
                if is_master:
                    print("[*] Iniciando a metamorfose: Deixando de ser Worker para virar Master...\n")
                    master.SERVER_UUID = f"NOVO_MASTER_{WORKER_UUID}"
                    master.start_master() 
                    break 
                else:
                    print(f"[*] Atualizando rota para o novo Master: {new_master_ip}")
                    MASTER_HOST = new_master_ip
                    connection_errors = 0 
                    time.sleep(3)
            else:
                time.sleep(2) 

if __name__ == "__main__":
    start_worker()