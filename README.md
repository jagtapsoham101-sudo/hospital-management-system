# CarePoint CRUD demo

Run in PowerShell:

```powershell
cd $HOME\Documents\hospital-management-system
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app complete_app:app init-db
.\.venv\Scripts\python.exe -m flask --app complete_app:app seed-indian-demo
.\.venv\Scripts\python.exe -m flask --app complete_app:app run --debug
```

Open http://127.0.0.1:5000/login. Use the existing demo administrator credentials established by `init-demo`.

All sections have connected create/list/edit/delete workflows: patients, doctors, appointments, invoices, admissions, wards/beds, staff accounts, clinical records and prescriptions. Changes preserve the existing database schema and seeded data. Staff account changes require admin login. Demo records must remain fictional; this application is not for real patient data or clinical operations.
