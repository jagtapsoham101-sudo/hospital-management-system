import os
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import click
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()
csrf = CSRFProtect()
DEMO_USERNAME = 'admin'
DEMO_PASSWORD = 'CarePointDemo2026!'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')
    active = db.Column(db.Boolean, nullable=False, default=True)
    def set_password(self, value): self.password_hash = generate_password_hash(value)
    def check_password(self, value): return check_password_hash(self.password_hash, value)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(30), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(160))
    blood_group = db.Column(db.String(5))
    address = db.Column(db.String(240))
    appointments = db.relationship('Appointment', back_populates='patient', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='patient', cascade='all, delete-orphan')
    admissions = db.relationship('Admission', back_populates='patient', cascade='all, delete-orphan')
    records = db.relationship('ClinicalRecord', back_populates='patient', cascade='all, delete-orphan')


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
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
    __table_args__ = (db.UniqueConstraint('ward_id', 'bed_number'),)


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


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.getenv('SECRET_KEY', 'local-demo-only-change-before-deployment'), SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///hospital.db'), SQLALCHEMY_TRACK_MODIFICATIONS=False, PERMANENT_SESSION_LIFETIME=timedelta(minutes=30), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    if test_config: app.config.update(test_config)
    db.init_app(app); csrf.init_app(app); app.jinja_env.globals['now'] = datetime.now

    @app.before_request
    def login_guard():
        g.user = None
        if request.endpoint in {'login', 'login_post', 'static'} or request.endpoint is None: return
        g.user = db.session.get(User, session.get('user_id')) if session.get('user_id') else None
        if not g.user or not g.user.active:
            session.clear(); return redirect(url_for('login', next=request.path))

    @app.context_processor
    def context(): return {'current_user': getattr(g, 'user', None), 'role_labels': {'admin': 'Administrator'}}

    @app.get('/login')
    def login(): return render_template('login.html')

    @app.post('/login')
    def login_post():
        user = User.query.filter_by(username=request.form.get('username', '').strip().lower()).first()
        if not user or not user.active or not user.check_password(request.form.get('password', '')):
            flash('Invalid username or password.', 'error'); return render_template('login.html'), 401
        session.clear(); session['user_id'] = user.id; session.permanent = True
        dest = request.args.get('next', '')
        return redirect(dest if dest.startswith('/') and not dest.startswith('//') else url_for('dashboard'))

    @app.post('/logout')
    def logout(): session.clear(); return redirect(url_for('login'))

    @app.get('/')
    def dashboard():
        start = datetime.combine(date.today(), datetime.min.time())
        stats = {'patients': Patient.query.count(), 'doctors': Doctor.query.count(), 'today': Appointment.query.filter(Appointment.starts_at >= start, Appointment.starts_at < start + timedelta(days=1)).count(), 'unpaid': db.session.query(func.coalesce(func.sum(Invoice.amount), 0)).filter_by(status='Unpaid').scalar(), 'admitted': Admission.query.filter_by(status='Admitted').count()}
        return render_template('dashboard.html', stats=stats, appointments=Appointment.query.order_by(Appointment.starts_at).limit(6).all())

    @app.get('/patients')
    def patients():
        q = request.args.get('q', '').strip(); query = Patient.query.filter(Patient.full_name.ilike(f'%{q}%')) if q else Patient.query
        return render_template('patients.html', patients=query.order_by(Patient.full_name).all(), search=q)

    @app.post('/patients/add')
    def add_patient():
        try: dob = date.fromisoformat(request.form.get('date_of_birth', ''))
        except ValueError: dob = None
        name, phone, gender = (request.form.get(k, '').strip() for k in ('full_name', 'phone', 'gender'))
        if not name or not phone or not dob or dob > date.today() or gender not in {'Female', 'Male', 'Non-binary', 'Prefer not to say'}:
            flash('Enter valid patient details.', 'error'); return redirect(url_for('patients'))
        db.session.add(Patient(full_name=name, date_of_birth=dob, gender=gender, phone=phone, email=request.form.get('email', '').strip() or None, blood_group=request.form.get('blood_group', '').strip() or None, address=request.form.get('address', '').strip() or None)); db.session.commit(); flash('Patient added.', 'success'); return redirect(url_for('patients'))

    @app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
    def edit_patient(patient_id):
        p = db.get_or_404(Patient, patient_id)
        if request.method == 'POST':
            try: dob = date.fromisoformat(request.form.get('date_of_birth', ''))
            except ValueError: dob = None
            name, phone, gender = (request.form.get(k, '').strip() for k in ('full_name', 'phone', 'gender'))
            if not name or not phone or not dob or dob > date.today() or gender not in {'Female', 'Male', 'Non-binary', 'Prefer not to say'}: flash('Invalid patient details.', 'error')
            else:
                p.full_name, p.date_of_birth, p.gender, p.phone = name, dob, gender, phone; p.email=request.form.get('email','').strip() or None; p.blood_group=request.form.get('blood_group','').strip() or None; p.address=request.form.get('address','').strip() or None; db.session.commit(); flash('Patient updated.', 'success'); return redirect(url_for('patients'))
        return render_template('edit_patient.html', patient=p)

    @app.post('/patients/<int:patient_id>/delete')
    def delete_patient(patient_id): db.session.delete(db.get_or_404(Patient, patient_id)); db.session.commit(); flash('Patient and linked records deleted.', 'success'); return redirect(url_for('patients'))

    @app.get('/doctors')
    def doctors(): return render_template('doctors.html', doctors=Doctor.query.order_by(Doctor.full_name).all())

    @app.post('/doctors/add')
    def add_doctor():
        fields={k:request.form.get(k,'').strip() or None for k in ('full_name','specialty','phone','email','room')}
        if not fields['full_name'] or not fields['specialty'] or not fields['phone']: flash('Name, specialty and phone are required.','error')
        else: db.session.add(Doctor(**fields)); db.session.commit(); flash('Doctor added.','success')
        return redirect(url_for('doctors'))

    @app.route('/doctors/<int:doctor_id>/edit', methods=['GET','POST'])
    def edit_doctor(doctor_id):
        d=db.get_or_404(Doctor,doctor_id)
        if request.method=='POST':
            name,specialty,phone=(request.form.get(k,'').strip() for k in ('full_name','specialty','phone'))
            if not name or not specialty or not phone: flash('Name, specialty and phone are required.','error')
            else: d.full_name,d.specialty,d.phone=name,specialty,phone; d.email=request.form.get('email','').strip() or None; d.room=request.form.get('room','').strip() or None; db.session.commit(); flash('Doctor updated.','success'); return redirect(url_for('doctors'))
        return render_template('edit_doctor.html',doctor=d)

    @app.post('/doctors/<int:doctor_id>/delete')
    def delete_doctor(doctor_id): db.session.delete(db.get_or_404(Doctor,doctor_id)); db.session.commit(); flash('Doctor and linked appointments deleted.','success'); return redirect(url_for('doctors'))

    @app.get('/appointments')
    def appointments(): return render_template('appointments.html',appointments=Appointment.query.order_by(Appointment.starts_at.desc()).all(),patients=Patient.query.order_by(Patient.full_name).all(),doctors=Doctor.query.order_by(Doctor.full_name).all(),statuses=['Scheduled','Checked in','Completed','Cancelled'])

    @app.post('/appointments/add')
    def add_appointment():
        try: pid,did=int(request.form.get('patient_id','')),int(request.form.get('doctor_id','')); dt=datetime.fromisoformat(request.form.get('starts_at',''))
        except (ValueError,TypeError): flash('Choose valid patient, doctor and date/time.','error'); return redirect(url_for('appointments'))
        reason=request.form.get('reason','').strip()
        if not db.session.get(Patient,pid) or not db.session.get(Doctor,did) or not reason: flash('Patient, doctor and reason required.','error')
        else: db.session.add(Appointment(patient_id=pid,doctor_id=did,starts_at=dt,reason=reason)); db.session.commit(); flash('Appointment scheduled.','success')
        return redirect(url_for('appointments'))

    @app.post('/appointments/<int:appointment_id>/status')
    def update_appointment(appointment_id):
        a=db.get_or_404(Appointment,appointment_id); s=request.form.get('status','')
        if s in {'Scheduled','Checked in','Completed','Cancelled'}: a.status=s; db.session.commit(); flash('Appointment updated.','success')
        return redirect(url_for('appointments'))

    @app.post('/appointments/<int:appointment_id>/delete')
    def delete_appointment(appointment_id): db.session.delete(db.get_or_404(Appointment,appointment_id)); db.session.commit(); flash('Appointment deleted.','success'); return redirect(url_for('appointments'))

    @app.get('/billing')
    def billing(): return render_template('billing.html',invoices=Invoice.query.order_by(Invoice.issued_on.desc(),Invoice.id.desc()).all(),patients=Patient.query.order_by(Patient.full_name).all())

    @app.post('/billing/add')
    def add_invoice():
        try: pid=int(request.form.get('patient_id','')); amount=Decimal(request.form.get('amount',''))
        except (ValueError,InvalidOperation): flash('Enter valid invoice details.','error'); return redirect(url_for('billing'))
        desc=request.form.get('description','').strip()
        if not db.session.get(Patient,pid) or not desc or not amount.is_finite() or amount<=0: flash('Select patient and enter description and positive amount.','error')
        else: db.session.add(Invoice(patient_id=pid,description=desc,amount=amount)); db.session.commit(); flash('Invoice created.','success')
        return redirect(url_for('billing'))

    @app.post('/billing/<int:invoice_id>/paid')
    def mark_paid(invoice_id): i=db.get_or_404(Invoice,invoice_id); i.status='Paid'; db.session.commit(); return redirect(url_for('billing'))
    @app.post('/billing/<int:invoice_id>/delete')
    def delete_invoice(invoice_id): db.session.delete(db.get_or_404(Invoice,invoice_id)); db.session.commit(); return redirect(url_for('billing'))

    @app.get('/admissions')
    def admissions():
        occupied={a.bed_id for a in Admission.query.filter_by(status='Admitted')}; beds=[b for b in Bed.query.order_by(Bed.ward_id,Bed.bed_number).all() if b.id not in occupied]
        return render_template('admissions.html',admissions=Admission.query.order_by(Admission.admitted_at.desc()).all(),patients=Patient.query.all(),beds=beds,wards=Ward.query.all())
    @app.post('/admissions/add')
    def add_admission():
        try: pid,bid=int(request.form.get('patient_id','')),int(request.form.get('bed_id',''))
        except ValueError: flash('Select patient and bed.','error'); return redirect(url_for('admissions'))
        reason=request.form.get('reason','').strip()
        if not db.session.get(Patient,pid) or not db.session.get(Bed,bid) or Admission.query.filter_by(bed_id=bid,status='Admitted').first() or not reason: flash('Patient, available bed and reason required.','error')
        else: db.session.add(Admission(patient_id=pid,bed_id=bid,reason=reason)); db.session.commit(); flash('Patient admitted.','success')
        return redirect(url_for('admissions'))
    @app.post('/admissions/<int:admission_id>/discharge')
    def discharge_admission(admission_id): a=db.get_or_404(Admission,admission_id); a.status='Discharged'; a.discharged_at=datetime.utcnow(); db.session.commit(); return redirect(url_for('admissions'))
    @app.post('/admissions/<int:admission_id>/delete')
    def delete_admission(admission_id): db.session.delete(db.get_or_404(Admission,admission_id)); db.session.commit(); return redirect(url_for('admissions'))
    @app.post('/wards/add')
    def add_ward():
        name=request.form.get('name','').strip(); nums=[n.strip() for n in request.form.get('bed_numbers','').split(',') if n.strip()]
        if not name or not nums: flash('Ward name and bed numbers required.','error'); return redirect(url_for('admissions'))
        ward=Ward(name=name); db.session.add(ward)
        try: db.session.flush(); db.session.add_all(Bed(ward=ward,bed_number=n,bed_type=request.form.get('bed_type','General')) for n in nums); db.session.commit(); flash('Ward and beds added.','success')
        except Exception: db.session.rollback(); flash('Could not add ward; check duplicate names/beds.','error')
        return redirect(url_for('admissions'))

    @app.get('/records')
    def records(): return render_template('records.html',records=ClinicalRecord.query.order_by(ClinicalRecord.visit_date.desc()).all(),patients=Patient.query.all(),doctors=Doctor.query.all())
    @app.post('/records/add')
    def add_record():
        try: pid,did=int(request.form.get('patient_id','')),int(request.form.get('doctor_id',''))
        except ValueError: flash('Select patient and doctor.','error'); return redirect(url_for('records'))
        diagnosis,notes=request.form.get('diagnosis','').strip(),request.form.get('notes','').strip()
        if not db.session.get(Patient,pid) or not db.session.get(Doctor,did) or not diagnosis or not notes: flash('Complete required record fields.','error'); return redirect(url_for('records'))
        r=ClinicalRecord(patient_id=pid,doctor_id=did,record_type=request.form.get('record_type','Consultation'),diagnosis=diagnosis,notes=notes)
        med=request.form.get('medication','').strip()
        if med: r.prescriptions.append(Prescription(medication=med,dosage=request.form.get('dosage','').strip() or 'As directed',instructions=request.form.get('instructions','').strip() or 'As directed'))
        db.session.add(r); db.session.commit(); return redirect(url_for('records'))
    @app.post('/records/<int:record_id>/delete')
    def delete_record(record_id): db.session.delete(db.get_or_404(ClinicalRecord,record_id)); db.session.commit(); return redirect(url_for('records'))

    @app.get('/staff')
    def staff(): return render_template('staff.html',users=User.query.all(),roles={'admin':'Administrator'})
    @app.cli.command('init-db')
    def init_db_command(): db.create_all(); click.echo('Database tables created.')
    @app.cli.command('init-demo')
    def init_demo_command():
        db.create_all()
        admin=User.query.filter_by(username=DEMO_USERNAME).first()
        if not admin: admin=User(username=DEMO_USERNAME,role='admin'); db.session.add(admin)
        admin.role='admin'; admin.active=True; admin.set_password(DEMO_PASSWORD)
        pdata=[('Aarav Sharma',date(1991,4,12),'Male','+91 98765 10001','O+'),('Ananya Patel',date(1987,9,3),'Female','+91 98765 10002','A+'),('Vihaan Reddy',date(2000,1,25),'Male','+91 98765 10003','B+'),('Ishita Iyer',date(1978,6,18),'Female','+91 98765 10004','AB+'),('Arjun Mehta',date(1968,5,30),'Male','+91 98765 10005','O-'),('Kavya Nair',date(1998,10,17),'Female','+91 98765 10006','A-')]
        ddata=[('Dr. Priya Menon','Cardiology','+91 98765 20001','201'),('Dr. Rahul Verma','Pediatrics','+91 98765 20002','118'),('Dr. Neha Kulkarni','Neurology','+91 98765 20003','310'),('Dr. Vikram Rao','Family Medicine','+91 98765 20004','105')]
        ps,ds={},{}
        for name,dob,gender,phone,blood in pdata:
            p=Patient.query.filter_by(full_name=name).first()
            if not p: p=Patient(full_name=name,date_of_birth=dob,gender=gender,phone=phone,email=name.lower().replace(' ','.')+'@example.test',blood_group=blood,address='Fictional demo address, India'); db.session.add(p)
            ps[name]=p
        for name,spec,phone,room in ddata:
            d=Doctor.query.filter_by(full_name=name).first()
            if not d: d=Doctor(full_name=name,specialty=spec,phone=phone,email=name.lower().replace(' ','.')+'@example.test',room=room); db.session.add(d)
            ds[name]=d
        db.session.flush(); today=datetime.now().replace(second=0,microsecond=0)
        visits=[('Aarav Sharma','Dr. Priya Menon','Cardiology follow-up'),('Ananya Patel','Dr. Rahul Verma','Annual wellness visit'),('Vihaan Reddy','Dr. Neha Kulkarni','Neurology consultation'),('Ishita Iyer','Dr. Vikram Rao','Family medicine review'),('Arjun Mehta','Dr. Priya Menon','Heart health review'),('Kavya Nair','Dr. Rahul Verma','General consultation')]
        for idx,(pn,dn,reason) in enumerate(visits):
            p=ps[pn]
            if not Appointment.query.filter_by(patient_id=p.id,reason=reason).first(): db.session.add(Appointment(patient=p,doctor=ds[dn],starts_at=today+timedelta(days=idx),reason=reason))
            desc=reason+' - demo invoice'
            if not Invoice.query.filter_by(patient_id=p.id,description=desc).first(): db.session.add(Invoice(patient=p,description=desc,amount=Decimal(750+idx*250),status='Paid' if idx%2 else 'Unpaid'))
        ward=Ward.query.filter_by(name='General Ward').first()
        if not ward: ward=Ward(name='General Ward'); db.session.add(ward); db.session.flush()
        for i in range(1,7):
            if not Bed.query.filter_by(ward_id=ward.id,bed_number=f'G-{i:02}').first(): db.session.add(Bed(ward=ward,bed_number=f'G-{i:02}',bed_type='General'))
        db.session.flush(); bed=Bed.query.filter_by(ward_id=ward.id,bed_number='G-01').first()
        if not Admission.query.filter_by(patient_id=ps['Arjun Mehta'].id,status='Admitted').first(): db.session.add(Admission(patient=ps['Arjun Mehta'],bed=bed,reason='Fictional observation admission'))
        if not ClinicalRecord.query.filter_by(patient_id=ps['Aarav Sharma'].id,diagnosis='Demo wellness review').first():
            r=ClinicalRecord(patient=ps['Aarav Sharma'],doctor=ds['Dr. Vikram Rao'],diagnosis='Demo wellness review',notes='Fictional demo note only; not medical advice.'); r.prescriptions.append(Prescription(medication='Sample medicine',dosage='As directed',instructions='Fictional example only.')); db.session.add(r)
        db.session.commit(); click.echo('Demo data initialized. Login: admin / CarePointDemo2026!')
    return app

app = create_app()
