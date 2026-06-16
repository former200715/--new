"""首页路由"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Room, OrderRecord, RoomType, Credit

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    # 统计数据
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status=Room.STATUS_AVAILABLE).count()
    occupied_rooms = Room.query.filter_by(status=Room.STATUS_OCCUPIED).count()
    reserved_rooms = Room.query.filter_by(status=Room.STATUS_RESERVED).count()
    maintenance_rooms = Room.query.filter_by(status=Room.STATUS_MAINTENANCE).count()

    pending_orders = OrderRecord.query.filter_by(order_status=OrderRecord.ORDER_PENDING).count()
    confirmed_orders = OrderRecord.query.filter_by(order_status=OrderRecord.ORDER_CONFIRMED).count()
    completed_orders = OrderRecord.query.filter_by(order_status=OrderRecord.ORDER_COMPLETED).count()
    total_orders = OrderRecord.query.count()

    # 各房型数量
    room_types = RoomType.query.all()
    type_stats = []
    for rt in room_types:
        count = rt.rooms.count()
        type_stats.append({'name': rt.type_name, 'count': count, 'price': float(rt.base_price)})

    # 最近订单
    recent_orders = OrderRecord.query.order_by(OrderRecord.create_time.desc()).limit(5).all()

    return render_template('index.html',
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms,
        reserved_rooms=reserved_rooms,
        maintenance_rooms=maintenance_rooms,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        completed_orders=completed_orders,
        total_orders=total_orders,
        type_stats=type_stats,
        recent_orders=recent_orders,
    )
