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

## Quick Start

### 1) Backend

```bash
cd backend
pip install -r requirements.txt
python seed_vaccines.py
uvicorn app.main:app --reload
```

Backend:
- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2) Frontend

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

- Backend now uses a lightweight **pandas file store** (`backend/data_store/*.csv`), so no SQL database is required.
- `python seed_vaccines.py` initializes vaccine catalog CSV data from the rule file.
- Generated artifacts (`node_modules`, `dist`, `__pycache__`, local `.env`) are ignored by `.gitignore`.
- See `backend/README.md` and `frontend/README.md` for service-specific details.

## Recent Updates (Feb 21, 2026)

- Rule engine updates:
  - Dynamic required-dose logic for `pneu_c_15`, `hpv`, `hepatitis_b`, and `mmr`.
  - MMR cohort handling updated (born before 1970 treated as immune -> `UP_TO_DATE` with `doses_required = 0`).
  - Pneu-C-20 eligibility clarified for age 65+ path and high-risk medical conditions.
  - Rotavirus start-window guard enforced for unstarted series.
  - Men-C-ACYW long interval (`3285` days) supports grade-6 style booster timing.
- Frontend date handling:
  - Dashboard/Profile/Schedule now parse local dates explicitly to avoid timezone day-shift issues.
  - Dashboard overdue "Next Due" display now uses current date behavior consistently.
- UI content:
  - Emoji/symbol indicators in frontend source were replaced with plain text indicators.
- Validation:
  - Current backend test suite status: `74 passed` (`cd backend && pytest -q`).
