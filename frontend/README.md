# Frontend

React + Vite client for profile input, dashboard, schedule, reminders UI, and QDoc-themed styling.

## Structure

```text
frontend/
├── public/                   # Static assets (favicon/logo)
├── src/
│   ├── api/                  # Axios API client wrappers
│   ├── assets/               # App images/logos
│   ├── components/           # Shared UI components
│   ├── pages/                # Route-level pages
│   ├── App.jsx               # Route config
│   ├── main.jsx              # App bootstrap
│   └── index.css             # Global tokens/base styles
├── index.html
├── package.json
└── vite.config.js
```

## Run

```bash
cd frontend
npm install
npm run dev
```

## Build

```bash
cd frontend
npm run build
```

