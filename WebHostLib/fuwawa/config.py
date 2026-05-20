from __future__ import annotations

from typing import Any

from WebHostLib.fuwawa import DEFAULT_CONFIG


def get_fuwawa_config(app_config: dict[str, Any]) -> dict[str, Any]:
    raw_config = app_config.get("FUWAWA") or {}
    config = DEFAULT_CONFIG.copy()
    config.update(raw_config)
    config["ENABLED"] = bool(config.get("ENABLED"))
    config["SYNC_COMMANDS"] = bool(config.get("SYNC_COMMANDS"))
    config["BRIDGE_DISCORD_MESSAGES"] = bool(config.get("BRIDGE_DISCORD_MESSAGES"))
    config["GUILD_ID"] = int(config.get("GUILD_ID") or 0)
    config["CHANNEL_ID"] = int(config.get("CHANNEL_ID") or 0)
    config["ADMIN_ROLE_IDS"] = [int(role_id) for role_id in config.get("ADMIN_ROLE_IDS") or []]
    config["KEEPALIVE_TIMEOUT_SECONDS"] = int(config.get("KEEPALIVE_TIMEOUT_SECONDS") or 2147483647)
    return config


def is_enabled(app_config: dict[str, Any]) -> bool:
    return get_fuwawa_config(app_config)["ENABLED"]
