"""Pytest wrapper for multi-user automated simulation runner."""

import pytest
from tests.simulation_runner import run_simulation


@pytest.mark.asyncio
async def test_full_multi_user_simulation():
    res = await run_simulation()
    assert res["trip_id"] is not None
    assert res["total_spent"] > 0
    assert len(res["families"]) == 4
    assert len(res["meals"]) == 3
    assert len(res["expenses"]) == 4
