import unittest
from collections import defaultdict
from types import SimpleNamespace

from MultiServer import ClientMessageProcessor, ServerCommandProcessor


class TestClient:
    team = 0
    slot = 1


class TestDisableAliases(unittest.TestCase):
    unsupported_message = "Sorry, aliases are not supported on this server."

    def make_context(self) -> SimpleNamespace:
        return SimpleNamespace(
            name_aliases={(0, 1): "Existing"},
            player_names=defaultdict(str, {(0, 1): "Player"}),
            get_aliased_name=lambda team, slot: "Player",
            notify_client=lambda client, text, tags: None,
            broadcast_text_all=lambda text, tags=None: None,
            save=lambda: self.fail("Disabled alias command should not save"),
        )

    def test_client_alias_command_is_disabled(self) -> None:
        ctx = self.make_context()
        messages = []
        saves = []
        ctx.notify_client = lambda client, text, tags: messages.append(text)
        ctx.save = lambda: saves.append(True)

        result = ClientMessageProcessor(ctx, TestClient())("!alias NewAlias")

        self.assertFalse(result)
        self.assertEqual(ctx.name_aliases[0, 1], "Existing")
        self.assertEqual(messages, [self.unsupported_message])
        self.assertEqual(saves, [])

    def test_server_alias_command_is_disabled(self) -> None:
        ctx = self.make_context()
        messages = []
        processor = ServerCommandProcessor(ctx)
        processor.output = messages.append

        result = processor("/alias Player NewAlias")

        self.assertFalse(result)
        self.assertEqual(ctx.name_aliases[0, 1], "Existing")
        self.assertEqual(messages, [self.unsupported_message])
