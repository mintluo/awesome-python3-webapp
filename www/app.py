import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

def index(request):
#返回首页内容
    return web.Response(body=b'<hl>Awesome</hl>',content_type='text/html',charset='UTF-8')
#如果不添加content_type和charset参数（默认值是None），则服务器直接返回body，浏览器识别不老该页面内容，从而提示下载该页面文件。

#init含有yield，是个生成器。@asyncio.coroutine把一个generator标记为coroutine类型
@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET','/',index)
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
#从asyncio模块中直接获取一个EventLoop的引用，然后把需要执行的协程扔到EventLoop中执行
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
