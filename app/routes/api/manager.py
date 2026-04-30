from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models import Building, Unit, Dues, Payment, Announcement, MaintenanceRequest, User

api_manager_bp = Blueprint('api_manager', __name__)


def get_manager():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if user.role != 'manager':
        return None, jsonify({'error': 'Manager access required'}), 403
    return user, None, None


# Buildings
@api_manager_bp.route('/buildings', methods=['GET'])
@jwt_required()
def get_buildings():
    manager, err, code = get_manager()
    if err:
        return err, code
    buildings = Building.query.filter_by(manager_id=manager.id).all()
    return jsonify([{'id': b.id, 'name': b.name, 'address': b.address} for b in buildings]), 200


@api_manager_bp.route('/buildings', methods=['POST'])
@jwt_required()
def create_building():
    manager, err, code = get_manager()
    if err:
        return err, code
    data = request.get_json()
    name = data.get('name', '').strip()
    address = data.get('address', '').strip()
    if not name or not address:
        return jsonify({'error': 'Name and address are required'}), 400
    building = Building(name=name, address=address, manager_id=manager.id)
    db.session.add(building)
    db.session.commit()
    return jsonify({'id': building.id, 'name': building.name, 'address': building.address}), 201


@api_manager_bp.route('/buildings/<int:building_id>', methods=['PUT'])
@jwt_required()
def update_building(building_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    building = Building.query.filter_by(id=building_id, manager_id=manager.id).first_or_404()
    data = request.get_json()
    building.name = data.get('name', building.name).strip()
    building.address = data.get('address', building.address).strip()
    db.session.commit()
    return jsonify({'id': building.id, 'name': building.name, 'address': building.address}), 200


@api_manager_bp.route('/buildings/<int:building_id>', methods=['DELETE'])
@jwt_required()
def delete_building(building_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    building = Building.query.filter_by(id=building_id, manager_id=manager.id).first_or_404()
    db.session.delete(building)
    db.session.commit()
    return jsonify({'message': 'Building deleted'}), 200


# Units
@api_manager_bp.route('/buildings/<int:building_id>/units', methods=['GET'])
@jwt_required()
def get_units(building_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    Building.query.filter_by(id=building_id, manager_id=manager.id).first_or_404()
    units = Unit.query.filter_by(building_id=building_id).all()
    return jsonify([{'id': u.id, 'unit_number': u.unit_number, 'floor': u.floor, 'current_balance': u.current_balance, 'resident_id': u.resident_id} for u in units]), 200


@api_manager_bp.route('/buildings/<int:building_id>/units', methods=['POST'])
@jwt_required()
def create_unit(building_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    Building.query.filter_by(id=building_id, manager_id=manager.id).first_or_404()
    data = request.get_json()
    unit_number = data.get('unit_number', '').strip()
    floor = data.get('floor')
    if not unit_number or floor is None:
        return jsonify({'error': 'unit_number and floor are required'}), 400
    unit = Unit(unit_number=unit_number, floor=int(floor), building_id=building_id, resident_id=data.get('resident_id'))
    db.session.add(unit)
    db.session.commit()
    return jsonify({'id': unit.id, 'unit_number': unit.unit_number, 'floor': unit.floor}), 201


# Dues
@api_manager_bp.route('/dues', methods=['GET'])
@jwt_required()
def get_dues():
    manager, err, code = get_manager()
    if err:
        return err, code
    buildings = Building.query.filter_by(manager_id=manager.id).all()
    result = []
    for b in buildings:
        for u in b.units:
            for d in u.dues:
                result.append({'id': d.id, 'amount': d.amount, 'month': d.month, 'unit_id': d.unit_id, 'building': b.name})
    return jsonify(result), 200


@api_manager_bp.route('/dues', methods=['POST'])
@jwt_required()
def create_dues():
    manager, err, code = get_manager()
    if err:
        return err, code
    data = request.get_json()
    amount = data.get('amount')
    month = data.get('month', '').strip()
    building_id = data.get('building_id')
    if not amount or not month:
        return jsonify({'error': 'amount and month are required'}), 400
    if building_id == 'all':
        buildings = Building.query.filter_by(manager_id=manager.id).all()
    else:
        b = Building.query.filter_by(id=building_id, manager_id=manager.id).first_or_404()
        buildings = [b]
    count = 0
    for b in buildings:
        for u in b.units:
            db.session.add(Dues(amount=float(amount), month=month, unit_id=u.id))
            u.current_balance += float(amount)
            count += 1
    db.session.commit()
    return jsonify({'message': f'Dues created for {count} unit(s)'}), 201


# Payments
@api_manager_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    manager, err, code = get_manager()
    if err:
        return err, code
    buildings = Building.query.filter_by(manager_id=manager.id).all()
    result = []
    for b in buildings:
        for u in b.units:
            for p in u.payments:
                result.append({'id': p.id, 'amount': p.amount, 'month': p.month, 'status': p.status, 'unit_id': p.unit_id, 'building': b.name})
    return jsonify(result), 200


@api_manager_bp.route('/payments/<int:payment_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_payment(payment_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    payment = Payment.query.get_or_404(payment_id)
    unit = Unit.query.get_or_404(payment.unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=manager.id).first_or_404()
    if payment.status != 'pending':
        return jsonify({'error': 'Only pending payments can be confirmed'}), 400
    payment.status = 'confirmed'
    unit.current_balance -= payment.amount
    db.session.commit()
    return jsonify({'message': 'Payment confirmed'}), 200


@api_manager_bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
@jwt_required()
def reject_payment(payment_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    payment = Payment.query.get_or_404(payment_id)
    unit = Unit.query.get_or_404(payment.unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=manager.id).first_or_404()
    if payment.status != 'pending':
        return jsonify({'error': 'Only pending payments can be rejected'}), 400
    payment.status = 'rejected'
    db.session.commit()
    return jsonify({'message': 'Payment rejected'}), 200


# Announcements
@api_manager_bp.route('/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    manager, err, code = get_manager()
    if err:
        return err, code
    buildings = Building.query.filter_by(manager_id=manager.id).all()
    result = []
    for b in buildings:
        for a in b.announcements:
            result.append({'id': a.id, 'title': a.title, 'content': a.content, 'building': b.name, 'created_at': a.created_at.isoformat()})
    return jsonify(result), 200


@api_manager_bp.route('/announcements', methods=['POST'])
@jwt_required()
def create_announcement():
    manager, err, code = get_manager()
    if err:
        return err, code
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    building_id = data.get('building_id')
    if not title or not content or not building_id:
        return jsonify({'error': 'title, content, and building_id are required'}), 400
    if building_id == 'all':
        buildings = Building.query.filter_by(manager_id=manager.id).all()
    else:
        b = Building.query.filter_by(id=building_id, manager_id=manager.id).first_or_404()
        buildings = [b]
    for b in buildings:
        db.session.add(Announcement(title=title, content=content, building_id=b.id, manager_id=manager.id))
    db.session.commit()
    return jsonify({'message': 'Announcement posted'}), 201


# Maintenance
@api_manager_bp.route('/maintenance', methods=['GET'])
@jwt_required()
def get_maintenance():
    manager, err, code = get_manager()
    if err:
        return err, code
    buildings = Building.query.filter_by(manager_id=manager.id).all()
    result = []
    for b in buildings:
        for u in b.units:
            for r in u.maintenance_requests:
                result.append({'id': r.id, 'description': r.description, 'status': r.status, 'unit_id': r.unit_id, 'building': b.name, 'created_at': r.created_at.isoformat()})
    return jsonify(result), 200


@api_manager_bp.route('/maintenance/<int:request_id>/update', methods=['POST'])
@jwt_required()
def update_maintenance(request_id):
    manager, err, code = get_manager()
    if err:
        return err, code
    req = MaintenanceRequest.query.get_or_404(request_id)
    unit = Unit.query.get_or_404(req.unit_id)
    Building.query.filter_by(id=unit.building_id, manager_id=manager.id).first_or_404()
    data = request.get_json()
    new_status = data.get('status', '').strip()
    valid_transitions = {'pending': 'in_progress', 'in_progress': 'resolved'}
    if req.status not in valid_transitions or new_status != valid_transitions[req.status]:
        return jsonify({'error': 'Invalid status transition'}), 400
    req.status = new_status
    if new_status == 'resolved':
        req.resolved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': f'Request updated to {new_status}'}), 200
