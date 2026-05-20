from __future__ import annotations

from dataclasses import dataclass
from time import monotonic_ns
from typing import Any, Iterable

from NetUtils import ClientStatus, Hint, NetworkItem
from WebHostLib.fuwawa.bus import room_event


TEAM = 0
PROGRESSION_FLAG = 0b001


@dataclass(frozen=True)
class SlotRef:
    team: int
    slot: int
    name: str
    game: str
    discord_id: int | None = None


@dataclass(frozen=True)
class ItemEvent:
    event_key: str
    team: int
    receiver: SlotRef
    sender: SlotRef
    item_id: int
    item_name: str
    location_id: int
    location_name: str | None
    flags: int
    received_index: int

    @property
    def is_progression(self) -> bool:
        return bool(self.flags & PROGRESSION_FLAG)


@dataclass(frozen=True)
class HintEvent:
    event_key: str
    team: int
    receiver: SlotRef
    finder: SlotRef
    item_id: int
    item_name: str
    location_id: int
    location_name: str
    entrance_name: str
    flags: int
    found: bool
    status: int


@dataclass(frozen=True)
class GoalEvent:
    event_key: str
    team: int
    slot: SlotRef


def slot_ref(tracker, team: int, slot: int, discord_id: int | None = None) -> SlotRef:
    slot_info = tracker.get_slot_info(slot)
    return SlotRef(team=team, slot=slot, name=slot_info.name, game=slot_info.game, discord_id=discord_id)


def item_name(tracker, game: str, item_id: int) -> str:
    return tracker.item_id_to_name[game][item_id]


def location_name(tracker, game: str, location_id: int) -> str | None:
    if location_id < 0:
        return None
    return tracker.location_id_to_name[game][location_id]


def item_event_from_network_item(tracker, team: int, receiver_slot: int, item: NetworkItem, received_index: int,
                                 receiver_discord_id: int | None = None,
                                 sender_discord_id: int | None = None) -> ItemEvent:
    receiver = slot_ref(tracker, team, receiver_slot, receiver_discord_id)
    sender = slot_ref(tracker, team, item.player, sender_discord_id)
    return ItemEvent(
        event_key=f"item:{team}:{receiver_slot}:{received_index}",
        team=team,
        receiver=receiver,
        sender=sender,
        item_id=item.item,
        item_name=item_name(tracker, receiver.game, item.item),
        location_id=item.location,
        location_name=location_name(tracker, sender.game, item.location),
        flags=item.flags,
        received_index=received_index,
    )


def iter_item_events(tracker, slot_discord_ids: dict[int, int]) -> Iterable[ItemEvent]:
    for team, players in tracker.get_all_players().items():
        for player in players:
            for index, network_item in enumerate(tracker.get_player_received_items(team, player)):
                yield item_event_from_network_item(
                    tracker,
                    team,
                    player,
                    network_item,
                    index,
                    receiver_discord_id=slot_discord_ids.get(player),
                    sender_discord_id=slot_discord_ids.get(network_item.player),
                )


def hint_event_from_hint(tracker, team: int, hint: Hint, receiver_discord_id: int | None = None,
                         finder_discord_id: int | None = None) -> HintEvent:
    receiver = slot_ref(tracker, team, hint.receiving_player, receiver_discord_id)
    finder = slot_ref(tracker, team, hint.finding_player, finder_discord_id)
    return HintEvent(
        event_key=(
            f"hint:{team}:{hint.receiving_player}:{hint.finding_player}:"
            f"{hint.location}:{hint.item}:{hint.entrance}"
        ),
        team=team,
        receiver=receiver,
        finder=finder,
        item_id=hint.item,
        item_name=item_name(tracker, receiver.game, hint.item),
        location_id=hint.location,
        location_name=location_name(tracker, finder.game, hint.location) or f"Location {hint.location}",
        entrance_name=hint.entrance,
        flags=hint.item_flags,
        found=hint.found,
        status=int(hint.status),
    )


def iter_hint_events(tracker, slot_discord_ids: dict[int, int]) -> Iterable[HintEvent]:
    for team, hints in tracker.get_team_hints().items():
        for hint in sorted(hints, key=lambda h: (
            h.receiving_player, h.finding_player, h.location, h.item, h.entrance
        )):
            yield hint_event_from_hint(
                tracker,
                team,
                hint,
                receiver_discord_id=slot_discord_ids.get(hint.receiving_player),
                finder_discord_id=slot_discord_ids.get(hint.finding_player),
            )


def iter_goal_events(tracker, slot_discord_ids: dict[int, int]) -> Iterable[GoalEvent]:
    for team, players in tracker.get_all_players().items():
        for player in players:
            if tracker.get_player_client_status(team, player) == ClientStatus.CLIENT_GOAL:
                yield GoalEvent(
                    event_key=f"goal:{team}:{player}",
                    team=team,
                    slot=slot_ref(tracker, team, player, slot_discord_ids.get(player)),
                )


def _slot_payload(ctx, team: int, slot: int) -> dict[str, Any]:
    slot_info = ctx.slot_info[slot]
    return {
        "team": team,
        "slot": slot,
        "name": ctx.player_names.get((team, slot), slot_info.name),
        "game": slot_info.game,
    }


def item_payload_from_context(ctx, team: int, receiver_slot: int, item: NetworkItem,
                              received_index: int) -> dict[str, Any]:
    receiver = _slot_payload(ctx, team, receiver_slot)
    sender = _slot_payload(ctx, team, item.player)
    location_name_value = None
    if item.location >= 0:
        location_name_value = ctx.location_names[sender["game"]][item.location]
    event_key = f"item:{team}:{receiver_slot}:{received_index}"
    return room_event("item", ctx.room_id, event_key, {
        "team": team,
        "receiver": receiver,
        "sender": sender,
        "item_id": item.item,
        "item_name": ctx.item_names[receiver["game"]][item.item],
        "location_id": item.location,
        "location_name": location_name_value,
        "flags": item.flags,
        "received_index": received_index,
    })


def hint_payload_from_context(ctx, team: int, hint: Hint) -> dict[str, Any]:
    receiver = _slot_payload(ctx, team, hint.receiving_player)
    finder = _slot_payload(ctx, team, hint.finding_player)
    event_key = f"hint:{team}:{hint.receiving_player}:{hint.finding_player}:{hint.location}:{hint.item}:{hint.entrance}"
    return room_event("hint", ctx.room_id, event_key, {
        "team": team,
        "receiver": receiver,
        "finder": finder,
        "item_id": hint.item,
        "item_name": ctx.item_names[receiver["game"]][hint.item],
        "location_id": hint.location,
        "location_name": ctx.location_names[finder["game"]][hint.location],
        "entrance_name": hint.entrance,
        "flags": hint.item_flags,
        "found": hint.found,
        "status": int(hint.status),
    })


def goal_payload_from_context(ctx, team: int, slot: int) -> dict[str, Any]:
    event_key = f"goal:{team}:{slot}"
    return room_event("goal", ctx.room_id, event_key, {
        "team": team,
        "slot": _slot_payload(ctx, team, slot),
    })


def text_payload_from_context(ctx, text: str, message_type: str | None = None) -> dict[str, Any]:
    event_key = f"text:{ctx.room_id}:{monotonic_ns()}"
    return room_event("text", ctx.room_id, event_key, {
        "message": text,
        "message_type": message_type,
    })
