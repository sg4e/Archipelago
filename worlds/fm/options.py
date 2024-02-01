from dataclasses import dataclass
from Options import Toggle, Range, Choice, PerGameCommonOptions


class DuelistProgression(Choice):
    """
    Whenever you receive a "Progressive Duelist" item, the next duelist or group of duelists will be unlocked. This
    setting controls what those duelist groups are.

    "Thematic" places duelists in large groups based on theme. You will start with all of Egypt 1 unlocked, then unlock
    all of World Tournament, then all of Egypt 2, then Final 6 one at a time.

    "Campaign" unlocks duelists roughly the same way as in Campaign mode: you will start with all of Egypt 1 unlocked
    except Seto 1, then unlock Seto 1, then each of the World Tournament duelists one at a time, then Mage Soldier and
    the Jono and Teana refights all together, then 2 random low mage and high mage pairs at the same time, then
    Labryinth Mage, then Seto 2, then the rest of Egypt 2 all at once, then Final 6.

    "Singular" unlocks every duelist one at a time in the same order they're encountered in the campaign up until the
    mages, then unlocks mages one at a time at random without respecting low and high mage pairs.

    Regardless of your choice, you will always have Simon Muran and Duel Master K unlocked, and Heishin 1 is always
    excluded until Heishin 2 is unlocked.
    """
    display_name = "Duelist Progression"
    option_thematic = 0
    option_campaign = 1
    option_singular = 2
    default = 1


class Final6Progression(Choice):
    """
    "Fixed": The check you receive for defeating a member of Final 6 is guaranteed to unlock the next Final 6 duelist.
    This means you will have Go Mode as soon as the first Final 6 duelist is unlocked.

    "Shuffled": The Progressive Duelist items to unlock each Final 6 duelist are shuffled into the item pool.
    """
    display_name = "Final 6 Progression"
    option_fixed = 0
    option_shuffled = 1
    default = 0


class Final6Sequence(Choice):
    """
    "Vanilla": You will always unlock the Final 6 duelists in this order: Guardian Sebek, Guardian Neku, Heishin 2, Seto
    3, DarkNite, Nitemare.

    "First 5 Shuffled": The order you unlock the Final 6 duelists is randomized, except Nitemare will always be last.

    "All 6 Shuffled": The order you unlock the Final 6 duelists is completely randomized, and you'll reach your goal
    when you defeat the last one. Depending on your other settings, "All 6 Shuffled" could put Nitemare ATecs into logic
    in the lategame.
    """
    display_name = "Final 6 Sequence"
    option_vanilla = 0
    option_first_5_shuffled = 1
    option_all_6_shuffled = 2
    default = 0


class DropRateLogic(Range):
    """
    Prohibits progression items from being placed behind cards with a drop rate at or below the specified value (out of
    2048). This logic takes your duelist progression into account, such that if the duelists you logically have access
    to drop at or below this rate, the card will be excluded until you have access to a duelist with a higher rate if
    one exists, or forever excluded otherwise.
    """
    display_name = "Exclusion Drop Rate"
    range_start = 0
    range_end = 64
    default = 4


class ATecLogic(Choice):
    """
    Sets which duelists' SATec drop pools are considered in logic.

    "Off" means you'll never be expected to do an ATec for progression.

    "Pegasus Only" means only Pegasus's SATec pool is in logic.

    "Hundo ATecs" means that ATecs are in logic for the duelists typically ATec'd during a Hundo run, specifically:
    Pegasus, Kaiba, Mage Soldier, Meadow Mage, and NiteMare.

    "All" means all duelists' SATec pools are in logic.

    Regardless of your choice, you will never be expected to do an ATec until you have access to Pegasus, Isis, or Kaiba
    (to acquire an Acid Trap Hole or Widespread Ruin), or Bakura, Keith, or Mai if you have "Invisible Wire enables
    ATecs" set to "On".
    """
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


class InvisibleWireLogic(Toggle):
    """
    If set to "On", ATecs become part of logic if you have access to a duelist that drops Invisible Wire on BCD (Bakura,
    Keith, and Mai). Your other ATec settings are still respected.
    """
    display_name = "Invisible Wire enables ATecs"


@dataclass
class FMOptions(PerGameCommonOptions):
    duelist_progression: DuelistProgression
    final6_progression: Final6Progression
    final6_sequence: Final6Sequence
    atec_logic: ATecLogic
    invisible_wire_logic: InvisibleWireLogic
    drop_rate_logic: DropRateLogic
