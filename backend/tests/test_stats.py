from datetime import datetime, timedelta


def test_stats_counts_machines_and_bookings(client, machine, tomorrow_10am):
    client.post("/api/machines", json={"label": "W2", "location": "Block A"})
    client.post(
        "/api/bookings",
        json={
            "machine_id": machine["id"],
            "student_name": "Amrinder",
            "room_number": "A-204",
            "slot_start": tomorrow_10am,
        },
    )

    s = client.get("/api/stats").json()
    assert s["machines_total"] == 2
    assert s["bookings_upcoming"] == 1
    assert s["by_status"]["booked"] == 1
    assert s["machines_out_of_order"] == 0


def test_broken_machines_show_in_stats(client, machine):
    client.put(f"/api/machines/{machine['id']}/status", json={"status": "out_of_order"})
    assert client.get("/api/stats").json()["machines_out_of_order"] == 1
