#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'milletluo'

'''
这个脚本自动检查www目录下的.py文件的修改情况
用该脚本启动app.py，则当前目录下的任意.py文件被修改以后，服务器将自动重启
'''

import os, sys, time
# 该模块提供了派生新进程的能力
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 打印monitor日志信息
def log(s):
    print('[Monitor]%s' % s)

# 自定义的文件系统事件处理器，从watchdog.events.FileSystemEventHandler中继承
class MyFileSystemEventHandler(FileSystemEventHandler):
    # 初始化函数，将指定函数绑定到处理器的restart属性上
    def __init__(self, fn):
        super(MyFileSystemEventHandler, self).__init__()
        self.restart = fn
    # 覆盖on_any_event方法
    # on_any_event(event)捕获所有事件，文件或目录的创建，修改，删除等
    def on_any_event(self, event):
        # 此处只处理python脚本的事件
        if event.src_path.endswith('.py'):
            log('Python source file changed: %s' % event.src_path)
            self.restart()

# 要执行的程序
command = ['echo','ok']
process = None

# 杀死进程函数
def kill_process():
    global process
    if process:
        # process指向一个在start_process函数中被创建的Popen对象
        # 通过发送一个SIGKILL给子程序, 来杀死子程序. SIGKILL信号将不会储存数据, 此处也不需要
        # wait(timeout=None),等待进程终止,并返回一个结果码. 该方法只是单纯地等待, 并不会调用方法来终止进程, 因此需要kill()方法
        log('Kill process [%s]...' % process.pid)
        process.kill()
        process.wait()
        log('Process ended with code %s.' % process.returncode)
        process = None

# 启动进程程序
def start_process():
    global process, command
    log('Start process %s...' % ' '.join(command))
    # subprocess.Popen是一个构造器, 它将在一个新的进程中执行子程序
    # command是一个list, 即sequence. 此时, 将被执行的程序应为序列的第一个元素, 此处为python3
    process = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

# 先杀死进程，然后重启进程
def restart_process():
    kill_process()
    start_process()

# 启动看门狗
def start_watch(path, callback):
    # 创建监视器对象
    observer = Observer()
    # 重启进程函数绑定到处理的restart属性上
    # 为监视器对象安排时间表，即将处理器，路径注册到监视器对象上
    # 监控指定路径path，该路径触发任何事件都会调用event_handler来处理
    # recursive=True表示递归，即当前目录的子目录也在被监视范围内
    observer.schedule(MyFileSystemEventHandler(restart_process), path, recursive=True)
    # 启动监视器
    observer.start()
    log('Watching directory %s...' % path)
    # 启动进程，通过调用subprocess.Popen方法启动一个python子程序的进程
    start_process()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    argv = sys.argv[1:]
    # 如果没启动要监视的脚本，只是单一的启动了此脚本,即pymonitor.py
    if not argv:
        print('Usage: ./pymonitor your-script.py')
        exit(0)
    # 如果第一个参数不是python，添加python，这样才能在命令行中成功运行py脚本
    if argv[0] != 'python':
        argv.insert(0,'python')
    # 将输入参数赋值给command
    command = argv
    # 获取当前目录的绝对路径表示
    path = os.path.abspath('.')
    start_watch(path, None)
