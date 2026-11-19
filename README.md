# Full Indian-names demo data and editable modules

This update includes an additive sample-data initializer for fictional Indian-names demo rows across accounts, patients, doctors, appointments, invoices, wards, beds, admissions, clinical records and prescriptions. It preserves any existing database rows. Authenticated administrators can add/delete staff, wards, beds and prescriptions; the app already supports CRUD for patient/doctor profiles and add/delete/status changes for the other modules.

## Windows PowerShell

Stop the current server with Ctrl+C, then:

```powershell
cd $HOME\Documents\hospital-management-system
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app complete_app:app seed-indian-demo
.\.venv\Scripts\python.exe -m flask --app complete_app:app run --debug
```

Open <http://127.0.0.1:5000/login>.

Demo admin login: `admin` / `CarePointDemo2026!`.

The seeder is repeatable and does not delete database contents. It uses fictional names, contact details, clinical notes, invoices and admissions solely for software demos. Never put real patient information in this project; it is not approved for real hospital operations.
