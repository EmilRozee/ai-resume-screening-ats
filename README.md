# ATS Resume Screening System

A Flask-based Applicant Tracking System (ATS) backend with a modern, role-based frontend for Admin and Candidate workflows.

## Release Highlights

- JWT authentication with role-based access (`admin`, `candidate`)
- Separate Admin and Candidate views in the UI
- Job creation and listing flows
- Candidate job applications with PDF resume upload
- Resume text extraction and basic skill-match scoring
- SQLite persistence with simple local setup

## Product Preview

> Add your screenshots into `docs/screenshots/` using the exact names below for automatic rendering on GitHub.

### Admin View

![Admin Dashboard](docs/screenshots/admin-dashboard.png)

### Candidate View

![Candidate Dashboard](docs/screenshots/candidate-dashboard.png)

### Job List and Apply Flow

![Job Apply Flow](docs/screenshots/job-apply-flow.png)

## Project Structure

```text
ats/
├─ app.py
├─ instance/
│  └─ database.db
├─ resumes/
├─ static/
│  ├─ app.js
│  └─ style.css
├─ templates/
│  └─ index.html
└─ docs/
   └─ screenshots/
```

## Tech Stack

- Backend: Flask, Flask-SQLAlchemy, Flask-Login
- Auth: PyJWT, Werkzeug password hashing
- Resume Parsing: pdfminer.six
- Database: SQLite
- Frontend: Vanilla HTML/CSS/JavaScript served via Flask templates

## Quick Start

### 1) Clone and enter project

```bash
git clone https://github.com/EmilRozee/ai-resume-screening-ats.git
cd ai-resume-screening-ats
```

### 2) Create virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3) Install dependencies

```bash
pip install flask flask-sqlalchemy flask-login pyjwt pdfminer.six
```

### 4) Run the app

```bash
python app.py
```

App URLs:

- API health: `http://127.0.0.1:5000/`
- Frontend UI: `http://127.0.0.1:5000/ui`

## Core User Flows

### Admin Flow

1. Register/Login as `admin`
2. Create jobs with title, description, and required skills
3. View all applications
4. Review scored candidates per job
5. Shortlist candidates

### Candidate Flow

1. Register/Login as `candidate`
2. Browse jobs
3. Select a job ID
4. Upload resume PDF and apply

## API Overview

### Public

- `POST /register` - Register user
- `POST /login` - Login and receive JWT
- `GET /` - Health message
- `GET /ui` - Frontend page

### Protected (JWT required)

- `GET /profile`
- `GET /jobs`
- `POST /apply-job/<job_id>`
- `POST /upload-resume`

### Admin-only (JWT + admin role)

- `GET /admin-dashboard`
- `POST /create-job`
- `GET /applications`
- `GET /job-applications/<job_id>`
- `POST /shortlist/<application_id>`

## Configuration Notes

Current configuration is inside `app.py`:

- `SECRET_KEY` is hardcoded for local development
- SQLite DB URI is configured as `sqlite:///database.db`
- Flask debug mode is enabled

For production, move secrets to environment variables and run behind a production WSGI server.

## Known Limitations

- Basic keyword matching for skills (not semantic NLP)
- No pagination/filtering for large datasets
- Local file storage for resumes
- No refresh-token mechanism
