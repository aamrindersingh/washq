def test_add_and_list_machines(client):
    r = client.post("/api/machines", json={"label": "W1", "location": "Block A"})
    assert r.status_code == 201

    r = client.get("/api/machines")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["label"] == "W1"
    assert rows[0]["busy_now"] is False


def test_duplicate_label_is_rejected(client, machine):
    r = client.post("/api/machines", json={"label": "W1", "location": "Block B"})
    assert r.status_code == 409


def test_machine_can_be_marked_out_of_order(client, machine):
    r = client.put(f"/api/machines/{machine['id']}/status", json={"status": "out_of_order"})
    assert r.status_code == 200
    assert r.json()["status"] == "out_of_order"


def test_delete_machine(client, machine):
    assert client.delete(f"/api/machines/{machine['id']}").status_code == 204
    assert client.get("/api/machines").json() == []
