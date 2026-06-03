import os
import json
import requests
import utils.excel_operat as excel


def search_product(page):
    """
    模拟发送POST请求以搜索商品。
    """
    url = "https://grsf.rybsaas.com/api/trade/product/searchProduct"

    headers = {
        'Connection': 'keep-alive',
        'Authorization': 'bearer:wx_mini:user:d143469984768efbe8c7ca0853c9eca2:1772777478587',
        'X-Requested-With': 'XMLHttpRequest',
        'xweb_xhr': '1',
        'Content-Type': 'application/json',
        'version': '2.0.0',
        'Platform': 'wx_mini',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://servicewechat.com/wx5e26d555522396cc/95/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }

    request_body_data = {
        "page": page,
        "size": 10
    }

    try:
        print("正在发送POST请求...")
        print(f"请求体数据: {json.dumps(request_body_data, ensure_ascii=False)}")

        # 关键变化在这里：添加 verify=False
        response = requests.post(url, headers=headers, json=request_body_data, verify=False)

        if response.status_code == 200:
            json_data = response.json()
            return json_data
        else:
            print(f"\n请求失败。HTTP状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n请求过程中发生错误: {e}")
        return None


if __name__ == "__main__":
    page = 1
    result_list = []
    while True:
        try:
            result = search_product(page)
            data = result['data']['lists']
            if data:
                for i in data:
                    product_name = i['name']
                    brand = i['brand']
                    specifications = i['specifications'].replace(" ", "")
                    retailPrice = i['retailPrice']
                    price = i['price']
                    result_list.append([product_name, brand, specifications, retailPrice, price])
                page += 1
            else:
                break
        except Exception as e:
            print(e)
            print(page)
            break
    excel_path = r"D:\python\spider\resource\果然十分_多块好省商品数据.xlsx"
    if not os.path.exists(excel_path):
        excel.create_excel("果然十分_多块好省商品数据",
                           excel_path,
                           ['商品名称', '商品品牌', '销售单位', '零售价', '提货价'])
    excel.append_data_to_excel(result_list, excel_path, [])
