"""Complete CRUD routes layered onto app.py without endpoint collisions.

Use: python -m flask --app complete_app:app ...
All demo records must be fictional. Existing app routes and database schema remain.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import click
from flask import flash, g, redirect, render_template, request, url_for

from app import (Admission, Appointment, Bed, ClinicalRecord, Doctor, Invoice,
                 Patient, Prescription, User, Ward, app, db)

GENDERS = {'Female', 'Male', 'Non-binary', 'Prefer not to say'}
APPOINTMENT_STATUSES = {'Scheduled', 'Checked in', 'Completed', 'Cancelled'}
ADMISSION_STATUSES = {'Admitted', 'Discharged'}
INVOICE_STATUSES = {'Paid', 'Unpaid'}
ROLES = {'admin', 'clinician', 'reception', 'billing'}


def admin_required():
    if not getattr(g, 'user', None) or g.user.role != 'admin':
        flash('Administrator access is required for staff management.', 'error')
        return False
    return True


def add(rule, endpoint, view, methods=('GET', 'POST')):
    # Unique endpoint names prevent collisions with the existing app.py routes.
    app.add_url_rule(rule, endpoint, view, methods=list(methods))


def parse_int(value):
    try: return int(value)
    except (ValueError, TypeError): return None


# Patients and doctors

def patient_edit(id):
    item = db.get_or_404(Patient, id)
    if request.method == 'POST':
        try: dob = date.fromisoformat(request.form.get('date_of_birth', ''))
        except ValueError: dob = None
        name, phone = request.form.get('full_name', '').strip(), request.form.get('phone', '').strip()
        gender = request.form.get('gender', '').strip()
        if not name or not phone or not dob or dob > date.today() or gender not in GENDERS:
            flash('Enter valid patient details.', 'error')
        else:
            item.full_name, item.date_of_birth, item.gender, item.phone = name, dob, gender, phone
            item.email = request.form.get('email', '').strip() or None
            item.blood_group = request.form.get('blood_group', '').strip() or None
            item.address = request.form.get('address', '').strip() or None
            db.session.commit(); flash('Patient updated.', 'success'); return redirect(url_for('patients'))
    return render_template('edit_patient.html', patient=item)


def doctor_edit(id):
    item = db.get_or_404(Doctor, id)
    if request.method == 'POST':
        name, specialty, phone = (request.form.get(k, '').strip() for k in ('full_name', 'specialty', 'phone'))
        if not name or not specialty or not phone: flash('Name, specialty and phone are required.', 'error')
        else:
            item.full_name, item.specialty, item.phone = name, specialty, phone
            item.email = request.form.get('email', '').strip() or None
            item.room = request.form.get('room', '').strip() or None
            db.session.commit(); flash('Doctor updated.', 'success'); return redirect(url_for('doctors'))
    return render_template('edit_doctor.html', doctor=item)


def patient_delete(id):
    db.session.delete(db.get_or_404(Patient, id)); db.session.commit()
    flash('Patient and linked records deleted.', 'success'); return redirect(url_for('patients'))


def doctor_delete(id):
    item = db.get_or_404(Doctor, id)
    if ClinicalRecord.query.filter_by(doctor_id=item.id).first():
        flash('Cannot delete a doctor with clinical records. Reassign or remove the records first.', 'error')
    else:
        db.session.delete(item); db.session.commit(); flash('Doctor and linked appointments deleted.', 'success')
    return redirect(url_for('doctors'))


# Appointments and invoices

def appointment_edit(id):
    item = db.get_or_404(Appointment, id)
    patients, doctors = Patient.query.order_by(Patient.full_name).all(), Doctor.query.order_by(Doctor.full_name).all()
    if request.method == 'POST':
        pid, did = parse_int(request.form.get('patient_id')), parse_int(request.form.get('doctor_id'))
        try: starts = datetime.fromisoformat(request.form.get('starts_at', ''))
        except ValueError: starts = None
        reason, status = request.form.get('reason', '').strip(), request.form.get('status', '')
        if not pid or not did or not db.session.get(Patient, pid) or not db.session.get(Doctor, did) or not starts or not reason or status not in APPOINTMENT_STATUSES:
            flash('Enter valid appointment details.', 'error')
        else:
            item.patient_id, item.doctor_id, item.starts_at = pid, did, starts
            item.reason, item.status = reason, status
            db.session.commit(); flash('Appointment updated.', 'success'); return redirect(url_for('appointments'))
    return render_template('edit_appointment.html', item=item, patients=patients, doctors=doctors, statuses=sorted(APPOINTMENT_STATUSES))


def appointment_delete(id):
    db.session.delete(db.get_or_404(Appointment, id)); db.session.commit()
    flash('Appointment deleted.', 'success'); return redirect(url_for('appointments'))


def invoice_edit(id):
    item = db.get_or_404(Invoice, id)
    patients = Patient.query.order_by(Patient.full_name).all()
    if request.method == 'POST':
        pid = parse_int(request.form.get('patient_id'))
        try: amount = Decimal(request.form.get('amount', ''))
        except (InvalidOperation, ValueError): amount = Decimal('0')
        description, status = request.form.get('description', '').strip(), request.form.get('status', '')
        if not pid or not db.session.get(Patient, pid) or not description or not amount.is_finite() or amount <= 0 or status not in INVOICE_STATUSES:
            flash('Enter valid invoice details.', 'error')
        else:
            item.patient_id, item.description, item.amount, item.status = pid, description, amount, status
            db.session.commit(); flash('Invoice updated.', 'success'); return redirect(url_for('billing'))
    return render_template('edit_invoice.html', item=item, patients=patients)


def invoice_delete(id):
    db.session.delete(db.get_or_404(Invoice, id)); db.session.commit()
    flash('Invoice deleted.', 'success'); return redirect(url_for('billing'))


# Ward and bed inventory

def ward_edit(id):
    item = db.get_or_404(Ward, id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name: flash('Ward name is required.', 'error')
        else:
            item.name = name; db.session.commit(); flash('Ward updated.', 'success')
            return redirect(url_for('admissions'))
    return render_template('edit_ward.html', item=item)


def ward_delete(id):
    item = db.get_or_404(Ward, id)
    if any(Admission.query.filter_by(bed_id=bed.id, status='Admitted').first() for bed in item.beds):
        flash('Discharge patients before deleting this ward.', 'error')
    else:
        db.session.delete(item); db.session.commit(); flash('Ward and its beds deleted.', 'success')
    return redirect(url_for('admissions'))


def bed_edit(id):
    item = db.get_or_404(Bed, id)
    wards = Ward.query.order_by(Ward.name).all()
    if request.method == 'POST':
        ward_id = parse_int(request.form.get('ward_id'))
        number, kind = request.form.get('bed_number', '').strip(), request.form.get('bed_type', '').strip()
        if not ward_id or not db.session.get(Ward, ward_id) or not number or not kind:
            flash('Enter valid bed details.', 'error')
        else:
            item.ward_id, item.bed_number, item.bed_type = ward_id, number, kind
            try: db.session.commit(); flash('Bed updated.', 'success'); return redirect(url_for('admissions'))
            except Exception: db.session.rollback(); flash('That bed number already exists in this ward.', 'error')
    return render_template('edit_bed.html', item=item, wards=wards)


def bed_delete(id):
    item = db.get_or_404(Bed, id)
    if Admission.query.filter_by(bed_id=item.id, status='Admitted').first():
        flash('Discharge the patient before deleting this bed.', 'error')
    else:
        db.session.delete(item); db.session.commit(); flash('Bed deleted.', 'success')
    return redirect(url_for('admissions'))


# Admissions

def admission_edit(id):
    item = db.get_or_404(Admission, id)
    patients, beds = Patient.query.order_by(Patient.full_name).all(), Bed.query.order_by(Bed.ward_id, Bed.bed_number).all()
    if request.method == 'POST':
        pid, bid = parse_int(request.form.get('patient_id')), parse_int(request.form.get('bed_id'))
        reason, status = request.form.get('reason', '').strip(), request.form.get('status', '')
        occupied = Admission.query.filter(Admission.bed_id == bid, Admission.status == 'Admitted', Admission.id != item.id).first() if bid else None
        if not pid or not bid or not db.session.get(Patient, pid) or not db.session.get(Bed, bid) or not reason or status not in ADMISSION_STATUSES or (status == 'Admitted' and occupied):
            flash('Select a valid patient and available bed, and enter a reason/status.', 'error')
        else:
            item.patient_id, item.bed_id, item.reason, item.status = pid, bid, reason, status
            item.discharged_at = datetime.utcnow() if status == 'Discharged' else None
            db.session.commit(); flash('Admission updated.', 'success'); return redirect(url_for('admissions'))
    return render_template('edit_admission.html', item=item, patients=patients, beds=beds, statuses=sorted(ADMISSION_STATUSES))


def admission_delete(id):
    db.session.delete(db.get_or_404(Admission, id)); db.session.commit()
    flash('Admission deleted.', 'success'); return redirect(url_for('admissions'))


# Clinical record and prescription editing

def record_edit(id):
    item = db.get_or_404(ClinicalRecord, id)
    patients, doctors = Patient.query.order_by(Patient.full_name).all(), Doctor.query.order_by(Doctor.full_name).all()
    if request.method == 'POST':
        pid, did = parse_int(request.form.get('patient_id')), parse_int(request.form.get('doctor_id'))
        diagnosis, notes = request.form.get('diagnosis', '').strip(), request.form.get('notes', '').strip()
        record_type = request.form.get('record_type', 'Consultation').strip() or 'Consultation'
        if not pid or not did or not db.session.get(Patient, pid) or not db.session.get(Doctor, did) or not diagnosis or not notes:
            flash('Complete all required clinical record fields.', 'error')
        else:
            item.patient_id, item.doctor_id = pid, did
            item.diagnosis, item.notes, item.record_type = diagnosis, notes, record_type
            db.session.commit(); flash('Clinical record updated.', 'success'); return redirect(url_for('records'))
    return render_template('edit_record.html', item=item, patients=patients, doctors=doctors)


def record_delete(id):
    db.session.delete(db.get_or_404(ClinicalRecord, id)); db.session.commit()
    flash('Clinical record and prescriptions deleted.', 'success'); return redirect(url_for('records'))


def prescription_edit(id):
    item = db.get_or_404(Prescription, id)
    if request.method == 'POST':
        med, dosage, instructions = (request.form.get(k, '').strip() for k in ('medication', 'dosage', 'instructions'))
        if not med or not dosage or not instructions: flash('Complete all prescription fields.', 'error')
        else:
            item.medication, item.dosage, item.instructions = med, dosage, instructions
            db.session.commit(); flash('Prescription updated.', 'success'); return redirect(url_for('records'))
    return render_template('edit_prescription.html', item=item)


def prescription_delete(id):
    db.session.delete(db.get_or_404(Prescription, id)); db.session.commit()
    flash('Prescription deleted.', 'success'); return redirect(url_for('records'))


# Staff accounts

def staff_add():
    if not admin_required(): return redirect(url_for('staff'))
    username, password = request.form.get('username', '').strip().lower(), request.form.get('password', '')
    role = request.form.get('role', '')
    if len(username) < 3 or len(password) < 12 or role not in ROLES:
        flash('Use a username of at least 3 characters, password of 12+ characters, and a valid role.', 'error')
    elif User.query.filter_by(username=username).first(): flash('Username already exists.', 'error')
    else:
        user = User(username=username, role=role, active=True); user.set_password(password)
        db.session.add(user); db.session.commit(); flash('Staff account added.', 'success')
    return redirect(url_for('staff'))


def staff_edit(id):
    if not admin_required(): return redirect(url_for('staff'))
    item = db.get_or_404(User, id)
    if request.method == 'POST':
        role, active = request.form.get('role', ''), request.form.get('active') == 'true'
        password = request.form.get('password', '')
        if role not in ROLES or (password and len(password) < 12): flash('Choose a valid role and a password of 12+ characters.', 'error')
        elif item.id == g.user.id and not active: flash('You cannot disable your own signed-in account.', 'error')
        else:
            item.role, item.active = role, active
            if password: item.set_password(password)
            db.session.commit(); flash('Staff account updated.', 'success'); return redirect(url_for('staff'))
    return render_template('edit_staff.html', item=item)


def staff_delete(id):
    if not admin_required(): return redirect(url_for('staff'))
    item = db.get_or_404(User, id)
    if item.id == g.user.id: flash('You cannot delete your signed-in account.', 'error')
    else: db.session.delete(item); db.session.commit(); flash('Staff account deleted.', 'success')
    return redirect(url_for('staff'))


ROUTES = [
    ('/patients/<int:id>/edit', 'edit_patient_full', patient_edit, ('GET', 'POST')),
    ('/patients/<int:id>/delete', 'delete_patient_full', patient_delete, ('POST',)),
    ('/doctors/<int:id>/edit', 'edit_doctor_full', doctor_edit, ('GET', 'POST')),
    ('/doctors/<int:id>/delete', 'delete_doctor_full', doctor_delete, ('POST',)),
    ('/appointments/<int:id>/edit', 'edit_appointment_full', appointment_edit, ('GET', 'POST')),
    ('/appointments/<int:id>/delete', 'delete_appointment_full', appointment_delete, ('POST',)),
    ('/billing/<int:id>/edit', 'edit_invoice_full', invoice_edit, ('GET', 'POST')),
    ('/billing/<int:id>/delete', 'delete_invoice_full', invoice_delete, ('POST',)),
    ('/wards/<int:id>/edit', 'edit_ward_full', ward_edit, ('GET', 'POST')),
    ('/wards/<int:id>/delete', 'delete_ward_full', ward_delete, ('POST',)),
    ('/beds/<int:id>/edit', 'edit_bed_full', bed_edit, ('GET', 'POST')),
    ('/beds/<int:id>/delete', 'delete_bed_full', bed_delete, ('POST',)),
    ('/admissions/<int:id>/edit', 'edit_admission_full', admission_edit, ('GET', 'POST')),
    ('/admissions/<int:id>/delete', 'delete_admission_full', admission_delete, ('POST',)),
    ('/records/<int:id>/edit', 'edit_record_full', record_edit, ('GET', 'POST')),
    ('/records/<int:id>/delete', 'delete_record_full', record_delete, ('POST',)),
    ('/prescriptions/<int:id>/edit', 'edit_prescription_full', prescription_edit, ('GET', 'POST')),
    ('/prescriptions/<int:id>/delete', 'delete_prescription_full', prescription_delete, ('POST',)),
    ('/staff/add', 'add_staff_full', staff_add, ('POST',)),
    ('/staff/<int:id>/edit', 'edit_staff_full', staff_edit, ('GET', 'POST')),
    ('/staff/<int:id>/delete', 'delete_staff_full', staff_delete, ('POST',)),
]
for rule, endpoint, view, methods in ROUTES:
    add(rule, endpoint, view, methods)


if 'seed-indian-demo' not in app.cli.commands:
    @click.command('seed-indian-demo')
    def seed_indian_demo_command():
        from seed_indian_demo import seed
        seed()
        click.echo('Fictional Indian demo data is ready.')
    app.cli.add_command(seed_indian_demo_command)
