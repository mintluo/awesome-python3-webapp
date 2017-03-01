#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'milletluo'

'''
orm.
为了简化并更好地标识异步IO，从Python 3.5开始引入了新的语法async和await
把@asyncio.coroutine替换为async；
把yield from替换为await。
'''

import asyncio, logging, aiomysql, sys

# 输出信息，让你知道这个时间点程序在做什么
def log(sql, args=()):
    logging.info('SQL: %s' % sql)

# 创建全局连接池
# 这个函数将来会在app.py的init函数中引用
# 目的是为了让每个HTTP请求都能s从连接池中直接获取数据库连接
# 避免了频繁关闭和打开数据库连接
# 关键字参数允许传入0个或任意个含参数名的参数，这些关键字参数在函数内部自动组装为一个dict
async def create_pool(loop, **kw):
	logging.info('create database connection pool...')
	# 声明变量__pool是一个全局变量，如果不加声明，__pool就会被默认为一个私有变量，不能被其他函数引用
	global __pool
	#调用一个自协程创建全局的连接池，create_pool的返回值是一个pool实例对象
	__pool = await aiomysql.create_pool(
	#dict的get方法，如果dict中有对应的value值，则返回对应于key的value值，否则返回默认值
	#例如下面的host，如果dict里面没有'host',则返回后面的默认值，也就是'localhost'  
		host = kw.get('host', 'localhost'),
		port = kw.get('port', 3306),
		user = kw['user'],
		password = kw['password'],
		db = kw['db'],
		charset = kw.get('charset','utf8'),
		autocommit = kw.get('autocommit',True),#默认自动提交事务，不用手动去提交事务
		maxsize = kw.get('maxsize',10),
		minsize = kw.get('minsize',1),
		loop = loop# 传递消息循环对象，用于异步执行
	)
	
# =================================以下是SQL函数处理区====================================

#执行SELECT语句。使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击
# sql参数即为sql语句，args表示要搜索的参数
# size用于指定最大的查询数量，不指定将返回所有查询结果
async def select(sql, args, size = None):
	log(sql, args)
	global __pool
	# 用with语句可以封装清理（关闭conn)和处理异常工作
	#with 语句将该方法的返回值赋值给 as 子句中的 target
	# 从连接池中获得一个数据库连接
	async with __pool.get() as conn:
		# 使用cursor()方法获取操作游标,cursor返回格式为字典格式，默认以列表list表示
		async with conn.cursor(aiomysql.DictCursor) as cur:
			#SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换
			# 使用execute方法执行SQL语句args
			await cur.execute(sql.replace('?', '%s'), args or ())
			if size:
				# 使用 fetchmany() 方法每次读取size的数据量。
				rs = await cur.fetchmany(size)
			else:
			#否则，通过fetchall()获取所有记录
				rs = await cur.fetchall()
		logging.info('rows returned: %s' % len(rs))
		return rs
		
#要执行INSERT、UPDATE、DELETE语句，可以定义一个通用的execute()函数
#因为这3种SQL的执行都需要相同的参数，以及返回一个整数表示影响的行数
async def execute(sql, args, autocommit=True):
    log(sql)
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            # execute类型sql操作返回结果只有行号，不需要dict
            async with conn.cursor() as cur:
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
		#cursor对象不返回结果集，而是通过rowcount返回受影响的行数
        return affected
		
# 这个函数在元类中被引用，作用是创建一定数量的占位符
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    #比如说num=3，那L就是['?','?','?']，通过下面这句代码返回一个字符串'?,?,?'
    return ', '.join(L)

# =====================================Field定义域区==============================================
# 首先来定义Field类，它负责保存数据库表的字段名和字段类型

# 父定义域，可以被其他定义域继承
class Field(object):
    # 定义域的初始化，包括属性（列）名，属性（列）的类型，主键，默认值
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default  # 如果存在默认值，在getOrDefault()中会被用到

    # 定制输出信息为 类名，列的类型，列名
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

