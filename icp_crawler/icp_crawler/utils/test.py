import asyncio
import time
from get_sign import GetSign
from curl_cffi import AsyncSession
from get_token import GetToken
from get_img_info import GetImgInfo

async def main():
    async with AsyncSession(impersonate="chrome110", timeout=60) as session:
        for try_times in range(3):
            print(f"第{try_times + 1}次运行")
            session.cookies.clear()
            get_token_handler = GetToken(session)
            refresh, bussiness = await get_token_handler.main()
            time.sleep(5)
            img_handler = GetImgInfo(session, bussiness)
            key, value = await img_handler.main()
            get_sign = GetSign(session, bussiness, key, value)
            time.sleep(1)
            sign = await get_sign.main()

            if sign:

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
                    'pageNum': '',
                    'pageSize': '',
                    'unitName': 'baidu.com',
                    'serviceType': 1,
                }

                response = await session.post(
                    'https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition',
                    headers=headers,
                    json=json_data,
                )

                print(response.text)

                break

if __name__ == '__main__':
    asyncio.run(main())