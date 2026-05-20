import unittest

from WebHostLib.fuwawa.yamls import YamlValidationError, parse_submitted_games, summarize_games


class TestFuwawaYamls(unittest.TestCase):
    def test_parse_multi_document_yaml(self) -> None:
        games = parse_submitted_games("""
name: Alice
game: A Link to the Past
---
name: Bob
game: Ocarina of Time
""")

        self.assertEqual("A Link to the Past as Alice, Ocarina of Time as Bob", summarize_games(games))

    def test_rejects_invalid_names(self) -> None:
        with self.assertRaises(YamlValidationError):
            parse_submitted_games("name: ThisNameIsFarTooLong\ngame: Archipelago\n")

        with self.assertRaises(YamlValidationError):
            parse_submitted_games("name: Bad{Name\ngame: Archipelago\n")

    def test_rejects_duplicate_names_case_insensitively(self) -> None:
        with self.assertRaises(YamlValidationError):
            parse_submitted_games("""
name: Alice
game: A Link to the Past
---
name: alice
game: Ocarina of Time
""")


if __name__ == "__main__":
    unittest.main()

