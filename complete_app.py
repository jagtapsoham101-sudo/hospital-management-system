"""Optional CRUD extensions for the existing Flask application.

The base app already implements several routes (including patient/doctor
editing). Register only missing endpoints to avoid Flask's duplicate endpoint
AssertionError. Run with: flask --app complete_app:app ...
"""
from datetime import date, datetime

import click
from flask import flash, g, redirect, render_template, request, url_for

from app import (ACCESS, Admission, Appointment, Bed, ClinicalRecord, Doctor,
                 Invoice, Patient, Prescription, User, Ward, app, db)

GENDERS = {'Female', 'Male', 'Non-binary', 'Prefer not to say'}
STATUSES = {'Scheduled', 'Checked in', 'Completed', 'Cancelled'}


def register_if_missing(rule, endpoint, view, methods=('POST',)):
    """Keep the base app's route if already defined; add only missing endpoints."""
    if endpoint not in app.view_functions:
        app.add_url_rule(rule, endpoint, view, methods=list(methods))


def permit_roles(endpoint, roles):
    """Add this extension endpoint to configured role allow-lists."""
    for role in roles:
        allowed = ACCESS.get(role)
        if allowed is not None:
            allowed.add(endpoint)


def edit_patient(id):
    patient = db.get_or_404(Patient, id)
    if request.method == 'POST':
        try: dob = date.fromisoformat(request.form.get('date_of_birth', ''))
        except ValueError: dob = None
        name = request.form.get('full_name', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        if not name or not phone or not dob or dob > date.today() or gender not in GENDERS:
            flash('Enter valid patient details.', 'error')
        else:
            patient.full_name, patient.date_of_birth = name, dob
            patient.gender, patient.phone = gender, phone
            patient.email = request.form.get('email', '').strip() or None
            patient.blood_group = request.form.get('blood_group', '').strip() or None
            patient.address = request.form.get('address', '').strip() or None
            db.session.commit(); flash('Patient updated.', 'success')
            return redirect(url_for('patients'))
    return render_template('edit_patient.html', patient=patient)


def edit_doctor(id):
    doctor = db.get_or_404(Doctor, id)
    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        specialty = request.form.get('specialty', '').strip()
        phone = request.form.get('phone', '').strip()
        if not name or not specialty or not phone:
            flash('Name, specialty, and phone are required.', 'error')
        else:
            doctor.full_name, doctor.specialty, doctor.phone = name, specialty, phone
            doctor.email = request.form.get('email', '').strip() or None
            doctor.room = request.form.get('room', '').strip() or None
            db.session.commit(); flash('Doctor updated.', 'success')
            return redirect(url_for('doctors'))
    return render_template('edit_doctor.html', doctor=doctor)


def edit_appointment(id):
    item = db.get_or_404(Appointment, id)
    patients = Patient.query.order_by(Patient.full_name).all()
    doctors = Doctor.query.order_by(Doctor.full_name).all()
    if request.method == 'POST':
        try:
            patient_id = int(request.form['patient_id'])
            doctor_id = int(request.form['doctor_id'])
            starts_at = datetime.fromisoformat(request.form['starts_at'])
        except (ValueError, KeyError, TypeError):
            patient_id = doctor_id = 0; starts_at = None
        reason = request.form.get('reason', '').strip()
        status = request.form.get('status', item.status)
        if (not starts_at or not reason or status not in STATUSES
                or not db.session.get(Patient, patient_id)
                or not db.session.get(Doctor, doctor_id)):
            flash('Enter valid appointment details.', 'error')
        else:
            item.patient_id, item.doctor_id = patient_id, doctor_id
            item.starts_at, item.reason, item.status = starts_at, reason, status
            db.session.commit(); flash('Appointment updated.', 'success')
            return redirect(url_for('appointments'))
    return render_template('edit_appointment.html', item=item, patients=patients,
                           doctors=doctors, statuses=sorted(STATUSES))


def edit_invoice(id):
    item = db.get_or_404(Invoice, id)
    patients = Patient.query.order_by(Patient.full_name).all()
    if request.method == 'POST':
        try:
            patient_id = int(request.form['patient_id'])
            amount = float(request.form['amount'])
        except (ValueError, KeyError, TypeError):
            patient_id, amount = 0, 0
        description = request.form.get('description', '').strip()
        status = request.form.get('status', item.status)
        if not db.session.get(Patient, patient_id) or not description or amount <= 0 or status not in {'Paid', 'Unpaid'}:
            flash('Enter valid invoice details.', 'error')
        else:
            item.patient_id, item.description, item.amount, item.status = patient_id, description, amount, status
            db.session.commit(); flash('Invoice updated.', 'success')
            return redirect(url_for('billing'))
    return render_template('edit_invoice.html', item=item, patients=patients)


def delete_patient(id):
    db.session.delete(db.get_or_404(Patient, id)); db.session.commit()
    flash('Patient and linked records deleted.', 'success'); return redirect(url_for('patients'))


def delete_doctor(id):
    db.session.delete(db.get_or_404(Doctor, id)); db.session.commit()
    flash('Doctor and linked appointments deleted.', 'success'); return redirect(url_for('doctors'))


def delete_appointment(id):
    db.session.delete(db.get_or_404(Appointment, id)); db.session.commit()
    flash('Appointment deleted.', 'success'); return redirect(url_for('appointments'))


def delete_invoice(id):
    db.session.delete(db.get_or_404(Invoice, id)); db.session.commit()
    flash('Invoice deleted.', 'success'); return redirect(url_for('billing'))


def delete_admission(id):
    db.session.delete(db.get_or_404(Admission, id)); db.session.commit()
    flash('Admission deleted.', 'success'); return redirect(url_for('admissions'))


def delete_record(id):
    db.session.delete(db.get_or_404(ClinicalRecord, id)); db.session.commit()
    flash('Clinical record deleted.', 'success'); return redirect(url_for('records'))


def delete_prescription(id):
    db.session.delete(db.get_or_404(Prescription, id)); db.session.commit()
    flash('Prescription deleted.', 'success'); return redirect(url_for('records'))


def delete_ward(id):
    ward = db.get_or_404(Ward, id)
    occupied = Admission.query.join(Bed).filter(Bed.ward_id == ward.id, Admission.status == 'Admitted').first()
    if occupied:
        flash('Discharge patients before deleting this ward.', 'error')
    else:
        db.session.delete(ward); db.session.commit(); flash('Ward and beds deleted.', 'success')
    return redirect(url_for('admissions'))


def delete_bed(id):
    bed = db.get_or_404(Bed, id)
    if Admission.query.filter_by(bed_id=bed.id, status='Admitted').first():
        flash('Discharge the patient before deleting this bed.', 'error')
    else:
        db.session.delete(bed); db.session.commit(); flash('Bed deleted.', 'success')
    return redirect(url_for('admissions'))


def delete_staff(id):
    user = db.get_or_404(User, id)
    if getattr(g, 'user', None) and g.user.id == id:
        flash('You cannot delete the account currently signed in.', 'error')
    else:
        db.session.delete(user); db.session.commit(); flash('Staff account deleted.', 'success')
    return redirect(url_for('staff'))


# Existing base endpoints are intentionally retained. This avoids endpoint
# collisions when app.py already defines patient/doctor edit or delete routes.
EXTENSIONS = [
    ('/patients/<int:id>/edit', 'edit_patient', edit_patient, ('GET', 'POST')),
    ('/doctors/<int:id>/edit', 'edit_doctor', edit_doctor, ('GET', 'POST')),
    ('/appointments/<int:id>/edit', 'edit_appointment', edit_appointment, ('GET', 'POST')),
    ('/invoices/<int:id>/edit', 'edit_invoice', edit_invoice, ('GET', 'POST')),
    ('/patients/<int:id>/delete', 'delete_patient', delete_patient, ('POST',)),
    ('/doctors/<int:id>/delete', 'delete_doctor', delete_doctor, ('POST',)),
    ('/appointments/<int:id>/delete', 'delete_appointment', delete_appointment, ('POST',)),
    ('/billing/<int:id>/delete', 'delete_invoice', delete_invoice, ('POST',)),
    ('/admissions/<int:id>/delete', 'delete_admission', delete_admission, ('POST',)),
    ('/records/<int:id>/delete', 'delete_record', delete_record, ('POST',)),
    ('/prescriptions/<int:id>/delete', 'delete_prescription', delete_prescription, ('POST',)),
    ('/wards/<int:id>/delete', 'delete_ward', delete_ward, ('POST',)),
    ('/beds/<int:id>/delete', 'delete_bed', delete_bed, ('POST',)),
    ('/staff/<int:id>/delete', 'delete_staff', delete_staff, ('POST',)),
]
for rule, endpoint, view, methods in EXTENSIONS:
    register_if_missing(rule, endpoint, view, methods)

# Give extension routes the same permissions as their corresponding sections.
for endpoint in ('edit_patient', 'delete_patient'):
    permit_roles(endpoint, {'clinician', 'reception', 'billing'})
for endpoint in ('edit_doctor', 'delete_doctor'):
    permit_roles(endpoint, {'clinician', 'reception'})
for endpoint in ('edit_appointment', 'delete_appointment', 'delete_admission'):
    permit_roles(endpoint, {'clinician', 'reception'})
for endpoint in ('edit_invoice', 'delete_invoice'):
    permit_roles(endpoint, {'billing'})
for endpoint in ('delete_record', 'delete_prescription'):
    permit_roles(endpoint, {'clinician'})

# Register the extra seeder only when the base app has not already registered it.
if 'seed-indian-demo' not in app.cli.commands:
    @click.command('seed-indian-demo')
    def seed_indian_demo_command():
        from seed_indian_demo import seed
        seed()
        click.echo('Fictional Indian demo data is ready.')
    app.cli.add_command(seed_indian_demo_command)
