import unittest

from ..client import get_wins_and_losses_from_bytes


class TestSimple(unittest.TestCase):

    def test_get_wins_and_losses_from_bytes(self):
        actual_bytes = bytes.fromhex("02000100")
        parsed = get_wins_and_losses_from_bytes(actual_bytes)
        expected = (2, 1)
        self.assertEqual(parsed, expected)
