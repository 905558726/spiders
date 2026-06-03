import os
import time
import urllib3
import requests
import utils.excel_operat as excel
import utils.email_operate as email_util
from DrissionPage import ChromiumPage, ChromiumOptions
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ZhongChe():
    def __init__(self):
        self.folder = r'D:\中车电子商城福利套餐商品推送'
        os.makedirs(self.folder, exist_ok=True)
        self.send_info = {
            'smtp_server': "",
            'sender_email': "",
            'password': "",
        }
        self.review_list = ['', '']

    def get_acw_tc(self):
        acw_tc = ""
        co = ChromiumOptions()
        co.incognito(True)
        # 开启无头模式
        co.headless(True)
        # 关键：设置特定的启动参数，隐藏自动化特征
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')

        page = ChromiumPage(co)
        try:
            page.get('https://mall.crrcgo.cc/#/specialArea_coverPage?specialAreaId=2010660168304918529')
            print("等待页面加载...")
            page.wait(5)
            welfare_ele = page.ele('text=福利套餐')
            if welfare_ele:
                print("找到‘福利套餐’入口，正在执行点击...")
                welfare_ele.scroll.to_see()
                time.sleep(1)
                welfare_ele.click()
                print("正在等待页面跳转及 acw_tc 生成...")
                page.wait(4)
                final_url = page.url
                print(f"当前 URL: {final_url}")
                if "specialArea" in final_url:
                    print("✅ 恭喜！已成功进入专区页面。")
                    cookies_list = page.cookies()
                    cookies_dict = {c['name']: c['value'] for c in cookies_list}
                    if 'acw_tc' in cookies_dict:
                        acw_tc = cookies_dict['acw_tc']
                        print(f"\n--- 捕获成功 ---")
                        print(f"acw_tc: {cookies_dict['acw_tc']}")
                        print(f"\n你可以将以下字典用于 requests 请求：\n{cookies_dict}")
                    else:
                        print("未找到 acw_tc，可能该页面使用了其他校验方式。")
                else:
                    print("❌ 跳转后的 URL 不符合预期，可能依然被重定向回了首页。")
                    print(f"实际到达地址: {final_url}")
            else:
                print("❌ 依然找不到元素，请检查首页是否加载完全。")
        except Exception as e:
            print(f"运行异常: {e}")
        finally:
            page.quit()
        with open(f'{self.folder}/acw_tc.txt', 'w', encoding='utf-8') as f:
            f.write(acw_tc)
        return acw_tc

    def get_authorization(self):
        try:
            current_ts = int(time.time())
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'Referer': 'https://mall.crrcgo.cc/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }

            params = {
                't': current_ts,
            }

            response = requests.get(
                'https://mall.crrcgo.cc/serv/system-service/portal/api/portalEnt/checkEnable',
                params=params,
                headers=headers,
            )
            return response.json()['data']['token']
        except Exception as e:
            return None

    def get_data(self, acw_tc, authorization):
        get_acw_tc = False
        is_stop = False
        total = 0
        sku_info_list = []
        error_page = []
        for i in range(1, 1000):
            if not is_stop:
                for index in range(2):
                    try:
                        if acw_tc:
                            cookies = {
                                'acw_tc': acw_tc,
                            }
                        else:
                            cookies = {}
                        headers = {
                            'Accept': 'application/json, text/plain, */*',
                            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7',
                            'Authorization': f'Bearer {authorization}',
                            'Content-Type': 'application/json',
                            'Origin': 'https://mall.crrcgo.cc',
                            'Referer': 'https://mall.crrcgo.cc/',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'same-origin',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
                            'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                            'skey': '5362c8bcffe876ca22c2f8ef623e0382',
                            't': '1776992855983000',
                        }

                        json_data = {
                            "isQueryCatalog": True,
                            "purchaserId": "1007636225761517568",
                            "supplierIds": [],
                            "supplierName": "",
                            "goodsName": "",
                            "purchaserCatalogIds": [
                                "1374013891398471680"
                            ],
                            "catalogIds": [],
                            "isStandard": -1,
                            "brandIds": [],
                            "specList": [],
                            "priceMin": None,
                            "priceMax": None,
                            "sortType": 31,
                            "page": i,
                            "limit": 20,
                            "onlyDeliveryToday": False,
                            "protocolIdFilter": 1,
                            "searchType": "3",
                            "searchWords": "",
                            "searchData": "1374013891398471680",
                            "breadcrumb": "1374013891398471680",
                            "catalogOpen": "true",
                            "specialAreaId": "2010660168304918529",
                            "menuKeyId": "2010660387943841794",
                            "purchaserCatalogName": "",
                            "isRecordKey": True
                        }

                        response = requests.post(
                            'https://mall.crrcgo.cc/serv/order-service/api/goods/queryGoodsListWithStandardByCatalog',
                            cookies=cookies,
                            headers=headers,
                            json=json_data,
                            verify=False
                        )
                        print(response.text)
                        if total == 0:
                            total = response.json()['data']['total']
                        goodsList = response.json()['data']['goodsList']
                        for goods in goodsList:
                            sku_name = goods['goodsName']
                            sku_code = goods['goodsCode']
                            supplier_name = goods['supplierName']
                            brand_name = goods['brandName']
                            sku_info_list.append([sku_name, sku_code, supplier_name, brand_name])
                        if len(goodsList) != 20:
                            is_stop = True
                        break
                    except Exception as e:
                        if not get_acw_tc:
                            acw_tc = self.get_acw_tc()
                        else:
                            error_page.append(i)
                            break
        return {"total": total, "sku_info": sku_info_list, "error_page": error_page}

    def main(self):
        acw_tc = ""
        time_str = time.strftime("%Y年%m月%d日%H点", time.localtime())
        excel_path = f'{self.folder}/{time_str}中车电子商品数据.xlsx'
        excel.create_excel("中车电子商品数据", excel_path,
                           ["商品名称", "商品编码", "供应商名称" , "品牌信息"])
        with open(f'{self.folder}/acw_tc.txt', 'r', encoding='utf-8') as f:
            acw_tc = f.read()
        authorization = self.get_authorization()
        if authorization:
            result = self.get_data(acw_tc, authorization)
            excel.append_data_to_excel(result['sku_info'], excel_path, [2])
            for review in self.review_list:
                email_util.sender_email(self.send_info, review, excel_path)
            print(result['total'])
            print(result['error_page'])
            return result
        else:
            return {"total": 0, "sku_info": 0, "error_page": 0}

if __name__ == "__main__":
    zhongche_object = ZhongChe()
    zhongche_object.main()
