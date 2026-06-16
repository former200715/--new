"""数据模型 - 7张表"""
from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(32), unique=True, nullable=False)
    permissions = db.Column(db.Text, nullable=True)
    users = db.relationship('User', backref='role', lazy='dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    STATUS_ENABLED = 'enabled'
    STATUS_DISABLED = 'disabled'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column('password', db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(16), default=STATUS_ENABLED)
    create_time = db.Column(db.DateTime, default=datetime.now)

    order_records = db.relationship('OrderRecord', backref='operator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError('密码不可读取')

    @password.setter
    def password(self, plain_text):
        self.set_password(plain_text)

    def is_active(self):
        return self.status == self.STATUS_ENABLED

    def get_permissions(self):
        import json
        if self.role and self.role.permissions:
            try:
                return json.loads(self.role.permissions)
            except json.JSONDecodeError:
                return []
        return []

    def has_permission(self, permission):
        return permission in self.get_permissions()

    def is_admin(self):
        return self.role.role_name == '管理员' if self.role else False


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class RoomType(db.Model):
    __tablename__ = 'room_type'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(32), unique=True, nullable=False)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    facility = db.Column(db.String(256), nullable=True)
    rooms = db.relationship('Room', backref='room_type', lazy='dynamic')


class Room(db.Model):
    __tablename__ = 'room'
    STATUS_AVAILABLE = 'available'
    STATUS_OCCUPIED = 'occupied'
    STATUS_RESERVED = 'reserved'
    STATUS_MAINTENANCE = 'maintenance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_num = db.Column(db.String(16), unique=True, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False)
    floor = db.Column(db.SmallInteger, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(16), default=STATUS_AVAILABLE)
    remark = db.Column(db.String(256), nullable=True)

    order_records = db.relationship('OrderRecord', backref='room', lazy='dynamic')

    def is_available(self):
        return self.status == self.STATUS_AVAILABLE


class OrderRecord(db.Model):
    __tablename__ = 'order_record'
    ORDER_PENDING = 'pending'
    ORDER_CONFIRMED = 'confirmed'
    ORDER_COMPLETED = 'completed'
    ORDER_CANCELLED = 'cancelled'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(32), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=True)
    total_fee = db.Column(db.Numeric(10, 2), nullable=False)
    renewal_count = db.Column(db.Integer, default=0)
    order_status = db.Column(db.String(16), default=ORDER_PENDING)
    create_time = db.Column(db.DateTime, default=datetime.now)

    credit = db.relationship('Credit', backref='order_record', uselist=False,
                             cascade='all, delete-orphan')

    def calculate_fee(self, nights=None):
        if self.room:
            if self.check_out:
                days = max((self.check_out - self.check_in).days, 1)
            elif nights:
                days = nights
            else:
                days = 1
            self.total_fee = self.room.price * Decimal(str(days))

    def cancel(self):
        if self.order_status != self.ORDER_CANCELLED:
            self.order_status = self.ORDER_CANCELLED
            if self.room and self.room.status == Room.STATUS_RESERVED:
                self.room.status = Room.STATUS_AVAILABLE

    def renew(self, extend_days):
        from datetime import timedelta
        if self.check_out:
            self.check_out += timedelta(days=extend_days)
        else:
            self.check_out = datetime.now() + timedelta(days=extend_days)
        self.renewal_count += 1
        self.calculate_fee()

    @property
    def is_overdue(self):
        if self.check_out and self.order_status == self.ORDER_CONFIRMED:
            return datetime.now() > self.check_out
        return False

    @property
    def nights_stayed(self):
        if self.check_in:
            end = self.check_out if self.check_out else datetime.now()
            return max((end - self.check_in).days, 1)
        return 0


class Credit(db.Model):
    __tablename__ = 'credit'
    PAY_UNPAID = 'unpaid'
    PAY_PARTIAL = 'partial'
    PAY_FULL = 'full'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(128), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order_record.id'), unique=True, nullable=False)
    debt_fee = db.Column(db.Numeric(10, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    pay_status = db.Column(db.String(16), default=PAY_UNPAID)
    create_time = db.Column(db.DateTime, default=datetime.now)

    @property
    def remaining_debt(self):
        return (self.debt_fee or 0) - (self.paid_amount or 0)

    def make_payment(self, amount):
        self.paid_amount = (self.paid_amount or 0) + amount
        remaining = float(self.remaining_debt)
        if remaining <= 0:
            self.pay_status = self.PAY_FULL
        elif float(self.paid_amount) > 0:
            self.pay_status = self.PAY_PARTIAL


class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    rating = db.Column(db.SmallInteger, nullable=False)
    content = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(256), nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.now)

    room = db.relationship('Room', backref=db.backref('reviews', lazy='dynamic', cascade='all, delete-orphan'))
