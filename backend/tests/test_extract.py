from backend.app.services.extract import extract_action_items


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "ACTION: review PR" in items
    assert "Ship it!" in items


def test_extract_checkbox_and_numbered_items():
    text = """
    - [ ] Draft design doc
    - [x] Ship hotfix
    1. Schedule retro
    FIXME: broken cache
    """.strip()
    items = extract_action_items(text)
    assert "Draft design doc" in items
    assert "Ship hotfix" in items
    assert "Schedule retro" in items
    assert "FIXME: broken cache" in items


def test_extract_deduplicates_items():
    text = """
    TODO: write tests
    - TODO: write tests
    """.strip()
    items = extract_action_items(text)
    assert items.count("TODO: write tests") == 1


def test_extract_from_note_endpoint(client):
    payload = {
        "title": "Planning",
        "content": "TODO: finalize roadmap\n- [ ] Write docs\nRegular line",
    }
    r = client.post("/notes/", json=payload)
    note_id = r.json()["id"]

    r = client.post(f"/notes/{note_id}/extract")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2

    r = client.post("/notes/extract", json={"text": "ACTION: deploy @action"})
    assert r.status_code == 200
    assert r.json()["count"] >= 1
