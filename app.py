import os
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy(); csrf = CSRFProtect()

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80),unique=True,nullable=False); password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),default='reception'); active=db.Column(db.Boolean,default=True); created_at=db.Column(db.DateTime,default=datetime.utcnow)
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)
class Patient(db.Model):
    id=db.Column(db.Integer,primary_key=True); full_name=db.Column(db.String(120),nullable=False,index=True); date_of_birth=db.Column(db.Date,nullable=False); gender=db.Column(db.String(30),nullable=False); phone=db.Column(db.String(30),nullable=False); email=db.Column(db.String(160)); blood_group=db.Column(db.String(5)); address=db.Column(db.String(240)); created_at=db.Column(db.DateTime,default=datetime.utcnow)
    appointments=db.relationship('Appointment',back_populates='patient',cascade='all, delete-orphan'); invoices=db.relationship('Invoice',back_populates='patient',cascade='all, delete-orphan'); admissions=db.relationship('Admission',back_populates='patient',cascade='all, delete-orphan'); records=db.relationship('ClinicalRecord',back_populates='patient',cascade='all, delete-orphan')
class Doctor(db.Model):
    id=db.Column(db.Integer,primary_key=True); full_name=db.Column(db.String(120),nullable=False); specialty=db.Column(db.String(100),nullable=False); phone=db.Column(db.String(30),nullable=False); email=db.Column(db.String(160)); room=db.Column(db.String(30)); appointments=db.relationship('Appointment',back_populates='doctor',cascade='all, delete-orphan'); records=db.relationship('ClinicalRecord',back_populates='doctor')
class Appointment(db.Model):
    id=db.Column(db.Integer,primary_key=True); patient_id=db.Column(db.Integer,db.ForeignKey('patient.id',ondelete='CASCADE'),nullable=False); doctor_id=db.Column(db.Integer,db.ForeignKey('doctor.id',ondelete='CASCADE'),nullable=False); starts_at=db.Column(db.DateTime,nullable=False); reason=db.Column(db.String(240),nullable=False); status=db.Column(db.String(20),default='Scheduled'); patient=db.relationship('Patient',back_populates='appointments'); doctor=db.relationship('Doctor',back_populates='appointments')
class Invoice(db.Model):
    id=db.Column(db.Integer,primary_key=True); patient_id=db.Column(db.Integer,db.ForeignKey('patient.id',ondelete='CASCADE'),nullable=False); description=db.Column(db.String(200),nullable=False); amount=db.Column(db.Numeric(10,2),nullable=False); status=db.Column(db.String(20),default='Unpaid'); issued_on=db.Column(db.Date,default=date.today); patient=db.relationship('Patient',back_populates='invoices')
class Ward(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(100),unique=True,nullable=False); beds=db.relationship('Bed',back_populates='ward',cascade='all, delete-orphan')
class Bed(db.Model):
    id=db.Column(db.Integer,primary_key=True); ward_id=db.Column(db.Integer,db.ForeignKey('ward.id',ondelete='CASCADE'),nullable=False); bed_number=db.Column(db.String(30),nullable=False); bed_type=db.Column(db.String(30),default='General'); ward=db.relationship('Ward',back_populates='beds'); admissions=db.relationship('Admission',back_populates='bed'); __table_args__=(db.UniqueConstraint('ward_id','bed_number'),)
class Admission(db.Model):
    id=db.Column(db.Integer,primary_key=True); patient_id=db.Column(db.Integer,db.ForeignKey('patient.id'),nullable=False); bed_id=db.Column(db.Integer,db.ForeignKey('bed.id'),nullable=False); admitted_at=db.Column(db.DateTime,default=datetime.utcnow); discharged_at=db.Column(db.DateTime); reason=db.Column(db.String(240),nullable=False); status=db.Column(db.String(20),default='Admitted'); patient=db.relationship('Patient',back_populates='admissions'); bed=db.relationship('Bed',back_populates='admissions')
