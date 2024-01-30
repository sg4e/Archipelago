import typing

from BaseClasses import Location
from .cards import Card, all_cards
from .constants import Constants
from .duelists import Duelist


def get_location_name_for_card(card: Card) -> str:
    return f"{card.name} in library"


def get_location_id_for_card(card: Card) -> int:
    return Constants.CARD_ID_OFFSET + card.id


def get_location_name_for_duelist(duelist: Duelist) -> str:
    return f"{duelist} defeated"


def get_location_id_for_duelist(duelist: Duelist) -> int:
    return Constants.DUELIST_ID_OFFSET + duelist.id


class FMLocation(Location):
    game: Constants.GAME_NAME
    unique_id: int

    def __init__(self, player: int, name: str, id: int):
        super().__init__(player, name)
        self.unique_id = id


class LibraryLocation(FMLocation):
    """A check whenever a card is added to the library."""
    card: typing.ClassVar[Card]

    def __init__(self, player: int, card: Card):
        super().__init__(player, get_location_name_for_card(card), get_location_id_for_card(card))
        self.card = card


class DuelistLocation(FMLocation):
    """A check whenever a duelist is defeated (the first time)."""
    duelist: typing.ClassVar[Duelist]

    def __init__(self, player: int, duelist: Duelist):
        super().__init__(player, get_location_name_for_duelist(duelist), get_location_id_for_duelist(duelist))
        self.duelist = duelist


card_location_name_to_id: typing.Dict[str, int] = {}
for card in all_cards:
    card_location_name_to_id[get_location_name_for_card(card)] = get_location_id_for_card(card)

duelist_location_name_to_id: typing.Dict[str, int] = {}
for duelist in Duelist:
    duelist_location_name_to_id[get_location_name_for_duelist(duelist)] = get_location_id_for_duelist(duelist)

location_name_to_id: typing.Dict[str, int] = {**card_location_name_to_id, **duelist_location_name_to_id}
