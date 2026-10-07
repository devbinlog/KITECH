"""Test configuration for torus-mock."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from src.app.main import app
from src.app.services.machine_store import MachineStore, get_store, reset_store


DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def store() -> MachineStore:
    """Create a fresh store with default data for each test."""
    reset_store()
    s = get_store()
    s.load_from_json(DATA_DIR / "default_machines.json")
    return s


@pytest.fixture
async def client(store) -> AsyncClient:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
