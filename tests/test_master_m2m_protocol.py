import unittest
import master


class TestMasterM2MProtocol(unittest.TestCase):
    def setUp(self):
        with master.load_lock:
            master.workers_na_farm.clear()
            master.borrowed_workers.clear()

    def test_build_request_help_payload(self):
        message = master.build_m2m_message(
            "request_help",
            "1234-5678-9012",
            {
                "master_id": "MASTER_5",
                "master_address": "127.0.0.1:5000",
                "current_load": 120,
                "capacity": 100,
                "workers_needed": 2,
            },
        )
        self.assertEqual(message["type"], "request_help")
        self.assertEqual(message["request_id"], "1234-5678-9012")
        self.assertEqual(message["payload"]["master_id"], "MASTER_5")
        self.assertEqual(message["payload"]["workers_needed"], 2)

    def test_parse_host_port_valid(self):
        ip, port = master.parse_host_port("192.168.18.20:5001")
        self.assertEqual(ip, "192.168.18.20")
        self.assertEqual(port, 5001)

    def test_parse_host_port_invalid(self):
        self.assertEqual(master.parse_host_port("invalid_address"), (None, None))
        self.assertEqual(master.parse_host_port("") , (None, None))

    def test_count_available_workers_excludes_borrowed(self):
        with master.load_lock:
            master.workers_na_farm["W-1"] = ("127.0.0.1", 5002)
            master.workers_na_farm["W-2"] = ("127.0.0.1", 5003)
            master.borrowed_workers["W-2"] = "192.168.18.20:5001"

        self.assertEqual(master.count_available_workers(), ["W-1"])


if __name__ == "__main__":
    unittest.main()
