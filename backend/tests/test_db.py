"""Tests for db.py — engine, session factory, dependency."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import async_engine, get_db


async def test_engine_connects():
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_get_db_yields_session():
    """get_db is an async generator that yields an AsyncSession."""
    gen = get_db()
    session = await anext(gen)
    assert isinstance(session, AsyncSession)
    # cleanup
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass


async def test_get_db_session_is_usable_and_closes():
    """Verify the session yielded by get_db can execute and is cleanly closed."""
    gen = get_db()
    session = await anext(gen)
    result = await session.execute(text("SELECT 42"))
    assert result.scalar() == 42
    # exhaust the generator to trigger cleanup
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass
    # In SQLAlchemy 2.0, AsyncSession is reset after close (not truly closed):
    # the session context manager calls close() which ends the transaction but
    # leaves the session re-usable. We verify the session exited cleanly by
    # checking it is no longer in an active transaction.
    assert not session.in_transaction(), (
        "Session should not be in a transaction after get_db generator exits"
    )
