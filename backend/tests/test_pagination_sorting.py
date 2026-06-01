def _create_notes(client, count: int) -> list[int]:
    ids = []
    for index in range(count):
        r = client.post(
            "/notes/",
            json={"title": f"Note {index:02d}", "content": f"Content {index:02d}"},
        )
        assert r.status_code == 201
        ids.append(r.json()["id"])
    return ids


def test_notes_pagination(client):
    _create_notes(client, 5)

    r = client.get("/notes/", params={"skip": 0, "limit": 2, "sort": "id"})
    assert r.status_code == 200
    page_one = r.json()
    assert len(page_one["items"]) == 2
    assert page_one["meta"]["total"] >= 5
    assert page_one["meta"]["skip"] == 0
    assert page_one["meta"]["limit"] == 2

    r = client.get("/notes/", params={"skip": 4, "limit": 2, "sort": "id"})
    page_two = r.json()
    assert len(page_two["items"]) >= 1
    assert page_one["items"][0]["id"] != page_two["items"][0]["id"]


def test_notes_sorting(client):
    _create_notes(client, 3)

    asc_response = client.get("/notes/", params={"sort": "title", "limit": 10})
    desc_response = client.get("/notes/", params={"sort": "-title", "limit": 10})
    assert asc_response.status_code == 200
    assert desc_response.status_code == 200

    asc_titles = [item["title"] for item in asc_response.json()["items"]]
    desc_titles = [item["title"] for item in desc_response.json()["items"]]
    assert asc_titles == sorted(asc_titles)
    assert desc_titles == sorted(desc_titles, reverse=True)


def test_action_items_pagination_and_sorting(client):
    for index in range(4):
        client.post("/action-items/", json={"description": f"Task {index}"})

    open_response = client.get(
        "/action-items/",
        params={"completed": False, "skip": 0, "limit": 2, "sort": "description"},
    )
    assert open_response.status_code == 200
    body = open_response.json()
    assert len(body["items"]) == 2
    assert body["meta"]["total"] >= 4

    desc_response = client.get(
        "/action-items/",
        params={"sort": "-description", "limit": 10},
    )
    descriptions = [item["description"] for item in desc_response.json()["items"]]
    assert descriptions == sorted(descriptions, reverse=True)


def test_invalid_pagination_params(client):
    r = client.get("/notes/", params={"skip": -1})
    assert r.status_code == 422

    r = client.get("/notes/", params={"limit": 0})
    assert r.status_code == 422

    r = client.get("/action-items/", params={"sort": "not_a_field"})
    assert r.status_code == 400
