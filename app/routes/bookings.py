"""预订/订单路由"""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.forms import BookingForm, CheckinForm, RenewalForm, CheckoutForm
from app.models import OrderRecord, Room

bookings_bp = Blueprint('bookings', __name__)


@bookings_bp.route('/')
@login_required
def order_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = OrderRecord.query
    if status:
        query = query.filter_by(order_status=status)

    pagination = query.order_by(OrderRecord.create_time.desc()).paginate(
        page=page, per_page=15, error_out=False)

    return render_template('bookings/list.html', pagination=pagination, current_status=status)


@bookings_bp.route('/create/<int:room_id>', methods=['GET', 'POST'])
@login_required
def create_order(room_id):
    room = Room.query.get_or_404(room_id)
    if not room.is_available():
        flash('该房间当前不可预订', 'warning')
        return redirect(url_for('rooms.room_list'))

    form = BookingForm()
    form.room_id.data = room_id

    if form.validate_on_submit():
        order = OrderRecord(
            operator_id=current_user.id,
            customer_name=form.customer_name.data,
            phone=form.phone.data,
            room_id=room_id,
            check_in=form.check_in.data,
            check_out=form.check_out.data,
            order_status=OrderRecord.ORDER_PENDING,
        )
        order.calculate_fee()
        room.status = Room.STATUS_RESERVED
        db.session.add(order)
        db.session.commit()
        flash('预订成功', 'success')
        return redirect(url_for('bookings.order_list'))

    return render_template('bookings/create.html', form=form, room=room)


@bookings_bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    form = CheckinForm()
    if form.validate_on_submit():
        order = OrderRecord(
            operator_id=current_user.id,
            customer_name=form.customer_name.data,
            phone=form.phone.data,
            room_id=form.room_id.data,
            check_in=datetime.now(),
            check_out=form.check_out.data,
            order_status=OrderRecord.ORDER_CONFIRMED,
        )
        order.calculate_fee()
        room = Room.query.get(form.room_id.data)
        room.status = Room.STATUS_OCCUPIED
        db.session.add(order)
        db.session.commit()
        flash('入住登记成功', 'success')
        return redirect(url_for('bookings.order_list'))
    return render_template('bookings/checkin.html', form=form)


@bookings_bp.route('/<int:id>/renew', methods=['POST'])
@login_required
def renew(id):
    order = OrderRecord.query.get_or_404(id)
    form = RenewalForm()
    if form.validate_on_submit():
        order.renew(form.extend_days.data)
        db.session.commit()
        flash(f'续住 {form.extend_days.data} 天成功', 'success')
    return redirect(url_for('bookings.order_list'))


@bookings_bp.route('/<int:id>/checkout', methods=['POST'])
@login_required
def checkout(id):
    order = OrderRecord.query.get_or_404(id)
    form = CheckoutForm()
    if form.validate_on_submit():
        order.order_status = OrderRecord.ORDER_COMPLETED
        order.check_out = datetime.now()
        if form.discount.data:
            order.total_fee = max(0, order.total_fee - form.discount.data)
        if order.room:
            order.room.status = Room.STATUS_AVAILABLE
        db.session.commit()
        flash('退房结账成功', 'success')
    return redirect(url_for('bookings.order_list'))


@bookings_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    order = OrderRecord.query.get_or_404(id)
    order.cancel()
    db.session.commit()
    flash('订单已取消', 'info')
    return redirect(url_for('bookings.order_list'))
