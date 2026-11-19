# Demo data and delete controls

This update adds an idempotent fictional sample-data script and delete buttons/routes for patients, doctors, appointments, invoices, admissions, and clinical records. Existing data is not erased by the seeder. Delete actions are POST forms protected by the app's CSRF extension.

Stop Flask with Ctrl+C, pull the latest files, then use:

```powershell
cd $HOME\Documents\hospital-management-system
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m python seed_demo.py
```

Start the site with the route-compatibility module so delete routes are registered:

```powershell
.\.venv\Scripts\python.exe -m flask --app webapp run --debug
```

Open http://127.0.0.1:5000. The sample data is fictional. It is an academic demo, not a production system and must not contain real patient data.
