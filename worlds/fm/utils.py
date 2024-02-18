import typing

from typing import TypeVar
from dataclasses import dataclass
from itertools import chain


@dataclass
class Constants:
    """Constants for the FM world."""
    GAME_NAME: str = "Yu-Gi-Oh! Forbidden Memories"
    FM_ID_OFFSET: int = 0x4B1DDE000000
    CARD_ID_OFFSET: int = FM_ID_OFFSET + 0x00
    DUELIST_ID_OFFSET: int = FM_ID_OFFSET + 0x1000
    ITEM_ID_OFFSET: int = FM_ID_OFFSET + 0x10000
    STARCHIP_ITEM_ID_OFFSET: int = ITEM_ID_OFFSET + 0x100
    VICTORY_ITEM_ID: int = 0x4B1DDEFFFFFF
    VICTORY_ITEM_NAME: str = "Egypt saved"
    DUELIST_UNLOCK_ORDER_KEY: str = "d"
    FINAL_6_ORDER_KEY: str = "f"
    GAME_OPTIONS_KEY: str = "o"
    PROGRESSIVE_DUELIST_ITEM_NAME: str = "Progressive Duelist"
    PROGRESSIVE_DUELIST_ITEM_ID: int = ITEM_ID_OFFSET + 0x00


T = TypeVar("T")


def flatten(i: typing.Iterable[typing.Iterable[T]]) -> typing.List[T]:
    return list(chain.from_iterable(i))
