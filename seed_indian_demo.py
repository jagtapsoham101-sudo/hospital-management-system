"""Idempotently fill demo tables with fictional Indian sample entries.

No existing rows are deleted. Run via:
  .venv\\Scripts\\python.exe -m flask --app complete_app:app seed-indian-demo
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from app import (Admission, Appointment, Bed, ClinicalRecord, Doctor, Invoice,
                 Patient, Prescription, User, Ward, app, db)

PATIENT_DATA = [
    ('Aarav Sharma', date(1991, 4, 12), 'Male', '+91 98765 10001', 'O+'),
    ('Ananya Patel', date(1987, 9, 3), 'Female', '+91 98765 10002', 'A+'),
    ('Vihaan Reddy', date(2000, 1, 25), 'Male', '+91 98765 10003', 'B+'),
    ('Ishita Iyer', date(1978, 6, 18), 'Female', '+91 98765 10004', 'AB+'),
    ('Arjun Mehta', date(1968, 5, 30), 'Male', '+91 98765 10005', 'O-'),
    ('Kavya Nair', date(1998, 10, 17), 'Female', '+91 98765 10006', 'A-'),
]
DOCTOR_DATA = [
    ('Dr. Priya Menon', 'Cardiology', '+91 98765 20001', '201'),
    ('Dr. Rahul Verma', 'Pediatrics', '+91 98765 20002', '118'),
    ('Dr. Neha Kulkarni', 'Neurology', '+91 98765 20003', '310'),
    ('Dr. Vikram Rao', 'Family Medicine', '+91 98765 20004', '105'),
]


def seed():
    with app.app_context():
        db.create_all()
        users = [
            ('admin', 'admin'), ('dr.priya', 'clinician'),
            ('reception', 'reception'), ('billing', 'billing'),
        ]
        for username, role in users:
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(username=username, role=role)
                user.set_password('CarePointDemo2026!')
                db.session.add(user)
        db.session.flush()

        patients = {}
        for name, dob, gender, phone, blood in PATIENT_DATA:
            patient = Patient.query.filter_by(full_name=name).first()
            if patient is None:
                patient = Patient(full_name=name, date_of_birth=dob, gender=gender,
                    phone=phone, blood_group=blood,
                    email=name.lower().replace(' ', '.') + '@example.test',
                    address='Fictional demo address, India')
                db.session.add(patient)
            patients[name] = patient

        doctors = {}
        for name, specialty, phone, room in DOCTOR_DATA:
            doctor = Doctor.query.filter_by(full_name=name).first()
            if doctor is None:
                doctor = Doctor(full_name=name, specialty=specialty, phone=phone,
                    email=name.lower().replace(' ', '.') + '@example.test', room=room)
                db.session.add(doctor)
            doctors[name] = doctor
        db.session.flush()

        visits = [
            ('Aarav Sharma', 'Dr. Priya Menon', 'Cardiology follow-up'),
            ('Ananya Patel', 'Dr. Rahul Verma', 'Annual wellness visit'),
            ('Vihaan Reddy', 'Dr. Neha Kulkarni', 'Neurology consultation'),
            ('Ishita Iyer', 'Dr. Vikram Rao', 'Family medicine review'),
            ('Arjun Mehta', 'Dr. Priya Menon', 'Heart health review'),
            ('Kavya Nair', 'Dr. Rahul Verma', 'General consultation'),
        ]
        now = datetime.now().replace(second=0, microsecond=0)
        for index, (patient_name, doctor_name, reason) in enumerate(visits):
            patient = patients[patient_name]
            if not Appointment.query.filter_by(patient_id=patient.id, reason=reason).first():
                db.session.add(Appointment(patient=patient, doctor=doctors[doctor_name],
                    starts_at=now + timedelta(days=index), reason=reason,
                    status='Completed' if index == 0 else 'Scheduled'))
            description = reason + ' — sample invoice'
            if not Invoice.query.filter_by(patient_id=patient.id, description=description).first():
                db.session.add(Invoice(patient=patient, description=description,
                    amount=Decimal(750 + index * 250), status='Paid' if index % 2 else 'Unpaid'))

        ward = Ward.query.filter_by(name='General Ward — Demo').first()
        if ward is None:
            ward = Ward(name='General Ward — Demo'); db.session.add(ward); db.session.flush()
        for number in range(1, 7):
            bed_number = f'G-{number:02d}'
            if not Bed.query.filter_by(ward_id=ward.id, bed_number=bed_number).first():
                db.session.add(Bed(ward=ward, bed_number=bed_number, bed_type='General'))
        db.session.flush()
        bed = Bed.query.filter_by(ward_id=ward.id, bed_number='G-01').first()
        patient = patients['Arjun Mehta']
        if not Admission.query.filter_by(patient_id=patient.id, reason='Fictional observation admission').first():
            db.session.add(Admission(patient=patient, bed=bed, reason='Fictional observation admission'))

        patient = patients['Aarav Sharma']
        record = ClinicalRecord.query.filter_by(patient_id=patient.id, diagnosis='Demo wellness review').first()
        if record is None:
            record = ClinicalRecord(patient=patient, doctor=doctors['Dr. Vikram Rao'],
                record_type='Consultation', diagnosis='Demo wellness review',
                notes='Fictional training note only. Not medical advice.')
            record.prescriptions.append(Prescription(medication='Sample medicine', dosage='As directed',
                instructions='Fictional example only; not a real prescription.'))
            db.session.add(record)
        db.session.commit()

if __name__ == '__main__':
    seed()
    print('Seeded/verified demo records; existing rows preserved.')
