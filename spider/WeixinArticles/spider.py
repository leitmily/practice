# coding: utf-8
from urllib.parse import urlencode
from lxml.etree import XMLSyntaxError
from requests.exceptions import ConnectionError
import requests
from fake_useragent import UserAgent
from pyquery import PyQuery as pq
import pymongo
from config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

base_url = 'http://weixin.sogou.com/weixin?'


proxy = None


def get_proxy():
    response = requests.get(PROXY_POOL_URL)
    try:
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def get_html(url, count=1):
    print('Crawling', url)
    print('Trying count', count)
    global proxy
    ua = UserAgent()
    if count > MAX_COUNT:
        print('Tried too many counts')
        return None

    headers = {
        'Cookie': 'IPLOC=CN6101; SUID=7D0B8C712213940A000000005B350607; SUV=1530201607595340; ABTEST=7|1530201611|v1; SNUID=E3B20FA79A9FF62C49EFE65E9A871C56; weixinIndexVisited=1; sct=2; JSESSIONID=aaaGG94Cp3gMv_ieB6frw; ld=RZllllllll2b2bcVlllllV7Cs0DllllltYZaxyllllwlllll4ylll5@@@@@@@@@@; PHPSESSID=f3dmi1ltqedg6jso77v4qolgn3; SUIR=E3B20FA79A9FF62C49EFE65E9A871C56; LSTMV=411%2C24; LCLKINT=4824; ppinf=5|1530335357|1531544957|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTo1OmRlZW1vfGNydDoxMDoxNTMwMzM1MzU3fHJlZm5pY2s6NTpkZWVtb3x1c2VyaWQ6NDQ6bzl0Mmx1UEozVUdRNVkzNThDbTEzSDNXLWRYQUB3ZWl4aW4uc29odS5jb218; pprdig=phDTuyiWdagCQ8YuDlpH6igQv6MF5BTpXkkpv6N4dF1LosRKhjJlit2pbaJT8sMghduv9Ng7c3vki4bJuYyHdp_Z2Kwge6G3tP_itWZj0mS62xYp9Zn45QrsTsF0OStC52iZQYpjD02kYX5880Pz_bJU46X-u5I2zbctDW_7Gyk; sgid=10-34144725-AVs3EH2NGPTXHZ03MdK2ToE; ppmdig=15303353570000002461a59e8ced05958b05355819ccc6cb',
        'Host': 'weixin.sogou.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': ua.random
    }
    try:
        if proxy:
            print('Using proxy', proxy)
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects=False, headers=headers, proxies=proxies)  # 不自动跳转
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)  # 不自动跳转
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            # Need Proxy
            print(302)
            proxy = get_proxy()
            if proxy:
                count += 1
                return get_html(url)  # 更换代理，重新尝试
            else:
                print('Get Proxy Failed')
                return None
    except ConnectionError as e:  # 访问页面出错
        print('Error Occurred', e.args)
        count += 1
        proxy = get_proxy()
        return get_html(url, count)


def get_index(key, page):
    data = {
        'query': key,
        'page':	page,
        'type': 2
    }
    queries = urlencode(data)
    url = base_url + queries
    return get_html(url)


def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')


def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def parse_detail(html):
    try:
        doc = pq(html)
        title = doc('.rich_media_title').text()
        content = doc('.rich_media_content').text()  # 获取该标签下的所有文字信息
        date = doc('#publish_time').text()
        nickname = doc('.rich_media_meta_list #js_name').text()
        wechat = doc('p.profile_meta:nth-child(3) > span:nth-child(2)').text()
        return {
            'title': title,
            'content': content,
            'date': date,
            'nickname': nickname,
            'wechat': wechat
        }
    except XMLSyntaxError:
        return None


def save_to_mongo(data):
    if db['articles'].update({'title': data['title']}, {'$set': data}, True):
        print('Saved to mongo', data['title'])
    else:
        print('Saved to mongo failed', data['title'])


def main():
    for i in range(1, 101):
        html = get_index(KEYWORD, i)
        if html:
            for article_url in parse_index(html):
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    if article_data:
                        save_to_mongo(article_data)


if __name__ == '__main__':
    main()

