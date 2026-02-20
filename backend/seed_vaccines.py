# ===========================================
# File: backend/seed_vaccines.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

"""
Run this once to seed pandas vaccine store from vaccine_rules.json:
    python seed_vaccines.py
"""
import os
import sys

sys.path.append(os.path.dirname(__file__))

from app.pandas_store import ensure_vaccines_seeded

inserted, skipped = ensure_vaccines_seeded()

print(f"Seeding complete: {inserted} inserted, {skipped} already existed.")
