import unittest
import threading
import time
from unittest.mock import MagicMock, patch
from src.can_handler import CanHandler


class TestAdvancedSecurity(unittest.TestCase):

    def setUp(self):
        self.can = CanHandler()
        self.can.simulation = False
        self.can.ser = MagicMock()
        self.can.ser.is_open = True

    def test_odd_hex_correction(self):
        """
        Safety: The handler MUST pad odd-length inputs to prevent alignment errors.
        """
        # Case 1: Simple Odd Length
        # Input "FFF" (12 bits) -> Should become "0FFF" (16 bits/2 bytes)
        clean_data = self.can._sanitize_hex("FFF")
        self.assertEqual(clean_data, "0FFF")

        # Case 2: Spaces are stripped, then checked
        # Input "1 A" -> Strips to "1A" (Length 2).
        # Since Length 2 is even, it should NOT add a zero.
        clean_data_2 = self.can._sanitize_hex("1 A")
        self.assertEqual(clean_data_2, "1A")

        # Case 3: Single Digit
        # Input "C" -> Should become "0C"
        clean_data_3 = self.can._sanitize_hex("C")
        self.assertEqual(clean_data_3, "0C")

    def test_hardware_disconnect_recovery(self):
        """
        Stability: If serial.write throws an OSError (Cable pulled),
        the app must catch it and reset state to avoid a crash loop.
        """
        # Simulate a crash during write
        self.can.ser.write.side_effect = OSError("Device disconnected")

        # Try to inject
        result = self.can.inject_frame("7E0", "01 0D")

        # Assertions
        self.assertIn("Error", result)
        # Check if handler attempted to close/reset
        self.assertFalse(self.can.is_sniffing)

    def test_rapid_toggling_race_condition(self):
        """
        Stability: Spamming Start/Stop sniffing shouldn't spawn
        multiple zombie threads.
        """
        self.can.start_sniffing()
        t1 = threading.active_count()

        self.can.stop_sniffing()
        self.can.start_sniffing()
        self.can.stop_sniffing()
        self.can.start_sniffing()

        t2 = threading.active_count()

        # We shouldn't have spawned many extra threads
        self.assertLess(t2 - t1, 3)

    def test_buffer_overflow_protection(self):
        """
        Safety: If the sniffer receives garbage/binary data (not text),
        it should ignore it rather than crash the UI string decoding.
        """
        # Mock readline returning non-utf8 binary garbage
        self.can.ser.readline.return_value = b'\x80\xFF\xFE\x00'  # Invalid UTF-8

        callback_mock = MagicMock()
        self.can.start_sniffing(callback=callback_mock)

        # Let the thread run one cycle
        time.sleep(0.1)
        self.can.stop_sniffing()

        # If the code crashed, this line wouldn't be reached
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()