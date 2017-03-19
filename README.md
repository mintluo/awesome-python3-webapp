# 引言
断断续续终于过了一遍[廖雪峰的Python教程](http://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000)，于此梳理教程实战作业：搭建一个Blog网站。
由于欠缺前端知识，有些代码直接引用于项目源码，个人做了尽量详尽的注释以帮助理解，希望在今后能够学习HTML、CSS、JavaScript等知识，然后回头重新理解本项目。
作业托管于[我的github](https://github.com/milletluo/awesome-python3-webapp)
# 文件结构
```
awesome-python3-webapp/		<--根目录
|
+-www/                    	<--web项目目录
	|
	+-static/               <--静态资源目录
	|
	+-templates/            <--模板文件目录
	|	|
	|	+-__base__.html         <--基础模版，父模版
	|	|
	|	+-blog.html             <--文章详情模版，后加文章id构成完整路径
	|	|
	|	+-blogs.html            <--首页模版
	|	|
	|	+-manage_blog_edit.html <--编辑文章模版
	|	|
	|	+-manage_blogs.html     <--文章管理模版
	|	|
	|	+-manage_comments.html  <--评论管理模版
	|	|
	|	+-manage_users.html     <--用户管理模版
	|	|
	|	+-register.html         <--注册模版
	|	|
	|	+-signin.html           <--登陆模板
	|
	+-apis.py       　　   <--api接口，定义几个错误异常类和Page类用于分页
	|
	+-app.py       　　    <--HTTP服务器以及处理HTTP请求；拦截器、jinja2模板、URL处理函数注册等
	|
	+-config.py           <--默认和自定义配置文件合并
	|
	+-config_default.py   <--默认的配置文件信息
	|
	+-config_override.py  <--自定义的配置文件信息
	|
	+-coroweb.py       　　<--封装aiohttp，即写个装饰器更好的从Request对象获取参数和返回Response对象
	|
	+-favicon.ico         <--网页缩略图标
	|
	+-handlers.py         <--处理各种URL请求
	|
	+-markdown2.py        <--支持markdown显示的插件
	|
	+-models.py        　 <--采用ORM构建三个映射数据库表的类：User、Blog、Comment
	|
	+-models_test.py      <--测试ORM
	|
	+-orm.py              <--ORM框架
	|
	+-pymonitor.py        <--用于支持自动检测代码改动重启服务
	|
	+-schema.sql          <--创建表的SQL脚本
```

# 关键技术
## 1.http工作流程
![http流程](http://img.blog.csdn.net/20170319192219640?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvbG00MDk=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)
1. 客户端（浏览器）发起请求  
2. 路由分发请求（这个框架自动帮处理），add_routes函数就是注册路由。  
3. 中间件预处理  
   - 打印日志
   - 验证用户登陆
   - 收集Request（请求）的数据
4. RequestHandler清理参数并调用控制器（Django和Flask把这些处理请求的控制器称为view functions）
5. 控制器做相关的逻辑判断，有必要时通过ORM框架处理Model的事务。
6. 模型层的主要事务是数据库的查增改删。
7. 控制器再次接管控制权，返回相应的数据。
8. Response_factory根据控制器传过来的数据产生不同的响应。
9. 客户端（浏览器）接收到来自服务器的响应。

## 2.ORM框架Day3-Day4
> ORM全称为对象关系映射(Object Relation Mapping)，即用一个类来对应数据库中的一个表，一个对象来对应数据库中的一行，表现在代码中，即用**类属性**来对应一个表，用**实例属性**来对应数据库中的一行。具体步骤如下：

1. orm.py中实现**元类** ModelMetaclass：创建一些特殊的类属性，用来完成类属性和表的映射关系，并定义一些默认的SQL语句，如SELECT, INSERT, UPDATE, DELETE等
2. orm.py实现Model类：包含基本的getattr,setattr方法用于获取和设置实例属性的值，并实现相应的SQL处理函数，如find、findAll、save、remove等
3. model.py中实现三个映射数据库表的类：User、Blog、Comment，在应用层用户只要使用这三个类即可  

## 3.web框架Day5
> aiohttp已经是一个Web框架了，在此主要对aiohttp库做更高层次的封装，从简单的WSGI接口到一个复杂的web framework，本质上还是对request请求对象和response响应对象的处理，可以将这个过程想象成工厂中的一条流水线生产产品，request对象就是流水线的原料，这个原料在经过一系列的加工后，生成一个response对象返回给浏览器。具体步骤如下：

1. coroweb.py中@get()装饰器给http请求添加请求方法和请求路径这两个属性；RequestHandler()调用url参数，将结果转换位web.response
2. app.py中传入拦截器middlewares，通过add_routes()批量注册URL处理函数、init_jinja2()初始化jinja2模版、add_static()添加静态文件路径
3. create_server()创建服务器监听线程
4. 监听线程收到一个request请求
5. 经过几个拦截器(middlewares)的处理(app.py中的app = web.Application..这条语句指定)
6. 调用RequestHandler实例中的__call__方法；再调用__call__方法中的post或者get方法
7. 调用handlers.py中响应的URL处理函数，并返回结果
8. response_factory在拿到经URL处理函数返回过来的对象，经过一系列类型判断后，构造出正确web.Response对象，返回给客户端
# 作业成果
###博客首页：
![博客首页](http://img.blog.csdn.net/20170319233158620?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvbG00MDk=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

###写博客：
![写博客](http://img.blog.csdn.net/20170319233225763?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvbG00MDk=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

###文章管理：
![管理博客](http://img.blog.csdn.net/20170319233313779?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvbG00MDk=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

###文章详情：
![博客详情](http://img.blog.csdn.net/20170319233404732?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvbG00MDk=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)
# 总结
通过该作业，基本了解了一个webapp的开发流程和部分技术，了解了http的工作原理，复习了python的使用。但是也深刻认识到python知识点的不熟练和前端相关知识的匮乏，后续仍要加强python项目练习和前端知识的学习。
# 参考
[廖雪峰官网Blog网站实战
](http://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/001432170876125c96f6cc10717484baea0c6da9bee2be4000)
[moling3650/mblog
](https://github.com/moling3650/mblog)
[zhouxinkai/awesome-python3-webapp
](https://github.com/zhouxinkai/awesome-python3-webapp)
[ReedSun/Preeminent
](https://github.com/ReedSun/Preeminent)
