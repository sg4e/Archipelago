import typing

from typing import TypeVar
from itertools import chain
from worlds.AutoWorld import World, WebWorld
from BaseClasses import CollectionState, Region, Tutorial
from worlds.generic.Rules import set_rule
from .items import item_name_to_item_id as item_id_map
from .items import create_item as fabricate_item
from .items import (FMItem, progressive_duelist_item_name, victory_event_name, create_victory_event,
                    create_starchip_items)
from .constants import Constants
from .locations import location_name_to_id as location_map
from .locations import CardLocation, DuelistLocation
from .cards import Card, all_cards
from .options import FMOptions, DuelistProgression, Final6Progression, Final6Sequence, ATecLogic
from .duelists import Duelist, mage_pairs
from .drop_pools import DuelRank, Drop


T = TypeVar("T")


def flatten(i: typing.Iterable[typing.Iterable[T]]) -> typing.List[T]:
    return list(chain.from_iterable(i))


class FMWeb(WebWorld):
    theme = "dirt"

    setup_en = Tutorial(
        "Multiworld Setup Guide",
        f"A guide to setting up {Constants.GAME_NAME} connected to an Archipelago Multiworld.",
        "English",
        "setup_en.md",
        "setup/en",
        ["sg4e"]
    )

    tutorials = [setup_en]


