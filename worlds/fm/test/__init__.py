from test.bases import WorldTestBase
from BaseClasses import Location


class FMTestBase(WorldTestBase):
    from worlds.fm.utils import Constants
    game = Constants.GAME_NAME

    def assert_can_reach_location(self, location_name: str) -> None:
        if not self.can_reach_location(location_name):
            self.fail(f"Cannot reach {location_name}")

    def assert_cannot_reach_location(self, location_name: str) -> None:
        if self.can_reach_location(location_name):
            self.fail(f"Can reach {location_name}")

    def get_location(self, location_name: str) -> Location:
        # I don't know how to get a location without assuming a player id
        all_locations = self.multiworld.get_locations()
        wanted = [loc for loc in all_locations if loc.name == location_name]
        if not wanted:
            raise ValueError(f"Location {location_name} not found")
        return wanted[0]
