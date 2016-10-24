"""Provide core objects for streaming."""

__all__ = ['Stream', 'Streamer']

import functools
from collections import AsyncIterable, AsyncIterator, Awaitable

from .utils import aiter, anext, _await


# Exception

class StreamEmpty(Exception):
    """Exception raised when awaiting an empty stream."""
    pass


# Helpers

def operator(func=None, *, pipable=False, position=0):
    """Return a decorator to wrap function into a stream operator."""

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return Stream(lambda: func(*args, **kwargs))

        @functools.wraps(func)
        def pipe(*args, **kwargs):
            return lambda source: wrapper(
                *args[:position], source, *args[position:], **kwargs)

        wrapper.operator = True
        wrapper.pipe = pipe if pipable else None
        return wrapper

    return decorator if func is None else decorator(func)


async def wait_stream(stream):
    """Wait for a stream to finish and return the last item."""
    async with aiter(stream) as streamer:
        async for item in streamer:
            item
        try:
            return item
        except NameError:
            raise StreamEmpty()


# Core objects

class Stream(AsyncIterable, Awaitable):
    """Enhanced asynchronous iterable."""

    def __init__(self, factory):
        self._factory = factory

    def __aiter__(self):
        return Streamer(self._factory())

    def __await__(self):
        return _await(aiter(self))

    def __or__(self, func):
        return func(self)

    def __add__(self, value):
        from .stream import chain
        return chain(self, value)

    def __getitem__(self, value):
        from .stream import slice
        return slice(self, value.start, value.stop, value.step)

    stream = __aiter__


class Streamer(Stream, AsyncIterator):
    """"Enhanced asynchronous iterator."""

    def __init__(self, aiterable):
        self._aiterator = aiter(aiterable)

    def __aiter__(self):
        return self

    def __anext__(self):
        return anext(self._aiterator)

    def __await__(self):
        return _await(wait_stream(self))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        if hasattr(self._aiterator, 'aclose'):
            await self._aiterator.aclose()