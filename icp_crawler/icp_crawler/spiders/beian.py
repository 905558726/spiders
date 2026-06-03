import json
import scrapy
import asyncio
from scrapy import signals
from curl_cffi.requests import AsyncSession
from icp_crawler.items import IcpCrawlerItem
from icp_crawler.utils.get_sign import GetSign
from icp_crawler.utils.get_token import GetToken
from icp_crawler.utils.get_img_info import GetImgInfo


class BeianSpider(scrapy.Spider):
    name = "beian"
    allowed_domains = ["hlwicpfwc.miit.gov.cn"]
    start_urls = []

    # 🌟 修改 1：改为字典，结构为：{"单位名": "查回来的明文JSON字符串"}
    raw_api_responses = {}

    def __init__(self, *args, **kwargs):
        super(BeianSpider, self).__init__(*args, **kwargs)
        # 注意：这里不再创建全局 self.session，而是移到协程内部动态创建独立会话

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BeianSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        return spider

    async def spider_opened(self):
        """在前置流里并发抓取，但保持物理隔离"""
        self.logger.info("🚀 [信号前置流] 开始多任务并发闭环审计...")

        unit_names = ['baidu.com', 'jd.com', 'sunlogin.oray.com', 'todesk.com', '伊利', '淘宝', '京东']

        # 🌟 修改 2：并发执行多任务
        semaphore = asyncio.Semaphore(4)
        tasks = [self.async_execute_full_flow(name, semaphore) for name in unit_names]
        results = await asyncio.gather(*tasks)

        # 整理结果存入字典
        for name, res_json in results:
            if res_json:
                self.raw_api_responses[name] = res_json
                self.logger.info(f"✅ [信号前置流] 【{name}】数据抓取成功！")
            else:
                self.logger.error(f"❌ [信号前置流] 【{name}】抓取失败。")

    def start_requests(self):
        """根据成功拿到的数据任务，构建对应数量的内存桥接壳请求"""
        self.logger.info(f"📦 开始构建 Scrapy 内存桥接请求，共 {len(self.raw_api_responses)} 个任务...")

        # 🌟 修改 3：遍历字典，为每个成功的任务派发一个壳请求，通过 meta 传参
        for unit_name, json_text in self.raw_api_responses.items():
            yield scrapy.Request(
                url=f"https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition?name={unit_name}",
                method='POST',
                dont_filter=True,
                meta={
                    'skip_downloader': True,
                    'unit_name': unit_name  # 把单位名带给 parse
                },
                callback=self.parse
            )

    async def async_execute_full_flow(self, unit_name, semaphore):
        """纯正、原汁原味的 curl_cffi 链条（每个任务拥有完全独立的 Session 空间）"""
        # 🌟 修改 4：每个任务独立实例化自己的 AsyncSession，TCP 连接和 Cookie 完全隔离，并发不会冲突
        async with semaphore:
            async with AsyncSession(impersonate="chrome110", timeout=30) as session:
                for try_times in range(5):
                    self.logger.info(f"【{unit_name}】正在尝试第 {try_times + 1} 次完整凭证与业务请求...")
                    session.cookies.clear()
                    try:
                        # 1. 搞定凭证
                        get_token_handler = GetToken(session)
                        refresh, bussiness = await get_token_handler.main()
                        await asyncio.sleep(5)

                        img_handler = GetImgInfo(session, bussiness)
                        key, value = await img_handler.main()

                        get_sign = GetSign(session, bussiness, key, value)
                        await asyncio.sleep(1)
                        sign = await get_sign.main()

                        if sign:
                            self.logger.info(f"⚡ 【{unit_name}】凭证齐全，发送原生 curl_cffi 请求...")

                            headers = {
                                'accept': 'application/json, text/plain, */*',
                                'accept-language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7',
                                'content-type': 'application/json',
                                'origin': 'https://beian.miit.gov.cn',
                                'priority': 'u=1, i',
                                'referer': 'https://beian.miit.gov.cn/',
                                'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
                                'sec-ch-ua-mobile': '?0',
                                'sec-ch-ua-platform': '"Windows"',
                                'sec-fetch-dest': 'empty',
                                'sec-fetch-mode': 'cors',
                                'sec-fetch-site': 'same-site',
                                'sign': sign,
                                'token': bussiness,
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
                                'uuid': key,
                            }

                            json_data = {
                                'pageNum': '1',
                                'pageSize': '10',
                                'unitName': unit_name,
                                'serviceType': 1,
                            }

                            target_url = "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition"

                            response = await session.post(target_url, json=json_data, headers=headers)

                            if response.status_code == 200:
                                # 返回单位名和对应的明文结果
                                return unit_name, response.text
                            else:
                                self.logger.warning(f"【{unit_name}】请求非200状态码: {response.status_code}")

                    except Exception as e:
                        self.logger.warning(f"【{unit_name}】第 {try_times + 1} 次全流程失败: {e}")
                        await asyncio.sleep(2)
                return unit_name, None

    def parse(self, response):
        unit_name = response.meta.get('unit_name')
        res_text = self.raw_api_responses.get(unit_name)

        self.logger.info(f"👉 终点站 - 正在解析【{unit_name}】前置流带回的明文数据")

        if not res_text:
            self.logger.error(f"❌ 未能获取到【{unit_name}】的明文业务数据，跳过")
            return

        try:
            api_data = json.loads(res_text)
        except Exception as e:
            self.logger.error(f"【{unit_name}】解析明文 JSON 失败: {e}")
            return

        # 🌟 加一行调试：看看工信部返回的原始 JSON 长啥样，是不是结构对不上
        self.logger.info(f"🔍 【{unit_name}】返回值根节点Keys: {list(api_data.keys())} | 完整响应: {res_text[:200]}...")

        data_params = api_data.get("params", {})
        info_list = data_params.get("list", []) if isinstance(data_params, dict) else []

        # 🌟 再加一行调试：看看有没有拿到数组长度
        self.logger.info(f"📊 【{unit_name}】解析到的列表长度为: {len(info_list)}")

        for info in info_list:
            self.logger.info(f"🔥 【{unit_name}】成功切入 Item 构建逻辑 !!")
            item = IcpCrawlerItem()
            item['unit_name'] = info.get('unitName')
            item['nature_name'] = info.get('natureName')
            item['domain'] = info.get('domain')
            item['domain_id'] = info.get('domainId')
            item['main_licence'] = info.get('mainLicence')
            item['service_licence'] = info.get('serviceLicence')
            item['main_id'] = info.get('mainId')
            item['update_time'] = info.get('updateRecordTime')
            yield item