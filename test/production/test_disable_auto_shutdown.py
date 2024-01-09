from uuid import uuid4

from pony.orm import db_session

from test.webhost import TestBase
from WebHostLib.models import Room, Seed


class TestDisableAutoShutdown(TestBase):
    def test_new_rooms_default_to_max_timeout(self) -> None:
        with db_session:
            seed = Seed(multidata=b"", owner=uuid4())
            room = Room(seed=seed, owner=uuid4())
            self.assertEqual(room.timeout, 2147483647)
