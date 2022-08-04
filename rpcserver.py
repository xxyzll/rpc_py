# rpcserver.py
import socket
import json
from concurrent.futures import ThreadPoolExecutor
import select


def act(client_socket, event, funs):
    # 接受数据
    rev_json = json.loads(client_socket.recv(1024).decode('utf-8'))
    print(rev_json)
    # 调用方法
    call_method = rev_json['method_name']
    method_args = rev_json['method_args']
    method_kwargs = rev_json['method_kwargs']

    if(call_method not in funs):
        res = f"not func {call_method}"
    else: 
        res = funs[call_method](*method_args, **method_kwargs)
    data = {"res": res}
    # 返回结果
    client_socket.send(json.dumps(data).encode('utf-8'))


class RPCServer(object):
    def __init__(self, address, port, backlog=128, num_works=8):
        """
            address: 绑定地址，一般是本地地址
            port: 端口
            backlog: 半连接队列
            num_works: 线程池数量
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

    def run(self):
        try:
            connections = {}; requests = {}; responses = {}
            error_events = [select.EPOLLERR, select.EPOLLHUP, select.EPOLLMSG]
            while True:
                events = self.epoll.poll(-1)
                print(f'有{len(events)}个事件发生')
                for fileno, event in events:
                    # 新连接
                    if fileno == self.listen_socket.fileno():
                        client_socket, addr = self.listen_socket.accept()
                        self.epoll.register(client_socket.fileno(), select.EPOLLIN)
                        connections[client_socket.fileno()] = client_socket
                        client_socket.setblocking(0)
                        print(f'客户{addr} 已经连接')
                    elif (event & select.EPOLLIN) or (event & select.EPOLLOUT):
                        self.th_pool.submit(act, connections[fileno], event, self.func)
                        print(f'提交任务')

                    for idx, e in enumerate(error_events):
                        if(e & event):
                            print(f'{idx}错误发生')
                            break
        finally:
            # 关闭对应的文件描述符
            self.epoll.unregister(self.listen_socket.fileno())
            self.epoll.close()
            self.listen_socket.close()
        
    # 注册一个函数
    def register(self, func, name=None):
        if(name is None):
            name = func.__name__
        self.func[name] = func