#继承于Field
class StringField(Field):
    #ddl是数据定义语言("data definition languages")，默认值是'varchar(100)'，意思是可变字符串，长度为100
    #和char相对应，char是固定长度，字符串长度不够会自动补齐，varchar则是多长就是多长，但最长不能超过规定长度
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		#子类重写了父类中同名方法__init__，在重写的实现中通过super实例化的代理对象调用父类的同名方法
        super().__init__(name, ddl, primary_key, default)

class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

# =====================================Model元类区==========================================

# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作  
   
# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：  
# ***读取具体子类(user)的映射信息  
# 创造类的时候，排除对Model类的修改  
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除Field(防止实例属性遮住类的同名属性)  
# 将数据库表名保存到__table__中 
# metaclass是类的模板，所以必须从`type`类型派生：
class ModelMetaclass(type):
	# __new__控制__init__的执行，所以在其执行之前  
    # cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)  
    # bases：代表继承父类的集合  
    # attrs：类的方法集合
    def __new__(cls, name, bases, attrs):
        # 排除Model类本身，因为要排除对model类的修改
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名称，如果存在表名，则返回表名，否则返回 name
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        # 先定义空的字典、列表，用来获取所有定义域中的属性和主键
        mappings = dict()
		#fields保存的是除主键外的属性名
        fields = []
        primaryKey = None
        for k, v in attrs.items():# 这个k是表示字段名 
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                # 先判断找到的映射是不是主键
                if v.primary_key:
                    if primaryKey:  # 若主键已存在（已被赋值）,又找到一个主键,将报错,每张表'有且仅有'一个主键
                        raise StandardError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        # 如果没有找到主键，也会报错
        if not primaryKey:
            raise StandardError('Primary key not found.')
        # 定义域中的key值已经添加到fields里了，就要在attrs中删除，避免重名导致运行时错误
        for k in mappings.keys():
            attrs.pop(k)
        # 将非主键的属性变形成这种反单引号形式,放入escaped_fields中,方便sql语句的书写
		#x = range(10)
		#print(list(map(hex, x)))
		#print(list(map(lambda y : y * 2 + 1, x)))  
		#print(list(map(lambda y, z : y * 2 + z, x, x))) 
		#结果输出：
		#['0x0', '0x1', '0x2', '0x3', '0x4', '0x5', '0x6', '0x7', '0x8', '0x9']
		#[1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
		#[0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = tableName  # 表名
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        # 构造默认的SELECT, INSERT, UPDATE, DELETE语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)

# =====================================Model基类区==========================================

