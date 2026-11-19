"""Extended local-demo entry point with admin-only CRUD for related tables.

Run the project using `flask --app complete_app:app ...`.
"""
from datetime import datetime

from flask import flash, redirect, url_for

from app import Admission, Bed, ClinicalRecord, Doctor, Invoice, Patient, Prescription, User, Ward, app, db


def require_admin():
    from flask import g
    if not getattr(g, 'user', None) or g.user.role != 'admin':
        flash('Administrator access is required.', 'error')
        return False
    return True


def register_route(rule, endpoint, view, methods=('POST',)):
    app.add_url_rule(rule, endpoint, view, methods=list(methods))


def delete_bed(bed_id):
    if not require_admin(): return redirect(url_for('admissions'))
    bed = db.get_or_404(Bed, bed_id)
    if Admission.query.filter_by(bed_id=bed.id, status='Admitted').first():
        flash('Discharge the patient before deleting this occupied bed.', 'error')
    else:
        db.session.delete(bed); db.session.commit(); flash('Bed deleted.', 'success')
    return redirect(url_for('admissions'))


def delete_ward(ward_id):
    if not require_admin(): return redirect(url_for('admissions'))
    ward = db.get_or_404(Ward, ward_id)
    if any(Admission.query.filter_by(bed_id=bed.id, status='Admitted').first() for bed in ward.beds):
        flash('Discharge patients before deleting this ward.', 'error')
    else:
        db.session.delete(ward); db.session.commit(); flash('Ward and its beds deleted.', 'success')
    return redirect(url_for('admissions'))


def add_staff():
    from flask import request
    if not require_admin(): return redirect(url_for('dashboard'))
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    role = request.form.get('role', '')
    if len(username) < 3 or len(password) < 12 or role not in {'admin', 'clinician', 'reception', 'billing'}:
        flash('Use a username of 3+ characters, password of 12+ characters, and a valid role.', 'error')
    elif User.query.filter_by(username=username).first():
        flash('That username already exists.', 'error')
    else:
        user = User(username=username, role=role); user.set_password(password)
        db.session.add(user); db.session.commit(); flash('Staff account added.', 'success')
    return redirect(url_for('staff'))


def delete_staff(user_id):
    from flask import g
    if not require_admin(): return redirect(url_for('dashboard'))
    user = db.get_or_404(User, user_id)
    if user.id == g.user.id:
        flash('You cannot delete the account currently signed in.', 'error')
    else:
        db.session.delete(user); db.session.commit(); flash('Staff account deleted.', 'success')
    return redirect(url_for('staff'))


def delete_prescription(prescription_id):
    if not require_admin(): return redirect(url_for('records'))
    db.session.delete(db.get_or_404(Prescription, prescription_id)); db.session.commit()
    flash('Prescription deleted.', 'success')
    return redirect(url_for('records'))


register_route('/wards/<int:ward_id>/delete', 'delete_ward', delete_ward)
register_route('/beds/<int:bed_id>/delete', 'delete_bed', delete_bed)
register_route('/staff/add', 'add_staff', add_staff)
register_route('/staff/<int:user_id>/delete', 'delete_staff', delete_staff)
register_route('/prescriptions/<int:prescription_id>/delete', 'delete_prescription', delete_prescription)


@app.cli.command('seed-indian-demo')
def seed_indian_demo_command():
    """Ensure demo rows exist; this is additive and never clears the database."""
    from click import echo
    from seed_indian_demo import seed
    seed()
    echo('Fictional Indian demo records are ready. Existing data was preserved.')


if __name__ == '__main__':
    app.run(debug=True)
