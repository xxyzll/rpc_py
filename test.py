from re import A
import rpcclient
import time

test_cnt = 10
c = rpcclient.RPCClient()
c.connect('192.168.31.132', 10000)


for i in range(test_cnt):
    a= time.time()
    if(c.add(1, 2, c=3) != 6):
        print('执行错误')
        break
    b= time.time()
    print((b-a))

