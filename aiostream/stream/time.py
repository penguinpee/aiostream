
import asyncio

from ..utils import anext
from ..core import operator


@operator(pipable=True)
async def space_out(source, interval):
    timeout = 0
    loop = asyncio.get_event_loop()
    async with source.stream() as streamer:
        async for item in streamer:
            await asyncio.sleep(timeout - loop.time())
            yield item
            timeout = loop.time() + interval


@operator(pipable=True)
async def timeout(source, timeout):
    loop = asyncio.get_event_loop()
    async with source.stream() as streamer:
        while True:
            try:
                item = await asyncio.wait_for(anext(streamer), timeout)
            except StopAsyncIteration:
                break
            else:
                yield item