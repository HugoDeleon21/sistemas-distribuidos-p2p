import unittest
import worker


class FakeSocket:
    def __init__(self, data=b""):
        self.data = data
        self.sent = b""
        self.timeout = None

    def sendall(self, payload):
        self.sent += payload

    def recv(self, bufsize):
        if self.data:
            data = self.data
            self.data = b""
            return data
        return b""


class TestWorkerBorrowedLifecycle(unittest.TestCase):
    def test_parse_host_port_valid(self):
        ip, port = worker.parse_host_port("10.0.0.5:5000")
        self.assertEqual(ip, "10.0.0.5")
        self.assertEqual(port, 5000)

    def test_parse_host_port_invalid(self):
        self.assertEqual(worker.parse_host_port("bad-format"), (None, None))
        self.assertEqual(worker.parse_host_port(""), (None, None))

    def test_send_and_receive_json_roundtrip(self):
        data = b'{"type":"command_redirect","request_id":"abc-123","payload":{"new_master_address":"127.0.0.1:5000"}}\n'
        fake_socket = FakeSocket(data=data)
        message = worker.receive_json(fake_socket)

        self.assertEqual(message["type"], "command_redirect")
        self.assertEqual(message["payload"]["new_master_address"], "127.0.0.1:5000")

        send_socket = FakeSocket()
        worker.send_json(send_socket, message)
        actual = send_socket.sent.decode("utf-8")
        self.assertEqual(
            __import__("json").loads(actual.strip()),
            {
                "type": "command_redirect",
                "request_id": "abc-123",
                "payload": {"new_master_address": "127.0.0.1:5000"},
            },
        )


if __name__ == "__main__":
    unittest.main()
