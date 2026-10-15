"""Put a few machines in so the UI is not empty on a fresh database."""
from app.db import SessionLocal
from app.models import Machine

ROWS = [
    ("W1", "Block A ground floor"),
    ("W2", "Block A ground floor"),
    ("W3", "Block B ground floor"),
    ("W4", "Block B ground floor"),
    ("D1", "Block A dryer corner"),
]


def main() -> None:
    db = SessionLocal()
    try:
        existing = {m.label for m in db.query(Machine).all()}
        added = 0
        for label, location in ROWS:
            if label not in existing:
                db.add(Machine(label=label, location=location))
                added += 1
        db.commit()
        print(f"seed: {added} machines added, {len(existing)} already there")
    finally:
        db.close()


if __name__ == "__main__":
    main()
