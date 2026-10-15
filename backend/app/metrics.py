from prometheus_client import Counter, Gauge

bookings_created = Counter(
    "washq_bookings_created_total",
    "Slots booked successfully",
)

double_booking_rejected = Counter(
    "washq_double_booking_rejected_total",
    "Booking attempts refused because the slot was already taken",
)

bookings_cancelled = Counter(
    "washq_bookings_cancelled_total",
    "Bookings cancelled by a student",
)

machines_busy = Gauge(
    "washq_machines_busy",
    "Machines running a wash right now",
)

machines_out_of_order = Gauge(
    "washq_machines_out_of_order",
    "Machines marked broken",
)
