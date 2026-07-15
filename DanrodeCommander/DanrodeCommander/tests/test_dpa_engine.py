"""
tests/test_dpa_engine.py
Basic unit tests for the DPA encryption engine.
Run with: python -m pytest tests/ -v   (or plain unittest)
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import dpa_engine


class TestDpaEngine(unittest.TestCase):
    def test_xor_round_trip(self) -> None:
        source = 'print("hello")\nx = 1 + 1\n'
        key = "TestKey123"
        encoded = dpa_engine.xor_encode(source, key)
        decoded = dpa_engine.xor_decode(encoded, key)
        self.assertEqual(decoded, source)

    def test_encrypt_decrypt_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_path = os.path.join(tmp, "script.py")
            with open(py_path, "w", encoding="utf-8") as f:
                f.write('print("round trip")\n')

            dpa_path = dpa_engine.encrypt_to_dpa(py_path, key="MyKey")
            self.assertTrue(os.path.exists(dpa_path))
            self.assertEqual(dpa_engine.detect_dpa_type(dpa_path), "encrypted")

            recovered = dpa_engine.decrypt_dpa(dpa_path, key="MyKey")
            self.assertIn('print("round trip")', recovered)

    def test_plain_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dpa_path = os.path.join(tmp, "plain.dpa")
            with open(dpa_path, "w", encoding="utf-8") as f:
                f.write("#DPA-PLAIN\nprint('plain')\n")
            self.assertEqual(dpa_engine.detect_dpa_type(dpa_path), "plain")
            source = dpa_engine.decrypt_dpa(dpa_path)
            self.assertIn("print('plain')", source)

    def test_run_dpa_source_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_path = os.path.join(tmp, "ok.py")
            with open(py_path, "w", encoding="utf-8") as f:
                f.write("x = 21 * 2\n")
            dpa_path = dpa_engine.encrypt_to_dpa(py_path, key="K")
            success, message = dpa_engine.run_dpa_source(dpa_path, key="K")
            self.assertTrue(success)

    def test_run_dpa_source_syntax_error_gives_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_path = os.path.join(tmp, "bad.py")
            with open(py_path, "w", encoding="utf-8") as f:
                f.write("ptint('oops')\n")
            dpa_path = dpa_engine.encrypt_to_dpa(py_path, key="K")
            success, message = dpa_engine.run_dpa_source(dpa_path, key="K")
            self.assertFalse(success)
            self.assertIn("ptint", message)


if __name__ == "__main__":
    unittest.main()
