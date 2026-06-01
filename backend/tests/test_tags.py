def test_tag_crud_and_note_relationship(client):
    r = client.post("/tags/", json={"name": "backend"})
    assert r.status_code == 201, r.text
    tag = r.json()
    assert tag["name"] == "backend"

    r = client.post("/tags/", json={"name": "backend"})
    assert r.status_code == 409

    r = client.post("/notes/", json={"title": "Tagged note", "content": "Content"})
    note_id = r.json()["id"]

    r = client.put(f"/notes/{note_id}/tags", json={"tag_ids": [tag["id"]]})
    assert r.status_code == 200
    updated = r.json()
    assert tag["id"] in updated["tag_ids"]

    r = client.post(
        "/action-items/",
        json={"description": "From note", "note_id": note_id},
    )
    assert r.status_code == 201
    assert r.json()["note_id"] == note_id

    r = client.get("/action-items/", params={"note_id": note_id})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1

    r = client.delete(f"/tags/{tag['id']}")
    assert r.status_code == 204


def test_tag_list_sorting(client):
    client.post("/tags/", json={"name": "zebra"})
    client.post("/tags/", json={"name": "alpha"})

    r = client.get("/tags/", params={"sort": "name", "limit": 10})
    assert r.status_code == 200
    names = [tag["name"] for tag in r.json()]
    assert names == sorted(names)
