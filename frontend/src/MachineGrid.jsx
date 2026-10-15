import React from "react";

function clock(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function stateOf(machine) {
  if (machine.status === "out_of_order") return { cls: "bad", text: "Out of order" };
  if (machine.busy_now) return { cls: "busy", text: `Free at ${clock(machine.free_at)}` };
  return { cls: "good", text: "Free now" };
}

export default function MachineGrid({ machines, onToggle }) {
  if (machines.length === 0) {
    return <p className="muted">No machines yet. Add one on the left.</p>;
  }

  return (
    <div className="grid">
      {machines.map((m) => {
        const state = stateOf(m);
        return (
          <article key={m.id} className={`card ${state.cls}`}>
            <div className="card-top">
              <h3>{m.label}</h3>
              <span className="dot" aria-hidden="true" />
            </div>
            <p className="where">{m.location}</p>
            <p className="state">{state.text}</p>
            <button className="link" onClick={() => onToggle(m)}>
              {m.status === "out_of_order" ? "Mark working" : "Report broken"}
            </button>
          </article>
        );
      })}
    </div>
  );
}
