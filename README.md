# QDoc — Smart Vaccine Eligibility & Reminder System

## Project Structure

```
qdoc/
├── backend/        # FastAPI + PostgreSQL
└── frontend/       # React + Vite
```

---

## Prerequisites

Make sure you have these installed:
- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (running)

---

## Step 1 — PostgreSQL Setup

Make sure PostgreSQL is running, then create the database:

```bash
psql postgres
```

```sql
CREATE DATABASE qdoc;
\q
```

---

## Step 2 — Backend Setup

```bash
cd qdoc/backend
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Configure environment
Edit the `.env` file and set your Mac username:
```
DATABASE_URL=postgresql://YOUR_MAC_USERNAME@localhost:5432/qdoc
JWT_SECRET=supersecretkey123
JWT_EXPIRE_MINUTES=60
```
> Run `whoami` in terminal to get your Mac username.

### Seed the vaccines table
```bash
python seed_vaccines.py
```
You should see:
```
Seeding complete: 15 inserted, 0 already existed.
```

### Start the backend server
```bash
uvicorn app.main:app --reload
```
Backend runs at: **http://127.0.0.1:8000**
API docs at: **http://127.0.0.1:8000/docs**

---

## Step 3 — Frontend Setup

Open a **new terminal tab**, then:

```bash
cd qdoc/frontend
```

### Install dependencies
```bash
npm install
```

### Start the frontend
```bash
npm run dev
```
Frontend runs at: **http://localhost:5173**

---

## Running the Full App

You need **two terminals open at the same time**:

| Terminal 1 (Backend) | Terminal 2 (Frontend) |
|---|---|
| `cd qdoc/backend` | `cd qdoc/frontend` |
| `uvicorn app.main:app --reload` | `npm run dev` |

Then open **http://localhost:5173** in your browser.

---

## How to Use

1. Go to `http://localhost:5173`
2. Click **Create Account** and sign up
3. You'll be redirected to **Profile Creation** — fill in your info
4. After saving, you'll land on the **Dashboard** showing your vaccine statuses
5. Click **Schedule** in the navbar to see upcoming vaccines
6. Click **Remind Me** on any overdue/due-soon vaccine to log a reminder

---

## API Endpoints Quick Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Login |
| POST | `/api/profile` | Create patient profile |
| GET | `/api/profile/me` | Get your profile |
| GET | `/api/dashboard/me` | Get vaccine statuses |
| GET | `/api/schedule/me` | Get upcoming schedule |
| POST | `/api/reminders/send` | Log a reminder |

Full interactive docs: **http://127.0.0.1:8000/docs**
