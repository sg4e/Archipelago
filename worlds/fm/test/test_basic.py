from . import FMTestBase
from ..items import progressive_duelist_item_name


class TestDuelistRestrictions(FMTestBase):
    options = {
        "Duelist Progression": "campaign",
        "Final 6 Sequence": "vanilla",
        "ATec Logic": "off"
    }

    def test_cannot_access_final_boss_at_start(self) -> None:
        self.assertFalse(self.can_reach_location("Nitemare defeated"))

    def test_obtain_WSR(self) -> None:
        """This test doesn't work"""
        duelist_unlocks = [[progressive_duelist_item_name]*8]
        self.assertAccessDependency(["Widespread Ruin in library"], duelist_unlocks, only_check_listed=True)
