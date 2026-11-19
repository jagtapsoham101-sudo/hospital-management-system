"""Repository entry point that registers all CRUD routes and demo data.

Run with:
  python -m flask --app complete_app:app run --debug
"""
from datetime import date, datetime

from flask import flash, g, redirect, render_template, request, url_for

from app import (Admission, Appointment, Bed, ClinicalRecord, Doctor, Invoice,
                 Patient, Prescription, User, Ward, app, db)


GENDERS = ['Female', 'Male', 'Non-binary', 'Prefer not to say']
STATUSES = ['Scheduled', 'Checked in', 'Completed', 'Cancelled']


@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
def edit_patient(id):
    patient = db.get_or_404(Patient, id)
    if request.method == 'POST':
        try:
            dob = date.fromisoformat(request.form.get('date_of_birth', ''))
        except ValueError:
            dob = None
        name = request.form.get('full_name', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        if not name or not phone or dob is None or dob > date.today() or gender not in GENDERS:
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


@app.route('/doctors/<int:id>/edit', methods=['GET', 'POST'])
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


@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
def edit_appointment(id):
    item = db.get_or_404(Appointment, id)
    if request.method == 'POST':
        try:
            patient_id = int(request.form['patient_id'])
            doctor_id = int(request.form['doctor_id'])
            starts_at = datetime.fromisoformat(request.form['starts_at'])
        except (ValueError, KeyError, TypeError):
            patient_id = doctor_id = 0
            starts_at = None
        reason = request.form.get('reason', '').strip()
        if not starts_at or not reason or not db.session.get(Patient, patient_id) or not db.session.get(Doctor, doctor_id):
            flash('Enter valid appointment details.', 'error')
        else:
            item.patient_id, item.doctor_id = patient_id, doctor_id
            item.starts_at, item.reason = starts_at, reason
            item.status = request.form.get('status', item.status)
            db.session.commit(); flash('Appointment updated.', 'success')
            return redirect(url_for('appointments'))
    return render_template('edit_appointment.html', item=item,
                           patients=Patient.query.order_by(Patient.full_name).all(),
                           doctors=Doctor.query.order_by(Doctor.full_name).all(), statuses=STATUSES)


@app.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
def edit_invoice(id):
    item = db.get_or_404(Invoice, id)
    if request.method == 'POST':
        try:
            patient_id = int(request.form['patient_id'])
            amount = float(request.form['amount'])
        except (ValueError, KeyError, TypeError):
            patient_id = 0
            amount = 0
        description = request.form.get('description', '').strip()
        if not db.session.get(Patient, patient_id) or not description or amount <= 0:
            flash('Enter valid invoice details.', 'error')
        else:
            item.patient_id, item.description = patient_id, description
            item.amount = amount
            item.status = request.form.get('status', item.status)
            db.session.commit(); flash('Invoice updated.', 'success')
            return redirect(url_for('billing'))
    return render_template('edit_invoice.html', item=item,
                           patients=Patient.query.order_by(Patient.full_name).all())


@app.post('/patients/<int:id>/delete')
def delete_patient(id):
    db.session.delete(db.get_or_404(Patient, id)); db.session.commit()
    flash('Patient and linked records deleted.', 'success')
    return redirect(url_for('patients'))


@app.post('/doctors/<int:id>/delete')
def delete_doctor(id):
    db.session.delete(db.get_or_404(Doctor, id)); db.session.commit()
    flash('Doctor and linked appointments deleted.', 'success')
    return redirect(url_for('doctors'))


@app.post('/appointments/<int:id>/delete')
def delete_appointment(id):
    db.session.delete(db.get_or_404(Appointment, id)); db.session.commit()
    flash('Appointment deleted.', 'success')
    return redirect(url_for('appointments'))


@app.post('/billing/<int:id>/delete')
def delete_invoice(id):
    db.session.delete(db.get_or_404(Invoice, id)); db.session.commit()
    flash('Invoice deleted.', 'success')
    return redirect(url_for('billing'))


@app.post('/admissions/<int:id>/delete')
def delete_admission(id):
    db.session.delete(db.get_or_404(Admission, id)); db.session.commit()
    flash('Admission deleted.', 'success')
    return redirect(url_for('admissions'))


@app.post('/records/<int:id>/delete')
def delete_record(id):
    db.session.delete(db.get_or_404(ClinicalRecord, id)); db.session.commit()
    flash('Clinical record deleted.', 'success')
    return redirect(url_for('records'))


@app.post('/prescriptions/<int:id>/delete')
def delete_prescription(id):
    db.session.delete(db.get_or_404(Prescription, id)); db.session.commit()
    flash('Prescription deleted.', 'success')
    return redirect(url_for('records'))


@app.post('/wards/<int:id>/delete')
def delete_ward(id):
    ward = db.get_or_404(Ward, id)
    occupied = Admission.query.join(Bed).filter(Bed.ward_id == ward.id, Admission.status == 'Admitted').first()
    if occupied:
        flash('Discharge patients before deleting this ward.', 'error')
    else:
        db.session.delete(ward); db.session.commit(); flash('Ward and beds deleted.', 'success')
    return redirect(url_for('admissions'))


@app.post('/beds/<int:id>/delete')
def delete_bed(id):
    bed = db.get_or_404(Bed, id)
    if Admission.query.filter_by(bed_id=bed.id, status='Admitted').first():
        flash('Discharge the patient before deleting this bed.', 'error')
    else:
        db.session.delete(bed); db.session.commit(); flash('Bed deleted.', 'success')
    return redirect(url_for('admissions'))


@app.post('/staff/<int:id>/delete')
def delete_staff(id):
    if g.user.id == id:
        flash('You cannot delete the account currently signed in.', 'error')
    else:
        db.session.delete(db.get_or_404(User, id)); db.session.commit()
        flash('Staff account deleted.', 'success')
    return redirect(url_for('staff'))


@app.cli.command('seed-indian-demo')
def seed_indian_demo():
    """Add fictional Indian demo rows only; never remove existing records."""
    import click
    from seed_indian_demo import seed
    seed()
    click.echo('Fictional Indian demo data is ready.')
