# 爬取微信文章

使用代理池处理反爬情况，并抓取搜狗中的微信文章

* 使用requests模块请求数据并获取网页源码

* 使用代理池提供的API接口获取代理地址

* 使用代理地址访问被反爬取的网站

* 使用pyquery模块匹配带爬取的信息

* 使用mongodb存储解析的结果

* 参考自崔庆才的[网络爬虫][1]视屏教程以及[源码][2]

    [1]: https://edu.hellobi.com/course/156 'Python3爬虫三大案例实战分享'
    [2]: https://github.com/Germey/Weixin 'github'