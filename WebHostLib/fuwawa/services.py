from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pony.orm import commit, db_session, select

from Utils import utcnow
from WebHostLib import to_url
from WebHostLib.fuwawa.events import ItemEvent, PROGRESSION_FLAG
from WebHostLib.fuwawa.models import (
    FuwawaItemEvent,
    FuwawaMultiworld,
    FuwawaPing,
    FuwawaPlayer,
    STATE_COMPLETED,
    STATE_IN_PROGRESS,
    STATE_REGISTRATION_CLOSED,
    STATE_REGISTRATION_OPEN,
)
from WebHostLib.models import Room


def room_page_path(room: Room) -> str:
    return f"/room/{to_url(room.id)}"


def connect_address(host_address: str, room: Room) -> str:
    return f"{host_address}:{room.last_port}" if room.last_port else host_address


def sync_player_slots(multiworld: FuwawaMultiworld) -> None:
    if multiworld.room is None:
        return
    room_slots = {
        slot.player_name.casefold(): slot.player_id
        for slot in multiworld.room.seed.slots
    }
    for player in multiworld.players:
        player.slot = room_slots.get(player.name_in_game.casefold())


def slot_discord_ids(multiworld: FuwawaMultiworld) -> dict[int, int]:
    return {
        player.slot: player.discord_id
        for player in multiworld.players
        if player.slot is not None
    }


def player_by_slot(multiworld: FuwawaMultiworld, slot: int) -> FuwawaPlayer | None:
    return select(
        player for player in FuwawaPlayer
        if player.multiworld == multiworld and player.slot == slot
    ).first()


def players_for_discord(multiworld: FuwawaMultiworld, discord_id: int) -> list[FuwawaPlayer]:
    return list(select(
        player for player in FuwawaPlayer
        if player.multiworld == multiworld and player.discord_id == discord_id
    ))


def attach_room(multiworld: FuwawaMultiworld, room: Room, host_address: str, keepalive_timeout_seconds: int) -> None:
    room.timeout = keepalive_timeout_seconds
    multiworld.room = room
    multiworld.ap_server = connect_address(host_address, room)
    multiworld.web_page = room_page_path(room)
    multiworld.total_participants = len(list(multiworld.players))
    multiworld.state = STATE_IN_PROGRESS
    multiworld.updated_at = utcnow()
    sync_player_slots(multiworld)


def close_registration(multiworld: FuwawaMultiworld) -> None:
    multiworld.state = STATE_REGISTRATION_CLOSED
    multiworld.updated_at = utcnow()


def open_registration(multiworld: FuwawaMultiworld, theme: str, role_id: int, unix_start_time: int) -> None:
    multiworld.state = STATE_REGISTRATION_OPEN
    multiworld.theme = theme
    multiworld.discord_role_id = role_id
    multiworld.unix_start_time = unix_start_time
    multiworld.updated_at = utcnow()


def increment_finished(multiworld: FuwawaMultiworld) -> int:
    multiworld.participants_finished += 1
    multiworld.updated_at = utcnow()
    return multiworld.participants_finished


def complete_multiworld(multiworld: FuwawaMultiworld) -> None:
    multiworld.state = STATE_COMPLETED
    multiworld.updated_at = utcnow()


def upsert_item_event(multiworld: FuwawaMultiworld, event: ItemEvent) -> bool:
    event_key = scoped_event_key(multiworld, event.event_key)
    if FuwawaItemEvent.get(event_key=event_key):
        return False
    FuwawaItemEvent(
        event_key=event_key,
        multiworld=multiworld,
        team=event.team,
        receiver_slot=event.receiver.slot,
        receiver_name=event.receiver.name,
        receiver_game=event.receiver.game,
        receiver_discord_id=event.receiver.discord_id,
        sender_slot=event.sender.slot,
        sender_name=event.sender.name,
        sender_game=event.sender.game,
        sender_discord_id=event.sender.discord_id,
        item_id=event.item_id,
        item_name=event.item_name,
        location_id=event.location_id,
        location_name=event.location_name,
        flags=event.flags,
        received_index=event.received_index,
    )
    return True


def upsert_item_payload(multiworld: FuwawaMultiworld, payload: dict,
                        receiver_discord_id: int | None,
                        sender_discord_id: int | None) -> bool:
    event_key = scoped_event_key(multiworld, payload["event_key"])
    if FuwawaItemEvent.get(event_key=event_key):
        return False
    data = payload["data"]
    receiver = data["receiver"]
    sender = data["sender"]
    FuwawaItemEvent(
        event_key=event_key,
        multiworld=multiworld,
        team=data["team"],
        receiver_slot=receiver["slot"],
        receiver_name=receiver["name"],
        receiver_game=receiver["game"],
        receiver_discord_id=receiver_discord_id,
        sender_slot=sender["slot"],
        sender_name=sender["name"],
        sender_game=sender["game"],
        sender_discord_id=sender_discord_id,
        item_id=data["item_id"],
        item_name=data["item_name"],
        location_id=data["location_id"],
        location_name=data["location_name"],
        flags=data["flags"],
        received_index=data["received_index"],
    )
    return True


def scoped_event_key(multiworld: FuwawaMultiworld, event_key: str) -> str:
    return f"fuwawa:{multiworld.id}:{event_key}"


def user_pings_for_item(multiworld: FuwawaMultiworld, discord_id: int, item_name: str) -> list[FuwawaPing]:
    return [
        ping for ping in select(
            ping for ping in FuwawaPing
            if ping.multiworld == multiworld and ping.discord_id == discord_id
        )
        if ping.item_name.casefold() == item_name.casefold()
    ]


def progression_rows_since(multiworld: FuwawaMultiworld, discord_id: int,
                           since: datetime | None) -> list[tuple[str, str, str]]:
    query = select(
        item for item in FuwawaItemEvent
        if item.multiworld == multiworld
        and item.receiver_discord_id == discord_id
    )
    rows = []
    for item in query:
        if not item.flags & PROGRESSION_FLAG:
            continue
        if since is not None and item.time_acquired <= since:
            continue
        rows.append((item.receiver_game, item.receiver_name, item.item_name))
    return rows


def set_user_progression_cursor(multiworld: FuwawaMultiworld, discord_id: int, when: datetime) -> None:
    for player in players_for_discord(multiworld, discord_id):
        player.last_progression_call = when
    commit()


@db_session
def get_room(room_id: UUID) -> Room | None:
    return Room.get(id=room_id)
