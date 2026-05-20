from __future__ import annotations

from datetime import datetime

from pony.orm import Optional, PrimaryKey, Required, Set, LongStr

from Utils import utcnow
from WebHostLib.models import Room, db


STATE_UNPLANNED = "UNPLANNED"
STATE_REGISTRATION_OPEN = "REGISTRATION_OPEN"
STATE_REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
STATE_IN_PROGRESS = "IN_PROGRESS"
STATE_COMPLETED = "COMPLETED"


class FuwawaMultiworld(db.Entity):
    id = PrimaryKey(int, auto=True)
    state = Required(str, default=STATE_UNPLANNED)
    theme = Optional(str)
    unix_start_time = Optional(int)
    discord_role_id = Optional(int, size=64)
    room = Optional(Room, reverse="fuwawa_multiworlds")
    ap_server = Optional(str)
    web_page = Optional(str)
    total_participants = Required(int, default=0)
    participants_finished = Required(int, default=0)
    created_at: datetime = Required(datetime, default=lambda: utcnow())
    updated_at: datetime = Required(datetime, default=lambda: utcnow())
    yamls = Set("FuwawaYaml")
    players = Set("FuwawaPlayer")
    pings = Set("FuwawaPing")
    items = Set("FuwawaItemEvent")
    dispatched_events = Set("FuwawaDispatchedEvent")


class FuwawaYaml(db.Entity):
    id = PrimaryKey(int, auto=True)
    multiworld = Required(FuwawaMultiworld)
    discord_id = Required(int, size=64, index=True)
    discord_name = Required(str)
    filename = Required(str)
    contents = Required(LongStr)
    created_at: datetime = Required(datetime, default=lambda: utcnow())


class FuwawaPlayer(db.Entity):
    id = PrimaryKey(int, auto=True)
    multiworld = Required(FuwawaMultiworld)
    discord_id = Required(int, size=64, index=True)
    discord_name = Required(str)
    name_in_game = Required(str, index=True)
    game_name = Required(str)
    slot = Optional(int)
    pinged_when_helpful = Required(bool, default=False)
    ping_all_progression = Required(bool, default=False)
    last_progression_call = Optional(datetime)


class FuwawaPing(db.Entity):
    id = PrimaryKey(int, auto=True)
    multiworld = Required(FuwawaMultiworld)
    discord_id = Required(int, size=64, index=True)
    item_name = Required(str)


class FuwawaItemEvent(db.Entity):
    event_key = PrimaryKey(str)
    multiworld = Required(FuwawaMultiworld)
    team = Required(int, default=0)
    receiver_slot = Required(int)
    receiver_name = Required(str)
    receiver_game = Required(str)
    receiver_discord_id = Optional(int, size=64)
    sender_slot = Required(int)
    sender_name = Required(str)
    sender_game = Optional(str)
    sender_discord_id = Optional(int, size=64)
    item_id = Required(int)
    item_name = Required(str)
    location_id = Required(int)
    location_name = Optional(str)
    flags = Required(int, default=0)
    received_index = Required(int)
    time_acquired: datetime = Required(datetime, default=lambda: utcnow())


class FuwawaDispatchedEvent(db.Entity):
    event_key = PrimaryKey(str)
    multiworld = Required(FuwawaMultiworld)
    event_type = Required(str)
    created_at: datetime = Required(datetime, default=lambda: utcnow())
