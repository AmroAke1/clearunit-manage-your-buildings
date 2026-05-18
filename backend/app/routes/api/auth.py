from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import requests as http_requests
from app import db
from app.models import User

api_auth_bp = Blueprint('api_auth', __name__)


@api_auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    user = User.query.filter(db.func.lower(User.email) == email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'role': user.role, 'full_name': user.full_name}), 200


@api_auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', '')
    if not all([full_name, email, password, role]):
        return jsonify({'error': 'All fields are required'}), 400
    if role not in ('manager', 'resident'):
        return jsonify({'error': 'Invalid role'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    user = User(full_name=full_name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Account created successfully'}), 201


@api_auth_bp.route('/google', methods=['POST'])
def google_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    id_token = data.get('id_token', '').strip()
    if not id_token:
        return jsonify({'error': 'id_token is required'}), 400

    resp = http_requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}', timeout=5)
    if resp.status_code != 200:
        return jsonify({'error': 'Invalid Google token'}), 401

    info = resp.json()
    if info.get('aud') != current_app.config['GOOGLE_CLIENT_ID']:
        return jsonify({'error': 'Token audience mismatch'}), 401

    google_id = info['sub']
    email = info['email'].lower()
    full_name = info.get('name', email)

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter(db.func.lower(User.email) == email).first()
        if user:
            user.google_id = google_id
            db.session.commit()

    if not user:
        role = data.get('role', '').strip()
        if role not in ('manager', 'resident'):
            return jsonify({'error': 'role is required for new users (manager or resident)'}), 400
        user = User(full_name=full_name, email=email, google_id=google_id, role=role)
        db.session.add(user)
        db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'role': user.role, 'full_name': user.full_name}), 200


@api_auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify({'id': user.id, 'full_name': user.full_name, 'email': user.email, 'role': user.role}), 200
