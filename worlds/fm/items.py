import typing

from BaseClasses import Item
from .constants import Constants

starchip_values: typing.Tuple[int] = (1, 5, 100)
starchip_values_to_strings: typing.Dict[int, str] = {
    value: f"Starchip{'' if value == 1 else f's x{value}'}"
    for value in starchip_values
}
progressive_duelist_item_name: str = "Progressive Duelist"
progressive_duelist_item_id: int = Constants.ITEM_ID_OFFSET + 0x00

victory_event_id = None  # as required by the World API
victory_event_name = "Egypt saved"

# ids are Progressive Duelist's id, then each index in starchip_values
item_id_to_item_name: typing.Dict[int, str] = {}
item_id_to_item_name[progressive_duelist_item_id] = progressive_duelist_item_name
for i in range(len(starchip_values)):
    item_id_to_item_name[Constants.STARCHIP_ITEM_ID_OFFSET + i] = starchip_values_to_strings[starchip_values[i]]

item_name_to_item_id: typing.Dict[str, int] = {value: key for key, value in item_id_to_item_name.items()}


class FMItem(Item):
    game: str = Constants.GAME_NAME
