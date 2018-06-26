import time
from multiprocessing import Process
import asyncio
import aiohttp

try:
    from aiohttp.errors import ProxyConnectionError, ServerDisconnectedError, ClientResponseError, ClientConnectorError
except:
    from aiohttp import ClientProxyConnectionError as ProxyConnectionError, ServerDisconnectedError, \
    ClientResponseError, ClientConnectorError, ClientOSError
from proxypool.db import RedisClient
from proxypool.error import ResourceDepletionError
from proxypool.getter import FreeProxyGetter
from proxypool.setting import *
from asyncio import TimeoutError


class ValidityTester(object):  # 检测代理是否有效，将有效的代理存入redis
    test_api = TEST_API

    def __init__(self):
        self._conn = None
        self._raw_proxies = None  # 存储原始代理数据，列表类型
        self._usable_proxies = []

    def set_raw_proxies(self, proxies):
        self._raw_proxies = proxies
        self._conn = RedisClient()  # redis连接对象

    async def test_single_proxy(self, proxy):  # 异步检测单个代理地址
        """
        text one proxy, if valid, put them to usable_proxies.
        """
        try:
            async with aiohttp.ClientSession() as session:  # 异步请求
                try:
                    if isinstance(proxy, bytes):
                        proxy = proxy.decode('utf-8')
                    real_proxy = 'http://' + proxy  # 代理地址
                    print('Testing', proxy)
                    async with session.get(self.test_api, proxy=real_proxy, timeout=get_proxy_timeout) as response:
                        if response.status == 200:
                            self._conn.put(proxy)  # 有效代理，存入redis
                            print('Valid proxy', proxy)
                except (ProxyConnectionError, TimeoutError, ValueError):  # 无效代理
                    print('Invalid proxy', proxy)
        except (ServerDisconnectedError, ClientResponseError, ClientConnectorError, ClientOSError) as s:
            print('async error:', s)
            pass

    def test(self):  # 测试代理
        """
        aio test all proxies.
        """
        print('ValidityTester is working')
        try:
            loop = asyncio.get_event_loop()
            tasks = [self.test_single_proxy(proxy) for proxy in self._raw_proxies]  # 添加多个任务同时进行检测
            loop.run_until_complete(asyncio.wait(tasks))  # 开启异步事件
        except ValueError:
            print('Async Error')


class PoolAdder(object):
    """
    add proxy to pool
    """

    def __init__(self, threshold):
        self._threshold = threshold  # 代理数量上限
        self._conn = RedisClient()
        self._tester = ValidityTester()  # 检测代理并存入redis
        self._crawler = FreeProxyGetter()  # 从网页中获取免费代理

    def is_over_threshold(self):
        """
        judge if count is overflow.
        """
        if self._conn.queue_len >= self._threshold:
            return True
        else:
            return False

    def add_to_queue(self):
        print('PoolAdder is working')
        proxy_count = 0
        while not self.is_over_threshold():
            for callback_label in range(self._crawler.__CrawlFuncCount__):
                callback = self._crawler.__CrawlFunc__[callback_label]  # 获取解析代理地址的回调函数
                raw_proxies = self._crawler.get_raw_proxies(callback)  # 执行回调函数，返回原始代理地址
                # test crawled proxies
                self._tester.set_raw_proxies(raw_proxies)
                self._tester.test()  # 检测代理并存入redis
                proxy_count += len(raw_proxies)
                if self.is_over_threshold():
                    print('IP is enough, waiting to be used')
                    break
            if proxy_count == 0:
                # raise ResourceDepletionError
                continue


class Schedule(object):
    @staticmethod
    def valid_proxy(cycle=VALID_CHECK_CYCLE):
        """
        Get half of proxies which in redis
        """
        conn = RedisClient()  # redis连接对象
        tester = ValidityTester()  # 代理检测对象
        while True:
            print('Refreshing ip')
            count = int(0.5 * conn.queue_len)  # 需要从redis中取出一半的代理地址
            if count == 0:
                print('Waiting for adding')
                time.sleep(cycle)
                continue
            raw_proxies = conn.get(count)  # 从redis中取出一半的代理地址,返回列表
            tester.set_raw_proxies(raw_proxies)
            tester.test()
            time.sleep(cycle)

    @staticmethod
    def check_pool(lower_threshold=POOL_LOWER_THRESHOLD,
                   upper_threshold=POOL_UPPER_THRESHOLD,
                   cycle=POOL_LEN_CHECK_CYCLE):
        """
        If the number of proxies less than lower_threshold, add proxy
        """
        conn = RedisClient()
        adder = PoolAdder(upper_threshold)
        while True:
            if conn.queue_len < lower_threshold:
                adder.add_to_queue()
            time.sleep(cycle)

    @staticmethod
    def run():
        print('Ip processing running')
        valid_process = Process(target=Schedule.valid_proxy)  # 检测代理是否有效
        check_process = Process(target=Schedule.check_pool)  # 获取代理地址，并做筛选,结果存入redis
        valid_process.start()
        check_process.start()
