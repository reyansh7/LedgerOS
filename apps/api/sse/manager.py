"""Server-Sent Events (SSE) Manager for streaming live agent activity to the UI."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, Dict, List


class SSEManager:
    """Manages active event channels for real-time agent execution milestones."""

    def __init__(self):
        self._channels: dict[str, list[asyncio.Queue]] = {}

    async def subscribe(self, channel_id: str) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()
        self._channels.setdefault(channel_id, []).append(queue)
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            if channel_id in self._channels:
                self._channels[channel_id].remove(queue)
                if not self._channels[channel_id]:
                    del self._channels[channel_id]

    async def broadcast(self, channel_id: str, data: dict):
        if channel_id in self._channels:
            for queue in self._channels[channel_id]:
                await queue.put(data)


sse_manager = SSEManager()
