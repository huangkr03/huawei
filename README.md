# README

这个项目的爬虫基于BeautifulSoup和curl_cffi库。curl_cffi库能够模拟浏览器的TLS指纹，从而越过CloudFlare的防护盾。不过同时也需要ip没有问题。

curl_cffi库中有requests库的功能，使用方法和requests库基本一样，加了`impersonate`字段，里面可以填入其支持的浏览器类型：

```python
from curl_cffi import requests

r = requests.get('https://www.google.com', impersonate='chrome110') # 此处模拟的是chrome110的TLS指纹
```

因为我写的爬虫是在外网上的服务器运行的，因此我使用了clash代理来使用不同的ip进行爬取，也可仅仅基于本机的ip爬取，使用`crawl.py`即可。

并且由于外网无法访问内网服务器，因此我暂时将数据存到本地的`datas`文件夹中，每10w条数据一个单独的`csv`文件，之后再将数据传到内网服务器上。

我前后写了几个版本的爬虫，分别是：
 - `crawl.py`：不使用ip池，直接使用curl_cffi库进行爬取，速度较慢，但是稳定性较高。可使用特定的clash代理，也可以使用本机ip。但是测试使用5s爬一次仍然会被封ip。
 - `crawl_ip_pool.py`：使用ip池，使用curl_cffi库进行爬取，每次爬取之后会向clash发送请求，获取新的ip。但是效果并不好，最终结果是ip池中的ip全被封禁了。
 - `crawl_ip_pool.py`: 使用ip池，使用curl_cffi库进行爬取，爬取每个artifact里的所有版本会使用一个相同的ip及session，但是还是会被封。

我还尝试过多线程爬取，但是ip基本上被秒封，因此效果并不好。

使用ip池的时候，由于频繁切换代理ip，因此总会出现许许多多的bug，至今还不知道是什么原因。

目前最大的问题还是不知道`mvnrepository.com`网站的封ip策略，因此无法有效的避免被封ip。并且这个网站的防护很全面，不仅有cloudflare的防护，网站本身也有防爬虫的机制，因此很难爬取。

**我们发现有些时候，在访问次数达到一定程度之后，`mvnrepository.com`网站不会封禁ip，但是会返回一个数据完全是错误的页面，其结构和正常页面完全一样，但是里面的数据是错误的。经过我们的研究，发现错误的页面中没有`gtag()`的`JavaScript`代码，因此我们可以通过检测返回的HTML源码是否有`gtag('js', new Date());`代码段来判断是否是错误页面。**