"""客房管理路由"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from app import db
from app.forms import RoomForm, RoomTypeForm
from app.models import Room, RoomType
from app import permission_required

rooms_bp = Blueprint('rooms', __name__)


@rooms_bp.route('/')
@login_required
def room_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    type_id = request.args.get('type_id', 0, type=int)

    query = Room.query
    if status:
        query = query.filter_by(status=status)
    if type_id:
        query = query.filter_by(type_id=type_id)

    pagination = query.order_by(Room.floor, Room.room_num).paginate(
        page=page, per_page=12, error_out=False)
    room_types = RoomType.query.all()

    return render_template('rooms/list.html',
        pagination=pagination, room_types=room_types,
        current_status=status, current_type=type_id)


@rooms_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('room:manage')
def room_add():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            room_num=form.room_num.data,
            type_id=form.type_id.data,
            floor=form.floor.data,
            price=form.price.data,
            status=form.status.data,
            remark=form.remark.data,
        )
        db.session.add(room)
        db.session.commit()
        flash('客房添加成功', 'success')
        return redirect(url_for('rooms.room_list'))
    return render_template('rooms/form.html', form=form, title='添加客房')


@rooms_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('room:manage')
def room_edit(id):
    room = Room.query.get_or_404(id)
    form = RoomForm(original_room_num=room.room_num, obj=room)
    if form.validate_on_submit():
        form.populate_obj(room)
        db.session.commit()
        flash('客房信息已更新', 'success')
        return redirect(url_for('rooms.room_list'))
    return render_template('rooms/form.html', form=form, title='编辑客房')


@rooms_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('room:manage')
def room_delete(id):
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    flash('客房已删除', 'success')
    return redirect(url_for('rooms.room_list'))


@rooms_bp.route('/types')
@login_required
def type_list():
    types = RoomType.query.all()
    return render_template('rooms/types.html', types=types)


@rooms_bp.route('/types/add', methods=['GET', 'POST'])
@login_required
@permission_required('room_type:manage')
def type_add():
    form = RoomTypeForm()
    if form.validate_on_submit():
        rt = RoomType(type_name=form.type_name.data, base_price=form.base_price.data,
                      facility=form.facility.data)
        db.session.add(rt)
        db.session.commit()
        flash('房型添加成功', 'success')
        return redirect(url_for('rooms.type_list'))
    return render_template('rooms/type_form.html', form=form, title='添加房型')


@rooms_bp.route('/types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('room_type:manage')
def type_edit(id):
    rt = RoomType.query.get_or_404(id)
    form = RoomTypeForm(original_name=rt.type_name, obj=rt)
    if form.validate_on_submit():
        form.populate_obj(rt)
        db.session.commit()
        flash('房型已更新', 'success')
        return redirect(url_for('rooms.type_list'))
    return render_template('rooms/type_form.html', form=form, title='编辑房型')
