import typing

from worlds.AutoWorld import World
from BaseClasses import Item, MultiWorld, Tutorial, ItemClassification, Region
from .items import item_name_to_item_id as item_id_map
from .constants import Constants
from .locations import location_name_to_id as location_map


class FMWorld(World):
    game: str = Constants.GAME_NAME
    required_client_version = (0, 4, 4)

    location_name_to_id = location_map
    item_name_to_id = item_id_map

    def generate_early(self) -> None:
        pass

    def create_regions(self) -> None:
        # All duelists are accessible from the menu, so it's our only region
        menu_region = Region("Menu", self.player, self.multiworld)
        