class ClinicalRecord(db.Model):
    id=db.Column(db.Integer,primary_key=True); patient_id=db.Column(db.Integer,db.ForeignKey('patient.id',ondelete='CASCADE'),nullable=False); doctor_id=db.Column(db.Integer,db.ForeignKey('doctor.id'),nullable=False); visit_date=db.Column(db.DateTime,default=datetime.utcnow); record_type=db.Column(db.String(40),default='Consultation'); diagnosis=db.Column(db.String(240),nullable=False); notes=db.Column(db.Text,nullable=False); patient=db.relationship('Patient',back_populates='records'); doctor=db.relationship('Doctor',back_populates='records'); prescriptions=db.relationship('Prescription',back_populates='record',cascade='all, delete-orphan')
class Prescription(db.Model):
    id=db.Column(db.Integer,primary_key=True); record_id=db.Column(db.Integer,db.ForeignKey('clinical_record.id',ondelete='CASCADE'),nullable=False); medication=db.Column(db.String(160),nullable=False); dosage=db.Column(db.String(120),nullable=False); instructions=db.Column(db.String(240),nullable=False); record=db.relationship('ClinicalRecord',back_populates='prescriptions')

ROLES={'admin':'Administrator','clinician':'Clinician','reception':'Reception','billing':'Billing'}
ACCESS={'admin':None,'clinician':{'dashboard','patients','doctors','appointments','admissions','records','add_patient','add_appointment','update_appointment','add_admission','discharge_admission','add_record'},'reception':{'dashboard','patients','doctors','appointments','admissions','add_patient','add_doctor','add_appointment','update_appointment','add_admission','discharge_admission'},'billing':{'dashboard','patients','billing','add_patient','add_invoice','mark_paid'}}

