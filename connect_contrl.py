from operator import ne
import time


class Node(object):
    """双向链表节点"""
    def __init__(self, item=0, fd=0):
        self.item = item
        self.next = None
        self.prev = None
        self.fd = fd

class connect_contrl():
    def __init__(self, inter_time) -> None:
        """
            inter_time: 间隔时间
        """
        # begin 里面藏着用户数量
        self.begin = Node()
        self.end = Node()
        self.begin.next = self.end
        self.end.prev = self.begin
        self.has_connect = {}
        self.inter_time = inter_time

    # 在最后插入数据
    def insert(self, n: Node):
        tmp = self.end.prev
        tmp.next = n
        n.prev = tmp
        n.next = self.end
        self.end.prev = n
        self.begin.item += 1

    def add_connect(self, fd):
        self.has_connect[fd] = Node(item = int(time.time())+self.inter_time, fd=fd)
        self.insert(self.has_connect[fd])

    def del_node(self, fd) -> bool:
        # 没有在
        if(fd not in self.has_connect):
            return True

        self.has_connect[fd].prev.next = self.has_connect[fd].next
        self.has_connect[fd].next.prev = self.has_connect[fd].prev
        self.begin.item -= 1
        del self.has_connect[fd]
        return True

    def modify(self, fd) ->bool:
        # 没有在
        if(fd not in self.has_connect):
            return False
        self.del_node(fd)
        self.add_connect(fd)

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

    def get_connect_num(self):
        return self.begin.item

    def print_all_connect(self):
        work = self.begin.next
        fds = []
        while(work != self.end):
            fds.append(work.fd)
            work = work.next
     
