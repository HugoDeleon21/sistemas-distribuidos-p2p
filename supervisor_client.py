import socket
import ssl
import json
import time
import threading


def send_metrics(payload, host='nuted-ia.dev', port=443, timeout=5, use_tls=True, sni=None):
    data = (json.dumps(payload, ensure_ascii=False) + '\n').encode('utf-8')
    print(f"[SUPERVISOR] === SEND_METRICS START === host={host} port={port} use_tls={use_tls} sni={sni} data_len={len(data)}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    print(f"[SUPERVISOR] Socket criado com timeout={timeout}s")
    try:
        if use_tls:
            print(f"[SUPERVISOR] Usando TLS com server_hostname={sni or host}")
            context = ssl.create_default_context()
            print(f"[SUPERVISOR] SSL context criado, wrapping socket...")
            wrapped = context.wrap_socket(sock, server_hostname=sni or host)
            print(f"[SUPERVISOR] Socket wrapped com sucesso, tentando conectar a {host}:{port}...")
            wrapped.connect((host, port))
            print(f"[SUPERVISOR] CONECTADO COM SUCESSO! Enviando dados...")
            try:
                print(json.dumps(payload, indent=4))
            except Exception as _e:
                print(f"[SUPERVISOR] Falha ao imprimir payload: {_e}")
            wrapped.sendall(data)
            print(f"[SUPERVISOR] Dados enviados com sucesso, fechando conexão...")
            wrapped.close()
            print(f"[SUPERVISOR] Conexão fechada, retornando True")
        else:
            print(f"[SUPERVISOR] Modo sem TLS, conectando a {host}:{port}...")
            sock.connect((host, port))
            print(f"[SUPERVISOR] CONECTADO COM SUCESSO (sem TLS)! Enviando dados...")
            try:
                print(json.dumps(payload, indent=4))
            except Exception as _e:
                print(f"[SUPERVISOR] Falha ao imprimir payload: {_e}")
            sock.sendall(data)
            print(f"[SUPERVISOR] Dados enviados com sucesso, fechando conexão...")
            sock.close()
            print(f"[SUPERVISOR] Conexão fechada, retornando True")
        return True
    except socket.timeout as e:
        print(f"[SUPERVISOR] ❌ TIMEOUT ERRO: Conexão expirou após {timeout}s: {e}")
        import traceback
        traceback.print_exc()
        try:
            sock.close()
        except Exception:
            pass
        return False
    except ssl.SSLError as e:
        print(f"[SUPERVISOR] ❌ SSL ERROR: {e}")
        import traceback
        traceback.print_exc()
        try:
            sock.close()
        except Exception:
            pass
        return False
    except ConnectionRefusedError as e:
        print(f"[SUPERVISOR] ❌ CONEXAO RECUSADA por {host}:{port}: {e}")
        import traceback
        traceback.print_exc()
        try:
            sock.close()
        except Exception:
            pass
        return False
    except OSError as e:
        print(f"[SUPERVISOR] ❌ ERRO DE REDE/OS: {e}")
        import traceback
        traceback.print_exc()
        try:
            sock.close()
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"[SUPERVISOR] ❌ ERRO GERAL/INESPERADO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        try:
            sock.close()
        except Exception:
            pass
        return False


def send_periodic(payload_builder, host='nuted-ia.dev', port=443, interval=10, use_tls=True, sni=None, stop_event=None):
    """Call payload_builder() to get payload, send over TLS/TCP every `interval` seconds.
    payload_builder: callable returning a dict payload.
    """
    print(f"[SUPERVISOR] === SEND_PERIODIC INICIADA === interval={interval}s host={host}:{port} use_tls={use_tls}")
    iteration = 0
    while stop_event is None or not stop_event.is_set():
        iteration += 1
        print(f"[SUPERVISOR] *** ITERAÇÃO {iteration} *** (próxima em {interval}s)")
        try:
            print(f"[SUPERVISOR] Chamando payload_builder()...")
            payload = payload_builder()
            print(f"[SUPERVISOR] payload_builder() retornou: {type(payload).__name__} com {len(payload) if isinstance(payload, dict) else '?'} keys")
            
            print(f"[SUPERVISOR] Chamando send_metrics() com payload...")
            result = send_metrics(payload, host=host, port=port, use_tls=use_tls, sni=sni)
            print(f"[SUPERVISOR] send_metrics() retornou: {result}")
            
        except Exception as e:
            print(f"[SUPERVISOR] ❌ ERRO EM SEND_PERIODIC ITERAÇÃO {iteration}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[SUPERVISOR] Dormindo por {interval}s até próxima iteração...")
        time.sleep(interval)
