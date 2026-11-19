# CarePoint ready-to-run demo

Use this repository through the consistent CRUD entry point:

```powershell
cd $HOME\Documents\hospital-management-system
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app complete_app:app init-db
.\.venv\Scripts\python.exe -m flask --app complete_app:app seed-indian-demo
.\.venv\Scripts\python.exe -m flask --app complete_app:app run --debug
```

Open http://127.0.0.1:5000/login.

All routes use the same `<int:id>` parameter convention. Patients and doctors have edit pages and delete actions. Appointments and invoices have edit, delete, status/payment actions. Admissions, beds, wards, staff, clinical records and prescriptions have delete controls registered by `complete_app.py`.

Login credentials are created or reset by `init-demo` or `seed-indian-demo` depending on repository setup. Use fictional data only: this is an academic demo, not a production clinical system.
