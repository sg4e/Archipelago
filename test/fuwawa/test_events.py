import unittest

from NetUtils import ClientStatus, Hint, HintStatus, NetworkItem, NetworkSlot, SlotType
from WebHostLib.fuwawa.events import (
    goal_payload_from_context,
    hint_payload_from_context,
    item_payload_from_context,
    iter_goal_events,
    iter_hint_events,
    iter_item_events,
    text_payload_from_context,
)
from WebHostLib.fuwawa.formatting import format_hint_event, format_item_event


class FakeTracker:
    item_id_to_name = {
        "Game A": {1: "Progressive Sword"},
        "Game B": {1: "Progressive Sword"},
    }
    location_id_to_name = {
        "Game A": {10: "Cave"},
        "Game B": {20: "Tower"},
    }

    def get_all_players(self):
        return {0: [1, 2]}

    def get_slot_info(self, slot):
        return {
            1: NetworkSlot("Alice", "Game A", SlotType.player),
            2: NetworkSlot("Bob", "Game B", SlotType.player),
        }[slot]

    def get_player_received_items(self, team, player):
        if player == 1:
            return [NetworkItem(1, 20, 2, 1)]
        return []

    def get_team_hints(self):
        return {
            0: {
                Hint(
                    receiving_player=1,
                    finding_player=2,
                    location=20,
                    item=1,
                    found=False,
                    item_flags=1,
                    status=HintStatus.HINT_PRIORITY,
                )
            }
        }

    def get_player_client_status(self, team, player):
        return ClientStatus.CLIENT_GOAL if player == 2 else ClientStatus.CLIENT_PLAYING


class FakeContext:
    room_id = "room-1"
    slot_info = {
        1: NetworkSlot("Alice", "Game A", SlotType.player),
        2: NetworkSlot("Bob", "Game B", SlotType.player),
    }
    player_names = {
        (0, 1): "Alice",
        (0, 2): "Bob",
    }
    item_names = {
        "Game A": {1: "Progressive Sword"},
        "Game B": {1: "Progressive Sword"},
    }
    location_names = {
        "Game A": {10: "Cave"},
        "Game B": {20: "Tower"},
    }


class TestFuwawaEvents(unittest.TestCase):
    def test_item_events_use_structured_ids(self) -> None:
        event = list(iter_item_events(FakeTracker(), {1: 100, 2: 200}))[0]

        self.assertEqual("item:0:1:0", event.event_key)
        self.assertEqual("Progressive Sword", event.item_name)
        self.assertEqual("Tower", event.location_name)
        self.assertEqual("Bob sent **Progressive Sword** to Alice (Tower)", format_item_event(event))

    def test_hint_events_do_not_parse_text(self) -> None:
        event = list(iter_hint_events(FakeTracker(), {1: 100, 2: 200}))[0]

        self.assertEqual("hint:0:1:2:20:1:", event.event_key)
        self.assertEqual("[Hint]: Alice's **Progressive Sword** is at Tower in Bob's World. (not found)",
                         format_hint_event(event))

    def test_goal_events(self) -> None:
        event = list(iter_goal_events(FakeTracker(), {1: 100, 2: 200}))[0]

        self.assertEqual("goal:0:2", event.event_key)
        self.assertEqual("Bob", event.slot.name)

    def test_item_payload_from_live_context(self) -> None:
        payload = item_payload_from_context(FakeContext(), 0, 1, NetworkItem(1, 20, 2, 1), 3)

        self.assertEqual("item", payload["type"])
        self.assertEqual("room-1", payload["room_id"])
        self.assertEqual("item:0:1:3", payload["event_key"])
        self.assertEqual("Progressive Sword", payload["data"]["item_name"])
        self.assertEqual("Tower", payload["data"]["location_name"])

    def test_hint_payload_from_live_context(self) -> None:
        hint = Hint(
            receiving_player=1,
            finding_player=2,
            location=20,
            item=1,
            found=False,
            item_flags=1,
            status=HintStatus.HINT_PRIORITY,
        )
        payload = hint_payload_from_context(FakeContext(), 0, hint)

        self.assertEqual("hint", payload["type"])
        self.assertEqual("hint:0:1:2:20:1:", payload["event_key"])
        self.assertEqual("Alice", payload["data"]["receiver"]["name"])
        self.assertEqual("Bob", payload["data"]["finder"]["name"])

    def test_goal_and_text_payloads_from_live_context(self) -> None:
        goal = goal_payload_from_context(FakeContext(), 0, 2)
        text = text_payload_from_context(FakeContext(), "hello", "Notice")

        self.assertEqual("goal:0:2", goal["event_key"])
        self.assertEqual("Bob", goal["data"]["slot"]["name"])
        self.assertEqual("text", text["type"])
        self.assertEqual("hello", text["data"]["message"])


if __name__ == "__main__":
    unittest.main()
