from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from app import db
from app.models import Building, Unit, Dues, Payment, Announcement, MaintenanceRequest, User

manager_bp = Blueprint('manager', __name__)


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'manager':
            flash('Access denied. Manager privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@manager_bp.route('/dashboard')
@login_required
@manager_required
def dashboard():
    buildings = Building.query.filter_by(manager_id=current_user.id).all()
    stats = []
    for b in buildings:
        total_units = len(b.units)
        pending_payments = sum(1 for u in b.units for p in u.payments if p.status == 'pending')
        open_maintenance = sum(1 for u in b.units for r in u.maintenance_requests if r.status in ('pending', 'in_progress'))
        total_balance = sum(u.current_balance for u in b.units)
        stats.append({
            'building': b,
            'total_units': total_units,
            'pending_payments': pending_payments,
            'open_maintenance': open_maintenance,
            'total_balance': total_balance,
        })
    return render_template('manager/dashboard.html', stats=stats)


@manager_bp.route('/buildings')
@login_required
@manager_required
def buildings():
    buildings_list = Building.query.filter_by(manager_id=current_user.id).all()
    return render_template('manager/buildings.html', buildings=buildings_list)


@manager_bp.route('/buildings/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_building():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        if not name or not address:
            flash('Name and address are required.', 'danger')
            return render_template('manager/add_building.html', edit=False)
        building = Building(name=name, address=address, manager_id=current_user.id)
        db.session.add(building)
        db.session.commit()
        flash(f'Building "{name}" created successfully.', 'success')
        return redirect(url_for('manager.buildings'))
    return render_template('manager/add_building.html', edit=False)


@manager_bp.route('/buildings/<int:building_id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_building(building_id):
    building = Building.query.filter_by(id=building_id, manager_id=current_user.id).first_or_404()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        if not name or not address:
            flash('Name and address are required.', 'danger')
            return render_template('manager/add_building.html', building=building, edit=True)
        building.name = name
        building.address = address
        db.session.commit()
        flash('Building updated successfully.', 'success')
        return redirect(url_for('manager.buildings'))
    return render_template('manager/add_building.html', building=building, edit=True)


@manager_bp.route('/buildings/<int:building_id>/delete', methods=['POST'])
@login_required
@manager_required
def delete_building(building_id):
    building = Building.query.filter_by(id=building_id, manager_id=current_user.id).first_or_404()
    name = building.name
    db.session.delete(building)
    db.session.commit()
    flash(f'Building "{name}" deleted.', 'success')
    return redirect(url_for('manager.buildings'))


@manager_bp.route('/buildings/<int:building_id>')
@login_required
@manager_required
def building_detail(building_id):
    building = Building.query.filter_by(id=building_id, manager_id=current_user.id).first_or_404()
    residents = User.query.filter_by(role='resident').all()
    return render_template('manager/building_detail.html', building=building, residents=residents)


@manager_bp.route('/buildings/<int:building_id>/units/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_unit(building_id):
    building = Building.query.filter_by(id=building_id, manager_id=current_user.id).first_or_404()
    residents = User.query.filter_by(role='resident').all()
    if request.method == 'POST':
        unit_number = request.form.get('unit_number', '').strip()
        floor_str = request.form.get('floor', '').strip()
        resident_id_str = request.form.get('resident_id', '').strip()
        if not unit_number or not floor_str:
            flash('Unit number and floor are required.', 'danger')
            return render_template('manager/add_unit.html', building=building, residents=residents)
        try:
            floor = int(floor_str)
        except ValueError:
            flash('Floor must be a valid number.', 'danger')
            return render_template('manager/add_unit.html', building=building, residents=residents)
        resident_id = None
        if resident_id_str:
            try:
                resident_id = int(resident_id_str)
            except ValueError:
                resident_id = None
        unit = Unit(unit_number=unit_number, floor=floor, building_id=building_id, resident_id=resident_id)
        db.session.add(unit)
        db.session.commit()
        flash(f'Unit {unit_number} added successfully.', 'success')
        return redirect(url_for('manager.building_detail', building_id=building_id))
    return render_template('manager/add_unit.html', building=building, residents=residents)


@manager_bp.route('/units/<int:unit_id>/assign', methods=['POST'])
@login_required
@manager_required
def assign_resident(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=current_user.id).first_or_404()
    resident_id_str = request.form.get('resident_id', '').strip()
    resident_id = None
    if resident_id_str:
        try:
            resident_id = int(resident_id_str)
        except ValueError:
            resident_id = None
    unit.resident_id = resident_id
    db.session.commit()
    flash('Resident assignment updated.', 'success')
    return redirect(url_for('manager.building_detail', building_id=unit.building_id))


@manager_bp.route('/dues')
@login_required
@manager_required
def dues():
    buildings = Building.query.filter_by(manager_id=current_user.id).all()
    all_dues = []
    for b in buildings:
        for u in b.units:
            for d in u.dues:
                all_dues.append({'due': d, 'unit': u, 'building': b})
    all_dues.sort(key=lambda x: x['due'].created_at, reverse=True)
    return render_template('manager/dues.html', all_dues=all_dues)


@manager_bp.route('/dues/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create_dues():
    buildings = Building.query.filter_by(manager_id=current_user.id).all()
    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        month = request.form.get('month', '').strip()
        building_id_str = request.form.get('building_id', '').strip()
        if not amount_str or not month or not building_id_str:
            flash('All fields are required.', 'danger')
            return render_template('manager/create_dues.html', buildings=buildings)
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Amount must be a positive number.', 'danger')
            return render_template('manager/create_dues.html', buildings=buildings)
        if building_id_str == 'all':
            target_buildings = buildings
        else:
            try:
                bid = int(building_id_str)
                b = Building.query.filter_by(id=bid, manager_id=current_user.id).first()
                if not b:
                    flash('Building not found.', 'danger')
                    return render_template('manager/create_dues.html', buildings=buildings)
                target_buildings = [b]
            except ValueError:
                flash('Invalid building selection.', 'danger')
                return render_template('manager/create_dues.html', buildings=buildings)
        count = 0
        for b in target_buildings:
            for u in b.units:
                due = Dues(amount=amount, month=month, unit_id=u.id)
                db.session.add(due)
                u.current_balance += amount
                count += 1
        db.session.commit()
        flash(f'Dues of ${amount:.2f} created for {count} unit(s) for {month}.', 'success')
        return redirect(url_for('manager.dues'))
    return render_template('manager/create_dues.html', buildings=buildings)


@manager_bp.route('/payments')
@login_required
@manager_required
def payments():
    buildings = Building.query.filter_by(manager_id=current_user.id).all()
    all_payments = []
    for b in buildings:
        for u in b.units:
            for p in u.payments:
                all_payments.append({'payment': p, 'unit': u, 'building': b})
    all_payments.sort(key=lambda x: x['payment'].payment_date, reverse=True)
    return render_template('manager/payments.html', all_payments=all_payments)


@manager_bp.route('/payments/<int:payment_id>/confirm', methods=['POST'])
@login_required
@manager_required
def confirm_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    unit = Unit.query.get_or_404(payment.unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=current_user.id).first_or_404()
    if payment.status != 'pending':
        flash('Only pending payments can be confirmed.', 'warning')
        return redirect(url_for('manager.payments'))
    payment.status = 'confirmed'
    unit.current_balance -= payment.amount
    db.session.commit()
    flash('Payment confirmed successfully.', 'success')
    return redirect(url_for('manager.payments'))


@manager_bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
@login_required
@manager_required
def reject_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    unit = Unit.query.get_or_404(payment.unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=current_user.id).first_or_404()
    if payment.status != 'pending':
        flash('Only pending payments can be rejected.', 'warning')
        return redirect(url_for('manager.payments'))
    payment.status = 'rejected'
    db.session.commit()
    flash('Payment rejected.', 'success')
    return redirect(url_for('manager.payments'))


@manager_bp.route('/announcements', methods=['GET', 'POST'])
@login_required
@manager_required
def announcements():
    buildings = Building.query.filter_by(manager_id=current_user.id).all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        building_id_str = request.form.get('building_id', '').strip()
        if not title or not content or not building_id_str:
            flash('All fields are required.', 'danger')
        elif building_id_str == 'all':
            for b in buildings:
                ann = Announcement(title=title, content=content, building_id=b.id, manager_id=current_user.id)
                db.session.add(ann)
            db.session.commit()
            flash('Announcement posted to all buildings.', 'success')
        else:
            try:
                bid = int(building_id_str)
                b = Building.query.filter_by(id=bid, manager_id=current_user.id).first()
                if not b:
                    flash('Building not found.', 'danger')
                else:
                    ann = Announcement(title=title, content=content, building_id=b.id, manager_id=current_user.id)
                    db.session.add(ann)
                    db.session.commit()
                    flash('Announcement posted successfully.', 'success')
            except ValueError:
                flash('Invalid building selection.', 'danger')
        return redirect(url_for('manager.announcements'))
    all_announcements = []
    for b in buildings:
        for ann in b.announcements:
            all_announcements.append({'announcement': ann, 'building': b})
    all_announcements.sort(key=lambda x: x['announcement'].created_at, reverse=True)
    return render_template('manager/announcements.html', all_announcements=all_announcements, buildings=buildings)


@manager_bp.route('/maintenance')
@login_required
@manager_required
def maintenance():
    buildings = Building.query.filter_by(manager_id=current_user.id).all()
    all_requests = []
    for b in buildings:
        for u in b.units:
            for r in u.maintenance_requests:
                all_requests.append({'request': r, 'unit': u, 'building': b})
    all_requests.sort(key=lambda x: x['request'].created_at, reverse=True)
    return render_template('manager/maintenance.html', all_requests=all_requests)


@manager_bp.route('/maintenance/<int:request_id>/update', methods=['POST'])
@login_required
@manager_required
def update_maintenance(request_id):
    req = MaintenanceRequest.query.get_or_404(request_id)
    unit = Unit.query.get_or_404(req.unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=current_user.id).first_or_404()
    new_status = request.form.get('status', '').strip()
    valid_transitions = {'pending': 'in_progress', 'in_progress': 'resolved'}
    if req.status not in valid_transitions or new_status != valid_transitions[req.status]:
        flash('Invalid status transition.', 'warning')
        return redirect(url_for('manager.maintenance'))
    req.status = new_status
    if new_status == 'resolved':
        req.resolved_at = datetime.utcnow()
    db.session.commit()
    flash(f'Request updated to "{new_status.replace("_", " ")}".', 'success')
    return redirect(url_for('manager.maintenance'))