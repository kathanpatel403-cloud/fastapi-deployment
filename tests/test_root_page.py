import asyncio

from main import root


def test_root_shows_backend_status_page():
    response = asyncio.run(root())
    body = response.body.decode()

    assert response.status_code == 200
    assert "FastAPI Backend Status" in body
    assert "Database" in body
    assert "Message Broker" in body
