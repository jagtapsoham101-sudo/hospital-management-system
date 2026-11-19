"""Register safe demo CRUD delete routes on the existing Flask app.

Run the website with `flask --app webapp run --debug` so these routes load.
"""
from app import Admission, Appointment, ClinicalRecord, Doctor, Invoice, Patient, app, db
from flask import flash, redirect, url_for


def delete_row(model, record_id, message):
    row = db.get_or_404(model, record_id)
    db.session.delete(row)
    db.session.commit()
    flash(message, 'success')


def delete_patient(patient_id):
    delete_row(Patient, patient_id, 'Patient and linked records deleted.')
    return redirect(url_for('patients'))


def delete_doctor(doctor_id):
    delete_row(Doctor, doctor_id, 'Doctor and linked appointments deleted.')
    return redirect(url_for('doctors'))


def delete_appointment(appointment_id):
    delete_row(Appointment, appointment_id, 'Appointment deleted.')
    return redirect(url_for('appointments'))


def delete_invoice(invoice_id):
    delete_row(Invoice, invoice_id, 'Invoice deleted.')
    return redirect(url_for('billing'))


def delete_admission(admission_id):
    delete_row(Admission, admission_id, 'Admission record deleted.')
    return redirect(url_for('admissions'))


def delete_record(record_id):
    delete_row(ClinicalRecord, record_id, 'Clinical record and prescriptions deleted.')
    return redirect(url_for('records'))


app.add_url_rule('/patients/<int:patient_id>/delete', 'delete_patient', delete_patient, methods=['POST'])
app.add_url_rule('/doctors/<int:doctor_id>/delete', 'delete_doctor', delete_doctor, methods=['POST'])
app.add_url_rule('/appointments/<int:appointment_id>/delete', 'delete_appointment', delete_appointment, methods=['POST'])
app.add_url_rule('/billing/<int:invoice_id>/delete', 'delete_invoice', delete_invoice, methods=['POST'])
app.add_url_rule('/admissions/<int:admission_id>/delete', 'delete_admission', delete_admission, methods=['POST'])
app.add_url_rule('/records/<int:record_id>/delete', 'delete_record', delete_record, methods=['POST'])
