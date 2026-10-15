import os
from zoneinfo import ZoneInfo

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://washq:washq@localhost:5432/washq",
)

# Hostel runs on local time. Slots are wall clock, no offsets stored.
HOSTEL_TZ = ZoneInfo(os.getenv("HOSTEL_TZ", "Asia/Kolkata"))

# One wash cycle. Every booking is exactly this long.
SLOT_MINUTES = int(os.getenv("SLOT_MINUTES", "45"))

APP_VERSION = os.getenv("APP_VERSION", "dev")
