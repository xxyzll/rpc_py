# PY_RPC 
- 事件驱动的reactor模型
- 线程池

主线程轮询任务，仅负责新连接的接受; 具体的工作由子线程实现; 每收到一个任务时，提交任务到线程池中进行处理；
```python
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
```
