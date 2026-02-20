# Backend

FastAPI + SQLAlchemy service for vaccine eligibility, schedule classification, and reminder simulation.

## Structure

```text
backend/
├── app/
│   ├── data/                 # Vaccine rule definitions (JSON)
│   ├── engine/               # Rule engine
│   ├── routers/              # API route modules
│   ├── database.py           # DB engine/session
│   ├── dependencies.py       # Auth deps
│   ├── main.py               # FastAPI app
│   ├── models.py             # ORM models
│   └── schemas.py            # Pydantic schemas + validation
├── tests/
│   ├── conftest.py           # Test import setup
│   ├── engine/               # Rule engine tests
│   └── schemas/              # Input/schema validation tests
├── requirements.txt
└── seed_vaccines.py
```

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
cd backend
pytest -q
```