class FMWorld(World):
    """Yu-Gi-Oh! Forbidden Memories is a game."""
    game: str = Constants.GAME_NAME
    options_dataclass = FMOptions
    options: FMOptions
    required_client_version = (0, 4, 4)
    web = FMWeb()

    final_6_order: typing.List[Duelist]
    # each tuple is a group of duelists unlocked with a single Progressive Duelist item before Final 6
    # Final 6 unlocks are handled separately
    duelist_unlock_order: typing.List[typing.Tuple[Duelist, ...]]
    duelists_unlocked_at_start: typing.List[Duelist]

    location_name_to_id = location_map
    item_name_to_id = item_id_map

    def determine_accessible_drops(self, card: Card, allowed_atecs: typing.List[Duelist]) -> typing.List[Drop]:
        remove_atecs: typing.List[Drop] = [drop for drop in card.drop_pool if drop.duel_rank is not DuelRank.SATEC
                                           or drop.duelist in allowed_atecs]
        remove_ultra_rares: typing.List[Drop] = [drop for drop in remove_atecs
                                                 if drop.probability > self.options.drop_rate_logic.value]
        return remove_ultra_rares

    def get_available_duelists(self, state: CollectionState) -> typing.List[Duelist]:
        progressive_duelist_item_count: int = state.count(progressive_duelist_item_name, self.player)
        duelists_available: typing.List[Duelist] = self.duelists_unlocked_at_start[:]
        if progressive_duelist_item_count >= len(self.duelist_unlock_order):
            duelists_available.extend(flatten(self.duelist_unlock_order))
            final_6_unlocks: int = progressive_duelist_item_count - len(self.duelist_unlock_order)
            if final_6_unlocks > 0:
                duelists_available.extend(self.final_6_order[:final_6_unlocks])
        else:
            for i in range(progressive_duelist_item_count):
                duelists_available.extend(self.duelist_unlock_order[i])
        return duelists_available

    def is_card_location_accessible(self, location: CardLocation, state: CollectionState) -> bool:
        duelists_available: typing.List[Duelist] = self.get_available_duelists(state)
        card_probs: typing.List[Drop] = [drop for drop in location.accessible_drops if drop.duelist in
                                         duelists_available]
        if not card_probs:
            return False
        if any(drop.duel_rank is DuelRank.SAPOW or drop.duel_rank is DuelRank.BCD for drop in card_probs):
            return True
        if any(drop.duel_rank is DuelRank.SATEC for drop in card_probs):
            # ATecs are in logic only if the player has access to farming a trap
            return any(duelist in duelists_available for duelist in (Duelist.PEGASUS, Duelist.ISIS, Duelist.KAIBA))
        return False

    def generate_early(self) -> None:
        self.final_6_order = [Duelist.GUARDIAN_SEBEK, Duelist.GUARDIAN_NEKU, Duelist.HEISHIN_2ND, Duelist.SETO_3RD,
                              Duelist.DARKNITE]
        if self.options.final6_sequence.value >= Final6Sequence.option_first_5_shuffled:
            self.random.shuffle(self.final_6_order)
        if self.options.final6_sequence.value == Final6Sequence.option_all_6_shuffled:
            self.final_6_order.insert(self.random.randint(0, len(self.final_6_order)), Duelist.NITEMARE)
        else:
            self.final_6_order.append(Duelist.NITEMARE)

        # FM-TODO: Break out into a YAML setting?
        self.duelists_unlocked_at_start = [Duelist.DUEL_MASTER_K, Duelist.SIMON_MURAN]
        if (self.options.duelist_progression.value == DuelistProgression.option_campaign or
                self.options.duelist_progression.value == DuelistProgression.option_campaign):
            self.duelists_unlocked_at_start.extend((Duelist.TEANA, Duelist.JONO, Duelist.VILLAGER1,
                                                    Duelist.VILLAGER2, Duelist.VILLAGER3))
        if self.options.duelist_progression.value == DuelistProgression.option_thematic:
            self.duelists_unlocked_at_start.append(Duelist.SETO)
            self.duelist_unlock_order = [
                (Duelist.TEANA, Duelist.JONO, Duelist.VILLAGER1, Duelist.VILLAGER2,
                 Duelist.VILLAGER3, Duelist.SETO),
                (Duelist.REX_RAPTOR, Duelist.WEEVIL_UNDERWOOD, Duelist.MAI_VALENTINE, Duelist.BANDIT_KEITH,
                 Duelist.SHADI, Duelist.YAMI_BAKURA, Duelist.PEGASUS, Duelist.ISIS, Duelist.KAIBA),
                (Duelist.MAGE_SOLDIER, Duelist.JONO_2ND, Duelist.TEANA_2ND, Duelist.OCEAN_MAGE,
                 Duelist.HIGH_MAGE_SECMETON, Duelist.FOREST_MAGE, Duelist.HIGH_MAGE_ANUBISIUS, Duelist.MOUNTAIN_MAGE,
                 Duelist.HIGH_MAGE_ATENZA, Duelist.DESERT_MAGE, Duelist.HIGH_MAGE_MARTIS, Duelist.MEADOW_MAGE,
                 Duelist.HIGH_MAGE_KEPURA, Duelist.LABYRINTH_MAGE, Duelist.SETO_2ND)
            ]
        elif self.options.duelist_progression.value == DuelistProgression.option_campaign:
            self.duelist_unlock_order = [
                (Duelist.SETO,),
                (Duelist.REX_RAPTOR,),
                (Duelist.WEEVIL_UNDERWOOD,),
                (Duelist.MAI_VALENTINE,),
                (Duelist.BANDIT_KEITH,),
                (Duelist.SHADI,),
                (Duelist.YAMI_BAKURA,),
                (Duelist.PEGASUS,),
                (Duelist.ISIS,),
                (Duelist.KAIBA,),
                (Duelist.MAGE_SOLDIER, Duelist.JONO_2ND, Duelist.TEANA_2ND)
            ]
            def pop_random_pair(x): return x.pop(self.random.randint(0, len(x) - 1))
            mages = list(mage_pairs)
            first_mages_unlocked: typing.List[Duelist] = []
            for _ in range(2):
                pair = pop_random_pair(mages)
                first_mages_unlocked.extend(pair)
            self.duelist_unlock_order.append(tuple(first_mages_unlocked))
            self.duelist_unlock_order.append((Duelist.LABYRINTH_MAGE,))
            self.duelist_unlock_order.append((Duelist.SETO_2ND,))
            self.duelist_unlock_order.append(tuple(flatten(mages)))
        elif self.options.duelist_progression.value == DuelistProgression.option_singular:
            mages = list(chain.from_iterable(mage_pairs))
            # These are already unlocked/disallowed
            do_not_add = (Duelist.HEISHIN, Duelist.SIMON_MURAN, Duelist.DUEL_MASTER_K)
            for duelist in Duelist:
                if duelist not in do_not_add and duelist not in mages and not duelist.is_final_6:
                    self.duelist_unlock_order.append((duelist,))
            self.random.shuffle(mages)
            for mage in mages:
                self.duelist_unlock_order.append((mage,))
        else:
            raise ValueError(f"Invalid DuelistProgression option: {self.options.duelist_progression.value}")

    def create_item(self, name: str) -> FMItem:
        return fabricate_item(name, self.player)

    def create_regions(self) -> None:
        menu_region = Region("Menu", self.player, self.multiworld)
        # All duelists are accessible from the menu, so it's our only region
        free_duel_region = Region("Free Duel", self.player, self.multiworld)

        # These cards are not obtainable by any means besides hacking
        unobtainable_ids: typing.Tuple[int, ...] = (
            7, 17, 18, 28, 51, 52, 56, 57, 60, 62, 63, 67, 235, 252, 284, 288, 299, 369, 428, 429, 499, 541, 554,
            555, 562, 603, 628, 640, 709, 711, 717, 721, 722
        )
        reachable_cards: typing.List[Card] = [card for card in all_cards if card.id not in unobtainable_ids]
        # FM-TODO: fusion-only and ritual-only card logic
        card_locations: typing.List[CardLocation] = []
        for card in reachable_cards:
            if card.drop_pool:  # It's in some drop pool
                card_locations.append(CardLocation(free_duel_region, self.player, card))

        # If obtaining a card is outside of the player's settings, set it to excluded
        logical_atec_duelists: typing.List[Duelist] = []
        if self.options.atec_logic.value == ATecLogic.option_all:
            logical_atec_duelists.extend([duelist for duelist in Duelist if duelist is not Duelist.HEISHIN])
        else:
            if self.options.atec_logic.value >= ATecLogic.option_pegasus_only:
                logical_atec_duelists.append(Duelist.PEGASUS)
            if self.options.atec_logic.value >= ATecLogic.option_hundo_atecs:
                logical_atec_duelists.extend((
                    Duelist.KAIBA, Duelist.MAGE_SOLDIER, Duelist.MEADOW_MAGE, Duelist.NITEMARE
                ))
        for location in card_locations:
            in_logic: typing.List[Drop] = self.determine_accessible_drops(location.card, logical_atec_duelists)
            location.attach_drops(in_logic)
            set_rule(location, lambda state, card=location: self.is_card_location_accessible(card, state))
        free_duel_region.locations.extend(card_locations)

        # Add duelist locations
        # Hold a reference to these to set locked items and victory event
        final_6_duelist_locations: typing.List[DuelistLocation] = []
        for duelist in Duelist:
            if duelist is not Duelist.HEISHIN:
                duelist_location: DuelistLocation = DuelistLocation(free_duel_region, self.player, duelist)
                set_rule(duelist_location, (lambda state, d=duelist_location:
                                            d.duelist in self.get_available_duelists(state)))
                if duelist.is_final_6:
                    final_6_duelist_locations.append(duelist_location)  # These get added to the region later
                else:
                    free_duel_region.locations.append(duelist_location)
        final_6_duelist_locations.sort(key=lambda x: self.final_6_order.index(x.duelist))
        self.multiworld.completion_condition[self.player] = lambda state: state.has(victory_event_name, self.player)

        itempool: typing.List[FMItem] = []
        if self.options.final6_progression.value == Final6Progression.option_fixed:
            for i in range(len(final_6_duelist_locations) - 1):
                final_6_duelist_locations[i].place_locked_item(self.create_item(progressive_duelist_item_name))
        elif self.options.final6_progression.value == Final6Progression.option_shuffled:
            for _ in range(len(final_6_duelist_locations) - 1):
                itempool.append(self.create_item(progressive_duelist_item_name))
        else:
            raise ValueError(f"Invalid Final6Progression option: {self.options.final6_progression.value}")
        final_6_duelist_locations[-1].place_locked_item(create_victory_event(self.player))
        # Event location and item both need to be "None" or the Generator complains
        final_6_duelist_locations[-1].address = None
        free_duel_region.locations.extend(final_6_duelist_locations)
        # Add progressive duelist items
        for _ in range(len(self.duelist_unlock_order) + 1):  # I think you need +1 for entry into Final 6
            itempool.append(self.create_item(progressive_duelist_item_name))
        # Fill the item pool with starchips; Final 6 duelist locations are all placed manually
        itempool.extend(create_starchip_items(self.player, len(free_duel_region.locations) - len(itempool)
                                              - len(final_6_duelist_locations)))
        self.multiworld.itempool.extend(itempool)

        menu_region.connect(free_duel_region)
        self.multiworld.regions.append(free_duel_region)
        self.multiworld.regions.append(menu_region)
