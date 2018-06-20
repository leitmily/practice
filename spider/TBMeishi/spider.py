# coding:utf-8

import re
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

# 注意：PhantomJS已被弃用
# browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)  # 打开一个客户端, Chrome默认可视化窗口，PhantomJS无可视化窗口
options = webdriver.ChromeOptions()  # FirefoxOptions(),下同
options.add_argument('--headless')  # 无可视化窗口
options.add_argument('--disable-gpu')
browser = webdriver.Chrome(options=options)
wait = WebDriverWait(browser, 10)  # 设置等待时间

browser.set_window_size(1366, 768)  # 设置窗口大小


def search():  # 获取第一页
    try:
        browser.get('http://www.taobao.com')
        input_ = wait.until(  # 等待输入框加载完成，等待时间为10s, 返回list
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#q'))  # 通过CSS选择器选取输入框
        )
        submit_ = wait.until(  # 等待搜索按钮处于可以点击状态，等待时间为10s，返回element
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-search'))  # 通过CSS选择器选取搜索按钮
        )
        input_[0].send_keys(KEYWORD)  # 输入内容
        submit_.click()  # 点击按钮
        total = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.total')))  # 等待总页数加载完成
        get_products()
        print('获取页面成功')
        return total[0].text  # 返回总页数
    except TimeoutException:
        print('获取页面失败，尝试重试')
        return search()  # 重试


def next_page(page_number):
    try:
        input_ = wait.until(  # 等待跳转索引页输入框加载完成
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input.input:nth-child(2)'))  # 通过CSS选择器选取输入框
        )
        submit_ = wait.until(  # 等待跳转按钮处于可以点击状态，等待时间为10s，返回element
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.btn:nth-child(4)'))  # 通过CSS选择器选取搜索按钮
        )
        input_[0].clear()
        input_[0].send_keys(page_number)
        submit_.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'span.num'), str(page_number)))  # 等待页面是否跳转至当前页码
        print('跳转至下一页成功', page_number)
        get_products()
    except TimeoutException:
        print('跳转至下一页失败，尝试重试', page_number)
        next_page(page_number)


def get_products():
    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))  # 等待页面元素是否加载成功
        html = browser.page_source  # 获取网页源码
        doc = pq(html)  # 使用pyquery解析网页
        items = doc('#mainsrp-itemlist .items .item').items()
        for item in items:
            product = {
                'image': item.find('.pic .img').attr('data-src'),
                'title': item.find('.J_ClickStat').text(),
                'deal': item.find('.deal-cnt').text()[: -3],
                'price': item.find('.price').text(),
                'location': item.find('.location').text(),
                'shop': item.find('.shop').text()
            }
            save_to_mongo(product)  # 保存至mongodb
    except TimeoutException:
        print('获取元素失败')


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('保存到mongodb成功', result)
    except Exception:
        print('存储到mongodb失败', result)


def main():
    try:
        total = search()
        total = int(re.search('(\d+)', total).group(1))
        print(total)
        for i in range(2, 4):
            next_page(i)
    except Exception:
        print('error')
    finally:
        browser.close()


if __name__ == '__main__':
    main()
