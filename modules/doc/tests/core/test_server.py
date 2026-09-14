import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import json
import logging
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server import (
    SSEManager,
    app,
    get_allowed_origins,
    sse_manager,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_allowed_origins_exception(caplog):
    from src.server import get_security_config
    get_security_config.cache_clear()
    with patch("tomllib.load", side_effect=Exception("Mocked tomllib error")):
        origins = get_allowed_origins()
        assert origins == ["http://localhost:8000", "http://127.0.0.1:8000"]
        assert "Could not load security config from config.toml" in caplog.text


@pytest.mark.asyncio
async def test_sse_manager_connect():
    test_manager = SSEManager()
    q = test_manager.connect()

    assert q in test_manager.active_queues


@pytest.mark.asyncio
async def test_sse_manager_disconnect():
    test_manager = SSEManager()
    q = test_manager.connect()
    assert q in test_manager.active_queues

    test_manager.disconnect(q)
    assert q not in test_manager.active_queues


def test_get_allowed_origins_open_error(caplog):
    from src.server import get_security_config
    get_security_config.cache_clear()
    with patch("builtins.open", side_effect=Exception("Test open error")):
        with caplog.at_level(logging.WARNING):
            origins = get_allowed_origins()

    assert origins == ["http://localhost:8000", "http://127.0.0.1:8000"]
    assert "Could not load security config from config.toml: Test open error" in caplog.text


@pytest.mark.asyncio
async def test_sse_manager_broadcast():
    test_manager = SSEManager()
    q1 = test_manager.connect()
    q2 = test_manager.connect()

    await test_manager.broadcast("test message")

    assert not q1.empty()
    assert not q2.empty()

    msg1 = await q1.get()
    msg2 = await q2.get()

    assert msg1 == "test message"
    assert msg2 == "test message"

def test_sync_post(client):
    response = client.post("/api/sync", json={"type": "focus", "targetId": "heading-1"})
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_sync_post_error(client, caplog):
    # Make broadcast raise an exception
    with patch.object(sse_manager, "broadcast", side_effect=Exception("Test broadcast error")):
        response = client.post("/api/sync", json={"type": "focus", "targetId": "heading-1"})
        assert response.status_code == 200
        assert response.json() == {"status": "error", "message": "Test broadcast error"}
        assert "Error in sync post: Test broadcast error" in caplog.text


@patch("src.server.aiofiles.open")
def test_receive_data_success(mock_file, client):
    mock_file_instance = AsyncMock()
    mock_file.return_value.__aenter__.return_value = mock_file_instance

    test_data = {"user_id": "123", "action": "click"}

    # We must start the lifespan events using the TestClient as a context manager
    with TestClient(app) as test_client:
        response = test_client.post("/api/data", json=test_data)
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

        # Give the background task time to process the queue
        import time
        time.sleep(0.1)

    # Verify file was written to
    mock_file_instance.write.assert_called_once()
    write_args = mock_file_instance.write.call_args[0][0]
    written_data = json.loads(write_args.strip())
    assert written_data == test_data


@patch("src.server.data_queue")
def test_receive_data_error(mock_queue, client):
    mock_queue.put = AsyncMock(side_effect=Exception("Queue full"))

    test_data = {"user_id": "123", "action": "click"}
    # we don't necessarily need lifespan context here if we mock the queue
    with TestClient(app) as test_client:
        # Patching inside the test to be safe since lifespan resets data_queue
        with patch("src.server.data_queue", mock_queue):
            response = test_client.post("/api/data", json=test_data)

    assert response.status_code == 200
    assert response.json() == {"status": "error", "message": "Queue full"}


@patch("uvicorn.run")
def test_main(mock_run):
    import runpy
    import sys

    # Ensure any previously imported instance of src.server is removed to avoid RuntimeWarning
    sys.modules.pop("src.server", None)
    # Run the server module as __main__ to hit the if __name__ == "__main__": block
    runpy.run_module("src.server", run_name="__main__")
    # assert_called_once checks that it was called once.
    # The actual app instance differs because runpy loads a new instance of the module,
    # so we just assert the host and port kwargs.
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["host"] == "0.0.0.0"
    assert mock_run.call_args.kwargs["port"] == 8000

@patch.dict("os.environ", {"ENVIRONMENT": "production"})
def test_get_security_config_production():
    from src.server import get_security_config
    get_security_config.cache_clear()

    config = get_security_config()

    # In production, "null" and "*" should be removed from origins
    assert "null" not in config["origins"]
    assert "*" not in config["origins"]
    # Methods should be restricted
    assert config["methods"] == ["GET", "POST", "OPTIONS"]
    # Headers should be restricted
    assert config["headers"] == ["Content-Type", "Content-Length", "Accept"]

@patch.dict("os.environ", {"ENVIRONMENT": "development"})
def test_get_security_config_development():
    from src.server import get_security_config
    get_security_config.cache_clear()

    config = get_security_config()

    # In development, it should use permissive defaults
    assert config["methods"] == ["*"]
    assert config["headers"] == ["*"]
