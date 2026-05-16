import socket
import json
import uuid

MASTER_HOST = "127.0.0.1"
MASTER_PORT = 5000

request_id = str(uuid.uuid4())
payload = {
    "type": "request_help",
    "request_id": request_id,
    "payload": {
        "master_id": "VIZINHO_FALSO",
        "current_load": 150,
        "capacity": 100,
        "workers_needed": 2
    }
}

print(f"[TEST] Conectando ao Master em {MASTER_HOST}:{MASTER_PORT}...")
try:
    with socket.create_connection((MASTER_HOST, MASTER_PORT), timeout=5) as s:
        s.settimeout(5.0)
        
        message = json.dumps(payload) + '\n'
        print(f"[TEST] Enviando request_help: request_id={request_id}")
        print(f"[TEST] Payload: {json.dumps(payload, indent=2)}")
        
        s.sendall(message.encode('utf-8'))
        
        response_data = s.recv(1024)
        if response_data:
            response_str = response_data.decode('utf-8').strip()
            response = json.loads(response_str)
            
            print(f"\n[TEST] Resposta recebida:")
            print(f"[TEST] Type: {response.get('type')}")
            print(f"[TEST] Request ID (esperado {request_id}): {response.get('request_id')}")
            print(f"[TEST] Payload: {json.dumps(response.get('payload'), indent=2)}")
            
            if response.get('request_id') == request_id:
                print(f"\n[OK] Request ID correlacionado corretamente!")
            else:
                print(f"\n[ERRO] Request ID não correlacionado!")
        else:
            print("[ERRO] Sem resposta do Master")

except Exception as e:
    print(f"[ERRO] Falha na conexão/comunicação: {e}")
