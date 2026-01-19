from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class TimestampMixin:
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    client_category = db.Column(db.String(20), default='Económico', nullable=False)  # Gold, Silver, Económico
    max_budget    = db.Column(db.Float, nullable=False)  # Orçamento máximo do cliente

    reservations = db.relationship(
        'Reservation',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_available_vehicles(self):
        """Retorna veículos disponíveis para a categoria do cliente"""
        if self.client_category == 'Gold':
            return Vehicle.query.filter(Vehicle.daily_rate <= 600, Vehicle.available == True).all()
        elif self.client_category == 'Silver':
            return Vehicle.query.filter(Vehicle.daily_rate <= 250, Vehicle.available == True).all()
        else:  # Económico
            return Vehicle.query.filter(Vehicle.daily_rate <= 50, Vehicle.available == True).all()


class PaymentMethod(TimestampMixin, db.Model):
    __tablename__ = 'payment_methods'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    reservations = db.relationship(
        'Reservation',
        back_populates='payment_method',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<PaymentMethod {self.name}>'


class Vehicle(TimestampMixin, db.Model):
    __tablename__ = 'vehicles'

    id                = db.Column(db.Integer, primary_key=True)
    brand             = db.Column(db.String(50), nullable=False)
    model             = db.Column(db.String(50), nullable=False)
    category          = db.Column(db.String(20), nullable=False)
    type              = db.Column(db.String(10), nullable=False)
    capacity          = db.Column(db.Integer, nullable=False)
    image_url         = db.Column(db.String(200))
    daily_rate        = db.Column(db.Float, nullable=False)
    last_legalization = db.Column(db.Date, nullable=False)
    next_review       = db.Column(db.Date, nullable=False)
    available         = db.Column(db.Boolean, default=True, nullable=False)

    reservations = db.relationship(
        'Reservation',
        back_populates='vehicle',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Vehicle {self.brand} {self.model}>'


class Reservation(TimestampMixin, db.Model):
    __tablename__ = 'reservations'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
    vehicle_id        = db.Column(
        db.Integer,
        db.ForeignKey('vehicles.id'),
        nullable=False
    )
    start_date        = db.Column(db.Date, nullable=False)
    end_date          = db.Column(db.Date, nullable=False)
    total_value       = db.Column(db.Float, nullable=False)
    payment_method_id = db.Column(
        db.Integer,
        db.ForeignKey('payment_methods.id'),
        nullable=False
    )
    status            = db.Column(db.String(20), default='Pendente', nullable=False)  # Pendente, Pago, Concluído, Cancelado
    pickup_date       = db.Column(db.DateTime)  # Data de recolha do veículo
    contract_number   = db.Column(db.String(50), unique=True)  # Número do contrato

    user           = db.relationship('User', back_populates='reservations')
    vehicle        = db.relationship('Vehicle', back_populates='reservations')
    payment_method = db.relationship('PaymentMethod', back_populates='reservations')

    def __repr__(self):
        return f'<Reservation {self.id} U{self.user_id} V{self.vehicle_id}>'
    
    def calculate_total_days(self):
        """Calcula o número total de dias de aluguer"""
        return (self.end_date - self.start_date).days + 1
    
    def calculate_total_cost(self):
        """Calcula o custo total do aluguer"""
        return self.vehicle.daily_rate * self.calculate_total_days()


class Payment(TimestampMixin, db.Model):
    __tablename__ = 'payments'

    id             = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('reservations.id'),
        nullable=False
    )
    amount         = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='Pendente', nullable=False)  # Pendente, Pago, Falhado
    payment_date   = db.Column(db.DateTime)
    transaction_id = db.Column(db.String(100), unique=True)  # ID da transação

    reservation = db.relationship('Reservation')

    def __repr__(self):
        return f'<Payment {self.id} R{self.reservation_id}>'
