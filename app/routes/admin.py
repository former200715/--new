"""后台管理路由"""
import json

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from app import db, permission_required
from app.forms import UserCreateForm, UserEditForm, PasswordResetForm, RoleForm, AVAILABLE_PERMISSIONS
from app.models import User, Role

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users')
@login_required
@permission_required('user:manage')
def user_list():
    users = User.query.order_by(User.create_time.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@permission_required('user:manage')
def user_add():
    form = UserCreateForm()
    form.role_id.choices = [(r.id, r.role_name) for r in Role.query.all()]
    if form.validate_on_submit():
        user = User(username=form.username.data, name=form.name.data,
                    role_id=form.role_id.data, status=form.status.data)
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('用户创建成功', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/user_form.html', form=form, title='添加用户')


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('user:manage')
def user_edit(id):
    user = User.query.get_or_404(id)
    form = UserEditForm(original_username=user.username, obj=user)
    form.role_id.choices = [(r.id, r.role_name) for r in Role.query.all()]
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        flash('用户信息已更新', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/user_form.html', form=form, title='编辑用户')


@admin_bp.route('/users/<int:id>/reset-password', methods=['GET', 'POST'])
@login_required
@permission_required('user:manage')
def reset_password(id):
    user = User.query.get_or_404(id)
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.password = form.new_password.data
        db.session.commit()
        flash('密码已重置', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/reset_password.html', form=form, user=user)


@admin_bp.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
@permission_required('user:manage')
def toggle_user(id):
    user = User.query.get_or_404(id)
    user.status = User.STATUS_DISABLED if user.status == User.STATUS_ENABLED else User.STATUS_ENABLED
    db.session.commit()
    flash(f'用户已{"启用" if user.status == "enabled" else "禁用"}', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/roles')
@login_required
@permission_required('role:manage')
def role_list():
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)


@admin_bp.route('/roles/add', methods=['GET', 'POST'])
@login_required
@permission_required('role:manage')
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(role_name=form.role_name.data, permissions=form.get_permissions())
        db.session.add(role)
        db.session.commit()
        flash('角色创建成功', 'success')
        return redirect(url_for('admin.role_list'))
    return render_template('admin/role_form.html', form=form, title='添加角色',
                           permissions=AVAILABLE_PERMISSIONS)


@admin_bp.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('role:manage')
def role_edit(id):
    role = Role.query.get_or_404(id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        role.role_name = form.role_name.data
        role.permissions = form.get_permissions()
        db.session.commit()
        flash('角色已更新', 'success')
        return redirect(url_for('admin.role_list'))

    # 回填权限复选框
    if role.permissions:
        perms = json.loads(role.permissions)
        for perm_key, _ in AVAILABLE_PERMISSIONS:
            getattr(form, f'perm_{perm_key}').data = perm_key in perms

    return render_template('admin/role_form.html', form=form, title='编辑角色',
                           permissions=AVAILABLE_PERMISSIONS)
