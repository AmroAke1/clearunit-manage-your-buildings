from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, oauth
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('resident.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('resident.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.role == 'manager':
                return redirect(url_for('manager.dashboard'))
            return redirect(url_for('resident.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        if not all([full_name, email, password, role]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        if role not in ('manager', 'resident'):
            flash('Invalid role selected.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('auth/register.html')
        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token['userinfo']
    google_id = userinfo['sub']
    email = userinfo['email'].lower()
    full_name = userinfo.get('name', email)

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user:
            user.google_id = google_id
            db.session.commit()

    if user:
        login_user(user)
        flash(f'Welcome back, {user.full_name}!', 'success')
        if user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('resident.dashboard'))

    session['google_user'] = {'google_id': google_id, 'email': email, 'full_name': full_name}
    return redirect(url_for('auth.google_complete'))


@auth_bp.route('/register/google/complete', methods=['GET', 'POST'])
def google_complete():
    google_user = session.get('google_user')
    if not google_user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        role = request.form.get('role', '')
        if role not in ('manager', 'resident'):
            flash('Please select a valid role.', 'danger')
            return render_template('auth/google_complete.html', google_user=google_user)
        user = User(
            full_name=google_user['full_name'],
            email=google_user['email'],
            google_id=google_user['google_id'],
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        session.pop('google_user', None)
        login_user(user)
        flash(f'Welcome to ClearUnit, {user.full_name}!', 'success')
        if user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        return redirect(url_for('resident.dashboard'))

    return render_template('auth/google_complete.html', google_user=google_user)