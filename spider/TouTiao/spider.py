import json
import os
import re
from hashlib import md5
from json import JSONDecodeError

import pymongo
import requests
# from urllib.parse import urlencode # urlencode对字典参数编码
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from multiprocessing import Pool
from config import *

client = pymongo.MongoClient(MONGO_URL, connect=False) # 生成mongol数据库客户端, connect参数用于解决多进程下的警告
db = client[MONGO_DB] # 创建一个对象

headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
        }

current_path = os.getcwd()

# 在xhr处获取请求方式
def get_page_index(keyword, offset): # 获取图集板块列表页面的HTML源码
    data = { # 请求参数，图集板块
        "autoload": "true",
        "count": 20,
        "cur_tab": 3,
        "format": "json",
        "from": "gallery",
        "keyword": keyword,
        "offset": offset
    }
    # url = 'https://www.toutiao.com/search_content/?' + urlencode(data) # 生成带参数的url
    url = 'https://www.toutiao.com/search_content/'
    try:
        response = requests.get(url, params=data, headers=headers) # 使用get请求
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None

def parse_page_index(html): # 根据图集板块的HTML源码获取每个列表所关联的网址
    try:
        data = json.loads(html) # 将json数据转换成字典对象
        if data and 'data' in data.keys(): # 判断data对象是否创建成功并且包含data键
            for item in data.get('data'):
                yield item.get('article_url')
    except JSONDecodeError:
        pass

def get_page_detail(url): # 根据列表所关联的网址获取目标页面的HTML源码
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页出错', url)
        return None

def parse_page_detail(html, url): # 目标页面解析，获取图片地址以及标题
    soup = BeautifulSoup(html, 'lxml')
    # title = soup.select('title')[0] # 使用css匹配标签，返回的是list,用索引[0]表示取其元素
    title = soup.title.string # 使用beautifulsoup模块获取网页title
    images_pattern = re.compile('JSON.parse\("(.*?)"\),', re.S) # 正则表达式匹配包含图集url的字符串
    result = re.search(images_pattern, html) # 匹配的结果
    if result:
        data = json.loads(result.group(1).replace(r'\"', '"')) # 获取组1的数据，其形式为字典形式，且键用双引号包含的字符串，并转化为json对象,结果为字典对象
        if data and 'sub_images' in data.keys(): # 若字典中包括我们想要的键
            sub_images = data.get('sub_images')
            images = [item.get('url').replace(r'\/', '/') for item in sub_images] # 获取图像url
            for image in images: save_image(download_image(image), title) # 保存图片至本地
            return  {
                'title': title,
                'url': url,
                'images': images
            }
    return None

def save_to_mongo(result): # 将结果保存至mongodb中
    if db[MONGO_TABLE].insert(result):
        print('存储到MongoBD成功', result)
        return True
    return False

def download_image(url): # 下载图片并保存
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print('正在下载', url)
            return response.content # content返回二进制数据
        return None
    except RequestException:
        print('请求图片出错', url)
        return None

def save_image(content, title): # 保存图片
    if not content:
        return
    save_path = os.path.join(current_path, title)
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    file_name = '%s.jpg' % md5(content).hexdigest() # 使用md5编码是为了防止文件重名,使用 md5需要先对传入的参数进行编码
    file_path = os.path.join(save_path, file_name)
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)


def main(offset):
    html = get_page_index(KEYWORD, offset)
    for url in parse_page_index(html):
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html, url)
            if result: save_to_mongo(result)


if __name__ == '__main__':
    groups = [x * 20 for x in range(GROUP_START, GROUP_END + 1)]
    pool = Pool()
    pool.map(main, groups)