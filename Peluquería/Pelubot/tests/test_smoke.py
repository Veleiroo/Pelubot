# tests/test_smoke.py
import asyncio
import pytest

def test_basic_math():
    assert 2 + 2 == 4

@pytest.mark.asyncio
async def test_async_smoke():
    await asyncio.sleep(0)
    assert True
