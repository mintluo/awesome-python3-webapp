#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'milletluo'

'''
采用orm构建Web App需要的3个表
'''

# uuid是python中生成唯一ID的库
import time, uuid

from orm import Model, StringField, BooleanField, FloatField, TextField
# 这个函数的作用是生成一个基于时间的独一无二的id，来作为数据库表中每一行的主键
def next_id():
    # time.time() 返回当前时间的时间戳(相对于1970.1.1 00:00:00以秒计算的偏移量)
    # uuid4()——由伪随机数得到，有一定的重复概率，该概率可以计算出来。
    return '%015d%s000' % (int(time.time()*1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'
    """docstring for User"""
    id = StringField(primary_key = True, default = next_id, ddl = 'varchar(50)')
    email = StringField(ddl = 'varchar(50)')
    passwd = StringField(ddl = 'varchar(50)')
    admin = BooleanField()
    name = StringField(ddl = 'varchar(50)')
    image = StringField(ddl = 'varchar(500)')
    created_at = FloatField(default = time.time)# 创建时间默认是为当前时间

class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)
