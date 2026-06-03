import os
import asyncio
import aiohttp
import urllib3
import requests
import utils.excel_operat as excel


def get_data(categoryId):
    url = "https://www.ruixiangmall.cn:8443/huarui-api/api/product/list"
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    params = {
        "categoryId": categoryId,
        "seachString": "",
        "randomNum": 11120,
        "orderType": 1,
        "pageNum": 1,
        "pageSize": 1000
    }

    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254160e) XWEB/18055',
        'xweb_xhr': '1',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://servicewechat.com/wxaa27e205bb4757e6/11/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    try:
        # 关键修改：添加 verify=False
        response = requests.get(url, params=params, headers=headers, verify=False)

        response.raise_for_status()
        data = response.json()

        print("请求成功！")
        print(f"状态码: {response.status_code}")
        print(f"当前请求有{len(data['rows'])}个商品数据")
        return data
    except Exception as e:
        print(f'发生未知错误: {e}')
        return ""


def process_data(data, category_01, category_02, session):
    semaphore = asyncio.Semaphore(10)
    tasks = [
        asyncio.create_task(_fetch_get_sku_code_semaphore(row, category_01, category_02, semaphore, session))
        for row in data['rows']
    ]
    return tasks

async def _fetch_get_sku_code_semaphore(data, category_01, category_02, semaphore, session):
    async with semaphore:
        return await get_sku_code(data, category_01, category_02, session)

async def get_sku_code(data, category_01, category_02, session):
    headers = {
        'Host': 'www.ruixiangmall.cn:8443',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254186b) XWEB/19481',
        'xweb_xhr': '1',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://servicewechat.com/wxaa27e205bb4757e6/17/page-frame.html',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    params = {
        'goodsId': str(data['goods']),
        'goodsZoneId': str(data['goodsZoneId']),
        'commonGoodsZoneType': '',
    }

    async with session.get(
            'https://www.ruixiangmall.cn:8443/huarui-api/api/product/detail',
            params=params,
            headers=headers,
            ssl=False) as resp:
        json_data = await resp.json()

    sku_name = data['name']
    sales = data['sales']
    price = data['price']
    merchant_name = data['merchantName']
    print([category_01, category_02, sku_name, merchant_name, sales, price, json_data['productList'][0]['sn']])
    return  [category_01, category_02, sku_name, merchant_name, sales, price, json_data['productList'][0]['sn']]

async def main():
    category_dict = {
        "个人护理": {
            "口腔护理": 190,
            "身体护理": 192,
            "个护清洁": 189,
            "面部护理": 194,
            "女性护理": 191,
            "洗发护发": 193
        },
        "纸品/清洁": {
            "生活用纸": 264,
            "衣务清洁": 265,
            "环境清洁": 259,
            "驱蚊驱虫": 262,
            "清洁用品": 263
        },
        "食物饮品": {
            "饼干/糕点": 146,
            "茶叶/茶包": 147,
            "冲饮谷物": 341,
            "蜂蜜/蜂产品": 365,
            "坚果/炒货": 333,
            "咖啡/奶茶": 346,
            "蜜饯果干": 330,
            "牛奶/酸奶": 410,
            "肉干肉脯": 331,
            "糖果/巧克力": 334,
            "休闲零食": 50,
            "饮料": 58,
            "饮用水": 351,
            "节庆食品": 148
        },
        "水果": {
            "应季水果等": 435
        }
    }
    folder = r"E:\华睿商城"
    file_name = "华睿商城商品数据"
    excel_path = rf"{folder}\{file_name}.xlsx"
    data_list = []
    excel.create_excel("华睿商城商品数据", excel_path,
                       ['一级分类', '二级分类', '商品名称', '供应商', '销量', '价格', '商品编码'])
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        for category_01, info in category_dict.items():
            for category_02, category_id in info.items():
                data = get_data(category_id)
                if data:
                    data_list += await asyncio.gather(*(process_data(data, category_01, category_02, session)))
    excel.append_data_to_excel(data_list, excel_path, [])


if __name__ == "__main__":
    asyncio.run(main())