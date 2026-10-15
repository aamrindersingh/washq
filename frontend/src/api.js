async function request(path, options) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (res.status === 204) return null;

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Request failed with ${res.status}`);
  }
  return body;
}

export const getMachines = () => request("/api/machines");
export const getStats = () => request("/api/stats");
export const getBookings = () => request("/api/bookings?limit=50");

export const addMachine = (body) =>
  request("/api/machines", { method: "POST", body: JSON.stringify(body) });

export const setMachineStatus = (id, status) =>
  request(`/api/machines/${id}/status`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });

export const bookSlot = (body) =>
  request("/api/bookings", { method: "POST", body: JSON.stringify(body) });

export const cancelBooking = (id) =>
  request(`/api/bookings/${id}`, { method: "DELETE" });

export const markCollected = (id) =>
  request(`/api/bookings/${id}`, {
    method: "PUT",
    body: JSON.stringify({ status: "collected" }),
  });
