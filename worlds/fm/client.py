import typing

from typing import TYPE_CHECKING
from NetUtils import ClientStatus
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from .utils import Constants
from .duelists import (Duelist, map_ids_to_duelists, ids_to_duelists, get_unlocked_duelists, UNLOCK_OFFSET)
from .items import progressive_duelist_item_id
from .locations import get_location_id_for_duelist, get_location_id_for_card_id

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

CARDS_IN_CHESTS_OFFSET: typing.Final[int] = 0x1D0250
MAIN_RAM: typing.Final[str] = "MainRAM"


class FMClient(BizHawkClient):
    game: str = Constants.GAME_NAME
    system: str = "PSX"
    patch_suffix: str = ".apfm"
    local_checked_locations: typing.Set[int]
    duelist_unlock_order: typing.Tuple[typing.Tuple[Duelist, ...], ...]
    final_6_order: typing.Tuple[Duelist, ...]

    def __init__(self) -> None:
        super().__init__()
        self.local_checked_locations = set()

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        # Forbidden Memories has a very active romhacking community. Although not all mods will be compatible with AP
        # since AP assumes specific card distributions (card drop tables), I see no reason to limit players to only a
        # small subset of mods when all the revelant memory addresses for the AP interface don't change. We could even
        # support modded drop tables in the future.
        #
        # I searched for a means to validate the ROM in a mod-agnostic way. PSX discs contain filesystems; some mods
        # extract the files, modify the relevant parts, then rebuild the ISO (FM card mod does this process). This can
        # cause files to move around inside the binary so offsets for strings may not be reliable. Some mods also update
        # the game's checksum so that they run on real consoles.
        #
        # I've found that the most reliable way is to search the RAM instead of the ROM. When the BIOS boots up, as soon
        # as the PlayStation "P" logo appears, a certain section of memory is initialized with the game's NTSC
        # identifier: BASLUS-01411-YUGIOH. This stays in memory at least through the game's main menu (as deep as I
        # checked) and probably for as long as the game is running. Most mods base themselves on the NTSC release, and
        # the speedrunning community uses it as well since it's faster than PAL and JP, although I'd like to validate
        # the others releases if there's demand to play them.
        fm_identifier_ram_address: int = 0x10384

        # = BASLUS-01411-YUGIOH in ASCII
        bytes_expected: bytes = bytes.fromhex("4241534C55532D30313431312D595547494F4800")
        try:
            bytes_actual: bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(
                fm_identifier_ram_address, len(bytes_expected), MAIN_RAM
            )]))[0]
            if bytes_actual != bytes_expected:
                return False
        except Exception:
            return False

        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        ctx.watcher_timeout = 0.125  # value taken from Pokemon Emerald's client
        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        # Example of the chest RAM (raw, set Bizhawk memory viewer to big-endian):
        # 0x00000000 0x00000000 0x02000000 0x00000001
        # 2 Shadow Specters (card ID: 9) in the chest and 1 Time Wizard (card ID: 16)
        # Cards in chest DO NOT include what's in the deck
        # Chest memory is updated after the player leaves the Build Deck screen

        # Pokemon Emerald checks the slot data here
        # Can this be evaluated only once?
        if ctx.slot_data is not None:
            self.duelist_unlock_order = map_ids_to_duelists(
                ctx.slot_data[Constants.DUELIST_UNLOCK_ORDER_KEY]
            )
            self.final_6_order = tuple(
                ids_to_duelists[id] for id in ctx.slot_data[Constants.FINAL_6_ORDER_KEY]
            )

            try:
                if self.duelist_unlock_order is not None and self.final_6_order is not None:
                    # Unlock duelists for Progressive Duelist item count
                    progressive_duelist_item_count: int = sum(
                        1 for id in ctx.items_received if id == progressive_duelist_item_id
                    )
                    unlocked_duelists: typing.List[Duelist] = get_unlocked_duelists(
                        progressive_duelist_item_count,
                        self.duelist_unlock_order,
                        self.final_6_order,
                    )
                    first_bit_field: int = 0
                    second_bit_field: int = 0
                    for duelist in unlocked_duelists:
                        if not duelist.is_5th_byte:
                            first_bit_field |= duelist.bitflag
                        else:
                            second_bit_field |= duelist.bitflag
                    if Duelist.HEISHIN_2ND in unlocked_duelists:
                        first_bit_field |= Duelist.HEISHIN.bitflag
                    await bizhawk.write(ctx.bizhawk_ctx, [(
                        UNLOCK_OFFSET,
                        first_bit_field.to_bytes(4, "little") + second_bit_field.to_bytes(1),
                        MAIN_RAM
                    )])
                # Read number of wins over each duelist for "Duelist defeated" locations
                all_duelists: typing.List[Duelist] = [d for d in Duelist]
                read_list: typing.List[typing.Tuple[int, int, str]] = [
                    (d.wins_address, 4, MAIN_RAM) for d in all_duelists
                ]
                wins_bytes: typing.List[bytes] = await bizhawk.read(ctx.bizhawk_ctx, read_list)
                duelists_to_wins: typing.Dict[Duelist, int] = {
                    d: int.from_bytes(w, "little") for d, w in zip(all_duelists, wins_bytes)
                }
                new_local_checked_locations: typing.Set[int] = set([
                    get_location_id_for_duelist(key) for key, value in duelists_to_wins.items() if value != 0
                ])
                # Now check the library (for now, the card chest)
                chest_memory: bytes = (await bizhawk.read(
                    ctx.bizhawk_ctx, [(CARDS_IN_CHESTS_OFFSET, 722, MAIN_RAM)]
                ))[0]
                owned_ids: set[int] = set([get_location_id_for_card_id(i) for i in range(722) if chest_memory[i] != 0])
                new_local_checked_locations |= owned_ids

                if new_local_checked_locations != self.local_checked_locations:
                    self.local_checked_locations = new_local_checked_locations
                    if new_local_checked_locations is not None:
                        await ctx.send_msgs([{
                            "cmd": "LocationChecks",
                            "locations": list(new_local_checked_locations)
                        }])
                if not ctx.finished_game and any(item.item == Constants.VICTORY_ITEM_ID for item in ctx.items_received):
                    await ctx.send_msgs([{
                        "cmd": "StatusUpdate",
                        "status": ClientStatus.CLIENT_GOAL
                    }])
            except bizhawk.RequestFailedError:
                pass
