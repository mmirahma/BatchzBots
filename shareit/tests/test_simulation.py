"""Pytest wrapper for multi-user automated simulation runner."""

import pytest
from tests.simulation_runner import run_simulation


@pytest.mark.asyncio
async def test_full_multi_user_simulation():
    res = await run_simulation()
    assert res is True
