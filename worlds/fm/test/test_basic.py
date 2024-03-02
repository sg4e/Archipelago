from . import FMTestBase
from ..utils import Constants
from ..options import DuelistProgression, duelist_progression_map
from ..utils import flatten
from ..duelists import get_duelist_defeat_location_name
from BaseClasses import LocationProgressType


base_options = {
    "duelist_progression": "campaign",
    "local_starchips": False,
    "final6_sequence": "vanilla",
    "final6_progression": "fixed",
    "atec_logic": "off",
    "atec_trap": "acid_trap_hole",
    "drop_rate_logic": 4,
}


class TestBasic(FMTestBase):
    options = base_options

    def test_cannot_access_final_boss_at_start(self) -> None:
        self.assertFalse(self.can_reach_location("Nitemare defeated"))

    def test_obtain_WSR(self) -> None:
        prog_items = self.get_items_by_name(Constants.PROGRESSIVE_DUELIST_ITEM_NAME)
        before_isis = prog_items[:8]
        self.collect(before_isis)
        self.assert_cannot_reach_location("Widespread Ruin")
        self.collect(prog_items[8])
        self.assert_can_reach_location("Widespread Ruin")

    def test_heishin_1_out_of_logic(self) -> None:
        prog_items = self.get_items_by_name(Constants.PROGRESSIVE_DUELIST_ITEM_NAME)
        before_isis = prog_items[:8]  # more than enough progression
        self.collect(before_isis)
        self.assert_cannot_reach_location("Pumpking the King of Ghosts")

    def test_no_atecs_required(self) -> None:
        raigeki = self.get_location("Raigeki")
        self.assertEqual(raigeki.progress_type, LocationProgressType.EXCLUDED)


class TestAtecLogic(FMTestBase):
    options = {
        **base_options,
        "atec_logic": "all",
        "duelist_progression": "campaign"
    }

    def test_atecs_not_excluded(self) -> None:
        raigeki = self.get_location("Raigeki")
        self.assertEqual(raigeki.progress_type, LocationProgressType.DEFAULT)

    def test_raigeki_not_in_logic_with_seto_but_no_trap(self) -> None:
        self.assert_cannot_reach_location("Raigeki")
        self.collect(self.get_item_by_name(Constants.PROGRESSIVE_DUELIST_ITEM_NAME))
        self.assert_cannot_reach_location("Raigeki")


class TestAtecTrapLogic(FMTestBase):
    options = {
        **base_options,
        "atec_logic": "all",
        "duelist_progression": "campaign",
        "atec_trap": "fake_trap"
    }

    def test_raigeki_in_logic_with_seto_and_invisible_wire(self) -> None:
        self.assert_cannot_reach_location("Raigeki")
        self.collect(self.get_item_by_name(Constants.PROGRESSIVE_DUELIST_ITEM_NAME))
        self.assert_can_reach_location("Raigeki")


# I see no way how to parameterize this at the class level
def impl_test_duelist_progression_unlocks(test: FMTestBase, unlock_order):
    for i in range(len(unlock_order)):
        duelists_available = flatten(unlock_order[:i+1])
        locked_duelists = flatten(unlock_order[i+1:])
        for duelist in duelists_available:
            test.assert_can_reach_location(get_duelist_defeat_location_name(duelist))
        for duelist in locked_duelists:
            test.assert_cannot_reach_location(get_duelist_defeat_location_name(duelist))
        progress = test.get_item_by_name(Constants.PROGRESSIVE_DUELIST_ITEM_NAME)
        test.collect(progress)


class TestThematicProgression(FMTestBase):
    options = {
        **base_options,
        "duelist_progression": "thematic"
    }

    def test_thematic_progression(self) -> None:
        impl_test_duelist_progression_unlocks(self, duelist_progression_map[DuelistProgression.option_thematic])


class TestCampaignProgression(FMTestBase):
    options = {
        **base_options,
        "duelist_progression": "campaign"
    }

    def test_campaign_progression(self) -> None:
        impl_test_duelist_progression_unlocks(self, duelist_progression_map[DuelistProgression.option_campaign])


class TestSingularProgression(FMTestBase):
    options = {
        **base_options,
        "duelist_progression": "singular"
    }

    def test_singular_progression(self) -> None:
        impl_test_duelist_progression_unlocks(self, duelist_progression_map[DuelistProgression.option_singular])


class TestShuffledFinal6Progression(FMTestBase):
    options = {
        **base_options,
        "final6_progression": "shuffled"
    }


class TestShuffleFinal5Order(FMTestBase):
    options = {
        **base_options,
        "final6_sequence": "first_5_shuffled"
    }


class TestShuffleFinal6Order(FMTestBase):
    options = {
        **base_options,
        "final6_sequence": "all_6_shuffled"
    }


class TestMostRandom(FMTestBase):
    options = {
        "duelist_progression": "singular",
        "final6_sequence": "all_6_shuffled",
        "final6_progression": "shuffled",
        "atec_logic": "all",
        "atec_trap": "fake_trap",
        "drop_rate_logic": 0,
    }


class TestLocalStarchips(FMTestBase):
    options = {
        **base_options,
        "local_starchips": True
    }


class TestLocalStarchipsTightProgression(FMTestBase):
    options = {
        **base_options,
        "local_starchips": True,
        "duelist_progression": "singular",
        "atec_logic": "off",
    }
