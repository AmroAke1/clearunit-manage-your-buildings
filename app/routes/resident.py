from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import date
from app import db
from app.models import Unit, Dues, Payment, Announcement, MaintenanceRequest

resident_bp = Blueprint('resident', __name__)


def resident_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'resident':
            flash('Access denied. Resident privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@resident_bp.route('/dashboard')
@login_required
@resident_required
def dashboard():
    unit = Unit.query.filter_by(resident_id=current_user.id).first()
    return render_template('resident/dashboard.html', unit=unit)


@resident_bp.route('/dues')
@login_required
@resident_required
def dues():
    unit = Unit.query.filter_by(resident_id=current_user.id).first()
    if not unit:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    dues_list = Dues.query.filter_by(unit_id=unit.id).order_by(Dues.created_at.desc()).all()
    return render_template('resident/dues.html', dues_list=dues_list, unit=unit)


@resident_bp.route('/payments')
@login_required
@resident_required
def payments():
    unit = Unit.query.filter_by(resident_id=current_user.id).first()
    if not unit:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    payments_list = Payment.query.filter_by(unit_id=unit.id).order_by(Payment.payment_date.desc()).all()
    return render_template('resident/payments.html', payments_list=payments_list, unit=unit)


@resident_bp.route('/payments/notify', methods=['GET', 'POST'])
@login_required
@resident_required
def notify_payment():
    unit = Unit.query.filter_by(resident_id=current_user.id).first()
    if not unit:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        month = request.form.get('month', '').strip()
        if not amount_str or not month:
            flash('Amount and month are required.', 'danger')
            return render_template('resident/notify_payment.html', unit=unit)
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'danger')
            return render_template('resident/notify_payment.html', unit=unit)
        payment = Payment(amount=amount, month=month, unit_id=unit.id, payment_date=date.today())
        db.session.add(payment)
        db.session.commit()
        flash('Payment notification sent to your manager.', 'success')
        return redirect(url_for('resident.payments'))
    return render_template('resident/notify_payment.html', unit=unit)


@resident_bp.route('/maintenance', methods=['GET', 'POST'])
@login_required
@resident_required
def maintenance():
    unit = Unit.query.filter_by(resident_id=current_user.id).first()
    if not unit:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash('Description is required.', 'danger')
        else:
            req = MaintenanceRequest(description=description, unit_id=unit.id)
            db.session.add(req)
            db.session.commit()
            flash('Maintenance request submitted successfully.', 'success')
        return redirect(url_for('resident.maintenance'))
    requests_list = MaintenanceRequest.query.filter_by(unit_id=unit.id).order_by(MaintenanceRequest.created_at.desc()).all()
    return render_template('resident/maintenance.html', requests_list=requests_list, unit=unit)


@resident_bp.route('/announcements')
@login_required
@resident_required
def announcements():
    unit = Unit.query.filter_by(resident_id=current_user.id).first()
    if not unit:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    announcements_list = Announcement.query.filter_by(building_id=unit.building_id).order_by(Announcement.created_at.desc()).all()
    return render_template('resident/announcements.html', announcements_list=announcements_list, unit=unit)


