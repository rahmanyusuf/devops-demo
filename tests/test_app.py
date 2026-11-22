import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import app as app_module  # noqa: E402


def client():
    app_module.NOTES.clear()
    return app_module.app.test_client()


def test_health_ok():
    r = client().get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok" and "version" in body


def test_index_renders():
    r = client().get("/")
    assert r.status_code == 200 and b"Release board" in r.data


def test_add_note_appears():
    c = client()
    c.post("/notes", data={"note": "first release"})
    assert b"first release" in c.get("/").data


def test_empty_note_rejected():
    assert client().post("/notes", data={"note": "   "}).status_code == 400


def test_html_is_escaped():
    c = client()
    c.post("/notes", data={"note": "<script>alert(1)</script>"})
    assert b"<script>alert(1)</script>" not in c.get("/").data
