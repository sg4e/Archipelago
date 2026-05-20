from __future__ import annotations

import multiprocessing
from typing import Any


def create_event_queues() -> tuple[multiprocessing.Queue, multiprocessing.Queue]:
    return multiprocessing.Queue(), multiprocessing.Queue()


def room_event(event_type: str, room_id: Any, event_key: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": event_type,
        "room_id": str(room_id),
        "event_key": event_key,
        "data": data,
    }

