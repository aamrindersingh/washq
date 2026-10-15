import React, { useEffect, useState } from "react";

function nextHalfHour() {
  const d = new Date();
  d.setSeconds(0, 0);
  d.setMinutes(d.getMinutes() + (30 - (d.getMinutes() % 30)));
  // datetime-local wants the value without a timezone on the end.
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

export default function BookingForm({ machines, onSubmit, onAddMachine }) {
  const usable = machines.filter((m) => m.status !== "out_of_order");
  const [form, setForm] = useState({
    machine_id: "",
    student_name: "",
    room_number: "",
    slot_start: nextHalfHour(),
  });
  const [newMachine, setNewMachine] = useState({ label: "", location: "" });

  useEffect(() => {
    if (!form.machine_id && usable.length > 0) {
      setForm((f) => ({ ...f, machine_id: String(usable[0].id) }));
    }
  }, [usable, form.machine_id]);

  function change(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function submit(e) {
    e.preventDefault();
    onSubmit({ ...form, machine_id: Number(form.machine_id) });
    setForm({ ...form, student_name: "", room_number: "" });
  }

  return (
    <>
      <form onSubmit={submit} className="form">
        <label>
          Machine
          <select name="machine_id" value={form.machine_id} onChange={change} required>
            {usable.length === 0 && <option value="">No machines available</option>}
            {usable.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label} ({m.location})
              </option>
            ))}
          </select>
        </label>

        <label>
          Your name
          <input
            name="student_name"
            value={form.student_name}
            onChange={change}
            placeholder="Amrinder Singh"
            minLength={2}
            required
          />
        </label>

        <label>
          Room
          <input
            name="room_number"
            value={form.room_number}
            onChange={change}
            placeholder="A-204"
            pattern="[A-Za-z]?-?[0-9]{1,4}[A-Za-z]?"
            required
          />
        </label>

        <label>
          Start
          <input
            type="datetime-local"
            name="slot_start"
            value={form.slot_start}
            onChange={change}
            required
          />
        </label>

        <button type="submit" disabled={usable.length === 0}>
          Book 45 minutes
        </button>
      </form>

      <details className="add-machine">
        <summary>Add a machine</summary>
        <form
          className="form"
          onSubmit={(e) => {
            e.preventDefault();
            onAddMachine(newMachine);
            setNewMachine({ label: "", location: "" });
          }}
        >
          <label>
            Label
            <input
              value={newMachine.label}
              onChange={(e) => setNewMachine({ ...newMachine, label: e.target.value })}
              placeholder="W5"
              required
            />
          </label>
          <label>
            Location
            <input
              value={newMachine.location}
              onChange={(e) => setNewMachine({ ...newMachine, location: e.target.value })}
              placeholder="Block C ground floor"
              minLength={2}
              required
            />
          </label>
          <button type="submit">Add</button>
        </form>
      </details>
    </>
  );
}
