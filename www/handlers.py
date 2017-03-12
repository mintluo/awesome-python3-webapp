#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'milletluo'

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post

from models import User, Comment, Blog, next_id

'''@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }'''

@get('/')
def index(request):
    # summary用于在博客首页上显示的句子,这样真的更有feel
    summary = 'milletluo! Welcome to the IT World!'
    # 这里只是手动写blogs的list，并没有调用数据库
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    # 返回一个字典，其指示了使用何种模板，模板的内容
    # app.py的response_factory将会对handler的返回值进行分类处理
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }
