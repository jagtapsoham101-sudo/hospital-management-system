# CarePoint Hospital Management System

A feature-rich **academic/demo** Flask + SQLAlchemy system with relational database support for SQLite, MySQL, and PostgreSQL. It includes staff sign-in with basic roles, patient and provider directories, appointments, admissions/bed assignment, clinician-entered visit notes and prescriptions, and billing.

> **Not a production clinical system.** The app is for coursework and local demonstrations only. Do not enter real patient/health data. It has not been validated for healthcare privacy/security regulations, clinical safety, legal record retention, or production availability. Production use requires professional security/privacy engineering, independent testing, legal/compliance review, backups/disaster recovery, monitoring, and clinical governance. A logged-in screen does not by itself make a system compliant.

## Features

- Staff authentication, hashed passwords, CSRF-protected forms, session timeout, and roles (administrator, clinician, reception, billing)
- Role-based access to patient, scheduling, clinical, admissions, billing, and staff-account pages
- Patient and doctor directories, appointment scheduling and status updates
- Ward/bed setup, bed occupancy, admission, and discharge flow
- Clinical visit records and optional prescription entries
- Invoice creation and payment tracking
- SQLite by default, configurable MySQL and PostgreSQL via `DATABASE_URL`
- Fictional sample data for demonstrations only

## Windows PowerShell setup (SQLite)

Requires Python 3.10+ and Git. Install Python from <https://www.python.org/downloads/windows/> (select **Add Python to PATH**) and Git from <https://git-scm.com/download/win>. Open a new PowerShell window after installation. If the repository is already cloned, skip the clone command.

```powershell
cd $HOME\Documents
git clone https://github.com/jagtapsoham101-sudo/hospital-management-system.git
cd hospital-management-system
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app create-admin
```

The `create-admin` command prompts for a username and password. Choose a unique username and password with at least 12 characters. Start the server:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

Open <http://127.0.0.1:5000> and sign in with that admin account. Keep the terminal open while using the app. Stop with Ctrl+C. For a populated fictional dashboard, run `seed-demo` before starting the server; do not seed a database containing real records.

```powershell
.\.venv\Scripts\python.exe -m flask --app app seed-demo
```

For macOS/Linux, activate the virtual environment with `source .venv/bin/activate`, then use `python -m pip ...` and `flask --app app ...` commands.

## Database configuration

SQLite runs by default. To use MySQL or PostgreSQL, create a database/user, then set `DATABASE_URL` **before** `init-db`, `create-admin`, and server startup. Install the project's pinned database drivers via requirements.

**MySQL URL:** `mysql+pymysql://USER:PASSWORD@localhost:3306/hospital_db?charset=utf8mb4`

**PostgreSQL URL:** `postgresql+psycopg://USER:PASSWORD@localhost:5432/hospital_db`

PowerShell example (use a URL-encoded password if it contains reserved URL characters):

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://hospital_app:CHANGE_ME@localhost:5432/hospital_db'
$env:SECRET_KEY = 'replace-with-a-long-random-secret'
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app create-admin
.\.venv\Scripts\python.exe -m flask --app app run
```

Set `SECRET_KEY` to a cryptographically random secret, keep it out of source control, and use HTTPS in any hosted environment. `COOKIE_SECURE=1` enables secure-only session cookies when HTTPS is configured.

## Roles

- **Administrator:** all pages; creates/disables staff; adds wards/beds; deletes directory entries.
- **Clinician:** patients, doctors, appointments, admissions, and clinical records.
- **Reception:** patient/provider directory, appointments, and admissions.
- **Billing:** patient directory and invoices.

Create additional accounts from the admin-only **Staff accounts** page. Password minimum is 12 characters. There is intentionally no public registration route.

## Data migration note

This version uses `db.create_all()` for a quick course-project setup. It does not alter existing tables when models change. For an older installation, **back up first**, then for an empty demo database only remove the local SQLite database and rerun `init-db`, `create-admin`, and optionally `seed-demo`. For any data that must be retained, set up and apply Alembic/Flask-Migrate migrations rather than deleting the database.

## Demo data

`seed-demo` inserts four fictional patients, three fictional doctors, sample appointments/invoices, and eight general-ward beds. It skips if any patient data already exists. The demo credentials are not hard-coded; create your own admin account using the CLI.
