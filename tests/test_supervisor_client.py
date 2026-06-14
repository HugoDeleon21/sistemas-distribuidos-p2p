import unittest
import threading
import socket
import time
import supervisor_client


class SimpleTCPServer(threading.Thread):
    def __init__(self, host='127.0.0.1', port=9009, respond=False):
        super().__init__()
        self.host = host
        self.port = port
        self.daemon = True
        self.respond = respond
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(1)
        self._stop = False

    def run(self):
        while not self._stop:
            try:
                conn, addr = self._sock.accept()
                data = conn.recv(4096)
                if self.respond:
                    conn.sendall(b'ACK')
                conn.close()
            except Exception:
                break

    def stop(self):
        self._stop = True
        try:
            self._sock.close()
        except Exception:
            pass


class TestSupervisorClient(unittest.TestCase):
    def test_send_metrics_plain_tcp(self):
        server = SimpleTCPServer(port=9010)
        server.start()
        time.sleep(0.1)
        ok = supervisor_client.send_metrics({"a":1}, host='127.0.0.1', port=9010, use_tls=False)
        server.stop()
        self.assertTrue(ok)

    def test_send_metrics_connection_refused(self):
        # No server on this port -> should return False but not raise
        ok = supervisor_client.send_metrics({"a":1}, host='127.0.0.1', port=9011, use_tls=False, timeout=0.5)
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
