"""Regression tests for long Unity MCP calls (server-side timeout propagation)."""
from importlib import import_module
from unittest.mock import AsyncMock

import pytest

execute_module = import_module("services.tools.execute_code")
batch_module = import_module("services.tools.batch_execute")


@pytest.mark.asyncio
@pytest.mark.parametrize("requested,expected", [
    (None, 300), (1, 1), (480, 480), (9999, 3600), (-5, 1),
])
async def test_execute_code_sends_unity_timeout(monkeypatch, requested, expected):
    send = AsyncMock(return_value={"success": True, "message": "ok", "data": 7})
    monkeypatch.setattr(execute_module, "get_unity_instance_from_context",
                        AsyncMock(return_value="unity-test"))
    monkeypatch.setattr(execute_module, "send_with_unity_instance", send)
    kwargs = {} if requested is None else {"timeout_seconds": requested}
    response = await execute_module.execute_code(
        object(), action="execute", code="return 7;", **kwargs
    )
    assert response["success"] is True
    assert send.await_args.args[1:3] == ("unity-test", "execute_code")
    assert send.await_args.args[3]["timeout_seconds"] == expected


@pytest.mark.asyncio
async def test_replay_also_sends_unity_timeout(monkeypatch):
    send = AsyncMock(return_value={"success": True})
    monkeypatch.setattr(execute_module, "get_unity_instance_from_context",
                        AsyncMock(return_value="unity-test"))
    monkeypatch.setattr(execute_module, "send_with_unity_instance", send)
    await execute_module.execute_code(
        object(), action="replay", index=0, timeout_seconds=420
    )
    assert send.await_args.args[3]["timeout_seconds"] == 420


@pytest.mark.asyncio
async def test_execute_code_preserves_error_when_message_is_null(monkeypatch):
    monkeypatch.setattr(execute_module, "get_unity_instance_from_context",
                        AsyncMock(return_value="unity-test"))
    monkeypatch.setattr(
        execute_module, "send_with_unity_instance",
        AsyncMock(return_value={
            "success": False,
            "message": None,
            "error": "Unity command timed out after 300 seconds",
            "data": {"command": "execute_code"},
        }),
    )
    result = await execute_module.execute_code(
        object(), action="execute", code="return 1;"
    )
    assert result["success"] is False
    assert result["message"] == "Unity command timed out after 300 seconds"
    assert result["error"] == "Unity command timed out after 300 seconds"
    assert result["data"] == {"command": "execute_code"}


@pytest.mark.asyncio
async def test_execute_code_failure_without_diagnostic_is_explicit(monkeypatch):
    monkeypatch.setattr(execute_module, "get_unity_instance_from_context",
                        AsyncMock(return_value="unity-test"))
    monkeypatch.setattr(
        execute_module, "send_with_unity_instance",
        AsyncMock(return_value={"success": False, "message": None, "error": None}),
    )
    result = await execute_module.execute_code(
        object(), action="execute", code="return 1;"
    )
    assert result["message"] == "Unity command failed without a diagnostic"


@pytest.mark.asyncio
@pytest.mark.parametrize("requested,expected", [
    (None, 300), (2, 2), (600, 600), (9000, 3600), (0, 1),
])
async def test_batch_execute_sends_unity_timeout(monkeypatch, requested, expected):
    send = AsyncMock(return_value={"success": True, "data": []})
    monkeypatch.setattr(batch_module, "get_unity_instance_from_context",
                        AsyncMock(return_value="unity-test"))
    monkeypatch.setattr(batch_module, "_get_max_commands_from_editor_state",
                        AsyncMock(return_value=25))
    monkeypatch.setattr(batch_module, "send_with_unity_instance", send)
    kwargs = {} if requested is None else {"timeout_seconds": requested}
    await batch_module.batch_execute(
        object(), commands=[{"tool": "read_console", "params": {}}], **kwargs
    )
    assert send.await_args.args[1:3] == ("unity-test", "batch_execute")
    assert send.await_args.args[3]["timeout_seconds"] == expected
