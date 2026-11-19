# CarePoint Hospital Management System

This is a complete **academic/demo** Flask + SQLAlchemy hospital-management project supporting SQLite, MySQL, and PostgreSQL. It includes staff login and roles, patients, doctors, appointments, admissions/beds, clinical records with optional prescriptions, and billing.

**Important:** this is not a production clinical system. Never enter real patient data. Production deployment requires professional security/privacy engineering, compliance review, migrations, backups, audit logging, monitoring, and clinical governance.

## Windows PowerShell

Install Python (select **Add Python to PATH**) and Git, then open a new PowerShell:

```powershell
cd $HOME\Documents
git pull origin main
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app create-admin
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

Open http://127.0.0.1:5000 and sign in with the account created by `create-admin`. For fictional sample dashboard data, run this before starting the server:

```powershell
.\.venv\Scripts\python.exe -m flask --app app seed-demo
```

The current database schema is newly expanded. For an empty local demo database, delete `instance\hospital.db` if it exists, then run `init-db` and `create-admin` again. Do not delete a database containing data you need.

## MySQL/PostgreSQL

Set `DATABASE_URL` before initialization. Examples:

```powershell
$env:DATABASE_URL='mysql+pymysql://USER:PASSWORD@localhost:3306/hospital_db?charset=utf8mb4'
# or
$env:DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/hospital_db'
$env:SECRET_KEY='use-a-long-random-secret'
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app create-admin
.\.venv\Scripts\python.exe -m flask --app app run
```

Use a URL-encoded password if it contains special URL characters. Use HTTPS and secure cookies when hosted.

## Roles

Administrator: all modules and staff management. Clinician: clinical records plus care operations. Reception: directories, appointments, and admissions. Billing: patients and invoices. Staff passwords are hashed and must be at least 12 characters.

## Pages

`/` dashboard, `/patients`, `/doctors`, `/appointments`, `/admissions`, `/records`, `/billing`, and `/staff` (administrator only).
