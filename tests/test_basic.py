import unittest
from src.obd_handler import OBDHandler


class TestOBDLogic(unittest.TestCase):

    def setUp(self):
        # Run in simulation mode for testing
        self.handler = OBDHandler(simulation=True)
        self.handler.connect()

    def test_connection_status(self):
        self.assertTrue(self.handler.connect())
        self.assertIn("Connected", self.handler.status)

    def test_rpm_range(self):
        rpm = self.handler.query_sensor("RPM")
        print(f"Testing RPM: Got {rpm}")
        self.assertIsInstance(rpm, int)
        self.assertGreaterEqual(rpm, 0)

    def test_voltage_format(self):
        volts = self.handler.query_sensor("CONTROL_MODULE_VOLTAGE")
        print(f"Testing Voltage: Got {volts}")
        self.assertIsInstance(volts, float)

    def test_dtc_structure(self):
        codes = self.handler.get_dtc()
        self.assertIsInstance(codes, list)
        if len(codes) > 0:
            self.assertEqual(len(codes[0]), 2)  # Should be (Code, Description)


if __name__ == '__main__':
    unittest.main()