def create_app(test_config=None):
    app=Flask(__name__); app.config.from_mapping(SECRET_KEY=os.getenv('SECRET_KEY','change-this-secret'),SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///hospital.db'),SQLALCHEMY_TRACK_MODIFICATIONS=False,PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
    if test_config: app.config.update(test_config)
    db.init_app(app); csrf.init_app(app); app.jinja_env.globals['now']=datetime.now
    @app.before_request
    def guard():
        g.user=None
        if request.endpoint in {'login','login_post','static'} or request.endpoint is None:return
        g.user=db.session.get(User,session.get('user_id')) if session.get('user_id') else None
        if not g.user or not g.user.active: session.clear(); return redirect(url_for('login',next=request.path))
        allowed=ACCESS[g.user.role]
        if allowed is not None and request.endpoint not in allowed: flash('You do not have permission for that page.','error'); return redirect(url_for('dashboard'))
    @app.context_processor
    def ctx(): return {'current_user':g.user,'role_labels':ROLES}
    @app.get('/login')
    def login(): return render_template('login.html')
    @app.post('/login')
    def login_post():
        u=User.query.filter_by(username=request.form.get('username','').strip().lower()).first()
        if not u or not u.active or not u.check_password(request.form.get('password','')): flash('Invalid username or password.','error'); return render_template('login.html'),401
        session.clear(); session['user_id']=u.id; session.permanent=True; return redirect(url_for('dashboard'))
    @app.post('/logout')
    def logout(): session.clear(); return redirect(url_for('login'))
    @app.get('/')
    def dashboard():
        today=date.today(); start=datetime.combine(today,datetime.min.time()); end=start+timedelta(days=1)
        stats={'patients':Patient.query.count(),'doctors':Doctor.query.count(),'today':Appointment.query.filter(Appointment.starts_at>=start,Appointment.starts_at<end).count(),'unpaid':db.session.query(func.coalesce(func.sum(Invoice.amount),0)).filter_by(status='Unpaid').scalar(),'admitted':Admission.query.filter_by(status='Admitted').count()}
        return render_template('dashboard.html',stats=stats,appointments=Appointment.query.order_by(Appointment.starts_at.desc()).limit(6).all())
    @app.get('/patients')
    def patients():
        q=request.args.get('q','').strip(); query=Patient.query.filter(Patient.full_name.ilike(f'%{q}%')) if q else Patient.query
        return render_template('patients.html',patients=query.order_by(Patient.full_name).all(),search=q)
    @app.post('/patients/add')
    def add_patient():
        try: dob=date.fromisoformat(request.form.get('date_of_birth',''))
        except ValueError: dob=None
        name=request.form.get('full_name','').strip(); gender=request.form.get('gender','').strip(); phone=request.form.get('phone','').strip()
        if not name or not phone or not dob or dob>date.today() or gender not in {'Female','Male','Non-binary','Prefer not to say'}: flash('Enter valid patient details.','error'); return redirect(url_for('patients'))
        db.session.add(Patient(full_name=name,date_of_birth=dob,gender=gender,phone=phone,email=request.form.get('email','').strip() or None,blood_group=request.form.get('blood_group','').strip() or None,address=request.form.get('address','').strip() or None)); db.session.commit(); flash('Patient registered.','success'); return redirect(url_for('patients'))
    @app.get('/doctors')
    def doctors(): return render_template('doctors.html',doctors=Doctor.query.order_by(Doctor.full_name).all())
    @app.post('/doctors/add')
    def add_doctor():
        v={k:request.form.get(k,'').strip() for k in ('full_name','specialty','phone','email','room')}
        if not v['full_name'] or not v['specialty'] or not v['phone']: flash('Name, specialty, and phone are required.','error'); return redirect(url_for('doctors'))
        db.session.add(Doctor(**v)); db.session.commit(); flash('Doctor added.','success'); return redirect(url_for('doctors'))
    @app.get('/appointments')
    def appointments(): return render_template('appointments.html',appointments=Appointment.query.order_by(Appointment.starts_at.desc()).all(),patients=Patient.query.order_by(Patient.full_name).all(),doctors=Doctor.query.order_by(Doctor.full_name).all(),statuses=['Scheduled','Checked in','Completed','Cancelled'])
    @app.post('/appointments/add')
    def add_appointment():
        try: pid,did=int(request.form['patient_id']),int(request.form['doctor_id']); when=datetime.fromisoformat(request.form['starts_at'])
        except (ValueError,KeyError): flash('Enter valid appointment details.','error'); return redirect(url_for('appointments'))
        reason=request.form.get('reason','').strip()
        if not db.session.get(Patient,pid) or not db.session.get(Doctor,did) or not reason: flash('Patient, doctor, and reason are required.','error'); return redirect(url_for('appointments'))
        db.session.add(Appointment(patient_id=pid,doctor_id=did,starts_at=when,reason=reason)); db.session.commit(); flash('Appointment scheduled.','success'); return redirect(url_for('appointments'))
    @app.post('/appointments/<int:id>/status')
    def update_appointment(id):
        a=db.get_or_404(Appointment,id); s=request.form.get('status','')
        if s in {'Scheduled','Checked in','Completed','Cancelled'}: a.status=s; db.session.commit(); flash('Appointment updated.','success')
        return redirect(url_for('appointments'))
    @app.get('/billing')
    def billing(): return render_template('billing.html',invoices=Invoice.query.order_by(Invoice.id.desc()).all(),patients=Patient.query.order_by(Patient.full_name).all())
    @app.post('/billing/add')
    def add_invoice():
        try: pid=int(request.form['patient_id']); amount=Decimal(request.form['amount'])
        except (ValueError,InvalidOperation,KeyError): flash('Enter valid invoice details.','error'); return redirect(url_for('billing'))
        desc=request.form.get('description','').strip()
        if not db.session.get(Patient,pid) or not desc or amount<=0: flash('Patient, description, and positive amount are required.','error'); return redirect(url_for('billing'))
        db.session.add(Invoice(patient_id=pid,description=desc,amount=amount)); db.session.commit(); flash('Invoice created.','success'); return redirect(url_for('billing'))
    @app.post('/billing/<int:id>/paid')
    def mark_paid(id): i=db.get_or_404(Invoice,id); i.status='Paid'; db.session.commit(); return redirect(url_for('billing'))
    @app.get('/admissions')
    def admissions():
        occupied={a.bed_id for a in Admission.query.filter_by(status='Admitted')}; beds=Bed.query.order_by(Bed.ward_id,Bed.bed_number).all()
        return render_template('admissions.html',admissions=Admission.query.order_by(Admission.admitted_at.desc()).all(),patients=Patient.query.order_by(Patient.full_name).all(),beds=[b for b in beds if b.id not in occupied],wards=Ward.query.all())
    @app.post('/admissions/add')
    def add_admission():
        try: pid,bid=int(request.form['patient_id']),int(request.form['bed_id'])
        except (ValueError,KeyError): flash('Select a patient and bed.','error'); return redirect(url_for('admissions'))
        if Admission.query.filter_by(bed_id=bid,status='Admitted').first() or not request.form.get('reason','').strip(): flash('Bed is unavailable or reason is missing.','error'); return redirect(url_for('admissions'))
        db.session.add(Admission(patient_id=pid,bed_id=bid,reason=request.form['reason'].strip())); db.session.commit(); flash('Patient admitted.','success'); return redirect(url_for('admissions'))
    @app.post('/admissions/<int:id>/discharge')
    def discharge_admission(id): a=db.get_or_404(Admission,id); a.status='Discharged'; a.discharged_at=datetime.utcnow(); db.session.commit(); flash('Patient discharged.','success'); return redirect(url_for('admissions'))
    @app.get('/records')
    def records(): return render_template('records.html',records=ClinicalRecord.query.order_by(ClinicalRecord.visit_date.desc()).all(),patients=Patient.query.all(),doctors=Doctor.query.all())
    @app.post('/records/add')
    def add_record():
        try: pid,did=int(request.form['patient_id']),int(request.form['doctor_id'])
        except (ValueError,KeyError): flash('Select patient and doctor.','error'); return redirect(url_for('records'))
        r=ClinicalRecord(patient_id=pid,doctor_id=did,record_type=request.form.get('record_type','Consultation'),diagnosis=request.form.get('diagnosis','').strip(),notes=request.form.get('notes','').strip())
        if not r.diagnosis or not r.notes: flash('Diagnosis and notes are required.','error'); return redirect(url_for('records'))
        if request.form.get('medication','').strip(): r.prescriptions.append(Prescription(medication=request.form['medication'].strip(),dosage=request.form.get('dosage','').strip() or 'As directed',instructions=request.form.get('instructions','').strip() or 'As directed'))
        db.session.add(r); db.session.commit(); flash('Clinical record saved.','success'); return redirect(url_for('records'))
    @app.get('/staff')
    def staff(): return render_template('staff.html',users=User.query.order_by(User.username).all(),roles=ROLES)
    @app.post('/staff/add')
    def add_staff():
        u=request.form.get('username','').strip().lower(); p=request.form.get('password',''); role=request.form.get('role','')
        if len(u)<3 or len(p)<12 or role not in ROLES: flash('Use a valid username, 12+ character password, and role.','error'); return redirect(url_for('staff'))
        if User.query.filter_by(username=u).first(): flash('Username already exists.','error'); return redirect(url_for('staff'))
        user=User(username=u,role=role); user.set_password(p); db.session.add(user); db.session.commit(); flash('Staff account created.','success'); return redirect(url_for('staff'))
    @app.post('/staff/<int:id>/toggle')
    def toggle_staff(id): u=db.get_or_404(User,id); u.active=not u.active; db.session.commit(); return redirect(url_for('staff'))
    @app.cli.command('init-db')
    def init_db(): db.create_all(); click.echo('Database tables created.')
    @app.cli.command('create-admin')
    def create_admin():
        db.create_all(); username=click.prompt('Admin username').strip().lower(); password=click.prompt('Password (12+ characters)',hide_input=True,confirmation_prompt=True)
        if len(password)<12: raise click.ClickException('Password must be at least 12 characters.')
        u=User(username=username,role='admin'); u.set_password(password); db.session.add(u); db.session.commit(); click.echo('Administrator created.')
    return app
app=create_app()
