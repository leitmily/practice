import redis
from proxypool.error import PoolEmptyError
from proxypool.setting import HOST, PORT, PASSWORD


class RedisClient(object):  # redis基本操作封装
    def __init__(self, host=HOST, port=PORT):
        if PASSWORD:
            self._db = redis.Redis(host=host, port=port, password=PASSWORD)
        else:
            self._db = redis.Redis(host=host, port=port)

    def get(self, count=1):  # 取出前count个数据，并从队列（表）中删除
        """
        get proxies from redis
        """
        proxies = self._db.lrange("proxies", 0, count - 1)  # 从队列的左侧取出数据，lrange()为范围查找，返回list
        self._db.ltrim("proxies", count, -1)  # ltrim为修剪队列，只保留队列起始下标到结束下标之间的数据
        return proxies

    def put(self, proxy):  # 在队列右侧添加元素
        """
        add proxy to right top
        """
        self._db.rpush("proxies", proxy)

    def pop(self):  # 从队列右侧取出元素，并返回
        """
        get proxy from right.
        """
        try:
            return self._db.rpop("proxies").decode('utf-8')
        except:
            return 'The proxy pool is empty'
            # raise PoolEmptyError

    @property  # 将类方法编程类属性
    def queue_len(self):  # 返回队列长度
        """
        get length from queue.
        """
        return self._db.llen("proxies")

    def flush(self):  # 刷星队列
        """
        flush db
        """
        self._db.flushall()


if __name__ == '__main__':
    conn = RedisClient()
    #conn.put('hello')
    print(conn.queue_len)
    print(conn.get())
