"""Idempotently add fictional sample data for a local project demonstration.

Run with: .venv\\Scripts\\python.exe seed_demo.py
This only adds missing sample rows; it does not erase existing data.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from app import Admission, Appointment, Bed, ClinicalRecord, Doctor, Invoice, Patient, Prescription, Ward, app, db

PATIENTS = [
    ('Jordan Lee', date(1989, 3, 14), 'Female', '+1 555 0141', 'A+'),
    ('Riley Morgan', date(1975, 11, 2), 'Male', '+1 555 0142', 'O+'),
    ('Casey Patel', date(2001, 7, 23), 'Non-binary', '+1 555 0143', 'B+'),
    ('Taylor Brooks', date(1994, 1, 9), 'Female', '+1 555 0144', 'AB+'),
    ('Alex Rivera', date(1968, 5, 30), 'Male', '+1 555 0145', 'O-'),
    ('Sam Kim', date(1998, 10, 17), 'Prefer not to say', '+1 555 0146', 'A-'),
]
DOCTORS = [
    ('Morgan Chen', 'Cardiology', '+1 555 0241', '201'),
    ('Jamie Okafor', 'Pediatrics', '+1 555 0242', '118'),
    ('Avery Singh', 'Neurology', '+1 555 0243', '310'),
    ('Drew Martinez', 'Family Medicine', '+1 555 0244', '105'),
]

with app.app_context():
    db.create_all()
    patients = {}
    for name, dob, gender, phone, blood in PATIENTS:
        obj = Patient.query.filter_by(full_name=name).first()
        if obj is None:
            obj = Patient(full_name=name, date_of_birth=dob, gender=gender, phone=phone,
                          email=name.lower().replace(' ', '.') + '@example.test', blood_group=blood,
                          address='Demo address')
            db.session.add(obj)
        patients[name] = obj

    doctors = {}
    for name, specialty, phone, room in DOCTORS:
        obj = Doctor.query.filter_by(full_name=name).first()
        if obj is None:
            obj = Doctor(full_name=name, specialty=specialty, phone=phone,
                          email=name.lower().replace(' ', '.') + '@example.test', room=room)
            db.session.add(obj)
        doctors[name] = obj
    db.session.flush()

    visits = [
        ('Jordan Lee', 'Morgan Chen', 'Cardiology follow-up', 1),
        ('Riley Morgan', 'Jamie Okafor', 'Annual wellness visit', 2),
        ('Casey Patel', 'Avery Singh', 'Headache consultation', 3),
        ('Taylor Brooks', 'Drew Martinez', 'Primary care review', 4),
        ('Alex Rivera', 'Morgan Chen', 'Heart health review', 5),
        ('Sam Kim', 'Jamie Okafor', 'General consultation', 6),
    ]
    for patient_name, doctor_name, reason, offset in visits:
        if not Appointment.query.filter_by(patient_id=patients[patient_name].id, reason=reason).first():
            db.session.add(Appointment(patient=patients[patient_name], doctor=doctors[doctor_name],
                starts_at=datetime.now().replace(second=0, microsecond=0) + timedelta(days=offset), reason=reason))
        description = reason + ' consultation'
        if not Invoice.query.filter_by(patient_id=patients[patient_name].id, description=description).first():
            db.session.add(Invoice(patient=patients[patient_name], description=description,
                                   amount=Decimal(str(80 + offset * 15))))

    ward = Ward.query.filter_by(name='Demo General Ward').first()
    if ward is None:
        ward = Ward(name='Demo General Ward')
        db.session.add(ward)
        db.session.flush()
    for number in range(1, 7):
        if not Bed.query.filter_by(ward_id=ward.id, bed_number=f'D-{number:02d}').first():
            db.session.add(Bed(ward=ward, bed_number=f'D-{number:02d}', bed_type='General'))
    db.session.flush()
    first_bed = Bed.query.filter_by(ward_id=ward.id, bed_number='D-01').first()
    if first_bed and not Admission.query.filter_by(patient_id=patients['Alex Rivera'].id, status='Admitted').first():
        if not Admission.query.filter_by(bed_id=first_bed.id, status='Admitted').first():
            db.session.add(Admission(patient=patients['Alex Rivera'], bed=first_bed,
                                     reason='Fictional observation admission'))

    if not ClinicalRecord.query.filter_by(patient_id=patients['Jordan Lee'].id, diagnosis='Demo wellness review').first():
        record = ClinicalRecord(patient=patients['Jordan Lee'], doctor=doctors['Drew Martinez'],
            record_type='Consultation', diagnosis='Demo wellness review',
            notes='Fictional sample note for demonstrating record management.')
        record.prescriptions.append(Prescription(medication='Sample medication', dosage='As directed',
            instructions='Fictional example only; not medical advice.'))
        db.session.add(record)

    db.session.commit()
    print('Demo data is ready: 6 sample patients, 4 sample doctors, 6 appointments, invoices, beds, an admission, and a clinical record.')
    print('Existing records were preserved. Run this script again safely to add any missing demo rows.')
