# ClearUnit — Property Management System

A web-based property management application built with Flask, SQLAlchemy, and Supabase PostgreSQL. Designed for building managers and their residents to manage units, dues, payments, maintenance requests, and announcements — all in one place.

---

## 👥 Team

| Name | Student ID | Role |
|------|-----------|------|
| Rafik Ajam | 2309116215 | Architecture, Backend, SAD |
| Amro Akel | 2309115620 | Use Cases, Resident UI, Testing |
| Hasan Altabbaa | 2309035318 | Database Design, Models, Deployment |

---

## 🚀 Features

**Manager**
- Register and manage multiple buildings and units
- Assign / unassign residents to units
- Create monthly dues for individual buildings or all buildings at once
- Confirm or reject resident payment notifications
- Post announcements to one or all buildings
- Track and update maintenance requests (pending → in progress → resolved)

**Resident**
- View assigned unit and outstanding balance
- Browse monthly dues statements
- Notify the manager of a payment
- Submit and track maintenance requests
- Read building announcements

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Web Framework | Flask + Werkzeug |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Database | PostgreSQL 15 via Supabase (AWS eu-west-1) |
| DB Migrations | Flask-Migrate (Alembic) |
| Authentication | Flask-Login (sessions) + Flask-JWT-Extended (API) |
| Password Hashing | Werkzeug Security (PBKDF2-SHA256) |
| CSRF Protection | Flask-WTF |
| Templates | Jinja2 |
| Styling | Tailwind CSS (CDN) |

---

## 📁 Project Structure

```
clearunit-manage-your-buildings/
├── run.py                          # App entry point
├── config.py                       # Config class (reads from .env)
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (not committed)
│
├── backend/
│   └── app/
│       ├── __init__.py             # App factory (registers blueprints & extensions)
│       ├── models.py               # SQLAlchemy models
│       └── routes/
│           ├── auth.py             # Register, login, logout
│           ├── manager.py          # All manager routes
│           ├── resident.py         # All resident routes
│           └── api/
│               ├── auth.py         # JWT login endpoint
│               ├── manager.py      # Manager JSON API
│               └── resident.py     # Resident JSON API
│
└── frontend/
    └── templates/
        ├── base.html               # Base layout (nav, flash messages)
        ├── auth/
        │   ├── login.html
        │   └── register.html
        ├── manager/
        │   ├── dashboard.html
        │   ├── buildings.html
        │   ├── building_detail.html
        │   ├── add_building.html
        │   ├── add_unit.html
        │   ├── dues.html
        │   ├── create_dues.html
        │   ├── payments.html
        │   ├── maintenance.html
        │   └── announcements.html
        └── resident/
            ├── dashboard.html
            ├── dues.html
            ├── payments.html
            ├── notify_payment.html
            ├── maintenance.html
            └── announcements.html
```

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/clearunit-manage-your-buildings.git
cd clearunit-manage-your-buildings
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
```

> **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 5. Run database migrations

```bash
flask db upgrade
```

### 6. Start the development server

```bash
python run.py
```

The app will be available at **http://127.0.0.1:5000**

---

## 🗄️ Database

ClearUnit uses **Supabase** (managed cloud PostgreSQL) as its database backend.

- Host: `aws-0-eu-west-1.pooler.supabase.com`
- Port: `5432` (transaction pooler)
- Connection is configured via the `DATABASE_URL` environment variable

### Models

| Model | Description |
|-------|-------------|
| `User` | Manager or Resident account |
| `Building` | Owned by a manager |
| `Unit` | Belongs to a building; optionally assigned to a resident |
| `Dues` | Monthly due amount for a unit |
| `Payment` | Resident payment notification (pending / confirmed / rejected) |
| `Announcement` | Building-level notice posted by a manager |
| `MaintenanceRequest` | Issue submitted by a resident (pending / in_progress / resolved) |

---

## 🔐 Authentication & Roles

- All routes are protected by `@login_required`
- Manager-only routes use the `manager_required` decorator
- Resident-only routes use the `resident_required` decorator
- All data queries are scoped by `manager_id` or `resident_id` — no cross-tenant access is possible
- The REST API (`/api/...`) uses JWT tokens instead of session cookies

---

## 📡 REST API (JWT)

Endpoints under `/api/` accept and return JSON and use Bearer token authentication.

```
POST   /api/auth/login          → Returns JWT access token
GET    /api/manager/buildings   → List manager's buildings
GET    /api/resident/dues       → List resident's dues
...
```

Include the token in requests:
```
Authorization: Bearer <access_token>
```

---

## 📄 Documentation

The Software Architecture Document (SAD) is included in the repository:

- `ClearUnit_SAD_v2_Phase1.docx` — Phase 1 submission (4+1 view model, UML diagrams, use cases, process workflows)

---

## 📋 Requirements

See `requirements.txt` for the full list. Key packages:

```
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
Flask-WTF
Flask-JWT-Extended
Werkzeug
psycopg2-binary
python-dotenv
```

