# PY_RPC 
- 事件驱动的reactor模型
- 线程池
- 链表定时断开非活跃连接

主线程轮询任务，仅负责新连接的接受; 具体的工作由子线程实现; 每收到一个任务时，提交任务到线程池中进行处理；
```python
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
        # 线程池
        t = self.th_pool.submit(self.action, fileno, event)
        t.add_done_callback(self.callback) 
```

定时断开非活跃连接在connect_contrl.py中实现，维护一个升序双链表定时检查双链表中时间是否到期，如有到期则结束当前连接
```python
def check(self):
    cur_time = int(time.time())
    work = self.begin.next
    fds = []
    while(work != self.end):
        tmp = work
        work = work.next
        if(tmp.item< cur_time):
            fds.append(tmp.fd)
            self.del_node(tmp)
        else:
            break
    return fds
```

返回需要结束的文件描述符，在主线程中: 
```python
def check_connect(self):
    fds = self.CC.check()
    for fd in fds:
        self.clear_connect(fd)
```