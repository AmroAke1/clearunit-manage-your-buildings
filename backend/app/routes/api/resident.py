from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from app import db
from app.models import Unit, Dues, Payment, Announcement, MaintenanceRequest, User

api_resident_bp = Blueprint('api_resident', __name__)


def get_resident():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    if user.role != 'resident':
        return None, None, jsonify({'error': 'Resident access required'}), 403
    unit = Unit.query.filter_by(resident_id=user.id).first()
    return user, unit, None, None


@api_resident_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'message': 'Not assigned to any unit'}), 200
    return jsonify({'unit_number': unit.unit_number, 'floor': unit.floor, 'current_balance': unit.current_balance, 'building_id': unit.building_id}), 200


@api_resident_bp.route('/dues', methods=['GET'])
@jwt_required()
def dues():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'error': 'Not assigned to any unit'}), 404
    dues_list = Dues.query.filter_by(unit_id=unit.id).order_by(Dues.created_at.desc()).all()
    return jsonify([{'id': d.id, 'amount': d.amount, 'month': d.month, 'created_at': d.created_at.isoformat()} for d in dues_list]), 200


@api_resident_bp.route('/payments', methods=['GET'])
@jwt_required()
def payments():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'error': 'Not assigned to any unit'}), 404
    payments_list = Payment.query.filter_by(unit_id=unit.id).order_by(Payment.payment_date.desc()).all()
    return jsonify([{'id': p.id, 'amount': p.amount, 'month': p.month, 'status': p.status, 'payment_date': p.payment_date.isoformat()} for p in payments_list]), 200


@api_resident_bp.route('/payments/notify', methods=['POST'])
@jwt_required()
def notify_payment():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'error': 'Not assigned to any unit'}), 404
    data = request.get_json()
    amount = data.get('amount')
    month = data.get('month', '').strip()
    if not amount or not month:
        return jsonify({'error': 'amount and month are required'}), 400
    if float(amount) <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    payment = Payment(amount=float(amount), month=month, unit_id=unit.id, payment_date=date.today())
    db.session.add(payment)
    db.session.commit()
    return jsonify({'message': 'Payment notification sent'}), 201


@api_resident_bp.route('/maintenance', methods=['GET'])
@jwt_required()
def get_maintenance():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'error': 'Not assigned to any unit'}), 404
    requests_list = MaintenanceRequest.query.filter_by(unit_id=unit.id).order_by(MaintenanceRequest.created_at.desc()).all()
    return jsonify([{'id': r.id, 'description': r.description, 'status': r.status, 'created_at': r.created_at.isoformat()} for r in requests_list]), 200


@api_resident_bp.route('/maintenance', methods=['POST'])
@jwt_required()
def create_maintenance():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'error': 'Not assigned to any unit'}), 404
    data = request.get_json()
    description = data.get('description', '').strip()
    if not description:
        return jsonify({'error': 'Description is required'}), 400
    req = MaintenanceRequest(description=description, unit_id=unit.id)
    db.session.add(req)
    db.session.commit()
    return jsonify({'message': 'Maintenance request submitted'}), 201


@api_resident_bp.route('/announcements', methods=['GET'])
@jwt_required()
def announcements():
    user, unit, err, code = get_resident()
    if err:
        return err, code
    if not unit:
        return jsonify({'error': 'Not assigned to any unit'}), 404
    announcements_list = Announcement.query.filter_by(building_id=unit.building_id).order_by(Announcement.created_at.desc()).all()
    return jsonify([{'id': a.id, 'title': a.title, 'content': a.content, 'created_at': a.created_at.isoformat()} for a in announcements_list]), 200
