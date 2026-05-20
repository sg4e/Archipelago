from __future__ import annotations

from typing import Iterable

from pony.orm import commit, db_session, desc, select

from Utils import utcnow
from WebHostLib.fuwawa.models import (
    FuwawaDispatchedEvent,
    FuwawaMultiworld,
    FuwawaPlayer,
    FuwawaPing,
    FuwawaYaml,
    STATE_COMPLETED,
    STATE_IN_PROGRESS,
    STATE_REGISTRATION_CLOSED,
    STATE_REGISTRATION_OPEN,
    STATE_UNPLANNED,
)
from WebHostLib.fuwawa.yamls import SubmittedGame


ACTIVE_STATES = {STATE_UNPLANNED, STATE_REGISTRATION_OPEN, STATE_REGISTRATION_CLOSED, STATE_IN_PROGRESS}


@db_session
def get_current_multiworld() -> FuwawaMultiworld:
    multiworld = select(
        mw for mw in FuwawaMultiworld
        if mw.state in ACTIVE_STATES
    ).order_by(desc(FuwawaMultiworld.id)).first()
    if multiworld is None:
        multiworld = FuwawaMultiworld()
    return multiworld


def active_multiworld_query():
    return select(
        mw for mw in FuwawaMultiworld
        if mw.state in {STATE_REGISTRATION_OPEN, STATE_REGISTRATION_CLOSED, STATE_IN_PROGRESS}
    ).order_by(desc(FuwawaMultiworld.id))


def replace_user_signup(multiworld: FuwawaMultiworld, discord_id: int, discord_name: str, filename: str,
                        contents: str, games: Iterable[SubmittedGame]) -> None:
    for yaml_row in select(y for y in FuwawaYaml if y.multiworld == multiworld and y.discord_id == discord_id):
        yaml_row.delete()
    for player in select(p for p in FuwawaPlayer if p.multiworld == multiworld and p.discord_id == discord_id):
        player.delete()

    FuwawaYaml(
        multiworld=multiworld,
        discord_id=discord_id,
        discord_name=discord_name,
        filename=filename,
        contents=contents,
    )
    for game in games:
        FuwawaPlayer(
            multiworld=multiworld,
            discord_id=discord_id,
            discord_name=discord_name,
            name_in_game=game.name.strip(),
            game_name=game.game.strip(),
        )
    multiworld.updated_at = utcnow()


def delete_user_signup(multiworld: FuwawaMultiworld, discord_id: int) -> int:
    count = 0
    for yaml_row in list(select(y for y in FuwawaYaml if y.multiworld == multiworld and y.discord_id == discord_id)):
        yaml_row.delete()
        count += 1
    for player in list(select(p for p in FuwawaPlayer if p.multiworld == multiworld and p.discord_id == discord_id)):
        player.delete()
    multiworld.updated_at = utcnow()
    return count


def registered_names(multiworld: FuwawaMultiworld, excluding_discord_id: int | None = None) -> list[str]:
    query = select(player.name_in_game for player in FuwawaPlayer if player.multiworld == multiworld)
    names = list(query)
    if excluding_discord_id is not None:
        names = [
            player.name_in_game
            for player in select(
                player for player in FuwawaPlayer
                if player.multiworld == multiworld and player.discord_id != excluding_discord_id
            )
        ]
    return names


def has_duplicate_registered_name(multiworld: FuwawaMultiworld, names: Iterable[str],
                                  excluding_discord_id: int | None = None) -> bool:
    registered = {name.casefold() for name in registered_names(multiworld, excluding_discord_id)}
    return any(name.casefold() in registered for name in names)


def mark_dispatched(multiworld: FuwawaMultiworld, event_key: str, event_type: str) -> bool:
    if FuwawaDispatchedEvent.get(event_key=event_key):
        return False
    FuwawaDispatchedEvent(event_key=event_key, multiworld=multiworld, event_type=event_type)
    commit()
    return True


def find_player_by_slot(multiworld: FuwawaMultiworld, slot: int) -> FuwawaPlayer | None:
    return select(
        player for player in FuwawaPlayer
        if player.multiworld == multiworld and player.slot == slot
    ).first()


def find_players_by_discord(multiworld: FuwawaMultiworld, discord_id: int) -> list[FuwawaPlayer]:
    return list(select(
        player for player in FuwawaPlayer
        if player.multiworld == multiworld and player.discord_id == discord_id
    ))


def pings_for_user(multiworld: FuwawaMultiworld, discord_id: int) -> list[FuwawaPing]:
    return list(select(ping for ping in FuwawaPing if ping.multiworld == multiworld and ping.discord_id == discord_id))

