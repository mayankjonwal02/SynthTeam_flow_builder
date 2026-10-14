"""Agent Builder API: auth, session ownership, no secret leakage."""

import copy

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.auth import verify_token
from app.main import app
from app.multi_agent import api as agent_api

OWNER = {"sub": "user_owner"}
OTHER = {"sub": "user_other"}


class FakeSessionManager:
    def __init__(self):
        self.sessions = {
            "s1": {
                "id": "s1",
                "user_id": OWNER["sub"],
                "status": "reviewing",
                "conversation": [{"role": "user", "content": "build it"}],
                "artifacts": {
                    "llm_config": {"llm_provider": "openai", "llm_model": "x", "api_key": "sk-secret"},
                    "secrets": {"n1": {"api_key": "sk-node"}},
                    "graph": {"nodes": [{"id": "n1", "data": {"config": {}}}], "edges": []},
                },
            }
        }

    async def get(self, session_id):
        s = self.sessions.get(session_id)
        return copy.deepcopy(s) if s else None

    async def update_status(self, session_id, status):
        self.sessions[session_id]["status"] = status

    async def update_artifact(self, session_id, key, value):
        self.sessions[session_id]["artifacts"][key] = value


@pytest.fixture
def fake_mgr(monkeypatch):
    mgr = FakeSessionManager()
    monkeypatch.setattr(agent_api, "_session_mgr", mgr)
    # Don't actually run the LLM pipeline in tests
    monkeypatch.setattr(agent_api, "_schedule_run", lambda *a, **k: None)
    yield mgr
    app.dependency_overrides.clear()


def as_user(user):
    app.dependency_overrides[verify_token] = lambda: user


@pytest.mark.parametrize("method,path", [
    ("get", "/agent/session/s1"),
    ("post", "/agent/session/start"),
    ("post", "/agent/session/s1/message"),
    ("post", "/agent/session/s1/secrets"),
    ("post", "/agent/session/s1/approve"),
    ("post", "/agent/session/s1/save"),
    ("get", "/agent/ollama/models"),
    ("get", "/api/files/abc"),
    ("get", "/api/projects"),
    ("get", "/api/agents/"),
])
def test_requires_authentication(method, path):
    app.dependency_overrides.clear()
    response = getattr(TestClient(app), method)(path)
    assert response.status_code in (401, 403)


def test_owner_gets_session_without_secrets(fake_mgr):
    as_user(OWNER)
    data = TestClient(app).get("/agent/session/s1").json()
    assert data["artifacts"]["llm_config"] == {"llm_provider": "openai", "llm_model": "x", "has_api_key": True}
    assert "secrets" not in data["artifacts"]
    assert "sk-secret" not in str(data) and "sk-node" not in str(data)


@pytest.mark.parametrize("method,path,body", [
    ("get", "/agent/session/s1", None),
    ("post", "/agent/session/s1/message", {"message": "hi"}),
    ("post", "/agent/session/s1/approve", None),
    ("post", "/agent/session/s1/secrets", {"secrets": {}}),
    ("post", "/agent/session/not-a-uuid/approve", None),
])
def test_other_users_cannot_touch_session(fake_mgr, method, path, body):
    as_user(OTHER)
    client = TestClient(app)
    response = client.request(method.upper(), path, json=body)
    assert response.status_code == 404


def test_approve_and_secrets_merge_into_graph(fake_mgr):
    as_user(OWNER)
    client = TestClient(app)
    assert client.post("/agent/session/s1/approve").json() == {"status": "approved"}
    assert fake_mgr.sessions["s1"]["status"] == "approved"

    r = client.post("/agent/session/s1/secrets", json={"secrets": {"n1": {"api_key": "sk-new"}}})
    assert r.status_code == 200
    node = fake_mgr.sessions["s1"]["artifacts"]["graph"]["nodes"][0]
    assert node["data"]["config"]["api_key"] == "sk-new"


def test_websocket_requires_token(fake_mgr):
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as err:
        with client.websocket_connect("/ws/agent/s1") as ws:
            ws.receive_text()
    assert err.value.code == 1008


def test_websocket_rejects_other_users_session(fake_mgr, monkeypatch):
    from app.multi_agent import ws as ws_module

    monkeypatch.setattr(ws_module, "decode_clerk_token", lambda token: OTHER)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as err:
        with client.websocket_connect("/ws/agent/s1?token=t") as ws:
            ws.receive_text()
    assert err.value.code == 1008


def test_websocket_accepts_owner(fake_mgr, monkeypatch):
    from app.multi_agent import ws as ws_module

    monkeypatch.setattr(ws_module, "decode_clerk_token", lambda token: OWNER)
    with TestClient(app).websocket_connect("/ws/agent/s1?token=t"):
        assert "s1" in ws_module.ConnectionStore
