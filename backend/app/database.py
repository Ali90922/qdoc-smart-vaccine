# ===========================================
# File: backend/app/database.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

# SQLAlchemy removed. Keeping this module as a compatibility shim.
engine = None
SessionLocal = None
Base = None


def get_db():
    yield None
