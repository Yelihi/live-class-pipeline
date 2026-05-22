import asyncio
import json
from typing import AsyncGenerator


class EventBus:
    def __init__(self):
        self._queues: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def publish(self, event: dict):
        """GLib 스레드 또는 asyncio에서 모든 SSE 구독자에게 이벤트 전송"""
        if self._loop is None:
            return
        for q in list(self._queues):
            asyncio.run_coroutine_threadsafe(q.put(event), self._loop)

    async def publish_async(self, event: dict):
        """asyncio 코루틴에서 직접 호출"""
        for q in list(self._queues):
            await q.put(event)

    async def subscribe(self) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.append(queue)
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            self._queues.remove(queue)


# 싱글톤 인스턴스
bus = EventBus()
