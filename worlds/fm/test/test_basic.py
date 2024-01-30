import typing

from . import FMTestBase
from ..cards import Card, all_cards


class TestBasic(FMTestBase):
    def test_typing(self) -> None:
        expected_types = typing.get_type_hints(Card)

        # Check the type of each attribute
        for card in all_cards:
            for attr, expected_type in expected_types.items():
                with self.subTest(attr=attr):
                    value = getattr(card, attr)
                    self.assertIsInstance(value, expected_type)