# 定义所有ORM映射的基类Model， 使他既可以像字典那样通过[]访问key值，也可以通过.访问key值
# 继承dict是为了使用方便，例如对象实例user['id']即可轻松通过UserModel去数据库获取到id
# 元类自然是为了封装我们之前写的具体的SQL处理函数，从数据库获取数据
# ORM映射基类,通过ModelMetaclass元类来构造类
# Model类可以看作是对所有数据库表操作的基本定义的映射 
class Model(dict, metaclass=ModelMetaclass):
    # 这里直接调用了Model的父类dict的初始化方法，把传入的关键字参数存入自身的dict中
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    # 获取dict的key
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    # 设置dict的值的，通过d.k = v 的方式
    def __setattr__(self, key, value):
        self[key] = value

    # 获取某个具体的值即Value,如果不存在则返回None
    def getValue(self, key):
        # getattr(object, name[, default]) 根据name(属性名）返回属性值，默认为None
        return getattr(self, key, None)

    # 与上一个函数类似，但是如果这个属性与之对应的值为None时，就需要返回定义的默认值
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            # self.__mapping__在metaclass中，用于保存不同实例属性在Model基类中的映射关系
            # field是一个定义域!
            field = self.__mappings__[key]
            # 如果field存在default属性，那可以直接使用这个默认值
            if field.default is not None:
                # 如果field的default属性是callable(可被调用的)，就给value赋值它被调用后的值，如果不可被调用直接返回这个值
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                # 把默认值设为这个属性的值
                setattr(self, key, value)
        return value

	# ==============往Model类添加类方法，就可以让所有子类调用类方法=================

    @classmethod  # 这个装饰器是类方法的意思，即可以不创建实例直接调用类方法
	# 类方法有类变量cls传入，从而可以用cls做一些相关的处理。
	# 并且有子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。
    async def find(cls, pk):
        '''查找对象的主键'''
        # select函数之前定义过，这里传入了三个参数分别是之前定义的 sql、args、size
        rs = await select("%s where `%s`=?" % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
		# **rs 是关键字参数，rs接收的是是一个dict，此处为select语句返回的查询结果
        return cls(**rs[0])

    # findAll() - 根据WHERE条件查找
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        # __select__调用后格式为'select `%s`, %s from `%s`'
        sql = [cls.__select__]
        # 如果有where参数就在sql语句中添加字符串where和参数where
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:  # 这个参数是在执行sql语句前嵌入到sql语句中的，如果为None则定义一个空的list
            args = []
        # 如果有OrderBy参数就在sql语句中添加字符串OrderBy和参数OrderBy，但是OrderBy是在关键字参数中定义的
        orderBy = kw.get("orderBy", None)
        if orderBy:
            sql.append("order by")
            sql.append(orderBy)
        limit = kw.get("limit", None)
        if limit is not None:
            sql.append("limit")
            if isinstance(limit, int):
                sql.append("?")
                args.append(limit)
            if isinstance(limit, tuple) and len(limit) == 2:
                sql.append("?,?")
                args.extend(limit)  # extend() 函数用于在列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表）。
            else:
                raise ValueError("错误的limit值：%s" % limit)
        rs = await select(" ".join(sql), args)
        return [cls(**r) for r in rs]

    # findNumber() - 根据WHERE条件查找，但返回的是整数，适用于select count(*)类型的SQL。
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append("where")
            sql.append(where)
        rs = await select(" ".join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

	# ===============往Model类添加实例方法，就可以让所有子类调用实例方法===================

    # save、update、remove这三个方法需要管理员权限才能操作，所以不定义为类方法，需要创建实例之后才能调用
    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))  # 将除主键外的属性名添加到args这个列表中
        args.append(self.getValueOrDefault(self.__primary_key__))  # 再把主键添加到这个列表的最后
        rows = await execute(self.__insert__, args)
        if rows != 1:  # 插入纪录受影响的行数应该为1，如果不是1 那就错了
            logging.warn("无法插入纪录，受影响的行：%s" % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)

# =====================================调试区==========================================

if __name__=='__main__':#一个类自带前后都有双下划线的方法，在子类继承该类的时候，这些方法会自动调用，比如__init__  
    #定义类的属性到列的映射，与本地数据库中的数据表保持一致！！
    class students(Model): #虽然students类乍看没有参数传入，但实际上，students类继承Model类，Model类又继承dict类，所以students类的实例可以传入关键字参数  
        id = IntegerField('id',primary_key=True) #主键为id， tablename为students，即类名  
        name = StringField('name')  
        sex = StringField('sex')  
        age = IntegerField('age')  
        tel = StringField('tel')  
   
    #创建实例  
    async def test():  
        await create_pool(loop=loop, host='localhost', port=3306, user='root', password='1234', db='mydatabse')  
        mystudents = students(id=3, name='Fiona', sex='F', age=18, tel='123456')  
		# 保存到数据库
        await mystudents.save()
        r = await students.findAll()  
        print(r)
   
    #创建异步事件的句柄  
    loop = asyncio.get_event_loop()  
    loop.run_until_complete(test())
    loop.close()
    if loop.is_closed():  
        sys.exit(0)  

# ===============调试结果===================
#[{'id': 1, 'name': 'Tom', 'sex': 'M', 'age': 17, 'tel': '111111'}, {'id': 2, 'name': 'Lucy', 'sex': 'F', 'age': 18, 'tel': '123456'}, {'id': 3, 'name': 'Fiona', 'sex': 'F', 'age': 18, 'tel': '123456'}]
