# rpcserver.py
from asyncore import write
from gc import callbacks
from operator import truediv
import socket
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import select
import traceback
import ctypes
import os
import schedule
from connect_contrl import connect_contrl


SYS_gettid = 186
libc = ctypes.cdll.LoadLibrary('libc.so.6')
class RPCServer(object):
    def __init__(self, address, port, backlog=128, 
                num_works=8, pipe='pipe.rpc', time_inter=1):
        """
            address: 绑定地址，一般是本地地址
            port: 端口
            backlog: 半连接队列
            num_works: 线程池数量
            pipe: 命名管道
            time_inter: 定时器间隔
        """
        # TCP相关
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        # TCP
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)      # IO复用
        self.listen_socket.bind((address, port))                                      # 地址和端口绑定
        self.listen_socket.listen(backlog)
        self.listen_socket.setblocking(0)                                             # 非阻塞模式

        # EPOLL相关
        self.epoll = select.epoll()
        self.epoll.register(self.listen_socket.fileno(), select.EPOLLIN)              # listen注册socket
    
        # 线程池对象
        self.th_pool = ThreadPoolExecutor(max_workers=num_works)
        
        # 支持的方法函数
        self.func = {}

        # 定时连接控制
        self.time_inter = time_inter
        self.CC = connect_contrl(time_inter)

    def run(self):
        self.connections = {}
        self.response = {}
        try:      
            error_events = [select.EPOLLERR, select.EPOLLHUP, select.EPOLLMSG]
            while True:
                events = self.epoll.poll(self.time_inter)
                for fileno, event in events:
                    # 新连接
                    if fileno == self.listen_socket.fileno():
                        client_socket, addr = self.listen_socket.accept()
                        self.epoll.register(client_socket.fileno(), select.EPOLLIN | select.EPOLLONESHOT)
                        self.connections[client_socket.fileno()] = client_socket
                        client_socket.setblocking(0)
                        self.CC.add_connect(client_socket.fileno())
                    else:
                        self.CC.modify(fileno)
                        if (event & select.EPOLLIN or event & select.EPOLLOUT):
                            t = self.th_pool.submit(self.action, fileno, event)
                            t.add_done_callback(self.callback)  
                self.check_connect()
        finally:
            # 关闭对应的文件描述符
            self.epoll.unregister(self.listen_socket.fileno())
            self.epoll.close()
            self.listen_socket.close()

    def check_connect(self):
        fds = self.CC.check()
        for fd in fds:
            self.clear_connect(fd)

    def callback(self, ret):
        res = ret.result()
        if(res[0] == False):
            self.clear_connect(res[1])
            self.CC.del_node(res[1])

    # 注册一个函数
    def register(self, func, name=None):
        if(name is None):
            name = func.__name__
        self.func[name] = func

    # 做任务
    def action(self, fd, event):
        # 有数据读取
        if(event & select.EPOLLIN):
            # 接受数据
            try:
                rev_str = self.connections[fd].recv(1024).decode('utf-8')
                # 对面可能关闭了
                if(len(rev_str) == 0):
                    return (False, fd)
                rev_json = json.loads(rev_str)
               # 调用方法
                call_method = rev_json['method_name']
                method_args = rev_json['method_args']
                method_kwargs = rev_json['method_kwargs']

                if(call_method not in self.func):
                    res = f"not func {call_method}"
                else: 
                    res = self.func[call_method](*method_args, **method_kwargs)
                data = {"res": res}
                self.response[fd] = json.dumps(data).encode('utf-8')
                self.modify(fd, epoll_out=True)
            except :
                # 输出错误原因
                print(traceback.format_exc())
                return (False, fd)
        if(event & select.EPOLLOUT):
            has_send = self.connections[fd].send(self.response[fd])
            self.response[fd] = self.response[fd][has_send:]
            # 数据发送完毕
            if(len(self.response[fd]) == 0):
                self.modify(fd, epoll_in=True)

        return (True, fd)

    # 修改一个文件描述符
    def modify(self, fd,
                     epoll_in=False,
                     epoll_out=False,
                     epoll_oneshort=True,
                     epoll_et = True):
        figs = [select.EPOLLIN, select.EPOLLOUT, select.EPOLLONESHOT, select.EPOLLET]
        args = [epoll_in, epoll_out, epoll_oneshort, epoll_et]
        set_fig = 0
        for arg, fig in zip(args, figs):
            if arg:
                set_fig |= fig
        self.epoll.modify(fd, set_fig)

    # 清除一个连接
    def clear_connect(self, fd):
        self.CC.print_all_connect()
        self.epoll.unregister(fd)
        self.connections[fd].close()
        self.CC.del_node(fd)
        del self.connections[fd]
        del self.response[fd]
        self.CC.print_all_connect()
