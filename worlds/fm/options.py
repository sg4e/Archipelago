from dataclasses import dataclass
from Options import Range, Choice, PerGameCommonOptions


class DropRateLogic(Range):
    """Prohibits progression items from being placed behind cards with a drop rate at or below the specified value (out
    of 2048). This logic takes your duelist progression into account, such that if the duelists you logically have
    access to drop at or below this rate, the card will be excluded until you have access to a duelist with a higher
    rate if one exists, or forever excluded otherwise."""
    display_name = "Exclusion Drop Rate"
    range_start = 0
    range_end = 64
    default = 4


class ATecLogic(Choice):
    """Sets which duelists' SATec drop pools are considered in logic.\n\n"Off" means you'll never be expected to do an
    ATec for progression.\n"Pegasus Only" means only Pegasus's SATec pool is in logic.\n"Hundo ATecs" means that ATecs
    are in logic for the duelists typically ATec'd during a Hundo run, specifically: Pegasus, Kaiba, Mage Soldier,
    Meadow Mage, and NiteMare.\n"All" means all duelists' SATec pools are in logic.\n\nRegardless of your choice, you
    will never be expected to do an ATec without access to a Magic card and Acid Trap Hole or Widespread Ruin."""
    display_name = "ATec Logic"
    option_off = 0
    option_pegasus_only = 1
    option_hundo_atecs = 2
    option_all = 3
    default = 2

    @classmethod
    def get_option_name(cls, value) -> str:
        if cls.auto_display_name:
            return cls.name_lookup[value].replace("Atec", "ATec")
        else:
            return cls.name_lookup[value]


@dataclass
class FMOptions(PerGameCommonOptions):
    atec_logic: ATecLogic
    drop_rate_logic: DropRateLogic
