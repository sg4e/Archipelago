from dataclasses import dataclass


@dataclass
class Constants:
    """Constants for the FM world."""
    GAME_NAME: str = "Yu-Gi-Oh! Forbidden Memories"
    FM_ID_OFFSET: int = 0x4B1DDE000000
    CARD_ID_OFFSET: int = FM_ID_OFFSET + 0x00
    DUELIST_ID_OFFSET: int = FM_ID_OFFSET + 0x1000
    ITEM_ID_OFFSET: int = FM_ID_OFFSET + 0x10000
    STARCHIP_ITEM_ID_OFFSET: int = ITEM_ID_OFFSET + 0x100
