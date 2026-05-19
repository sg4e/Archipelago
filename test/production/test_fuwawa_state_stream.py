import collections
import unittest
from types import SimpleNamespace

import MultiServer
from MultiServer import Context
from NetUtils import ClientStatus, Hint, HintStatus, NetworkItem, NetworkSlot, SlotType


def bind_fuwawa_helpers(ctx):
    ctx.fuwawa_slot_payload = lambda team, slot: Context.fuwawa_slot_payload(ctx, team, slot)
    ctx.fuwawa_item_payload = lambda team, player, item, index: Context.fuwawa_item_payload(
        ctx, team, player, item, index
    )
    ctx.fuwawa_hint_payload = lambda team, hint: Context.fuwawa_hint_payload(ctx, team, hint)
    ctx.fuwawa_goal_payload = lambda team, slot: Context.fuwawa_goal_payload(ctx, team, slot)
    ctx.broadcast_fuwawa_state_event = lambda event: Context.broadcast_fuwawa_state_event(ctx, event)
    return ctx


class TestFuwawaStateStream(unittest.TestCase):
    def make_context(self) -> SimpleNamespace:
        ctx = SimpleNamespace(
            endpoints=[],
            clients={0: {}},
            hints=collections.defaultdict(set),
            received_items={},
            client_game_state=collections.defaultdict(int),
            name_aliases={},
            player_names={(0, 1): "Finder", (0, 2): "Receiver"},
            slot_info={
                1: NetworkSlot("Finder", "Test Game", SlotType.player),
                2: NetworkSlot("Receiver", "Test Game", SlotType.player),
            },
            item_names={"Test Game": {200: "Progressive Thing"}},
            location_names={"Test Game": {100: "Important Location"}},
            logger=SimpleNamespace(info=lambda message: None),
        )
        ctx.recheck_hints = lambda team=None, slot=None: None
        ctx.slot_set = lambda slot: {slot}
        return bind_fuwawa_helpers(ctx)

    def test_read_fuwawa_state_snapshot_contains_durable_state(self) -> None:
        ctx = self.make_context()
        hint = Hint(2, 1, 100, 200, False, "Door", 1, HintStatus.HINT_PRIORITY)
        ctx.hints[0, 1].add(hint)
        ctx.received_items[0, 2, True] = [NetworkItem(200, 100, 1, 1)]
        ctx.client_game_state[0, 2] = ClientStatus.CLIENT_GOAL

        state = Context.get_fuwawa_state(ctx)

        self.assertEqual(state["schema"], "fuwawa_state")
        self.assertEqual(state["slots"][0]["name"], "Finder")
        self.assertEqual(state["items"][0]["event_key"], "item:0:2:0")
        self.assertEqual(state["items"][0]["item_name"], "Progressive Thing")
        self.assertEqual(state["hints"][0]["event_key"], "hint:0:2:1:100:200:Door")
        self.assertEqual(state["goals"][0]["event_key"], "goal:0:2")

    def test_live_item_events_are_bounced_only_to_fuwawa_monitors(self) -> None:
        ctx = self.make_context()
        sent = []
        monitor = SimpleNamespace(auth=True, tags=["FuwawaBot"], name="monitor")
        player = SimpleNamespace(auth=True, tags=[], name="player")
        unauthenticated = SimpleNamespace(auth=False, tags=["FuwawaBot"], name="unauthenticated")
        ctx.endpoints = [monitor, player, unauthenticated]
        ctx.broadcast = lambda endpoints, msgs: sent.append(([endpoint.name for endpoint in endpoints], msgs))

        MultiServer.send_items_to(ctx, 0, 2, NetworkItem(200, 100, 1, 1))

        self.assertEqual(ctx.received_items[0, 2, True][0].item, 200)
        self.assertEqual(sent[0][0], ["monitor"])
        self.assertEqual(sent[0][1][0]["cmd"], "Bounced")
        self.assertEqual(sent[0][1][0]["data"]["event"]["type"], "item")

    def test_new_hints_keep_upstream_visibility_and_emit_monitor_event(self) -> None:
        ctx = self.make_context()
        sent_messages = []
        monitor_events = []
        ctx.clients = {0: {
            1: [SimpleNamespace(name="finder", no_text=False)],
            2: [SimpleNamespace(name="receiver", no_text=False)],
            3: [SimpleNamespace(name="spectator", no_text=False)],
        }}
        async def send_msgs(client, msgs):
            sent_messages.append((client.name, msgs))
        ctx.send_msgs = send_msgs
        ctx.on_new_hint = lambda team, slot: None
        ctx.broadcast_fuwawa_state_event = monitor_events.append
        hint = Hint(2, 1, 100, 200, False)

        original_async_start = MultiServer.async_start
        try:
            MultiServer.async_start = lambda coroutine: MultiServer.asyncio.run(coroutine)
            Context.notify_hints(ctx, 0, [hint], recipients=(1,))
        finally:
            MultiServer.async_start = original_async_start

        self.assertEqual([name for name, _msgs in sent_messages], ["finder"])
        self.assertEqual(monitor_events[0]["type"], "hint")
        self.assertIn(hint, ctx.hints[0, 1])
        self.assertIn(hint, ctx.hints[0, 2])


if __name__ == "__main__":
    unittest.main()
