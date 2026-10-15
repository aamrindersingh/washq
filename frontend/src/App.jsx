import React, { useCallback, useEffect, useState } from "react";
import * as api from "./api.js";
import MachineGrid from "./MachineGrid.jsx";
import BookingForm from "./BookingForm.jsx";
import BookingList from "./BookingList.jsx";
import StatsBar from "./StatsBar.jsx";

export default function App() {
  const [machines, setMachines] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [m, b, s] = await Promise.all([
        api.getMachines(),
        api.getBookings(),
        api.getStats(),
      ]);
      setMachines(m);
      setBookings(b.items);
      setStats(s);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    // Machines free up on their own, so keep the board current.
    const timer = setInterval(refresh, 15000);
    return () => clearInterval(timer);
  }, [refresh]);

  function flash(message) {
    setNotice(message);
    setTimeout(() => setNotice(""), 4000);
  }

  async function run(action, okMessage) {
    try {
      await action();
      if (okMessage) flash(okMessage);
      setError("");
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <header>
        <div>
          <h1>WashQ</h1>
          <p className="tagline">Hostel laundry slots. One machine, one wash, no arguments.</p>
        </div>
      </header>

      {error && <div className="banner error">{error}</div>}
      {notice && <div className="banner ok">{notice}</div>}

      {loading ? (
        <p className="muted">Loading the laundry room...</p>
      ) : (
        <>
          <StatsBar stats={stats} />

          <section>
            <h2>Machines</h2>
            <MachineGrid
              machines={machines}
              onToggle={(m) =>
                run(
                  () =>
                    api.setMachineStatus(
                      m.id,
                      m.status === "out_of_order" ? "free" : "out_of_order"
                    ),
                  m.status === "out_of_order"
                    ? `${m.label} is back in service`
                    : `${m.label} marked out of order`
                )
              }
            />
          </section>

          <div className="columns">
            <section>
              <h2>Book a slot</h2>
              <BookingForm
                machines={machines}
                onSubmit={(body) => run(() => api.bookSlot(body), "Slot booked")}
                onAddMachine={(body) => run(() => api.addMachine(body), "Machine added")}
              />
            </section>

            <section>
              <h2>Bookings</h2>
              <BookingList
                bookings={bookings}
                onCancel={(id) => run(() => api.cancelBooking(id), "Booking cancelled")}
                onCollected={(id) => run(() => api.markCollected(id), "Marked collected")}
              />
            </section>
          </div>
        </>
      )}

      <footer>
        <span>WashQ</span>
        <a href="/api/docs">API docs</a>
        <a href="/metrics">Metrics</a>
      </footer>
    </div>
  );
}
