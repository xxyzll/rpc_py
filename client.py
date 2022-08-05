import rpcclient
import time

c = rpcclient.RPCClient()
c.connect('192.168.31.132', 10000)

while(1):
    res = c.add(1, 2, c=3)
    print(f'res: [{res}]')
    time.sleep(5)



