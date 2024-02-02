from test.bases import WorldTestBase


class FMTestBase(WorldTestBase):
    from worlds.fm.utils import Constants
    game = Constants.GAME_NAME

    def assert_can_reach_location(self, location_name: str) -> None:
        if not self.can_reach_location(location_name):
            self.fail(f"Cannot reach {location_name}")

    def assert_cannot_reach_location(self, location_name: str) -> None:
        if self.can_reach_location(location_name):
            self.fail(f"Can reach {location_name}")
