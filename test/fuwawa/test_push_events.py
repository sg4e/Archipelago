from pathlib import Path


def test_discord_worker_does_not_use_polling_monitor() -> None:
    bot_source = Path("WebHostLib/fuwawa/bot.py").read_text(encoding="utf-8")

    assert "POLL_SECONDS" not in bot_source
    assert "monitor_loop" not in bot_source
    assert "collect_room_actions" not in bot_source
