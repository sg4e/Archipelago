from __future__ import annotations

import asyncio
import io
import logging
import random
import threading
from datetime import timezone
from typing import Any
from uuid import UUID

from pony.orm import commit, db_session, select

from Utils import utcnow
from WebHostLib import to_python
from WebHostLib.fuwawa.config import get_fuwawa_config
from WebHostLib.fuwawa.formatting import (
    bold_progression_item,
    format_goal_event,
    format_players,
    format_progression_dm,
    mention,
    role_mention,
)
from WebHostLib.fuwawa.models import (
    FuwawaMultiworld,
    FuwawaPing,
    FuwawaPlayer,
    FuwawaYaml,
    STATE_COMPLETED,
    STATE_IN_PROGRESS,
    STATE_REGISTRATION_CLOSED,
    STATE_REGISTRATION_OPEN,
    STATE_UNPLANNED,
)
from WebHostLib.fuwawa.pings import parse_ping_lines
from WebHostLib.fuwawa.services import (
    attach_room,
    close_registration,
    complete_multiworld,
    increment_finished,
    player_by_slot,
    progression_rows_since,
    scoped_event_key,
    set_user_progression_cursor,
    sync_player_slots,
    upsert_item_payload,
    user_pings_for_item,
)
from WebHostLib.fuwawa.state import (
    delete_user_signup,
    get_current_multiworld,
    has_duplicate_registered_name,
    mark_dispatched,
    pings_for_user,
    replace_user_signup,
)
from WebHostLib.fuwawa.yamls import MAX_YAML_SIZE, YamlValidationError, parse_submitted_games, summarize_games
from WebHostLib.models import Room

LOG = logging.getLogger(__name__)


def to_python_room_id(value: str) -> UUID:
    return UUID(value)


def start_worker(flask_app, ap_to_discord_queue=None, discord_to_ap_queue=None) -> threading.Thread | None:
    config = get_fuwawa_config(flask_app.config)
    if not config["ENABLED"]:
        LOG.info("FUWAWA is disabled; Discord worker will not start.")
        return None
    if not config["DISCORD_TOKEN"] or not config["GUILD_ID"] or not config["CHANNEL_ID"]:
        LOG.error(
            "FUWAWA is enabled but required Discord configuration is missing "
            "(token_present=%s, guild_id=%s, channel_id=%s).",
            bool(config["DISCORD_TOKEN"]),
            config["GUILD_ID"],
            config["CHANNEL_ID"],
        )
        return None

    thread = threading.Thread(
        target=_run_bot_thread,
        args=(flask_app, config, ap_to_discord_queue, discord_to_ap_queue),
        name="FuwawaDiscord",
        daemon=True,
    )
    thread.start()
    LOG.info("Fuwawa Discord worker launched in thread %s.", thread.name)
    return thread


def _run_bot_thread(flask_app, config: dict[str, Any], ap_to_discord_queue=None, discord_to_ap_queue=None) -> None:
    try:
        asyncio.run(_run_bot(flask_app, config, ap_to_discord_queue, discord_to_ap_queue))
    except ImportError:
        LOG.exception("discord.py is required when FUWAWA.ENABLED is true.")
    except Exception as ex:
        discord_module = getattr(ex.__class__, "__module__", "")
        exception_name = ex.__class__.__name__
        if discord_module.startswith("discord") and exception_name == "LoginFailure":
            LOG.exception("Fuwawa Discord login failed. Check that DISCORD_TOKEN is a valid raw bot token.")
        elif discord_module.startswith("discord") and exception_name == "PrivilegedIntentsRequired":
            LOG.exception("Fuwawa Discord gateway rejected the requested privileged intents.")
        elif discord_module.startswith("discord") and exception_name in {"HTTPException", "GatewayNotFound"}:
            LOG.exception("Fuwawa Discord connection failed with a Discord HTTP/gateway error.")
        elif isinstance(ex, (OSError, TimeoutError)):
            LOG.exception("Fuwawa Discord connection failed with a network error.")
        else:
            LOG.exception("Fuwawa Discord worker crashed unexpectedly.")


