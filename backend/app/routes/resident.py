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


def _get_unit(units, unit_id):
    if unit_id:
        return next((u for u in units if u.id == unit_id), units[0])
    return units[0]


@resident_bp.route('/dashboard')
@login_required
@resident_required
def dashboard():
    units = Unit.query.filter_by(resident_id=current_user.id).all()
    return render_template('resident/dashboard.html', units=units)


@resident_bp.route('/dues')
@login_required
@resident_required
def dues():
    units = Unit.query.filter_by(resident_id=current_user.id).all()
    if not units:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    unit_id = request.args.get('unit_id', type=int)
    unit = _get_unit(units, unit_id)
    dues_list = Dues.query.filter_by(unit_id=unit.id).order_by(Dues.created_at.desc()).all()
    return render_template('resident/dues.html', dues_list=dues_list, unit=unit, units=units)


@resident_bp.route('/payments')
@login_required
@resident_required
def payments():
    units = Unit.query.filter_by(resident_id=current_user.id).all()
    if not units:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    unit_id = request.args.get('unit_id', type=int)
    unit = _get_unit(units, unit_id)
    payments_list = Payment.query.filter_by(unit_id=unit.id).order_by(Payment.payment_date.desc()).all()
    return render_template('resident/payments.html', payments_list=payments_list, unit=unit, units=units)


@resident_bp.route('/payments/notify', methods=['GET', 'POST'])
@login_required
@resident_required
def notify_payment():
    units = Unit.query.filter_by(resident_id=current_user.id).all()
    if not units:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    unit_id = request.args.get('unit_id', type=int) or request.form.get('unit_id', type=int)
    unit = _get_unit(units, unit_id)
    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        month = request.form.get('month', '').strip()
        if not amount_str or not month:
            flash('Amount and month are required.', 'danger')
            return render_template('resident/notify_payment.html', unit=unit, units=units)
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'danger')
            return render_template('resident/notify_payment.html', unit=unit, units=units)
        payment = Payment(amount=amount, month=month, unit_id=unit.id, payment_date=date.today())
        db.session.add(payment)
        db.session.commit()
        flash('Payment notification sent to your manager.', 'success')
        return redirect(url_for('resident.payments', unit_id=unit.id))
    return render_template('resident/notify_payment.html', unit=unit, units=units)


@resident_bp.route('/maintenance', methods=['GET', 'POST'])
@login_required
@resident_required
def maintenance():
    units = Unit.query.filter_by(resident_id=current_user.id).all()
    if not units:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    unit_id = request.args.get('unit_id', type=int) or request.form.get('unit_id', type=int)
    unit = _get_unit(units, unit_id)
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash('Description is required.', 'danger')
        else:
            req = MaintenanceRequest(description=description, unit_id=unit.id)
            db.session.add(req)
            db.session.commit()
            flash('Maintenance request submitted successfully.', 'success')
        return redirect(url_for('resident.maintenance', unit_id=unit.id))
    requests_list = MaintenanceRequest.query.filter_by(unit_id=unit.id).order_by(MaintenanceRequest.created_at.desc()).all()
    return render_template('resident/maintenance.html', requests_list=requests_list, unit=unit, units=units)


@resident_bp.route('/announcements')
@login_required
@resident_required
def announcements():
    units = Unit.query.filter_by(resident_id=current_user.id).all()
    if not units:
        flash('You are not assigned to any unit yet.', 'warning')
        return redirect(url_for('resident.dashboard'))
    building_ids = list({u.building_id for u in units})
    announcements_list = Announcement.query.filter(
        Announcement.building_id.in_(building_ids)
    ).order_by(Announcement.created_at.desc()).all()
    return render_template('resident/announcements.html', announcements_list=announcements_list, units=units)
