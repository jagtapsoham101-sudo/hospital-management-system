# Fix: route arguments must match their Flask endpoint parameters

The appointments page now passes `appointment_id` to the existing `update_appointment` route and uses the dedicated `*_full` endpoints for edit/delete. Billing passes `invoice_id` to `mark_paid` and the matching `*_full` endpoints for invoice editing/deletion. Admissions uses `*_full` routes for bed/ward/admission editing and deletion, while using the base app's `admission_id` for discharge. The bed availability display uses the `beds` list supplied by the existing admissions view.

After pulling, always start the extended app so its extra CRUD routes are loaded:

```powershell
.\.venv\Scripts\python.exe -m flask --app complete_app:app run --debug
```
