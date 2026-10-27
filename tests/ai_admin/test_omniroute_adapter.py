"""Unit tests for ai_admin/omniroute_adapter.py (mocked networking)."""

import pytest
from ai_admin.config import AIAdminConfig
from ai_admin.omniroute_adapter import OmniRouteAdapter


class FakeResponse:
    def __init__(self, status: int, data: bytes, headers: dict = None):
        self.status = status
        self._data = data
        self.headers = headers or {}

    async def read(self):
        return self._data

    async def text(self):
        return self._data.decode("utf-8", errors="replace")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeClientSession:
    def __init__(self, response_factory):
        self.response_factory = response_factory
        self.closed = False

    def post(self, url, **kwargs):
        return self.response_factory(url, **kwargs)

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_probe_missing_credentials_defaults_grammar_only():
    config = AIAdminConfig(omniroute_api_url="", omniroute_api_key="")
    adapter = OmniRouteAdapter(config)
    mode = await adapter.probe_capability()
    assert mode == "grammar_only"


@pytest.mark.asyncio
async def test_probe_native_tools_support():
    config = AIAdminConfig(omniroute_api_url="https://api.fake.com", omniroute_api_key="sk-test")

    mock_resp = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {"name": "echo_health", "arguments": '{"message": "pong"}'},
                        }
                    ]
                }
            }
        ]
    }

    import json
    session = FakeClientSession(lambda url, **kw: FakeResponse(200, json.dumps(mock_resp).encode("utf-8")))
    adapter = OmniRouteAdapter(config, session=session)

    mode = await adapter.probe_capability()
    assert mode == "native_tools"


@pytest.mark.asyncio
async def test_auth_error_names_variable_only():
    config = AIAdminConfig(omniroute_api_url="https://api.fake.com", omniroute_api_key="sk-invalid")
    session = FakeClientSession(lambda url, **kw: FakeResponse(401, b"Unauthorized"))
    adapter = OmniRouteAdapter(config, session=session)

    ok, tools, err = await adapter.plan_action("test instruction", [], [])
    assert ok is False
    assert "OMNIROUTE_API_KEY" in err
    assert "sk-invalid" not in err  # Value must never be printed


@pytest.mark.asyncio
async def test_response_size_cap_enforcement():
    config = AIAdminConfig(omniroute_api_url="https://api.fake.com", omniroute_api_key="sk-test")
    giant_payload = b"{" + b"a" * 150000 + b"}"
    session = FakeClientSession(lambda url, **kw: FakeResponse(200, giant_payload))
    adapter = OmniRouteAdapter(config, session=session)

    ok, tools, err = await adapter.plan_action("test", [], [])
    assert ok is False
    assert "exceeded size cap" in err


@pytest.mark.asyncio
async def test_multi_model_failover_on_rate_limit():
    import json

    config = AIAdminConfig(
        omniroute_api_url="https://api.fake.com",
        omniroute_api_key="sk-test",
        ai_models=["primary-model", "fallback-model"],
    )

    calls = []

    def fake_dispatcher(url, **kw):
        payload = kw.get("json", {})
        model = payload.get("model")
        calls.append(model)
        if model == "primary-model":
            # Simulate 429 rate limit on primary model
            return FakeResponse(429, b"Rate limited", headers={"Retry-After": "30"})
        # Fallback model succeeds with tool call
        resp_data = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_fallback",
                                "function": {"name": "jellyfin_search", "arguments": '{"query": "Dune"}'},
                            }
                        ]
                    }
                }
            ]
        }
        return FakeResponse(200, json.dumps(resp_data).encode("utf-8"))

    session = FakeClientSession(fake_dispatcher)
    adapter = OmniRouteAdapter(config, session=session)

    ok, tools, err = await adapter.plan_action("search for Dune", [], [])
    assert ok is True
    assert len(tools) == 1
    assert tools[0]["name"] == "jellyfin_search"
    assert tools[0]["params"] == {"query": "Dune"}
    # Verify primary model was attempted first, then fallback
    assert calls == ["primary-model", "fallback-model"]


@pytest.mark.asyncio
async def test_all_models_failover_exhaustion():
    config = AIAdminConfig(
        omniroute_api_url="https://api.fake.com",
        omniroute_api_key="sk-test",
        ai_models=["m1", "m2"],
    )

    session = FakeClientSession(lambda url, **kw: FakeResponse(429, b"Rate limited", headers={"Retry-After": "60"}))
    adapter = OmniRouteAdapter(config, session=session)

    ok, tools, err = await adapter.plan_action("search", [], [])
    assert ok is False
    assert "rate limit exceeded" in err

