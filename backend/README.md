# Backend

FastAPI service with a pandas-backed local store for vaccine eligibility, schedule classification, and reminder simulation.

## Structure

```text
backend/
├── app/
│   ├── data/                 # Vaccine rule definitions (JSON)
│   ├── engine/               # Rule engine
│   ├── pandas_store.py       # Pandas CSV persistence layer
│   ├── routers/              # API route modules
│   ├── database.py           # Legacy compatibility shim
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
python seed_vaccines.py
uvicorn app.main:app --reload
```

Backend persistence uses a pandas file store in `backend/data_store/*.csv`.
No SQL database setup is required.

## Test

```bash
cd backend
pytest -q
```
