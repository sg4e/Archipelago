# Yu-Gi-Oh! Forbidden Memories Setup Guide

## Required Software
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases). Please use version 0.4.4 or later for integrated
BizHawk support.
- Yu-Gi-Oh! Forbidden Memories NTSC: ISO or BIN/CUE. Card-drop mods are expressly supported. The Archipelago
implementation tries to be agnostic toward mods, but mods that alter drop tables will create unsupported logic. You do
not have to patch your ROM with Archipelago for it to work. Just make sure you launch a "New Game" for each seed.
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.7 or later

### Configuring BizHawk

Once you have installed BizHawk, open `EmuHawk.exe` and change the following settings:

- If you're using BizHawk 2.7 or 2.8, go to `Config > Customize`. On the Advanced tab, switch the Lua Core from
`NLua+KopiLua` to `Lua+LuaInterface`, then restart EmuHawk. (If you're using BizHawk 2.9, you can skip this step.)
- Under `Config > Customize`, check the "Run in background" option to prevent disconnecting from the client while you're
tabbed out of EmuHawk.
- Open any PlayStation game in EmuHawk and go to `Config > Controllers…` to configure your inputs. If you can't click
`Controllers…`, it's because you need to load a game first.
- Consider clearing keybinds in `Config > Hotkeys…` if you don't intend to use them. Select the keybind and press Esc to
clear it.

## Generating a Game

1. Create your options file (YAML). You can make one on the
[Yu-Gi-Oh! Forbidden Memories options page](../../../games/Yu-Gi-Oh!%20Forbidden%20Memories/player-options).
2. Follow the general Archipelago instructions for [generating a game](../../Archipelago/setup/en#generating-a-game).
3. Open `ArchipelagoLauncher.exe`
4. Select "BizHawk Client" in the right-side column. On your first time opening BizHawk Client, you will also be asked to
locate `EmuHawk.exe` in your BizHawk install.

## Connecting to a Server

1. If EmuHawk didn't launch automatically, open it manually.
2. Open your Yu-Gi-Oh! Forbidden Memories NTSC ISO or CUE file in EmuHawk.
3. Go to "New Game" and keep resetting until you're happy with your starter deck. **You need to commit to a starter deck
before connecting to the multiworld.**
4. When you're happy with your deck, save. From here on, you will **never** enter Campaign mode again and duel
exclusively in Free Duel mode.
5. In EmuHawk, go to `Tools > Lua Console`. This window must stay open while playing.
6. In the Lua Console window, go to `Script > Open Script…`.
7. Navigate to your Archipelago install folder and open `data/lua/connector_bizhawk_generic.lua`.
8. The emulator and client will eventually connect to each other. The BizHawk Client window should indicate that it
connected and recognized Yu-Gi-Oh! Forbidden Memories.
9. To connect the client to the server, enter your room's address and port (e.g. `archipelago.gg:38281`) into the
top text field of the client and click Connect.

You should now be able to receive and send items. You'll need to do these steps every time you want to reconnect. It is
perfectly safe to make progress offline; everything will re-sync when you reconnect.

## Beta Notes and Limitations

The current version of Yu-Gi-Oh! Forbidden Memories in Archipelago is still an early beta. As such, expect a few bugs
and limited features. Please be aware of the following issues specifically:

1. Only cards in chest count as checks. Cards in library (fusions, rituals, etc.) will be supported later.
2. Starchips are out of logic. The logic never expects you to buy a card with starchips. Consequently, starchip-only
cards never gate progression.
3. A lot of checks will award you starchips. Granting starchips in BizHawk isn't implemented yet, so your starchip
count won't actually increase from these (yet).
4. A card has to be in your chest at least temporarily to count as a check. Therefore, cards in your starter deck
won't be "checked" until you swap them out into your chest. Your chest memory isn't refreshed until you leave the
"Build Deck" screen, so you can't quickly swap a card in and out of your deck to check it. This is a limitation
with how the game writes to chest memory and will be fixed when card tracking checks the library instead of the chest.
5. Only card drops are considered for logic (since acquiring a card is the only way to get it in your chest).
6. If you get a Progressive Duelist item while on the Free Duel screen, you'll have to back out and re-enter to
refresh the available duelists.
7. Make sure to save at the end of every play session. The server will remember your duelists and card checks, but
will not save your card inventory. Your local save file is responsible for that.
