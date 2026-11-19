import os
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

import click
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()
csrf = CSRFProtect()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='reception')
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
    admissions = db.relationship('Admission', back_populates='patient', cascade='all, delete-orphan')
    records = db.relationship('ClinicalRecord', back_populates='patient', cascade='all, delete-orphan')


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False, index=True)
    specialty = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(160))
    room = db.Column(db.String(30))
    appointments = db.relationship('Appointment', back_populates='doctor', cascade='all, delete-orphan')
    records = db.relationship('ClinicalRecord', back_populates='doctor')


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


class Ward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    beds = db.relationship('Bed', back_populates='ward', cascade='all, delete-orphan')


class Bed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id', ondelete='CASCADE'), nullable=False)
    bed_number = db.Column(db.String(30), nullable=False)
    bed_type = db.Column(db.String(30), nullable=False, default='General')
    ward = db.relationship('Ward', back_populates='beds')
    admissions = db.relationship('Admission', back_populates='bed')
    __table_args__ = (db.UniqueConstraint('ward_id', 'bed_number', name='uq_ward_bed_number'),)


class Admission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('bed.id'), nullable=False)
    admitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    discharged_at = db.Column(db.DateTime)
    reason = db.Column(db.String(240), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Admitted')
    patient = db.relationship('Patient', back_populates='admissions')
    bed = db.relationship('Bed', back_populates='admissions')


class ClinicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    record_type = db.Column(db.String(40), nullable=False, default='Consultation')
    diagnosis = db.Column(db.String(240), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    patient = db.relationship('Patient', back_populates='records')
    doctor = db.relationship('Doctor', back_populates='records')
    prescriptions = db.relationship('Prescription', back_populates='record', cascade='all, delete-orphan')


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('clinical_record.id', ondelete='CASCADE'), nullable=False)
    medication = db.Column(db.String(160), nullable=False)
    dosage = db.Column(db.String(120), nullable=False)
    instructions = db.Column(db.String(240), nullable=False)
    record = db.relationship('ClinicalRecord', back_populates='prescriptions')


ROLE_LABELS = {'admin': 'Administrator', 'clinician': 'Clinician', 'reception': 'Reception', 'billing': 'Billing'}
ROLE_ENDPOINTS = {
    'admin': None,
    'clinician': {'dashboard', 'patients', 'doctors', 'appointments', 'add_appointment', 'update_appointment', 'admissions', 'add_admission', 'discharge_admission', 'records', 'add_record'},
    'reception': {'dashboard', 'patients', 'add_patient', 'doctors', 'add_doctor', 'appointments', 'add_appointment', 'update_appointment', 'admissions', 'add_admission', 'discharge_admission'},
    'billing': {'dashboard', 'patients', 'billing', 'add_invoice', 'mark_paid'},
}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'local-development-key-change-me'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///hospital.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', '0') == '1',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    csrf.init_app(app)
    app.jinja_env.globals['now'] = datetime.now

    @app.before_request
    def authenticate_and_authorize():
        g.user = None
        if request.endpoint in {'login', 'static'} or request.endpoint is None:
            return
        user_id = session.get('user_id')
        if user_id:
            g.user = db.session.get(User, user_id)
        if not g.user or not g.user.active:
            session.clear()
            return redirect(url_for('login', next=request.path))
        allowed = ROLE_ENDPOINTS.get(g.user.role, set())
        if allowed is not None and request.endpoint not in allowed:
            flash('Your account does not have permission to access that page.', 'error')
            return redirect(url_for('dashboard'))

    @app.context_processor
    def inject_user():
        return {'current_user': getattr(g, 'user', None), 'role_labels': ROLE_LABELS}

    @app.get('/login')
    def login():
        if session.get('user_id'):
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    @app.post('/login')
    def login_post():
        username = request.form.get('username', '').strip().lower()
        user = User.query.filter_by(username=username).first()
        if not user or not user.active or not user.check_password(request.form.get('password', '')):
            flash('Invalid username or password.', 'error')
            return render_template('login.html'), 401
        session.clear()
        session['user_id'] = user.id
        session.permanent = True
        next_path = request.args.get('next', '')
        if not next_path.startswith('/') or next_path.startswith('//'):
            next_path = url_for('dashboard')
        return redirect(next_path)

    @app.post('/logout')
    def logout():
        session.clear()
        flash('You have been signed out.', 'success')
        return redirect(url_for('login'))

    @app.get('/')
    def dashboard():
        today = date.today()
        start = datetime.combine(today, time.min)
        end = start + timedelta(days=1)
        stats = {
            'patients': Patient.query.count(), 'doctors': Doctor.query.count(),
            'today': Appointment.query.filter(Appointment.starts_at >= start, Appointment.starts_at < end).count(),
            'unpaid': db.session.query(func.coalesce(func.sum(Invoice.amount), 0)).filter_by(status='Unpaid').scalar(),
            'admitted': Admission.query.filter_by(status='Admitted').count(),
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
        name, phone = request.form.get('full_name', '').strip(), request.form.get('phone', '').strip()
        dob, gender = parse_date(request.form.get('date_of_birth', '')), request.form.get('gender', '').strip()
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
        if g.user.role != 'admin':
            flash('Only administrators can delete patient records.', 'error')
            return redirect(url_for('patients'))
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
        name, specialty, phone = (request.form.get(k, '').strip() for k in ('full_name', 'specialty', 'phone'))
        if not name or not specialty or not phone:
            flash('Name, specialty, and phone are required.', 'error')
            return redirect(url_for('doctors'))
        db.session.add(Doctor(full_name=name, specialty=specialty, phone=phone,
                              email=request.form.get('email', '').strip() or None,
                              room=request.form.get('room', '').strip() or None))
        db.session.commit()
        flash(f'Dr. {name} was added.', 'success')
        return redirect(url_for('doctors'))

    @app.post('/doctors/<int:doctor_id>/delete')
    def delete_doctor(doctor_id):
        if g.user.role != 'admin':
            flash('Only administrators can delete doctor records.', 'error')
            return redirect(url_for('doctors'))
        db.session.delete(db.get_or_404(Doctor, doctor_id))
        db.session.commit()
        flash('Doctor and linked appointments were deleted.', 'success')
        return redirect(url_for('doctors'))

    @app.get('/appointments')
    def appointments():
        return render_template('appointments.html', appointments=Appointment.query.order_by(Appointment.starts_at.desc()).all(),
                               patients=Patient.query.order_by(Patient.full_name).all(), doctors=Doctor.query.order_by(Doctor.full_name).all(),
                               statuses=['Scheduled', 'Checked in', 'Completed', 'Cancelled'])

    @app.post('/appointments/add')
    def add_appointment():
        try:
            patient_id, doctor_id = int(request.form.get('patient_id', '')), int(request.form.get('doctor_id', ''))
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
        item, status = db.get_or_404(Appointment, appointment_id), request.form.get('status', '')
        if status not in {'Scheduled', 'Checked in', 'Completed', 'Cancelled'}:
            flash('Invalid appointment status.', 'error')
        else:
            item.status = status
            db.session.commit()
            flash('Appointment updated.', 'success')
        return redirect(url_for('appointments'))

    @app.get('/admissions')
    def admissions():
        occupied = db.session.query(Admission.bed_id).filter_by(status='Admitted').subquery()
        available_beds = Bed.query.filter(~Bed.id.in_(occupied)).join(Ward).order_by(Ward.name, Bed.bed_number).all()
        return render_template('admissions.html', admissions=Admission.query.order_by(Admission.admitted_at.desc()).all(),
                               patients=Patient.query.order_by(Patient.full_name).all(), beds=available_beds,
                               wards=Ward.query.order_by(Ward.name).all(), occupied_ids={a.bed_id for a in Admission.query.filter_by(status='Admitted').all()})

    @app.post('/admissions/add')
    def add_admission():
        try:
            patient_id, bed_id = int(request.form.get('patient_id', '')), int(request.form.get('bed_id', ''))
        except ValueError:
            flash('Choose a valid patient and available bed.', 'error')
            return redirect(url_for('admissions'))
        bed = db.session.get(Bed, bed_id)
        occupied = Admission.query.filter_by(bed_id=bed_id, status='Admitted').first()
        reason = request.form.get('reason', '').strip()
        if not db.session.get(Patient, patient_id) or not bed or occupied or not reason:
            flash('Patient, available bed, and admission reason are required.', 'error')
            return redirect(url_for('admissions'))
        db.session.add(Admission(patient_id=patient_id, bed_id=bed_id, reason=reason))
        db.session.commit()
        flash('Patient admitted and bed assigned.', 'success')
        return redirect(url_for('admissions'))

    @app.post('/admissions/<int:admission_id>/discharge')
    def discharge_admission(admission_id):
        admission = db.get_or_404(Admission, admission_id)
        if admission.status == 'Admitted':
            admission.status, admission.discharged_at = 'Discharged', datetime.utcnow()
            db.session.commit()
            flash('Patient discharged; bed is now available.', 'success')
        return redirect(url_for('admissions'))

    @app.post('/wards/add')
    def add_ward():
        if g.user.role != 'admin':
            flash('Only administrators can manage wards and beds.', 'error')
            return redirect(url_for('admissions'))
        name = request.form.get('name', '').strip()
        numbers = [n.strip() for n in request.form.get('bed_numbers', '').split(',') if n.strip()]
        if not name or not numbers:
            flash('Ward name and one or more comma-separated bed numbers are required.', 'error')
            return redirect(url_for('admissions'))
        ward = Ward(name=name)
        db.session.add(ward)
        try:
            db.session.flush()
            db.session.add_all(Bed(ward=ward, bed_number=number, bed_type=request.form.get('bed_type', 'General')) for number in numbers)
            db.session.commit()
            flash(f'Ward {name} and {len(numbers)} beds added.', 'success')
        except Exception:
            db.session.rollback()
            flash('Could not add that ward. Check that the ward name is unique.', 'error')
        return redirect(url_for('admissions'))

    @app.get('/records')
    def records():
        return render_template('records.html', records=ClinicalRecord.query.order_by(ClinicalRecord.visit_date.desc()).all(),
                               patients=Patient.query.order_by(Patient.full_name).all(), doctors=Doctor.query.order_by(Doctor.full_name).all())

    @app.post('/records/add')
    def add_record():
        try:
            patient_id, doctor_id = int(request.form.get('patient_id', '')), int(request.form.get('doctor_id', ''))
        except ValueError:
            flash('Choose a valid patient and doctor.', 'error')
            return redirect(url_for('records'))
        diagnosis, notes = request.form.get('diagnosis', '').strip(), request.form.get('notes', '').strip()
        doctor = db.session.get(Doctor, doctor_id)
        if not db.session.get(Patient, patient_id) or not doctor or not diagnosis or not notes:
            flash('Patient, clinician, diagnosis, and visit notes are required.', 'error')
            return redirect(url_for('records'))
        record = ClinicalRecord(patient_id=patient_id, doctor_id=doctor_id,
                                record_type=request.form.get('record_type', 'Consultation'), diagnosis=diagnosis, notes=notes)
        medication = request.form.get('medication', '').strip()
        if medication:
            record.prescriptions.append(Prescription(medication=medication,
                dosage=request.form.get('dosage', '').strip() or 'See instructions',
                instructions=request.form.get('instructions', '').strip() or 'As directed by clinician'))
        db.session.add(record)
        db.session.commit()
        flash('Clinical record saved.', 'success')
        return redirect(url_for('records'))

    @app.get('/billing')
    def billing():
        return render_template('billing.html', invoices=Invoice.query.order_by(Invoice.issued_on.desc(), Invoice.id.desc()).all(),
                               patients=Patient.query.order_by(Patient.full_name).all())

    @app.post('/billing/add')
    def add_invoice():
        try:
            patient_id, amount = int(request.form.get('patient_id', '')), Decimal(request.form.get('amount', ''))
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

    @app.get('/staff')
    def staff():
        if g.user.role != 'admin':
            flash('Only administrators can manage staff accounts.', 'error')
            return redirect(url_for('dashboard'))
        return render_template('staff.html', users=User.query.order_by(User.username).all(), roles=ROLE_LABELS)

    @app.post('/staff/add')
    def add_staff():
        if g.user.role != 'admin':
            return redirect(url_for('dashboard'))
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        if len(username) < 3 or len(password) < 12 or role not in ROLE_LABELS:
            flash('Username must be at least 3 characters; password at least 12; choose a valid role.', 'error')
            return redirect(url_for('staff'))
        if User.query.filter_by(username=username).first():
            flash('That username already exists.', 'error')
            return redirect(url_for('staff'))
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account for {username} created.', 'success')
        return redirect(url_for('staff'))

    @app.post('/staff/<int:user_id>/toggle')
    def toggle_staff(user_id):
        if g.user.role != 'admin':
            return redirect(url_for('dashboard'))
        user = db.get_or_404(User, user_id)
        if user.id == g.user.id:
            flash('You cannot disable your own account.', 'error')
        else:
            user.active = not user.active
            db.session.commit()
            flash('Staff account status updated.', 'success')
        return redirect(url_for('staff'))

    @app.cli.command('init-db')
    def init_db_command():
        """Create database tables (use migrations for production changes)."""
        db.create_all()
        click.echo('Database tables created.')

    @app.cli.command('create-admin')
    def create_admin_command():
        """Create the initial administrator account interactively."""
        db.create_all()
        if User.query.filter_by(role='admin', active=True).first():
            click.echo('An active administrator already exists.')
            return
        username = click.prompt('Admin username').strip().lower()
        password = click.prompt('Admin password (minimum 12 characters)', hide_input=True, confirmation_prompt=True)
        if len(username) < 3 or len(password) < 12:
            raise click.ClickException('Username must be at least 3 characters and password at least 12 characters.')
        if User.query.filter_by(username=username).first():
            raise click.ClickException('That username already exists.')
        admin = User(username=username, role='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo('Administrator account created. Sign in through the web page.')

    @app.cli.command('seed-demo')
    def seed_demo_command():
        """Insert fictional sample records. Never use these as real patient data."""
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
        doctors = [Doctor(full_name='Olivia Chen', specialty='Cardiology', phone='+1 555 0201', email='olivia.chen@example.test', room='204'),
                   Doctor(full_name='Ethan Brooks', specialty='Pediatrics', phone='+1 555 0202', email='ethan.brooks@example.test', room='118'),
                   Doctor(full_name='Amara Okafor', specialty='Neurology', phone='+1 555 0203', email='amara.okafor@example.test', room='310')]
        db.session.add_all(patients + doctors)
        db.session.flush()
        now = datetime.now().replace(second=0, microsecond=0)
        db.session.add_all([
            Appointment(patient=patients[0], doctor=doctors[0], starts_at=now + timedelta(hours=1), reason='Cardiology follow-up'),
            Appointment(patient=patients[1], doctor=doctors[1], starts_at=now + timedelta(hours=2), reason='Annual wellness visit', status='Checked in'),
            Appointment(patient=patients[2], doctor=doctors[2], starts_at=now + timedelta(days=1), reason='Headache consultation'),
            Invoice(patient=patients[0], description='Cardiology consultation', amount=Decimal('180.00')),
            Invoice(patient=patients[1], description='Wellness visit', amount=Decimal('95.00'), status='Paid'),
            Invoice(patient=patients[3], description='Diagnostic tests', amount=Decimal('240.00')),
        ])
        ward = Ward(name='General Ward')
        db.session.add(ward)
        db.session.flush()
        db.session.add_all([Bed(ward=ward, bed_number=str(n), bed_type='General') for n in range(1, 9)])
        db.session.commit()
        click.echo('Fictional demo data and 8 sample beds inserted.')

    return app


def parse_date(value):
    try:
        parsed = date.fromisoformat(value)
        return parsed if parsed <= date.today() else None
    except (ValueError, TypeError):
        return None


app = create_app()
