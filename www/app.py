import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

#request为aiohttp.web.request实例，包含http请求的信息，一般不用自己构造
def index(request):
#返回首页内容
    return web.Response(body=b'<hl>Awesome Blog</hl>',content_type='text/html',charset='UTF-8')
#如果不添加content_type和charset参数（默认值是None），则服务器直接返回body，浏览器识别不了该页面内容，从而提示下载该页面文件。

#init含有yield，是个生成器generator。@asyncio.coroutine把一个generator标记为协程coroutine类型
#然后，我们就把这个coroutine扔到EventLoop中执行。
#协程内部可以用yield from调用另一个协程
@asyncio.coroutine#实现异步IO
def init(loop):
	#创建web服务器实例app，loop: event loop used for processing HTTP requests
    app = web.Application(loop=loop)
	#将处理函数注册到app.router中，这里应该就是说把index函数注册为request '/' 的处理函数
    app.router.add_route('GET','/',index)
	
	#用协程创建监听服务。loop为传入函数的协程，调用其类方法创建一个监听服务
	#yield from返回一个创建好的，绑定IP、端口、http协议簇的监听服务协程
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
	#控制台打印日志
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
	
#从asyncio模块中直接获取一个EventLoop的引用，然后把需要执行的协程扔到EventLoop中执行
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
#运行协程，直到调用stop()
loop.run_forever()
