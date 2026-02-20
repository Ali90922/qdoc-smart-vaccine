"""
Run this once to seed the vaccines table from vaccine_rules.json:
    python seed_vaccines.py
"""
import json
import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import Base, Vaccine

Base.metadata.create_all(bind=engine)

rules_path = os.path.join(os.path.dirname(__file__), "app/data/vaccine_rules.json")
with open(rules_path) as f:
    vaccines = json.load(f)["vaccines"]

db = SessionLocal()

inserted = 0
skipped = 0

for v in vaccines:
    existing = db.query(Vaccine).filter(Vaccine.vaccine_key == v["id"]).first()
    if existing:
        skipped += 1
        continue

    vaccine = Vaccine(
        vaccine_key=v["id"],
        name=v["name"],
        description=v.get("description"),
        min_age_months=v.get("min_age_months"),
        max_age_months=v.get("max_age_months"),
        doses_required=v["doses_required"],
        dose_interval_days=v.get("dose_interval_days"),
        repeat_interval_days=v.get("repeat_interval_days"),
    )
    db.add(vaccine)
    inserted += 1

db.commit()
db.close()

print(f"Seeding complete: {inserted} inserted, {skipped} already existed.")
