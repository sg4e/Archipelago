from . import FMTestBase
from ..items import progressive_duelist_item_name
from ..options import DuelistProgression, duelist_progression_map
from ..utils import flatten
from ..duelists import get_duelist_defeat_location_name


class TestBasic(FMTestBase):
    options = {
        "duelist_progression": "campaign",
        "final6_sequence": "vanilla",
        "final6_progression": "fixed",
        "atec_logic": "off"
    }

    def test_cannot_access_final_boss_at_start(self) -> None:
        self.assertFalse(self.can_reach_location("Nitemare defeated"))

    def test_obtain_WSR(self) -> None:
        prog_items = self.get_items_by_name(progressive_duelist_item_name)
        before_isis = prog_items[:8]
        self.collect(before_isis)
        self.assert_cannot_reach_location("Widespread Ruin in library")
        self.collect(prog_items[8])
        self.assert_can_reach_location("Widespread Ruin in library")


base_options = {
    "final6_sequence": "vanilla",
    "final6_progression": "fixed",
    "atec_logic": "off",
    "invisible_wire_logic": "Off",
    "drop_rate_logic": 4,
}


# I see no way how to parameterize this at the class level
def impl_test_duelist_progression_unlocks(test: FMTestBase, unlock_order):
    for i in range(len(unlock_order)):
        duelists_available = flatten(unlock_order[:i+1])
        locked_duelists = flatten(unlock_order[i+1:])
        for duelist in duelists_available:
            test.assert_can_reach_location(get_duelist_defeat_location_name(duelist))
        for duelist in locked_duelists:
            test.assert_cannot_reach_location(get_duelist_defeat_location_name(duelist))
        progress = test.get_item_by_name(progressive_duelist_item_name)
        test.collect(progress)


class TestThematicProgression(FMTestBase):
    options = {
        "duelist_progression": "thematic",
        **base_options
    }

    def test_thematic_progression(self) -> None:
        impl_test_duelist_progression_unlocks(self, duelist_progression_map[DuelistProgression.option_thematic])


class TestCampaignProgression(FMTestBase):
    options = {
        "duelist_progression": "campaign",
        **base_options
    }

    def test_campaign_progression(self) -> None:
        impl_test_duelist_progression_unlocks(self, duelist_progression_map[DuelistProgression.option_campaign])


class TestSingularProgression(FMTestBase):
    options = {
        "duelist_progression": "singular",
        **base_options
    }

    def test_singular_progression(self) -> None:
        impl_test_duelist_progression_unlocks(self, duelist_progression_map[DuelistProgression.option_singular])
