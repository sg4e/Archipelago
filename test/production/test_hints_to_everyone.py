import collections
import unittest
from types import SimpleNamespace

import MultiServer
from MultiServer import Context
from NetUtils import Hint


class TestHintsToEveryone(unittest.TestCase):
    def test_notify_hints_broadcasts_to_all_text_clients_and_still_persists(self) -> None:
        hint = Hint(receiving_player=2, finding_player=1, location=100, item=200, found=False)
        sent_messages = []
        new_hint_slots = []

        async def send_msgs(client, msgs):
            sent_messages.append((client.name, msgs))

        ctx = SimpleNamespace(
            clients={0: {
                1: [SimpleNamespace(name="finder", no_text=False)],
                2: [SimpleNamespace(name="receiver", no_text=False)],
                3: [SimpleNamespace(name="tracker", no_text=True)],
                4: [SimpleNamespace(name="spectator", no_text=False)],
            }},
            groups={},
            hints=collections.defaultdict(set),
            item_names={"Test Game": {200: "Progressive Thing"}},
            location_names={"Test Game": {100: "Important Location"}},
            logger=SimpleNamespace(info=lambda message: None),
            player_names={(0, 1): "Finder", (0, 2): "Receiver"},
            send_msgs=send_msgs,
            slot_info={
                1: SimpleNamespace(game="Test Game"),
                2: SimpleNamespace(game="Test Game"),
            },
        )
        ctx.slot_set = lambda slot: {slot}
        ctx.on_new_hint = lambda team, slot: new_hint_slots.append((team, slot))

        original_async_start = MultiServer.async_start
        try:
            MultiServer.async_start = lambda coroutine: MultiServer.asyncio.run(coroutine)
            Context.notify_hints(ctx, 0, [hint], recipients=(1,))
        finally:
            MultiServer.async_start = original_async_start

        expected_message = hint.as_network_message()
        self.assertEqual(
            sent_messages,
            [
                ("finder", [expected_message]),
                ("receiver", [expected_message]),
                ("spectator", [expected_message]),
            ],
        )
        self.assertEqual(set(new_hint_slots), {(0, 1), (0, 2)})
        self.assertIn(hint, ctx.hints[0, 1])
        self.assertIn(hint, ctx.hints[0, 2])
