import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.runtime import registry


class Echo:
    def __init__(self, value):
        self.value = value

    async def execute(self, request_data):
        return {"result": {"value": self.value}, "trace": []}


@pytest.fixture
def app():
    registry._ACTIVE_ROUTES.clear()
    application = FastAPI()

    @application.get("/builtin")
    def builtin():
        return {}

    yield application
    registry._ACTIVE_ROUTES.clear()


@pytest.mark.parametrize("path", [
    "/api/files/{file_id}", "/api", "/agent/session", "/ws/agent/x", "/docs", "/openapi.json", "/", "hello",
])
def test_reserved_paths_rejected(app, path):
    with pytest.raises(registry.DeployError) as err:
        registry.register_route(app, {"path": path, "method": "POST"}, Echo(1), workflow_id="w1")
    assert err.value.status_code == 422


def test_existing_platform_route_rejected(app):
    with pytest.raises(registry.DeployError):
        registry.register_route(app, {"path": "/builtin", "method": "GET"}, Echo(1), workflow_id="w1")


def test_other_workflow_cannot_take_a_path(app):
    registry.register_route(app, {"path": "/hello", "method": "GET"}, Echo(1), workflow_id="w1")
    with pytest.raises(registry.DeployError) as err:
        registry.register_route(app, {"path": "/hello", "method": "get"}, Echo(2), workflow_id="w2")
    assert err.value.status_code == 409
    assert TestClient(app).get("/hello").json() == {"value": 1}


def test_redeploy_replaces_only_own_route(app):
    registry.register_route(app, {"path": "/a", "method": "GET"}, Echo(1), workflow_id="w1")
    registry.register_route(app, {"path": "/b", "method": "GET"}, Echo(2), workflow_id="w2")
    registry.register_route(app, {"path": "/a2", "method": "GET"}, Echo(3), workflow_id="w1")
    client = TestClient(app)
    assert client.get("/a").status_code == 404
    assert client.get("/a2").json() == {"value": 3}
    assert client.get("/b").json() == {"value": 2}

    registry.unregister_route(app, workflow_id="w1")
    assert client.get("/a2").status_code == 404
    assert client.get("/b").json() == {"value": 2}
    assert client.get("/builtin").status_code == 200
