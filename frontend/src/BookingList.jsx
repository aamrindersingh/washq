import React from "react";

function when(iso) {
  const d = new Date(iso);
  return d.toLocaleString([], {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function BookingList({ bookings, onCancel, onCollected }) {
  if (bookings.length === 0) {
    return <p className="muted">Nothing booked yet.</p>;
  }

  return (
    <ul className="bookings">
      {bookings.map((b) => (
        <li key={b.id} className={`booking ${b.status}`}>
          <div className="booking-main">
            <strong>{b.machine.label}</strong>
            <span>{when(b.slot_start)}</span>
            <span className="pill">{b.status.replace("_", " ")}</span>
          </div>
          <div className="booking-sub">
            {b.student_name}, room {b.room_number}
          </div>
          {b.status === "booked" && (
            <div className="booking-actions">
              <button className="link" onClick={() => onCollected(b.id)}>
                Collected
              </button>
              <button className="link danger" onClick={() => onCancel(b.id)}>
                Cancel
              </button>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
