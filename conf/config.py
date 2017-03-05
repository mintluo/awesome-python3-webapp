#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'milletluo'

'''
Configuration
'''

# 导入默认配置
import config_default

# 这个类很常见(orm中Model)，把dict类加工一下，使得新的Dict类创建的实例可以用x.y的方式来取值和赋值
class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        #zip返回由这些tuples组成的list（列表）
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

# 融合默认配置和自定义配置
def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            #如果该配置是字典，递归
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

# 这个函数的功能是把一个普通的字典转化为上面我们新建的类实现的那种字典
def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D

configs = config_default.configs

try:
    import config_override  # 导入自定义配置
    configs = merge(configs, config_override.configs)  # 融合自定义配置和默认配置
except ImportError:  # 导入自定义配置失败就直接pass跳过
    pass

configs = toDict(configs)  # 把配置字典转化成我们刚才新建类实现的那种字典
