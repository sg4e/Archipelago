import typing

from BaseClasses import Location, Region, LocationProgressType
from .cards import Card, all_cards
from .utils import Constants
from .duelists import Duelist, get_duelist_defeat_location_name
from .drop_pools import Drop


def get_location_name_for_card(card: Card) -> str:
    return f"{card.name}"


def get_location_id_for_card(card: Card) -> int:
    return Constants.CARD_ID_OFFSET + card.id


def get_location_name_for_duelist(duelist: Duelist) -> str:
    return get_duelist_defeat_location_name(duelist)


def get_location_id_for_duelist(duelist: Duelist) -> int:
    return Constants.DUELIST_ID_OFFSET + duelist.id


class FMLocation(Location):
    game: str

    def __init__(self, region: Region, player: int, name: str, id: int):
        super().__init__(player, name, parent=region)
        self.game = Constants.GAME_NAME
        self.address = id

    def exclude(self) -> None:
        self.progress_type = LocationProgressType.EXCLUDED


class CardLocation(FMLocation):
    """A check whenever a card is added to the library."""
    card: Card
    accessible_drops: typing.List[Drop]

    def __init__(self, region: Region, player: int, card: Card):
        super().__init__(region, player, get_location_name_for_card(card), get_location_id_for_card(card))
        self.card = card
        self.accessible_drops = []

    def attach_drops(self, drops: typing.List[Drop]):
        """Attaches all in-logic and in-settings drop probabilities to this location."""
        self.accessible_drops.extend(drops)


class DuelistLocation(FMLocation):
    """A check whenever a duelist is defeated (the first time)."""
    duelist: Duelist

    def __init__(self, region: Region, player: int, duelist: Duelist):
        super().__init__(region, player, get_location_name_for_duelist(duelist), get_location_id_for_duelist(duelist))
        self.duelist = duelist


card_location_name_to_id: typing.Dict[str, int] = {}
for card in all_cards:
    card_location_name_to_id[get_location_name_for_card(card)] = get_location_id_for_card(card)

duelist_location_name_to_id: typing.Dict[str, int] = {}
for duelist in Duelist:
    duelist_location_name_to_id[get_location_name_for_duelist(duelist)] = get_location_id_for_duelist(duelist)

location_name_to_id: typing.Dict[str, int] = {**card_location_name_to_id, **duelist_location_name_to_id}
