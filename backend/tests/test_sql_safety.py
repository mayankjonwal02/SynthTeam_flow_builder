import pytest

from app.db_connectors.sql_safety import build_bound_query, safe_ident


@pytest.mark.parametrize("name", ["users", "public.users", "_tmp1", "Users"])
def test_safe_ident_accepts_plain_identifiers(name):
    assert safe_ident(name) == name


@pytest.mark.parametrize("name", [
    "", "users;", "x) VALUES (1); DROP TABLE users;--", "a b", "a.b.c", "1abc", "na\"me", None,
])
def test_safe_ident_rejects_everything_else(name):
    with pytest.raises(ValueError):
        safe_ident(name)


def test_template_placeholders_become_bound_params_postgres():
    query, params = build_bound_query(
        "SELECT * FROM t WHERE name = '{{input.name}}' AND id = {{input.id}}",
        {"name": "x' OR 1=1--", "id": 5, "unused": 1},
        "postgres",
    )
    assert query == "SELECT * FROM t WHERE name = $1 AND id = $2"
    assert params == ["x' OR 1=1--", 5]


def test_named_placeholders_and_dialects():
    ctx = {"id": 7, "name": "bob"}
    q, p = build_bound_query("SELECT * FROM t WHERE id = :id AND n = :name", ctx, "mysql")
    assert q == "SELECT * FROM t WHERE id = %s AND n = %s" and p == [7, "bob"]
    q, p = build_bound_query("SELECT * FROM t WHERE id = :id", ctx, "sqlite")
    assert q == "SELECT * FROM t WHERE id = ?" and p == [7]


def test_casts_literals_and_unknown_names_left_alone():
    q, p = build_bound_query(
        "SELECT created::text, '10:30' FROM t WHERE x = :missing AND id = :id",
        {"id": 1},
        "postgres",
    )
    assert q == "SELECT created::text, '10:30' FROM t WHERE x = :missing AND id = $1"
    assert p == [1]