async def _run_bot(flask_app, config: dict[str, Any], ap_to_discord_queue=None, discord_to_ap_queue=None) -> None:
    import discord
    from discord import app_commands

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = bool(config["BRIDGE_DISCORD_MESSAGES"])
    LOG.info(
        "Fuwawa Discord worker connecting to Discord "
        "(guild_id=%s, channel_id=%s, bridge_messages=%s, sync_commands=%s).",
        config["GUILD_ID"],
        config["CHANNEL_ID"],
        config["BRIDGE_DISCORD_MESSAGES"],
        config["SYNC_COMMANDS"],
    )
    client = FuwawaDiscordClient(
        flask_app,
        config,
        ap_to_discord_queue=ap_to_discord_queue,
        discord_to_ap_queue=discord_to_ap_queue,
        intents=intents,
    )
    client.build_commands(app_commands)
    await client.start(config["DISCORD_TOKEN"])


class FuwawaDiscordClient:
    def __init__(self, flask_app, config: dict[str, Any], ap_to_discord_queue=None,
                 discord_to_ap_queue=None, **kwargs):
        import discord

        self.flask_app = flask_app
        self.config = config
        self.ap_to_discord_queue = ap_to_discord_queue
        self.discord_to_ap_queue = discord_to_ap_queue
        self.client = discord.Client(**kwargs)
        self.tree = discord.app_commands.CommandTree(self.client)
        self.discord = discord
        self.random = random.Random()
        self.client.event(self.on_connect)
        self.client.event(self.on_ready)
        self.client.event(self.on_disconnect)
        self.client.event(self.on_resumed)
        self.client.event(self.on_message)

    async def start(self, token: str) -> None:
        await self.client.start(token)

    def build_commands(self, app_commands) -> None:
        discord = self.discord

        yaml_group = app_commands.Group(name="yaml", description="Commands for multiworld YAML registration")
        ping_group = app_commands.Group(name="ping", description="Commands for item acquisition pings")
        advance_group = app_commands.Group(name="advance_state", description="Advances the Fuwawa multiworld state")

        @yaml_group.command(name="add", description="Adds a YAML to the upcoming multiworld")
        async def yaml_add(interaction, yaml_file: discord.Attachment):
            await interaction.response.defer(ephemeral=False)
            if not self.registration_is_open():
                await interaction.followup.send("Sorry, registration for the next multiworld isn't open yet. BAU BAU!")
                return
            if yaml_file.size > MAX_YAML_SIZE:
                await interaction.followup.send("Sorry, YAML files bigger than 64MB aren't supported. BAU BAU!")
                return
            try:
                contents = (await yaml_file.read()).decode("utf-8")
                games = parse_submitted_games(contents)
                with db_session:
                    multiworld = get_current_multiworld()
                    if has_duplicate_registered_name(
                        multiworld, [game.name for game in games], excluding_discord_id=interaction.user.id
                    ):
                        names = ", ".join(sorted(player.name_in_game for player in multiworld.players))
                        await interaction.followup.send(
                            "Sorry, I couldn't add your YAML because another player has already taken your name. "
                            f"Here's the list of names in the multiworld: {names}. BAU BAU!"
                        )
                        return
                    replace_user_signup(
                        multiworld,
                        interaction.user.id,
                        self.member_display_name(interaction.user),
                        yaml_file.filename,
                        contents,
                        games,
                    )
                    role_id = multiworld.discord_role_id
                    commit()
                if role_id and isinstance(interaction.user, discord.Member):
                    role = interaction.guild.get_role(role_id)
                    if role:
                        await interaction.user.add_roles(role)
                await interaction.followup.send(f"I've saved your YAML: {summarize_games(games)}. BAU BAU!")
            except (UnicodeDecodeError, YamlValidationError) as ex:
                await interaction.followup.send(
                    f"Sorry, I couldn't add your YAML because I encountered this problem trying to read it: {ex}. "
                    "BAU BAU!"
                )

        @yaml_group.command(name="get", description="Posts all YAMLs you've submitted")
        async def yaml_get(interaction):
            await self.send_yamls(interaction, interaction.user.id, "You haven't")

        @yaml_group.command(name="peek", description="Posts all YAMLs submitted by a Discord user")
        async def yaml_peek(interaction, participant: discord.Member):
            await self.send_yamls(interaction, participant.id, f"{participant.display_name} hasn't")

        @yaml_group.command(name="summarize", description="Replies with all games you've submitted")
        async def yaml_summarize(interaction):
            await interaction.response.defer(ephemeral=False)
            with db_session:
                multiworld = get_current_multiworld()
                rows = [
                    (player.game_name, player.name_in_game)
                    for player in select(
                        player for player in FuwawaPlayer
                        if player.multiworld == multiworld and player.discord_id == interaction.user.id
                    )
                ]
            if not rows:
                await interaction.followup.send("You haven't submitted any YAMLs yet. BAU BAU!")
                return
            summary = ", ".join(f"{game} as {name}" for game, name in rows)
            await interaction.followup.send(f"You've signed up to play {summary}. BAU BAU!")

        @yaml_group.command(name="delete", description="Deletes all YAMLs you've submitted")
        async def yaml_delete(interaction):
            await interaction.response.defer(ephemeral=False)
            with db_session:
                multiworld = get_current_multiworld()
                deleted = delete_user_signup(multiworld, interaction.user.id)
                role_id = multiworld.discord_role_id
                commit()
            if not deleted:
                await interaction.followup.send("You haven't submitted any YAMLs yet. BAU BAU!")
                return
            if role_id and isinstance(interaction.user, discord.Member):
                role = interaction.guild.get_role(role_id)
                if role:
                    await interaction.user.remove_roles(role)
            await interaction.followup.send("Deleted all your YAMLs. BAU BAU!")

        @ping_group.command(name="add", description="Sends a ping whenever you receive the specified item")
        async def ping_add(interaction, item: str):
            await interaction.response.defer(ephemeral=True)
            if not await self.require_participant(interaction):
                return
            with db_session:
                multiworld = get_current_multiworld()
                existing = [
                    ping for ping in pings_for_user(multiworld, interaction.user.id)
                    if ping.item_name.casefold() == item.casefold()
                ]
                if existing:
                    await interaction.followup.send(f"You've already requested a ping for {item}. BAU BAU!")
                    return
                FuwawaPing(multiworld=multiworld, discord_id=interaction.user.id, item_name=item)
                commit()
            await interaction.followup.send(f"Ok, I'll ping you whenever you receive an item called \"{item}\". BAU BAU!")

        @ping_group.command(name="add_multiple", description="Registers pings for all items in a file")
        async def ping_add_multiple(interaction, text_file: discord.Attachment):
            await interaction.response.defer(ephemeral=True)
            if not await self.require_participant(interaction):
                return
            if text_file.size > MAX_YAML_SIZE:
                await interaction.followup.send("Sorry, files bigger than 64MB aren't supported. BAU BAU!")
                return
            contents = (await text_file.read()).decode("utf-8")
            with db_session:
                multiworld = get_current_multiworld()
                already = {ping.item_name for ping in pings_for_user(multiworld, interaction.user.id)}
                new_pings = parse_ping_lines(contents, already)
                for item_name in new_pings:
                    FuwawaPing(multiworld=multiworld, discord_id=interaction.user.id, item_name=item_name)
                commit()
            await interaction.followup.send(f"Ok, I registered {len(new_pings)} pings from the file you sent me. BAU BAU!")

        @ping_group.command(name="list", description="Lists all items for which you've registered pings")
        async def ping_list(interaction):
            await interaction.response.defer(ephemeral=True)
            with db_session:
                multiworld = get_current_multiworld()
                items = sorted((ping.item_name for ping in pings_for_user(multiworld, interaction.user.id)), key=str.casefold)
            if not items:
                await interaction.followup.send("You haven't requested any pings yet. BAU BAU!")
                return
            await interaction.followup.send(f"You've requested pings for the following item(s): {', '.join(items)}. BAU BAU!")

        @ping_group.command(name="remove", description="Stops sending pings for the specified item")
        async def ping_remove(interaction, item: str):
            await interaction.response.defer(ephemeral=True)
            with db_session:
                multiworld = get_current_multiworld()
                removed = 0
                for ping in list(pings_for_user(multiworld, interaction.user.id)):
                    if ping.item_name.casefold() == item.casefold():
                        ping.delete()
                        removed += 1
                commit()
            if not removed:
                await interaction.followup.send(
                    f"You didn't request a ping for {item}. Did you mean to remove a different item? "
                    "Use /ping list to see all your requested pings. BAU BAU!"
                )
                return
            await interaction.followup.send(f"Ok, I won't ping you anymore when you receive {item}. BAU BAU!")

        @ping_group.command(name="remove_all", description="Stops sending all pings on item acquisitions")
        async def ping_remove_all(interaction):
            await interaction.response.defer(ephemeral=True)
            with db_session:
                multiworld = get_current_multiworld()
                for ping in list(pings_for_user(multiworld, interaction.user.id)):
                    ping.delete()
                commit()
            await interaction.followup.send("Ok, I'll only ping you when someone hints an item in your world. BAU BAU!")

        @ping_group.command(name="when_im_helpful", description="Ping you too when you found a specifically requested item")
        async def ping_when_helpful(interaction, on: bool):
            await interaction.response.defer(ephemeral=True)
            with db_session:
                multiworld = get_current_multiworld()
                for player in select(
                    player for player in FuwawaPlayer
                    if player.multiworld == multiworld and player.discord_id == interaction.user.id
                ):
                    player.pinged_when_helpful = on
                commit()
            await interaction.followup.send(f"Ok, I've turned \"I was useful\" pings {'on' if on else 'off'} for you. BAU BAU!")

        @ping_group.command(name="all_progress", description="Sends a ping for any item labeled Progression")
        async def ping_all_progress(interaction, on: bool):
            await interaction.response.defer(ephemeral=True)
            with db_session:
                multiworld = get_current_multiworld()
                for player in select(
                    player for player in FuwawaPlayer
                    if player.multiworld == multiworld and player.discord_id == interaction.user.id
                ):
                    player.ping_all_progression = on
                commit()
            await interaction.followup.send(f"Ok, I've turned \"All Progression\" pings {'on' if on else 'off'} for you. BAU BAU!")

        @advance_group.command(name="registration_open", description="Opens registration to accept YAMLs")
        async def advance_registration_open(interaction, theme_name: str, participant_role: str, unix_starttime: int):
            if not await self.require_admin(interaction):
                return
            with db_session:
                multiworld = get_current_multiworld()
                if multiworld.state != STATE_UNPLANNED:
                    await interaction.response.send_message("You must advance state one step at a time.", ephemeral=True)
                    return
            role = await interaction.guild.create_role(name=participant_role, mentionable=True)
            with db_session:
                multiworld = get_current_multiworld()
                from WebHostLib.fuwawa.services import open_registration
                open_registration(multiworld, theme_name, role.id, unix_starttime)
                commit()
            message = (
                f"{interaction.user.display_name} has opened a new async multiworld!\n\n"
                f"Theme: {theme_name}\nStart: <t:{unix_starttime}:F>.\n\n"
                "Please add your YAMLs with `/yaml add` before then. Everyone is welcome to join us! BAU BAU!"
            )
            await interaction.response.send_message(message)
            await self.pin_original(interaction)
            await self.set_topic(f"Multiworld begins at <t:{unix_starttime}:F>")

        @advance_group.command(name="registration_closed", description="Closes registration")
        async def advance_registration_closed(interaction):
            if not await self.require_admin(interaction):
                return
            with db_session:
                multiworld = get_current_multiworld()
                if multiworld.state != STATE_REGISTRATION_OPEN:
                    await interaction.response.send_message("You must advance state one step at a time.", ephemeral=True)
                    return
                close_registration(multiworld)
                commit()
            await interaction.response.send_message(f"{interaction.user.display_name} has closed registration for the next multiworld. BAU BAU!")

        @advance_group.command(name="in_progress", description="Attaches a WebHost room and begins monitoring progress")
        async def advance_in_progress(interaction, room_id: str):
            if not await self.require_admin(interaction):
                return
            await interaction.response.defer(ephemeral=False)
            try:
                room_uuid = to_python(room_id)
            except Exception:
                await interaction.followup.send("That room_id is not a valid Archipelago short room id.", ephemeral=True)
                return
            with db_session:
                multiworld = get_current_multiworld()
                if multiworld.state != STATE_REGISTRATION_CLOSED:
                    await interaction.followup.send("You must advance state one step at a time.", ephemeral=True)
                    return
                room = Room.get(id=room_uuid)
                if room is None:
                    await interaction.followup.send("I couldn't find that room. BAU BAU!", ephemeral=True)
                    return
                attach_room(
                    multiworld,
                    room,
                    self.flask_app.config["HOST_ADDRESS"],
                    self.config["KEEPALIVE_TIMEOUT_SECONDS"],
                )
                role_id = multiworld.discord_role_id
                web_page = multiworld.web_page
                ap_server = multiworld.ap_server
                commit()
            role_text = f"<@&{role_id}>" if role_id else ""
            await interaction.followup.send(
                f"{role_text} The multiworld is now open!\n\nRoom: {web_page}\nAP Server: {ap_server}\n\n"
                "Good luck and have fun! BAU BAU!"
            )
            await self.set_topic(web_page or "")

        @self.tree.command(name="players", description="Lists all participants in the current or upcoming multiworld")
        async def players(interaction):
            await interaction.response.defer(ephemeral=False)
            with db_session:
                multiworld = get_current_multiworld()
                rows = [(player.discord_name, player.game_name, player.name_in_game) for player in multiworld.players]
            await interaction.followup.send(format_players(rows))

        @self.tree.command(name="status", description="Queries the current multiworld status")
        async def status(interaction):
            with db_session:
                multiworld = get_current_multiworld()
                message = f"The current multiworld is in the {multiworld.state} state."
                if multiworld.state == STATE_REGISTRATION_OPEN and multiworld.unix_start_time:
                    message += f" It will begin at <t:{multiworld.unix_start_time}:F>."
                if multiworld.state == STATE_IN_PROGRESS:
                    message += f" {multiworld.participants_finished} out of {multiworld.total_participants} players have finished so far."
            await interaction.response.send_message(f"{message} BAU BAU!")

        @self.tree.command(name="song_request", description="Fuwawa offers you a song to listen to")
        async def song_request(interaction):
            songs = list(self.config["SONGS"])
            await interaction.response.send_message(self.random.choice(songs) if songs else "No songs are configured. BAU BAU!")

        @self.tree.command(name="progression", description="DMs you with progression items obtained since your last check")
        async def progression(interaction):
            await interaction.response.defer(ephemeral=True)
            with db_session:
                multiworld = get_current_multiworld()
                if multiworld.state != STATE_IN_PROGRESS:
                    await interaction.followup.send("There's no multiworld in progress right now. BAU BAU!")
                    return
                players = [
                    player for player in multiworld.players
                    if player.discord_id == interaction.user.id
                ]
                if not players:
                    await interaction.followup.send("You're not in this multiworld! BAU BAU!")
                    return
                since = players[0].last_progression_call
                rows = progression_rows_since(multiworld, interaction.user.id, since)
                set_user_progression_cursor(multiworld, interaction.user.id, utcnow())
            if not rows:
                await interaction.followup.send("No new progression items since you last checked. BAU BAU...")
                return
            await interaction.followup.send("I'll send you a DM with all your latest progression items. BAU BAU!")
            await interaction.user.send(format_progression_dm(rows, since))

        @self.tree.command(name="increment_finished", description="Manually increment the number of finished players")
        async def increment_finished_command(interaction):
            if not await self.require_admin(interaction):
                return
            with db_session:
                multiworld = get_current_multiworld()
                if multiworld.state != STATE_IN_PROGRESS:
                    await interaction.response.send_message(
                        "increment_finished command is only supported while the multiworld is in progress.",
                        ephemeral=True,
                    )
                    return
                finished = increment_finished(multiworld)
                if multiworld.total_participants and finished >= multiworld.total_participants:
                    complete_multiworld(multiworld)
                commit()
            await interaction.response.send_message(f"Number of finished players is now set to {finished}", ephemeral=True)

        self.tree.add_command(yaml_group)
        self.tree.add_command(ping_group)
        self.tree.add_command(advance_group)

    async def on_ready(self) -> None:
        guild = self.discord.Object(id=self.config["GUILD_ID"])
        if self.config["SYNC_COMMANDS"]:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        LOG.info("Fuwawa Discord integration ready as %s (%s).", self.client.user, self.client.user.id)
        if self.ap_to_discord_queue:
            self.client.loop.create_task(self.ap_event_consumer_loop())

    async def on_connect(self) -> None:
        LOG.info("Fuwawa Discord gateway connected.")

    async def on_disconnect(self) -> None:
        LOG.warning("Fuwawa Discord gateway disconnected.")

    async def on_resumed(self) -> None:
        LOG.info("Fuwawa Discord gateway session resumed.")

    async def on_message(self, message) -> None:
        if (
            not self.config["BRIDGE_DISCORD_MESSAGES"]
            or message.author.bot
            or message.channel.id != self.config["CHANNEL_ID"]
        ):
            return
        content = message.content.strip()
        if not content:
            return
        with db_session:
            multiworld = get_current_multiworld()
            if multiworld.state != STATE_IN_PROGRESS or multiworld.room is None:
                return
            room_id = str(multiworld.room.id)
        if self.discord_to_ap_queue:
            self.discord_to_ap_queue.put({
                "room_id": room_id,
                "command": f"/fuwawa_say {message.author.display_name} from Discord: {content}",
            })

    async def ap_event_consumer_loop(self) -> None:
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            try:
                payload = await self.client.loop.run_in_executor(None, self.ap_to_discord_queue.get)
                await self.handle_ap_event(payload)
            except Exception:
                LOG.exception("Error in Fuwawa AP event consumer")

    async def handle_ap_event(self, payload: dict[str, Any]) -> None:
        channel = self.client.get_channel(self.config["CHANNEL_ID"])
        if channel is None:
            channel = await self.client.fetch_channel(self.config["CHANNEL_ID"])
        event_type = payload.get("type")
        if event_type not in {"item", "hint", "goal", "text"}:
            LOG.warning("Ignoring unknown Fuwawa AP event: %r", payload)
            return

        message = None
        update_topic = False
        with db_session:
            room = Room.get(id=to_python_room_id(payload["room_id"]))
            if room is None:
                return
            multiworld = select(
                mw for mw in FuwawaMultiworld
                if mw.room == room and mw.state == STATE_IN_PROGRESS
            ).first()
            if multiworld is None:
                return
            sync_player_slots(multiworld)
            if event_type == "text":
                message = payload["data"]["message"]
                return_send_only = True
            else:
                return_send_only = False
            event_key = scoped_event_key(multiworld, payload["event_key"])
            if not return_send_only and not mark_dispatched(multiworld, event_key, event_type):
                return
            if return_send_only:
                pass
            elif event_type == "item":
                message = self.build_item_message(multiworld, payload)
            elif event_type == "hint":
                message = self.build_hint_message(multiworld, payload)
            elif event_type == "goal":
                message, update_topic = self.build_goal_message(multiworld, payload)
            commit()

        if message:
            await channel.send(message)
        if update_topic:
            await self.set_topic(f"Completed at <t:{int(utcnow().replace(tzinfo=timezone.utc).timestamp())}:F>")

    def build_item_message(self, multiworld: FuwawaMultiworld, payload: dict[str, Any]) -> str:
        data = payload["data"]
        receiver_data = data["receiver"]
        sender_data = data["sender"]
        receiver = player_by_slot(multiworld, receiver_data["slot"])
        sender = player_by_slot(multiworld, sender_data["slot"])
        receiver_discord_id = receiver.discord_id if receiver else None
        sender_discord_id = sender.discord_id if sender else None
        upsert_item_payload(multiworld, payload, receiver_discord_id, sender_discord_id)
        item = bold_progression_item(data["item_name"], data["flags"])
        location = f" ({data['location_name']})" if data["location_name"] else ""
        if sender_data["slot"] == receiver_data["slot"]:
            message = f"{receiver_data['name']} found their {item}{location}"
        else:
            message = f"{sender_data['name']} sent {item} to {receiver_data['name']}{location}"
        if receiver:
            specific_pings = user_pings_for_item(multiworld, receiver.discord_id, data["item_name"])
            all_progression = receiver.ping_all_progression and bool(data["flags"] & 0b001)
            if specific_pings or all_progression:
                message = f"{message} {mention(receiver.discord_id)}"
                if specific_pings and sender and sender.pinged_when_helpful and sender.discord_id != receiver.discord_id:
                    message = f"{message} (Given by {mention(sender.discord_id)})"
        return message

    def build_hint_message(self, multiworld: FuwawaMultiworld, payload: dict[str, Any]) -> str:
        data = payload["data"]
        item = bold_progression_item(data["item_name"], data["flags"])
        entrance = f" at {data['entrance_name']}" if data["entrance_name"] else ""
        status = "found" if data["found"] else "not found"
        message = (
            f"[Hint]: {data['receiver']['name']}'s {item} is at {data['location_name']} "
            f"in {data['finder']['name']}'s World{entrance}. ({status})"
        )
        receiver = player_by_slot(multiworld, data["receiver"]["slot"])
        finder = player_by_slot(multiworld, data["finder"]["slot"])
        if (
            not data["found"]
            and finder
            and (not receiver or receiver.discord_id != finder.discord_id)
        ):
            message = f"{message} {mention(finder.discord_id)}"
        return message

    def build_goal_message(self, multiworld: FuwawaMultiworld, payload: dict[str, Any]) -> tuple[str, bool]:
        data = payload["data"]
        finished = increment_finished(multiworld)
        total = multiworld.total_participants or len(list(multiworld.players))
        complete = bool(total and finished >= total)
        if complete:
            complete_multiworld(multiworld)
        return (
            format_goal_event(data["slot"]["name"], finished, total, complete, role_mention(multiworld.discord_role_id)),
            complete,
        )

    async def send_yamls(self, interaction, discord_id: int, subject_verb: str) -> None:
        await interaction.response.defer(ephemeral=False)
        with db_session:
            multiworld = get_current_multiworld()
            rows = [
                (row.filename, row.contents)
                for row in select(
                    row for row in FuwawaYaml
                    if row.multiworld == multiworld and row.discord_id == discord_id
                )
            ]
        if not rows:
            await interaction.followup.send(f"{subject_verb} submitted any YAMLs yet. BAU BAU!")
            return
        files = [
            self.discord.File(io.BytesIO(contents.encode("utf-8")), filename=filename)
            for filename, contents in rows
        ]
        await interaction.followup.send(files=files)

    async def require_participant(self, interaction) -> bool:
        with db_session:
            multiworld = get_current_multiworld()
            participating = bool([
                player for player in multiworld.players
                if player.discord_id == interaction.user.id
            ])
        if not participating:
            await interaction.followup.send("You need to be a participant in the multiworld to request pings. BAU BAU!")
            return False
        return True

    async def require_admin(self, interaction) -> bool:
        if self.is_admin(interaction.user):
            return True
        if not interaction.response.is_done():
            await interaction.response.send_message("Sorry, you don't have permission to use that command.", ephemeral=True)
        else:
            await interaction.followup.send("Sorry, you don't have permission to use that command.", ephemeral=True)
        return False

    def is_admin(self, member) -> bool:
        role_ids = set(self.config["ADMIN_ROLE_IDS"])
        if role_ids and hasattr(member, "roles"):
            return any(role.id in role_ids for role in member.roles)
        guild_permissions = getattr(member, "guild_permissions", None)
        return bool(guild_permissions and guild_permissions.manage_guild)

    def registration_is_open(self) -> bool:
        with db_session:
            return get_current_multiworld().state == STATE_REGISTRATION_OPEN

    async def set_topic(self, topic: str) -> None:
        channel = self.client.get_channel(self.config["CHANNEL_ID"])
        if channel is None:
            channel = await self.client.fetch_channel(self.config["CHANNEL_ID"])
        if hasattr(channel, "edit"):
            await channel.edit(topic=topic)

    async def pin_original(self, interaction) -> None:
        try:
            message = await interaction.original_response()
            await message.pin()
        except Exception:
            LOG.exception("Could not pin Fuwawa announcement")

    @staticmethod
    def member_display_name(member) -> str:
        return getattr(member, "display_name", None) or getattr(member, "name", str(member))
