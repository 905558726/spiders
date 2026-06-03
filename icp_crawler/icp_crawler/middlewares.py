from scrapy import signals


class IcpCrawlerSpiderMiddleware:
    """保持默认，不做改动"""
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class IcpCrawlerDownloaderMiddleware:
    """🌟 真正的请求拦截层：在这里接管并进行 curl_cffi 伪装"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    async def process_request(self, request, spider):
        # 🌟 核心：如果带了 skip_downloader 标记，直接原地返回空响应，阻断真正网络请求
        if request.meta.get('skip_downloader'):
            spider.logger.info("🚀 [Bridge中间件] 检测到壳请求，已启用内存桥接，跳过真实网关。")
            from scrapy.http import HtmlResponse
            return HtmlResponse(
                url=request.url,
                status=200,
                body=b"{}",
                encoding='utf-8',
                request=request
            )

        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)