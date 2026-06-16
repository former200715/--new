"""生成测试数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from random import choice, randint, uniform
from app import create_app, db
from app.models import RoomType, Room, OrderRecord, User, Role

app = create_app()

with app.app_context():
    # 创建房型
    types_data = [
        ('标准单人间', 198, 'WiFi,电视,空调,独立卫浴'),
        ('豪华大床房', 358, 'WiFi,电视,空调,冰箱,浴缸,迷你吧'),
        ('商务双床房', 298, 'WiFi,电视,空调,办公桌,保险箱'),
        ('行政套房', 588, 'WiFi,电视,空调,冰箱,浴缸,客厅,迷你吧,保险箱'),
        ('总统套房', 1288, 'WiFi,电视,空调,冰箱,浴缸,客厅,书房,迷你吧,保险箱,桑拿'),
    ]
    room_types = []
    for name, price, facility in types_data:
        rt = RoomType.query.filter_by(type_name=name).first()
        if not rt:
            rt = RoomType(type_name=name, base_price=price, facility=facility)
            db.session.add(rt)
            db.session.flush()
        room_types.append(rt)

    # 创建客房（3层楼，每层10间）
    statuses = ['available'] * 6 + ['occupied'] * 3 + ['reserved'] * 1
    rooms = []
    for floor in range(1, 4):
        for num in range(1, 11):
            room_num = f'{floor}{num:02d}'
            room = Room.query.filter_by(room_num=room_num).first()
            if not room:
                rt = choice(room_types[:3]) if num <= 7 else choice(room_types[2:])
                room = Room(
                    room_num=room_num,
                    type_id=rt.id,
                    floor=floor,
                    price=rt.base_price * round(uniform(0.9, 1.1), 2),
                    status=choice(statuses),
                )
                db.session.add(room)
                rooms.append(room)

    db.session.flush()

    # 创建订单（最近30天）
    all_rooms = Room.query.all()
    names = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十',
             '郑强', '王芳', '刘伟', '陈静', '杨洋', '黄磊', '朱丽']
    phones = ['138', '139', '136', '137', '158', '159', '186', '187']

    if OrderRecord.query.count() < 10:
        for i in range(40):
            room = choice(all_rooms)
            days_ago = randint(0, 29)
            check_in = datetime.now() - timedelta(days=days_ago, hours=randint(8, 18))
            stay_days = randint(1, 5)
            check_out = check_in + timedelta(days=stay_days)

            order = OrderRecord(
                customer_name=choice(names),
                phone=choice(phones) + str(randint(10000000, 99999999)),
                room_id=room.id,
                check_in=check_in,
                check_out=check_out,
                total_fee=room.price * stay_days,
                order_status=choice(['completed', 'completed', 'confirmed', 'cancelled']),
                create_time=check_in,
            )
            db.session.add(order)

    db.session.commit()
    print('[OK] Test data generated!')
    print(f'  Room types: {RoomType.query.count()}')
    print(f'  Rooms: {Room.query.count()}')
    print(f'  Orders: {OrderRecord.query.count()}')
