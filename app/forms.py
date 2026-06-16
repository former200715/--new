"""表单模块"""
import json
from datetime import date, datetime

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, DateField, DateTimeField, DecimalField, HiddenField,
    IntegerField, PasswordField, SelectField, StringField, SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange, Optional, ValidationError

from app.models import RoomType, User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登 录')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    name = StringField('真实姓名', validators=[DataRequired(), Length(min=2, max=32)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(), EqualTo('password', message='两次密码不一致')])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被注册')


class BookingForm(FlaskForm):
    room_id = HiddenField('房间ID', validators=[DataRequired()])
    customer_name = StringField('客户姓名', validators=[DataRequired(), Length(min=2, max=32)])
    phone = StringField('联系电话', validators=[DataRequired(), Length(min=11, max=20)])
    check_in = DateField('入住日期', validators=[DataRequired()])
    check_out = DateField('退房日期', validators=[DataRequired()])
    submit = SubmitField('确认预订')

    def validate_check_in(self, field):
        if field.data < date.today():
            raise ValidationError('入住日期不能早于今天')

    def validate_check_out(self, field):
        if self.check_in.data and field.data <= self.check_in.data:
            raise ValidationError('退房日期必须晚于入住日期')


class CheckinForm(FlaskForm):
    room_id = SelectField('分配房间', coerce=int, validators=[DataRequired()])
    customer_name = StringField('客户姓名', validators=[DataRequired(), Length(min=2, max=32)])
    phone = StringField('联系电话', validators=[DataRequired(), Length(min=11, max=20)])
    check_out = DateField('预计退房日期', validators=[DataRequired()])
    remark = TextAreaField('备注', validators=[Optional(), Length(max=256)])
    submit = SubmitField('确认入住')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import Room
        available = Room.query.filter_by(status=Room.STATUS_AVAILABLE).all()
        self.room_id.choices = [
            (r.id, f'{r.room_num} ({r.room_type.type_name} · {r.floor}F · ¥{float(r.price):.0f})')
            for r in available
        ]


class RenewalForm(FlaskForm):
    order_id = HiddenField('订单ID', validators=[DataRequired()])
    extend_days = IntegerField('续住天数', validators=[
        DataRequired(), NumberRange(min=1, max=365)])
    submit = SubmitField('确认续费')


class CheckoutForm(FlaskForm):
    order_id = HiddenField('订单ID', validators=[DataRequired()])
    discount = DecimalField('折扣（元）', places=2, default=0, validators=[Optional()])
    payment_method = SelectField('支付方式', choices=[
        ('cash', '现金'), ('wechat', '微信'), ('alipay', '支付宝'),
        ('card', '银行卡'), ('credit', '挂账')
    ], default='wechat')
    submit = SubmitField('确认结账')


class RoomTypeForm(FlaskForm):
    type_name = StringField('类型名称', validators=[DataRequired(), Length(min=2, max=32)])
    base_price = DecimalField('基础价格（元/晚）', places=2, validators=[
        DataRequired(), NumberRange(min=0)])
    facility = StringField('配套设施', validators=[Optional(), Length(max=256)])
    submit = SubmitField('保存')

    def __init__(self, original_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_type_name(self, field):
        if self.original_name and field.data == self.original_name:
            return
        if RoomType.query.filter_by(type_name=field.data).first():
            raise ValidationError('该类型名称已存在')


class RoomForm(FlaskForm):
    room_num = StringField('房间号', validators=[DataRequired(), Length(min=2, max=16)])
    type_id = SelectField('房型', coerce=int, validators=[DataRequired()])
    floor = IntegerField('楼层', validators=[DataRequired(), NumberRange(min=1)])
    price = DecimalField('售价（元/晚）', places=2, validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('状态', choices=[
        ('available', '空闲'), ('occupied', '已入住'),
        ('reserved', '已预订'), ('maintenance', '维护中')
    ], default='available')
    remark = TextAreaField('备注', validators=[Optional(), Length(max=256)])
    submit = SubmitField('保存')

    def __init__(self, original_room_num=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_room_num = original_room_num
        types = RoomType.query.all()
        self.type_id.choices = [(t.id, f'{t.type_name} (¥{float(t.base_price):.0f}/晚)') for t in types]

    def validate_room_num(self, field):
        if self.original_room_num and field.data == self.original_room_num:
            return
        from app.models import Room
        if Room.query.filter_by(room_num=field.data).first():
            raise ValidationError('该房间号已存在')


class CreditForm(FlaskForm):
    order_id = SelectField('关联订单', coerce=int, validators=[DataRequired()])
    company_name = StringField('挂账单位', validators=[DataRequired(), Length(min=2, max=128)])
    debt_fee = DecimalField('挂账金额', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('确认挂账')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models import OrderRecord
        completed = OrderRecord.query.filter_by(order_status=OrderRecord.ORDER_CONFIRMED).all()
        self.order_id.choices = [
            (o.id, f'#{o.id} {o.customer_name} · ¥{float(o.total_fee):.0f}') for o in completed
        ]


class CreditPaymentForm(FlaskForm):
    credit_id = HiddenField('挂账ID', validators=[DataRequired()])
    pay_amount = DecimalField('还款金额', places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('确认还款')


class UserCreateForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    name = StringField('真实姓名', validators=[DataRequired(), Length(min=2, max=32)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6, max=128)])
    role_id = SelectField('角色', coerce=int, validators=[DataRequired()])
    status = SelectField('状态', choices=[('enabled', '启用'), ('disabled', '禁用')], default='enabled')
    submit = SubmitField('创建')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')


class UserEditForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=64)])
    name = StringField('真实姓名', validators=[DataRequired(), Length(min=2, max=32)])
    role_id = SelectField('角色', coerce=int, validators=[DataRequired()])
    status = SelectField('状态', choices=[('enabled', '启用'), ('disabled', '禁用')])
    submit = SubmitField('保存')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, field):
        if field.data != self.original_username and User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')


class PasswordResetForm(FlaskForm):
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(), EqualTo('new_password', message='两次密码不一致')])
    submit = SubmitField('重置密码')


AVAILABLE_PERMISSIONS = [
    ('admin:dashboard', '控制台'), ('room:view', '客房查看'), ('room:manage', '客房管理'),
    ('order:create', '订单创建'), ('order:view', '订单查看'), ('order:cancel', '订单取消'),
    ('order:checkout', '退房操作'), ('credit:view', '挂账查看'), ('credit:manage', '挂账管理'),
    ('user:manage', '操作员管理'), ('role:manage', '角色权限'), ('system:settings', '系统设置'),
]


class RoleForm(FlaskForm):
    role_name = StringField('角色名称', validators=[DataRequired(), Length(min=2, max=32)])
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for perm_key, perm_label in AVAILABLE_PERMISSIONS:
            setattr(self, f'perm_{perm_key}', BooleanField(perm_label))

    def get_permissions(self):
        selected = [k for k, _ in AVAILABLE_PERMISSIONS
                    if getattr(self, f'perm_{k}', None) and getattr(self, f'perm_{k}').data]
        return json.dumps(selected, ensure_ascii=False)
