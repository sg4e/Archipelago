from test.bases import WorldTestBase


class FMTestBase(WorldTestBase):
    from worlds.fm.constants import Constants
    game = Constants.GAME_NAME
