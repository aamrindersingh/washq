import React from "react";

export default function StatsBar({ stats }) {
  if (!stats) return null;

  const free = stats.machines_total - stats.machines_busy_now - stats.machines_out_of_order;

  const tiles = [
    { label: "Free now", value: free, tone: "good" },
    { label: "Washing", value: stats.machines_busy_now, tone: "busy" },
    { label: "Out of order", value: stats.machines_out_of_order, tone: "bad" },
    { label: "Booked today", value: stats.bookings_today, tone: "plain" },
    { label: "Upcoming", value: stats.bookings_upcoming, tone: "plain" },
  ];

  return (
    <div className="stats">
      {tiles.map((t) => (
        <div key={t.label} className={`tile ${t.tone}`}>
          <span className="value">{t.value}</span>
          <span className="label">{t.label}</span>
        </div>
      ))}
    </div>
  );
}
