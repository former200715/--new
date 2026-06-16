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

    @app.context_processor
    def inject_permissions():
        return {
            'has_perm': lambda p: (
                current_user.is_authenticated and
                current_user.has_permission(p)
            )
        }

    return app
