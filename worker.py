import socket
import json
import time
import random
import shutil
import master # Importa o seu código do Master para podermos acioná-lo depois!

# ATENÇÃO: IP do Notebook
MASTER_HOST = '127.0.0.1' 
MASTER_PORT = 5001
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
        s.connect((MASTER_HOST, MASTER_PORT)) # Finge conectar no master só para o Windows decidir a placa de rede
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

def send_json(sock, payload):
    """Envia um JSON delimitado por newline."""
    sock.sendall((json.dumps(payload) + '\n').encode('utf-8'))


def receive_json(sock):
    """Recebe um JSON delimitado por newline."""
    buffer = ""
    while True:
        data = sock.recv(1024)
        if not data:
            return None
        buffer += data.decode('utf-8')
        if '\n' in buffer:
            message, _ = buffer.split('\n', 1)
            if message.strip():
                try:
                    return json.loads(message)
                except json.JSONDecodeError:
                    continue
    return None


def start_worker():
    global MASTER_HOST, SERVER_UUID
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
                         
                    send_json(s, payload)

                    response = receive_json(s)
                    if response is None:
                        raise ConnectionResetError()

                    # Verificar se é um comando de redirecionamento
                    if response.get("type") == "command_redirect":
                        new_master_addr = response.get("payload", {}).get("new_master_address")
                        print(f"[REDIRECT] Recebido comando de redirecionamento para {new_master_addr}")
                        
                        # Encerrar conexão atual
                        print(f"[REDIRECT] Encerrando conexão com Master atual...")
                        s.close()
                        
                        # Extrair IP e porta do novo Master
                        try:
                            new_ip, new_port_str = new_master_addr.split(":")
                            new_port = int(new_port_str)
                        except Exception as e:
                            print(f"[ERRO] Endereço de novo Master inválido {new_master_addr}: {e}")
                            break
                        
                        # Conectar ao novo Master
                        print(f"[REDIRECT] Conectando ao novo Master em {new_ip}:{new_port}...")
                        try:
                            new_sock = socket.create_connection((new_ip, new_port), timeout=5)
                            new_sock.settimeout(5.0)
                        except Exception as e:
                            print(f"[ERRO] Falha ao conectar ao novo Master: {e}")
                            break
                        
                        # Enviar register_temporary_worker
                        original_master_address = f"{MASTER_HOST}:{MASTER_PORT}"
                        reg_payload = {
                            "type": "register_temporary_worker",
                            "request_id": str(random.randint(100000, 999999)),
                            "payload": {
                                "worker_id": WORKER_UUID,
                                "original_master_address": original_master_address
                            }
                        }
                        
                        print(f"[REDIRECT] Enviando register_temporary_worker ao novo Master...")
                        send_json(new_sock, reg_payload)
                        
                        # Receber confirmação (idealmente um ACK ou similar)
                        ack = receive_json(new_sock)
                        print(f"[REDIRECT] Resposta do novo Master: {ack}")
                        
                        # Continuar o protocolo normal com o novo socket
                        s = new_sock
                        continue

                    elif response.get("type") == "command_release":
                        origin_address = response.get("payload", {}).get("original_master_address")
                        print(f"[RELEASE] Recebido command_release para retornar a {origin_address}")
                        
                        if not origin_address:
                            print("[ERRO] original_master_address ausente no command_release")
                            break
                        
                        print(f"[RELEASE] Encerrando conexão com Master atual...")
                        s.close()
                        
                        try:
                            origin_ip, origin_port_str = origin_address.split(":")
                            origin_port = int(origin_port_str)
                        except Exception as e:
                            print(f"[ERRO] Endereço do Master de origem inválido {origin_address}: {e}")
                            break
                        
                        print(f"[RELEASE] Conectando de volta ao Master de origem em {origin_ip}:{origin_port}...")
                        try:
                            return_sock = socket.create_connection((origin_ip, origin_port), timeout=5)
                            return_sock.settimeout(5.0)
                        except Exception as e:
                            print(f"[ERRO] Falha ao reconectar ao Master de origem: {e}")
                            break
                        
                        MASTER_HOST = origin_ip
                        SERVER_UUID = None
                        
                        s = return_sock
                        continue

                    if response.get("TASK") == "QUERY":
                        user = response.get("USER")
                        print(f"[*] Tarefa recebida: QUERY para o usuário '{user}'. Processando...")
                        time.sleep(random.uniform(8, 12)) 
                        
                        status_payload = {"STATUS": "OK", "TASK": "QUERY", "WORKER_UUID": WORKER_UUID}
                        send_json(s, status_payload)
                        
                        ack_response = receive_json(s)
                        if ack_response is None:
                            raise ConnectionResetError()
                        
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