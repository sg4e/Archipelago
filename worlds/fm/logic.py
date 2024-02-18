import typing

from .cards import all_cards, Card
from .duelists import Duelist
from .drop_pools import Drop, DuelRank
from .options import FMOptions, ATecLogic
from .utils import flatten


class ValueProxy:
    value: int

    def __init__(self, value: int) -> None:
        self.value = value


class OptionsProxy:
    serialized_options: typing.Dict[str, int]

    def __init__(self, serialized_options: typing.Dict[str, int]) -> None:
        self.serialized_options = serialized_options

    def __getattr__(self, item: str) -> ValueProxy:
        return ValueProxy(self.serialized_options[item])


def determine_accessible_drops(
        card: Card,
        allowed_atecs: typing.List[Duelist],
        options: typing.Union[FMOptions, OptionsProxy]) -> typing.List[Drop]:
    remove_atecs: typing.List[Drop] = [drop for drop in card.drop_pool if drop.duel_rank is not DuelRank.SATEC
                                       or drop.duelist in allowed_atecs]
    remove_ultra_rares: typing.List[Drop] = [drop for drop in remove_atecs
                                             if drop.probability > options.drop_rate_logic.value]
    return remove_ultra_rares


def get_obtainable_cards(options: typing.Union[FMOptions, OptionsProxy]) -> typing.List[Card]:
    # These cards are not obtainable by any means besides hacking
    unobtainable_ids: typing.Tuple[int, ...] = (
        7, 17, 18, 28, 51, 52, 56, 57, 60, 62, 63, 67, 235, 252, 284, 288, 299, 369, 428, 429, 499, 541, 554,
        555, 562, 603, 628, 640, 709, 711, 717, 721, 722
    )
    obtainable_cards: typing.List[Card] = [card for card in all_cards if card.id not in unobtainable_ids]

    logical_atec_duelists: typing.List[Duelist] = []
    if options.atec_logic.value == ATecLogic.option_all:
        logical_atec_duelists.extend([duelist for duelist in Duelist if duelist is not Duelist.HEISHIN])
    else:
        if options.atec_logic.value >= ATecLogic.option_pegasus_only:
            logical_atec_duelists.append(Duelist.PEGASUS)
        if options.atec_logic.value >= ATecLogic.option_hundo_atecs:
            logical_atec_duelists.extend((
                Duelist.KAIBA, Duelist.MAGE_SOLDIER, Duelist.MEADOW_MAGE, Duelist.NITEMARE
            ))
    for card in obtainable_cards:
        in_logic: typing.List[Drop] = determine_accessible_drops(card, logical_atec_duelists, options)
        card.attach_accessible_drops(in_logic)
    # FM-TODO: fusion-only and ritual-only card logic
    # For now, non-drop cards are excluded from the multiworld entirely
    return [card for card in obtainable_cards if card.accessible_drops]


def get_unlocked_duelists(
        progressive_duelist_item_count: int,
        duelist_unlock_order: typing.Sequence[typing.Tuple[Duelist, ...]],
        final_6_order: typing.Sequence[Duelist]
) -> typing.List[Duelist]:
    duelists_available: typing.List[Duelist] = []
    # the first element is unlocked at the start
    progressive_duelist_item_count += 1
    if progressive_duelist_item_count >= len(duelist_unlock_order):
        duelists_available.extend(flatten(duelist_unlock_order))
        final_6_unlocks: int = progressive_duelist_item_count - len(duelist_unlock_order)
        if final_6_unlocks > 0:
            duelists_available.extend(final_6_order[:final_6_unlocks])
    else:
        for i in range(progressive_duelist_item_count):
            duelists_available.extend(duelist_unlock_order[i])
    return duelists_available
