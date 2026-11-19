import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

import click
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError


db = SQLAlchemy()
csrf = CSRFProtect()


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(30), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(160))
    blood_group = db.Column(db.String(5))
    address = db.Column(db.String(240))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    appointments = db.relationship('Appointment', back_populates='patient', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='patient', cascade='all, delete-orphan')


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False, index=True)
    specialty = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(160))
    room = db.Column(db.String(30))
    appointments = db.relationship('Appointment', back_populates='doctor', cascade='all, delete-orphan')


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False, index=True)
    reason = db.Column(db.String(240), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unpaid')
    issued_on = db.Column(db.Date, nullable=False, default=date.today)
    patient = db.relationship('Patient', back_populates='invoices')


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'local-development-key-change-me'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///hospital.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    csrf.init_app(app)

    @app.get('/')
    def dashboard():
        today = date.today()
        start = datetime.combine(today, time.min)
        end = start + timedelta(days=1)
        stats = {
            'patients': Patient.query.count(),
            'doctors': Doctor.query.count(),
            'today': Appointment.query.filter(Appointment.starts_at >= start, Appointment.starts_at < end).count(),
            'unpaid': db.session.query(func.coalesce(func.sum(Invoice.amount), 0)).filter_by(status='Unpaid').scalar(),
        }
        appointments = Appointment.query.order_by(Appointment.starts_at.desc()).limit(6).all()
        return render_template('dashboard.html', stats=stats, appointments=appointments)

    @app.get('/patients')
    def patients():
        search = request.args.get('q', '').strip()
        query = Patient.query
        if search:
            query = query.filter(Patient.full_name.ilike(f'%{search}%'))
        return render_template('patients.html', patients=query.order_by(Patient.full_name).all(), search=search)

    @app.post('/patients/add')
    def add_patient():
        name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = parse_date(request.form.get('date_of_birth', ''))
        gender = request.form.get('gender', '').strip()
        if not name or not phone or not dob or gender not in {'Female', 'Male', 'Non-binary', 'Prefer not to say'}:
            flash('Enter a name, valid date of birth, phone number, and gender.', 'error')
            return redirect(url_for('patients'))
        patient = Patient(full_name=name, phone=phone, date_of_birth=dob, gender=gender,
                          email=request.form.get('email', '').strip() or None,
                          blood_group=request.form.get('blood_group', '').strip() or None,
                          address=request.form.get('address', '').strip() or None)
        db.session.add(patient)
        db.session.commit()
        flash(f'{patient.full_name} was registered.', 'success')
        return redirect(url_for('patients'))

    @app.post('/patients/<int:patient_id>/delete')
    def delete_patient(patient_id):
        patient = db.get_or_404(Patient, patient_id)
        db.session.delete(patient)
        db.session.commit()
        flash('Patient and linked records were deleted.', 'success')
        return redirect(url_for('patients'))

    @app.get('/doctors')
    def doctors():
        return render_template('doctors.html', doctors=Doctor.query.order_by(Doctor.full_name).all())

    @app.post('/doctors/add')
    def add_doctor():
        name = request.form.get('full_name', '').strip()
        specialty = request.form.get('specialty', '').strip()
        phone = request.form.get('phone', '').strip()
        if not name or not specialty or not phone:
            flash('Name, specialty, and phone are required.', 'error')
            return redirect(url_for('doctors'))
        doctor = Doctor(full_name=name, specialty=specialty, phone=phone,
                        email=request.form.get('email', '').strip() or None,
                        room=request.form.get('room', '').strip() or None)
        db.session.add(doctor)
        db.session.commit()
        flash(f'Dr. {doctor.full_name} was added.', 'success')
        return redirect(url_for('doctors'))

    @app.post('/doctors/<int:doctor_id>/delete')
    def delete_doctor(doctor_id):
        doctor = db.get_or_404(Doctor, doctor_id)
        db.session.delete(doctor)
        db.session.commit()
        flash('Doctor and linked appointments were deleted.', 'success')
        return redirect(url_for('doctors'))

    @app.get('/appointments')
    def appointments():
        items = Appointment.query.order_by(Appointment.starts_at.desc()).all()
        return render_template('appointments.html', appointments=items, patients=Patient.query.order_by(Patient.full_name).all(),
                               doctors=Doctor.query.order_by(Doctor.full_name).all(), statuses=['Scheduled', 'Checked in', 'Completed', 'Cancelled'])

    @app.post('/appointments/add')
    def add_appointment():
        try:
            patient_id = int(request.form.get('patient_id', ''))
            doctor_id = int(request.form.get('doctor_id', ''))
            starts_at = datetime.fromisoformat(request.form.get('starts_at', ''))
        except (ValueError, TypeError):
            flash('Select a patient and doctor and enter a valid appointment date and time.', 'error')
            return redirect(url_for('appointments'))
        reason = request.form.get('reason', '').strip()
        if not db.session.get(Patient, patient_id) or not db.session.get(Doctor, doctor_id) or not reason:
            flash('Please provide a valid patient, doctor, and appointment reason.', 'error')
            return redirect(url_for('appointments'))
        db.session.add(Appointment(patient_id=patient_id, doctor_id=doctor_id, starts_at=starts_at, reason=reason))
        db.session.commit()
        flash('Appointment scheduled.', 'success')
        return redirect(url_for('appointments'))

    @app.post('/appointments/<int:appointment_id>/status')
    def update_appointment(appointment_id):
        item = db.get_or_404(Appointment, appointment_id)
        status = request.form.get('status', '')
        if status not in {'Scheduled', 'Checked in', 'Completed', 'Cancelled'}:
            flash('Invalid appointment status.', 'error')
        else:
            item.status = status
            db.session.commit()
            flash('Appointment updated.', 'success')
        return redirect(url_for('appointments'))

    @app.get('/billing')
    def billing():
        return render_template('billing.html', invoices=Invoice.query.order_by(Invoice.issued_on.desc(), Invoice.id.desc()).all(),
                               patients=Patient.query.order_by(Patient.full_name).all())

    @app.post('/billing/add')
    def add_invoice():
        try:
            patient_id = int(request.form.get('patient_id', ''))
            amount = Decimal(request.form.get('amount', ''))
        except (ValueError, InvalidOperation):
            flash('Choose a patient and enter a valid amount.', 'error')
            return redirect(url_for('billing'))
        description = request.form.get('description', '').strip()
        if not db.session.get(Patient, patient_id) or not description or amount <= 0 or amount > Decimal('99999999.99'):
            flash('A valid patient, description, and positive amount are required.', 'error')
            return redirect(url_for('billing'))
        db.session.add(Invoice(patient_id=patient_id, description=description, amount=amount))
        db.session.commit()
        flash('Invoice created.', 'success')
        return redirect(url_for('billing'))

    @app.post('/billing/<int:invoice_id>/paid')
    def mark_paid(invoice_id):
        invoice = db.get_or_404(Invoice, invoice_id)
        invoice.status = 'Paid'
        db.session.commit()
        flash('Invoice marked as paid.', 'success')
        return redirect(url_for('billing'))

    @app.cli.command('init-db')
    def init_db_command():
        """Create the database tables."""
        with app.app_context():
            db.create_all()
        click.echo('Database tables created.')

    @app.cli.command('seed-demo')
    def seed_demo_command():
        """Insert fictional sample data for the dashboard demo."""
        with app.app_context():
            db.create_all()
            if Patient.query.first():
                click.echo('Database already has patients; demo seed skipped.')
                return
            patients = [
                Patient(full_name='Aarav Sharma', date_of_birth=date(1991, 4, 12), gender='Male', phone='+1 555 0101', email='aarav@example.test', blood_group='O+'),
                Patient(full_name='Maya Patel', date_of_birth=date(1987, 9, 3), gender='Female', phone='+1 555 0102', email='maya@example.test', blood_group='A+'),
                Patient(full_name='Noah Williams', date_of_birth=date(2000, 1, 25), gender='Male', phone='+1 555 0103', blood_group='B+'),
                Patient(full_name='Sofia Garcia', date_of_birth=date(1978, 6, 18), gender='Female', phone='+1 555 0104', blood_group='AB+'),
            ]
            doctors = [
                Doctor(full_name='Olivia Chen', specialty='Cardiology', phone='+1 555 0201', email='olivia.chen@example.test', room='204'),
                Doctor(full_name='Ethan Brooks', specialty='Pediatrics', phone='+1 555 0202', email='ethan.brooks@example.test', room='118'),
                Doctor(full_name='Amara Okafor', specialty='Neurology', phone='+1 555 0203', email='amara.okafor@example.test', room='310'),
            ]
            db.session.add_all(patients + doctors)
            db.session.flush()
            now = datetime.now().replace(second=0, microsecond=0)
            appointments = [
                Appointment(patient=patients[0], doctor=doctors[0], starts_at=now + timedelta(hours=1), reason='Cardiology follow-up', status='Scheduled'),
                Appointment(patient=patients[1], doctor=doctors[1], starts_at=now + timedelta(hours=2), reason='Annual wellness visit', status='Checked in'),
                Appointment(patient=patients[2], doctor=doctors[2], starts_at=now + timedelta(days=1), reason='Headache consultation', status='Scheduled'),
                Appointment(patient=patients[3], doctor=doctors[0], starts_at=now - timedelta(days=1), reason='Blood pressure review', status='Completed'),
            ]
            invoices = [
                Invoice(patient=patients[0], description='Cardiology consultation', amount=Decimal('180.00'), status='Unpaid'),
                Invoice(patient=patients[1], description='Wellness visit', amount=Decimal('95.00'), status='Paid'),
                Invoice(patient=patients[3], description='Diagnostic tests', amount=Decimal('240.00'), status='Unpaid'),
            ]
            db.session.add_all(appointments + invoices)
            db.session.commit()
            click.echo('Demo data inserted (fictional records).')

    return app


def parse_date(value):
    try:
        parsed = date.fromisoformat(value)
        return parsed if parsed <= date.today() else None
    except (ValueError, TypeError):
        return None


app = create_app()
