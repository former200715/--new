"""数据统计路由"""
from datetime import datetime, timedelta

from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models import OrderRecord, Room, RoomType, Credit

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/')
@login_required
def dashboard():
    return render_template('stats/dashboard.html')


@stats_bp.route('/api/room-status')
@login_required
def room_status_data():
    """房间状态分布 - 饼图数据"""
    data = db.session.query(Room.status, func.count(Room.id)).group_by(Room.status).all()
    labels = []
    values = []
    status_map = {
        'available': '空闲', 'occupied': '已入住',
        'reserved': '已预订', 'maintenance': '维护中'
    }
    for status, count in data:
        labels.append(status_map.get(status, status))
        values.append(count)
    return jsonify({'labels': labels, 'values': values})


@stats_bp.route('/api/order-trend')
@login_required
def order_trend_data():
    """近30天订单趋势 - 折线图数据"""
    today = datetime.now().date()
    dates = []
    counts = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        count = OrderRecord.query.filter(
            func.date(OrderRecord.create_time) == d
        ).count()
        dates.append(d.strftime('%m-%d'))
        counts.append(count)
    return jsonify({'labels': dates, 'values': counts})


@stats_bp.route('/api/revenue')
@login_required
def revenue_data():
    """近7天收入 - 柱状图数据"""
    today = datetime.now().date()
    dates = []
    revenues = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        result = db.session.query(func.sum(OrderRecord.total_fee)).filter(
            func.date(OrderRecord.create_time) == d,
            OrderRecord.order_status.in_([OrderRecord.ORDER_COMPLETED, OrderRecord.ORDER_CONFIRMED])
        ).scalar()
        dates.append(d.strftime('%m-%d'))
        revenues.append(float(result or 0))
    return jsonify({'labels': dates, 'values': revenues})


@stats_bp.route('/api/room-type-distribution')
@login_required
def room_type_distribution():
    """房型分布 - 饼图"""
    data = db.session.query(RoomType.type_name, func.count(Room.id)).join(
        Room, Room.type_id == RoomType.id
    ).group_by(RoomType.type_name).all()
    labels = [r[0] for r in data]
    values = [r[1] for r in data]
    return jsonify({'labels': labels, 'values': values})


@stats_bp.route('/api/floor-occupancy')
@login_required
def floor_occupancy():
    """楼层入住率 - 柱状图"""
    floors = db.session.query(Room.floor).distinct().order_by(Room.floor).all()
    result = []
    for (floor,) in floors:
        total = Room.query.filter_by(floor=floor).count()
        occupied = Room.query.filter(
            Room.floor == floor,
            Room.status.in_([Room.STATUS_OCCUPIED, Room.STATUS_RESERVED])
        ).count()
        rate = round(occupied / total * 100, 1) if total > 0 else 0
        result.append({'floor': f'{floor}F', 'rate': rate, 'total': total, 'occupied': occupied})
    return jsonify(result)
