class GetSign:
    def __init__(self, session, token, key, value):
        self.session = session
        self.token = token
        self.key = key
        self.value = value

    async def get_sign(self):

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
            'token': self.token,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        }

        json_data = {
            'key': self.key,
            'value': self.value,
        }

        response = await self.session.post(
            'https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/checkImage',
            headers=headers,
            json=json_data,
        )

        return response.json()['params']

    async def main(self):
        sign = await self.get_sign()
        return sign

