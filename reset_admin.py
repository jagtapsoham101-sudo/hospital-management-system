"""Create or reset a local demo administrator login.

Run from the project directory with the project's venv:
    .\\.venv\\Scripts\\python.exe reset_admin.py

Do not use this utility as a production password-reset workflow.
"""
from getpass import getpass

from app import User, app, db


def main():
    with app.app_context():
        db.create_all()
        username = input('Admin username [admin]: ').strip().lower() or 'admin'
        if len(username) < 3:
            raise SystemExit('Username must be at least 3 characters.')

        password = getpass('New password (at least 12 characters): ')
        confirm = getpass('Confirm new password: ')
        if len(password) < 12:
            raise SystemExit('Password must be at least 12 characters.')
        if password != confirm:
            raise SystemExit('Passwords did not match; no changes were made.')

        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            db.session.add(user)
        user.role = 'admin'
        user.active = True
        user.set_password(password)
        db.session.commit()
        print(f'Admin login created/reset for username: {username}')
        print('Use the password you just entered at http://127.0.0.1:5000/login')


if __name__ == '__main__':
    main()
