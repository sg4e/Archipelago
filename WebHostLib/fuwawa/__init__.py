"""Optional Fuwawa Discord integration for fork-local WebHost deployments."""

from __future__ import annotations

DEFAULT_CONFIG = {
    "ENABLED": False,
    "DISCORD_TOKEN": "",
    "GUILD_ID": 0,
    "CHANNEL_ID": 0,
    "SYNC_COMMANDS": False,
    "BRIDGE_DISCORD_MESSAGES": False,
    "ADMIN_ROLE_IDS": [],
    "SONGS": [],
    "YAML_FOLDER": "fuwawa_yamls",
    "KEEPALIVE_TIMEOUT_SECONDS": 2147483647,
}
