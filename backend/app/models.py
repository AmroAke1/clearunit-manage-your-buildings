from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    managed_buildings = db.relationship('Building', backref='manager', lazy=True, foreign_keys='Building.manager_id')
    unit = db.relationship('Unit', backref='resident', uselist=False, foreign_keys='Unit.resident_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Building(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    units = db.relationship('Unit', backref='building', lazy=True, cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='building', lazy=True, cascade='all, delete-orphan')


class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    current_balance = db.Column(db.Float, default=0.0)
    building_id = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=False)
    resident_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    dues = db.relationship('Dues', backref='unit', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='unit', lazy=True, cascade='all, delete-orphan')
    maintenance_requests = db.relationship('MaintenanceRequest', backref='unit', lazy=True, cascade='all, delete-orphan')


class Dues(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(20), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    building_id = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    manager = db.relationship('User', foreign_keys=[manager_id])


class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)