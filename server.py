# server.py

import rpcserver

def add(a, b, c=10):
    sum = a + b + c
    return sum

s = rpcserver.RPCServer('192.168.31.132', 10000)
s.register(add)
s.run()