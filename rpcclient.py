from fileinput import hook_compressed
import socket
import json


class TCPClient(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        self.host = host
        self.port = port
        '''链接Server端'''
        self.sock.connect((host, port))

    def send(self, data):
        self.sock.send(data)

    def recv(self, length):
        '''接受Server端回传的数据'''
        return self.sock.recv(length)
    def __del__(self):
        self.sock.close()


class RPCStub(object):
    def __getattr__(self, function):
        def _func(*args, **kwargs):
            d = {'method_name': function, 'method_args': args, 'method_kwargs': kwargs}
            try:
                self.send(json.dumps(d).encode('utf-8')) 
                data = json.loads(self.recv(1024))['res'] 
            except:
                self.sock.close()
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connect(self.host, self.port)
                self.send(json.dumps(d).encode('utf-8')) # 发送数据
                data = json.loads(self.recv(1024))['res'] # 接收方法执行后返回的结果
            return data

        setattr(self, function, _func)
        return _func

class RPCClient(TCPClient, RPCStub):
    def __del__(self):
        self.sock.close()