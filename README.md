# QDoc Vaccine Portal

Rule-based vaccine eligibility + reminder system with a FastAPI backend and React frontend.

## Repository Layout

```text
qdoc-smart-vaccine/
├── backend/
│   ├── app/                  # API, models, schemas, rule engine
│   ├── tests/                # Organized backend test suites
│   │   ├── engine/
│   │   └── schemas/
│   ├── requirements.txt
│   └── seed_vaccines.py
├── frontend/
│   ├── public/               # Static assets (favicon/logo)
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   └── pages/
│   ├── package.json
│   └── vite.config.js
└── .gitignore
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

## Quick Start

### 1) Database

```bash
psql postgres
```

```sql
CREATE DATABASE qdoc;
\q
```

### 2) Backend

```bash
cd backend
pip install -r requirements.txt
python seed_vaccines.py
uvicorn app.main:app --reload
```

Backend:
- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:
- App: [http://localhost:5173](http://localhost:5173)

## Testing

Backend test suites:

```bash
cd backend
pytest -q
```

Current organized coverage includes:
- `backend/tests/engine/` for rule-engine behavior
- `backend/tests/schemas/` for input/validation behavior

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Login |
| POST | `/api/profile` | Create patient profile |
| GET | `/api/profile/me` | Get profile |
| PUT | `/api/profile/me` | Update profile |
| GET | `/api/dashboard/me` | Vaccine statuses + summary |
| GET | `/api/schedule/me` | Upcoming schedule |
| POST | `/api/reminders/send` | Reminder simulation |
| GET | `/api/reminders/me` | Reminder history |

## Notes

- Generated artifacts (`node_modules`, `dist`, `__pycache__`, local `.env`) are ignored by `.gitignore`.
- See `backend/README.md` and `frontend/README.md` for service-specific details.

