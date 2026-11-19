## Fixes for duplicate Flask endpoints

The `complete_app.py` entry point now conditionally registers only routes missing from `app.py`, preventing startup errors like `View function mapping is overwriting an existing endpoint function`. Pull the latest version and use this entry point consistently:

```powershell
git pull origin main
.\.venv\Scripts\python.exe -m flask --app complete_app:app init-db
.\.venv\Scripts\python.exe -m flask --app complete_app:app seed-indian-demo
.\.venv\Scripts\python.exe -m flask --app complete_app:app run --debug
```
