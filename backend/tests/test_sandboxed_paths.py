import pytest

from app.ai.tools.file_ops import FileReadTool, FileWriteTool
from app.core.config import settings
from app.db_connectors.sqlite_connector import resolve_sqlite_path


def test_file_tools_stay_inside_base_path(tmp_path):
    writer = FileWriteTool(base_path=str(tmp_path))
    reader = FileReadTool(base_path=str(tmp_path))
    assert "Written" in writer._run('{"path": "sub/a.txt", "content": "hi"}')
    assert reader._run("sub/a.txt") == "hi"

    for bad in ["/etc/passwd", "../outside.txt", "sub/../../x"]:
        assert "must be inside" in reader._run(bad)
    assert "must be inside" in writer._run('{"path": "../evil.py", "content": "x"}')


def test_sqlite_paths_confined(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SQLITE_BASE_DIR", str(tmp_path))
    assert resolve_sqlite_path(":memory:") == ":memory:"
    assert resolve_sqlite_path("app.db") == str(tmp_path / "app.db")
    assert resolve_sqlite_path(str(tmp_path / "x" / "y.db")) == str(tmp_path / "x" / "y.db")
    for bad in ["/etc/passwd", "../escape.db", str(tmp_path.parent / "other.db")]:
        with pytest.raises(ValueError):
            resolve_sqlite_path(bad)
