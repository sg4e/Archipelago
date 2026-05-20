from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import yaml


MAX_YAML_SIZE = 64 * 1024 * 1024
MAX_PLAYER_NAME_LENGTH = 16
RESERVED_PLAYER_NAMES = {"fuwawa"}


@dataclass(frozen=True)
class SubmittedGame:
    game: str
    name: str


class YamlValidationError(ValueError):
    pass


def parse_submitted_games(contents: str) -> list[SubmittedGame]:
    games: list[SubmittedGame] = []
    for document in yaml.safe_load_all(contents):
        if document is None:
            continue
        if not isinstance(document, dict):
            raise YamlValidationError("Each YAML document must be a mapping.")
        name = document.get("name")
        game = document.get("game")
        if not isinstance(name, str) or not isinstance(game, str):
            raise YamlValidationError("Each YAML must include string 'name' and 'game' fields.")
        games.append(SubmittedGame(game=game, name=name))
    if not games:
        raise YamlValidationError("No game settings were found in the YAML.")
    validate_submitted_games(games)
    return games


def validate_submitted_games(games: Iterable[SubmittedGame]) -> None:
    seen: set[str] = set()
    for game in games:
        name = game.name.strip()
        if not name:
            raise YamlValidationError("Player names cannot be blank.")
        if len(name) > MAX_PLAYER_NAME_LENGTH:
            raise YamlValidationError(f"Player names cannot be longer than {MAX_PLAYER_NAME_LENGTH} characters: {name}")
        if "{" in name or "}" in name:
            raise YamlValidationError(f"Player names cannot contain curly braces: {name}")
        lowered = name.lower()
        if lowered in RESERVED_PLAYER_NAMES:
            raise YamlValidationError(f"Player name {name} is reserved.")
        if lowered in seen:
            raise YamlValidationError(f"Player name {name} appears more than once in this upload.")
        seen.add(lowered)


def summarize_games(games: Iterable[SubmittedGame]) -> str:
    return ", ".join(f"{game.game} as {game.name}" for game in games)

