import unittest
import metrics


class TestMetricsPayload(unittest.TestCase):
    def test_build_payload_keys(self):
        p = metrics.build_payload('master_x', 'host.local', 'master', 'performance_report')
        self.assertIn('server_uid', p)
        self.assertIn('hostname', p)
        self.assertIn('performance', p)
        self.assertIn('timestamp', p)


if __name__ == '__main__':
    unittest.main()
