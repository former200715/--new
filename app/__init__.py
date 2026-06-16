"""Flask 应用工厂"""
from datetime import timedelta
from functools import wraps

from flask import Flask, flash, redirect, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('请先登录', 'warning')
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(permission):
                flash('权限不足', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _seed_admin():
    from app.models import Role, User
    if User.query.first() is not None:
        return

    import json
    all_perms = [
        'user:manage', 'role:manage', 'room:view', 'room:manage',
        'room_type:manage', 'order:view', 'order:create', 'order:cancel',
        'order:checkin', 'order:checkout', 'credit:view', 'credit:manage',
        'stats:view', 'review:view', 'review:manage',
    ]
    admin_role = Role(role_name='管理员', permissions=json.dumps(all_perms))
    db.session.add(admin_role)
    db.session.flush()

    admin = User(username='admin', name='管理员', role_id=admin_role.id)
    admin.password = 'admin123'
    db.session.add(admin)
    db.session.commit()
    print('✅ 默认管理员: admin / admin123')


def _seed_test_data():
    from app.models import RoomType, Room, OrderRecord
    from datetime import datetime, timedelta
    from random import choice, randint, uniform

    if RoomType.query.first() is not None:
        return

    types_data = [
        ('标准单人间', 198, 'WiFi,电视,空调,独立卫浴'),
        ('豪华大床房', 358, 'WiFi,电视,空调,冰箱,浴缸,迷你吧'),
        ('商务双床房', 298, 'WiFi,电视,空调,办公桌,保险箱'),
        ('行政套房', 588, 'WiFi,电视,空调,冰箱,浴缸,客厅,迷你吧,保险箱'),
        ('总统套房', 1288, 'WiFi,电视,空调,冰箱,浴缸,客厅,书房,迷你吧,保险箱,桑拿'),
    ]
    room_types = []
    for name, price, facility in types_data:
        rt = RoomType(type_name=name, base_price=price, facility=facility)
        db.session.add(rt)
        db.session.flush()
        room_types.append(rt)

    statuses = ['available'] * 6 + ['occupied'] * 3 + ['reserved'] * 1
    for floor in range(1, 4):
        for num in range(1, 11):
            room_num = f'{floor}{num:02d}'
            rt = choice(room_types[:3]) if num <= 7 else choice(room_types[2:])
            room = Room(
                room_num=room_num, type_id=rt.id, floor=floor,
                price=rt.base_price * round(uniform(0.9, 1.1), 2),
                status=choice(statuses),
            )
            db.session.add(room)

    db.session.flush()

    all_rooms = Room.query.all()
    names = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十',
             '郑强', '王芳', '刘伟', '陈静', '杨洋', '黄磊', '朱丽']
    phones = ['138', '139', '136', '137', '158', '159', '186', '187']

    for i in range(40):
        room = choice(all_rooms)
        days_ago = randint(0, 29)
        check_in = datetime.now() - timedelta(days=days_ago, hours=randint(8, 18))
        stay_days = randint(1, 5)
        check_out = check_in + timedelta(days=stay_days)
        order = OrderRecord(
            customer_name=choice(names),
            phone=choice(phones) + str(randint(10000000, 99999999)),
            room_id=room.id, check_in=check_in, check_out=check_out,
            total_fee=room.price * stay_days,
            order_status=choice(['completed', 'completed', 'confirmed', 'cancelled']),
            create_time=check_in,
        )
        db.session.add(order)

    db.session.commit()
    print('✅ 测试数据已初始化: 5 房型, 30 客房, 40 订单')


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.rooms import rooms_bp
    from app.routes.bookings import bookings_bp
    from app.routes.admin import admin_bp
    from app.routes.stats import stats_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(rooms_bp, url_prefix='/rooms')
    app.register_blueprint(bookings_bp, url_prefix='/bookings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(stats_bp, url_prefix='/stats')

    from app import models  # noqa: F401

    with app.app_context():
        db.create_all()
        _seed_admin()
        _seed_test_data()

    @app.context_processor
    def inject_permissions():
        return {
            'has_perm': lambda p: (
                current_user.is_authenticated and
                current_user.has_permission(p)
            )
        }

    return app
