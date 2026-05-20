import unittest

from WebHostLib.fuwawa.pings import parse_ping_lines


class TestFuwawaPings(unittest.TestCase):
    def test_parse_ping_file(self) -> None:
        self.assertEqual(
            ["#Escaped", "Bow", "hookshot"],
            parse_ping_lines("""
# ignored
Bow
hookshot
Hookshot
\\#Escaped
"""),
        )

    def test_skips_already_registered(self) -> None:
        self.assertEqual(["Bow"], parse_ping_lines("Bow\nHookshot\n", {"hookshot"}))


if __name__ == "__main__":
    unittest.main()
