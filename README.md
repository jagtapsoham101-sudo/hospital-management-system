# CarePoint Hospital Management System — local demonstration

Flask/SQLAlchemy demo with patient and doctor add/edit/delete, appointments, billing, admissions/beds, visit records, and password-protected local administrator access. Seed data uses fictional Indian names and INR-style example charges.

**Not production-ready:** do not use real patient information or clinical decisions. Real deployment requires professional healthcare security/privacy, compliance and clinical safety review, audit logging, backups, migrations, monitoring, HTTPS, and validated operations.

## Windows PowerShell

```powershell
cd $HOME\Documents\hospital-management-system
git pull origin main
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-demo
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

Open <http://127.0.0.1:5000/login>.

Demo credentials: username `admin`, password `CarePointDemo2026!`. `init-demo` creates tables and adds missing sample records while preserving existing records; it resets this local demo admin password. Keep this only on your own machine.

The database defaults to SQLite. Set `DATABASE_URL` before initializing and running to choose MySQL/PostgreSQL. Set `SECRET_KEY` to a random secret for any non-demo deployment.
