# Hospital management system

A responsive hospital operations demo built with Flask, SQLAlchemy, and Bootstrap. It supports **SQLite out of the box**, plus **MySQL and PostgreSQL** through a single `DATABASE_URL` setting.

> Demo project only. The included sample records are fictional. Do not use this starter app for real patient data or production healthcare workflows without a security, privacy, compliance, backup, access-control, and clinical-safety review.

## Features

- Dashboard metrics and recent appointments
- Patient registration, search, and deletion
- Doctor directory and registration
- Appointment scheduling and status updates
- Invoice creation and payment status tracking
- CSRF protection on forms
- SQLAlchemy models and database portability across SQLite, MySQL, and PostgreSQL
- Fictional sample data for a populated first-run dashboard

## Run locally (SQLite — quickest)

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app init-db
flask --app app seed-demo
flask --app app run --debug
```

Open <http://127.0.0.1:5000>. To start with an empty database, skip `seed-demo`.

## MySQL

Create a database and a dedicated account, then set the connection URL before running the database commands:

```sql
CREATE DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hospital_app'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON hospital_db.* TO 'hospital_app'@'localhost';
```

```bash
# Linux/macOS shell example (quote the URL if the password has special characters)
export DATABASE_URL='mysql+pymysql://hospital_app:replace-with-a-strong-password@localhost:3306/hospital_db?charset=utf8mb4'
flask --app app init-db
flask --app app seed-demo
flask --app app run --debug
```

## PostgreSQL

Create a database and account, and configure the URL using the psycopg 3 driver:

```sql
CREATE USER hospital_app WITH PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE hospital_db OWNER hospital_app;
```

```bash
export DATABASE_URL='postgresql+psycopg://hospital_app:replace-with-a-strong-password@localhost:5432/hospital_db'
flask --app app init-db
flask --app app seed-demo
flask --app app run --debug
```

For Windows PowerShell, use `$env:DATABASE_URL='...'` in place of `export`. Set `SECRET_KEY` to a long random secret in any deployed environment. Never commit secrets.

## Pages

- `/` — Dashboard
- `/patients` — Patient list, search, and registration
- `/doctors` — Doctor directory and registration
- `/appointments` — Scheduling and status management
- `/billing` — Invoices and payment status

## Database notes

`flask --app app init-db` creates tables for the selected database. This starter uses `create_all()` for convenience; use a migration tool such as Flask-Migrate/Alembic for schema changes in a maintained deployment. To reset the local SQLite demo, stop the server and remove `instance/hospital.db`, then rerun the commands.

## Demo output

After `seed-demo`, the dashboard shows 4 fictional patients, 3 doctors, upcoming/recent appointments, and an unpaid balance of $420.00. The interface is responsive and uses a dark-blue sidebar with teal highlights.
