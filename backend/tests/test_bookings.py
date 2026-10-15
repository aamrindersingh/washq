from datetime import datetime, timedelta


def book(client, machine_id, start, name="Amrinder", room="A-204"):
    return client.post(
        "/api/bookings",
        json={
            "machine_id": machine_id,
            "student_name": name,
            "room_number": room,
            "slot_start": start,
        },
    )


def shift(iso, minutes):
    return (datetime.fromisoformat(iso) + timedelta(minutes=minutes)).isoformat()


def test_booking_a_free_slot_works(client, machine, tomorrow_10am):
    r = book(client, machine["id"], tomorrow_10am)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "booked"
    assert body["machine"]["label"] == "W1"

    # 45 minute cycle, so the slot must end 45 minutes after it starts.
    start = datetime.fromisoformat(body["slot_start"])
    end = datetime.fromisoformat(body["slot_end"])
    assert (end - start) == timedelta(minutes=45)


def test_the_same_slot_cannot_be_booked_twice(client, machine, tomorrow_10am):
    assert book(client, machine["id"], tomorrow_10am).status_code == 201

    second = book(client, machine["id"], tomorrow_10am, name="Rahul", room="B-101")
    assert second.status_code == 409
    assert "taken until" in second.json()["detail"]


def test_an_overlapping_slot_is_also_refused(client, machine, tomorrow_10am):
    assert book(client, machine["id"], tomorrow_10am).status_code == 201

    # Starts 20 minutes in, so it runs into the first wash.
    overlap = book(client, machine["id"], shift(tomorrow_10am, 20), name="Rahul")
    assert overlap.status_code == 409


def test_back_to_back_slots_are_allowed(client, machine, tomorrow_10am):
    assert book(client, machine["id"], tomorrow_10am).status_code == 201

    # Starts exactly when the first one ends, so it should fit.
    nxt = book(client, machine["id"], shift(tomorrow_10am, 45), name="Rahul")
    assert nxt.status_code == 201


def test_cancelling_frees_the_slot(client, machine, tomorrow_10am):
    first = book(client, machine["id"], tomorrow_10am).json()
    assert client.delete(f"/api/bookings/{first['id']}").status_code == 204

    again = book(client, machine["id"], tomorrow_10am, name="Rahul")
    assert again.status_code == 201


def test_two_machines_can_run_the_same_slot(client, machine, tomorrow_10am):
    other = client.post("/api/machines", json={"label": "W2", "location": "Block A"}).json()
    assert book(client, machine["id"], tomorrow_10am).status_code == 201
    assert book(client, other["id"], tomorrow_10am, name="Rahul").status_code == 201


def test_cannot_book_a_broken_machine(client, machine, tomorrow_10am):
    client.put(f"/api/machines/{machine['id']}/status", json={"status": "out_of_order"})
    r = book(client, machine["id"], tomorrow_10am)
    assert r.status_code == 409
    assert "out of order" in r.json()["detail"]


def test_cannot_book_the_past(client, machine):
    yesterday = (datetime.now() - timedelta(days=1)).replace(microsecond=0).isoformat()
    assert book(client, machine["id"], yesterday).status_code == 422


def test_rescheduling_checks_the_new_slot(client, machine, tomorrow_10am):
    first = book(client, machine["id"], tomorrow_10am).json()
    second = book(client, machine["id"], shift(tomorrow_10am, 45), name="Rahul").json()

    # Try to move the second booking on top of the first.
    r = client.put(f"/api/bookings/{second['id']}", json={"slot_start": tomorrow_10am})
    assert r.status_code == 409

    # Moving it somewhere empty is fine.
    ok = client.put(f"/api/bookings/{second['id']}", json={"slot_start": shift(tomorrow_10am, 90)})
    assert ok.status_code == 200


def test_booking_list_is_paginated(client, machine, tomorrow_10am):
    for i in range(3):
        book(client, machine["id"], shift(tomorrow_10am, 45 * i), name=f"Student{i}")

    page = client.get("/api/bookings", params={"limit": 2}).json()
    assert page["total_items"] == 3
    assert page["total_pages"] == 2
    assert len(page["items"]) == 2


def test_unknown_booking_is_404(client):
    assert client.get("/api/bookings/999").status_code == 404


def test_room_number_is_validated(client, machine, tomorrow_10am):
    r = book(client, machine["id"], tomorrow_10am, room="not a room")
    assert r.status_code == 422
