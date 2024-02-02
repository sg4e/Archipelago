import typing

from enum import Enum


class Duelist(Enum):
    SIMON_MURAN = (1, 5, "Simon Muran")
    TEANA = (2, 5, "Teana")
    JONO = (3, 5, "Jono")
    VILLAGER1 = (4, 5, "Villager1")
    VILLAGER2 = (5, 5, "Villager2")
    VILLAGER3 = (6, 5, "Villager3")
    SETO = (7, 10, "Seto")
    HEISHIN = (8, 20, "Heishin")
    REX_RAPTOR = (9, 8, "Rex Raptor")
    WEEVIL_UNDERWOOD = (10, 8, "Weevil Underwood")
    MAI_VALENTINE = (11, 10, "Mai Valentine")
    BANDIT_KEITH = (12, 12, "Bandit Keith")
    SHADI = (13, 12, "Shadi")
    YAMI_BAKURA = (14, 14, "Yami Bakura")
    PEGASUS = (15, 16, "Pegasus")
    ISIS = (16, 16, "Isis")
    KAIBA = (17, 16, "Kaiba")
    MAGE_SOLDIER = (18, 12, "Mage Soldier")
    JONO_2ND = (19, 10, "Jono 2nd")
    TEANA_2ND = (20, 10, "Teana 2nd")
    OCEAN_MAGE = (21, 14, "Ocean Mage")
    HIGH_MAGE_SECMETON = (22, 16, "High Mage Secmeton")
    FOREST_MAGE = (23, 14, "Forest Mage")
    HIGH_MAGE_ANUBISIUS = (24, 16, "High Mage Anubisius")
    MOUNTAIN_MAGE = (25, 14, "Mountain Mage")
    HIGH_MAGE_ATENZA = (26, 16, "High Mage Atenza")
    DESERT_MAGE = (27, 14, "Desert Mage")
    HIGH_MAGE_MARTIS = (28, 16, "High Mage Martis")
    MEADOW_MAGE = (29, 14, "Meadow Mage")
    HIGH_MAGE_KEPURA = (30, 16, "High Mage Kepura")
    LABYRINTH_MAGE = (31, 16, "Labyrinth Mage")
    SETO_2ND = (32, 18, "Seto 2nd")
    GUARDIAN_SEBEK = (33, 20, "Guardian Sebek", True)
    GUARDIAN_NEKU = (34, 20, "Guardian Neku", True)
    HEISHIN_2ND = (35, 20, "Heishin 2nd", True)
    SETO_3RD = (36, 20, "Seto 3rd", True)
    DARKNITE = (37, 20, "DarkNite", True)
    NITEMARE = (38, 20, "Nitemare", True)
    DUEL_MASTER_K = (39, 15, "Duel Master K")

    def __init__(self, _id, hand_size, _name, is_final_6: bool = False):
        self.id: int = _id
        self.hand_size: int = hand_size
        self._name: str = _name
        self.is_final_6: bool = is_final_6

    def __str__(self):
        return self._name


def get_duelist_defeat_location_name(duelist: Duelist) -> str:
    return f"{duelist} defeated"


mage_pairs: typing.Tuple[typing.Tuple[Duelist, Duelist], ...] = (
    (Duelist.OCEAN_MAGE, Duelist.HIGH_MAGE_SECMETON),
    (Duelist.FOREST_MAGE, Duelist.HIGH_MAGE_ANUBISIUS),
    (Duelist.MOUNTAIN_MAGE, Duelist.HIGH_MAGE_ATENZA),
    (Duelist.DESERT_MAGE, Duelist.HIGH_MAGE_MARTIS),
    (Duelist.MEADOW_MAGE, Duelist.HIGH_MAGE_KEPURA)
)
