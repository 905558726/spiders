import scrapy
import aiohttp
import asyncio
import requests
import zhong_yang.utils.tobacco_login as login


class OrderManagement(scrapy.Spider):
    name = "order_management"
    def __init__(self, cookie=None, *args, **kwargs):
        super(OrderManagement, self).__init__(*args, **kwargs)
        if cookie is None:
            tobacco_login = login.TobaccoLogin()
            cookie = tobacco_login.main_login("13608025388", "Yzh@12345")
        self.cookies = {
            'userInfo': cookie['userInfo'],
            'platform_code': 'zcy',
            'SESSION': cookie['SESSION'],
            'uid': cookie['uid'],
            'prod-yc_uid': cookie['prod-yc_uid'],
            'user_type': cookie['user_type'],
            'tenant_code': cookie['tenant_code'],
            'institution_id': cookie['institution_id'],
            'session_application_code': 'zcy.industry.trade',
        }
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://middle.dzsc.tobacco.com.cn',
            'Referer': 'https://middle.dzsc.tobacco.com.cn/trading-backstage/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def get_order_page(self):
        json_data = {
            'tag': 2,
            'applicationTag': 2,
            'statuses': [],
            'pageNo': 1,
            'pageSize': 10,
        }
        response = requests.post(
            'https://middle.dzsc.tobacco.com.cn/api/mall/order/list',
            cookies=self.cookies,
            headers=self.headers,
            json=json_data,
        )
        return int(int(response.json()['result']['total']) / 10 + (1 if response.json()['result']['total'] % 10 != 0 else 0))

    @staticmethod
    async def get_order_list(page, session, semaphore):
        async with semaphore:
            order_list = []
            json_data = {
                'tag': 2,
                'applicationTag': 2,
                'statuses': [],
                'pageNo': page,
                'pageSize': 10,
            }
            async with session.post('https://middle.dzsc.tobacco.com.cn/api/mall/order/list', json=json_data) as resp:
                response = await resp.json()
                for data in response['result']['data']:
                    order_list.append(data)
            return order_list

    async def get_order(self):
        semaphore = asyncio.Semaphore(5)
        order_list = []
        tasks = []
        page = self.get_order_page()
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout = timeout) as session:
            for i in range(1, page + 1):
                tasks.append(asyncio.create_task(self.get_order_list(i, session, semaphore)))
            results = await asyncio.gather(*tasks)
            for result in results:
                order_list += result
        return order_list

    def main(self):
        order_list = asyncio.run(self.get_order())
        print(len(order_list))
        return order_list

    async def start(self):
        order_list = await self.get_order()

        print("=" * 100)
        print(f"成功获取到订单数量: {len(order_list)}")
        print("=" * 100)

        for order in order_list:
            yield order