from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Iterable

from WebHostLib.fuwawa.events import HintEvent, ItemEvent, PROGRESSION_FLAG


def mention(discord_id: int | None) -> str:
    return f"<@{discord_id}>" if discord_id else ""


def role_mention(role_id: int | None) -> str:
    return f"<@&{role_id}>" if role_id else ""


def bold_progression_item(item_name: str, flags: int) -> str:
    return f"**{item_name}**" if flags & PROGRESSION_FLAG else item_name


def format_item_event(event: ItemEvent) -> str:
    item = bold_progression_item(event.item_name, event.flags)
    location = f" ({event.location_name})" if event.location_name else ""
    if event.sender.slot == event.receiver.slot:
        return f"{event.receiver.name} found their {item}{location}"
    return f"{event.sender.name} sent {item} to {event.receiver.name}{location}"


def format_hint_event(event: HintEvent) -> str:
    item = bold_progression_item(event.item_name, event.flags)
    entrance = f" at {event.entrance_name}" if event.entrance_name else ""
    status = "found" if event.found else "not found"
    return (
        f"[Hint]: {event.receiver.name}'s {item} is at {event.location_name} "
        f"in {event.finder.name}'s World{entrance}. ({status})"
    )


def format_goal_event(player_name: str, finished: int, total: int, complete: bool,
                      role_mention: str = "") -> str:
    message = f"# {player_name} has completed their goal.\n## {finished} out of {total} players have now finished."
    if complete:
        message += f"\n# The multiworld is now complete! Congratulations! {role_mention}".rstrip()
    return message


def format_players(rows: Iterable[tuple[str, str, str]]) -> str:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    total = 0
    for discord_name, game_name, player_name in rows:
        total += 1
        grouped[discord_name].append((game_name, player_name))
    if total == 0:
        return "No one has signed up for the multiworld yet. BAU BAU!"
    lines = [f"{total} players have joined the multiworld:"]
    for discord_name in sorted(grouped, key=str.casefold):
        lines.append(f"- {discord_name} is playing:")
        for game_name, player_name in sorted(grouped[discord_name], key=lambda row: row[0].casefold()):
            lines.append(f" - {game_name} as {player_name}")
    return "\n".join(lines)


def format_progression_dm(rows: Iterable[tuple[str, str, str]], since: datetime | None) -> str:
    grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for game_name, player_name, item_name in rows:
        grouped[game_name, player_name][item_name] += 1
    if since is None:
        header = "Progression since the start of the multiworld:"
    else:
        timestamp = int(since.replace(tzinfo=timezone.utc).timestamp())
        header = f"Progression since <t:{timestamp}:F>:"
    lines = [header]
    for game_name, player_name in sorted(grouped, key=lambda row: (row[0].casefold(), row[1].casefold())):
        lines.append(f"- {game_name} as {player_name}")
        for item_name in sorted(grouped[game_name, player_name], key=str.casefold):
            count = grouped[game_name, player_name][item_name]
            suffix = f" x{count}" if count != 1 else ""
            lines.append(f" - {item_name}{suffix}")
    lines.append("BAU BAU!")
    return "\n".join(lines)
