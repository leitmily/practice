# coding:utf-8

from urllib import request

class HtmlDownloader(object):
    def download(self, url):
        if url is None:
            return None
        with request.urlopen(url) as response:
            if response.status != 200:
                return None
            # print(response.status)
            return response.read().decode('utf-8')