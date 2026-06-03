import requests
import string
import random

class uploadHuiceOrder:
    def generate_custom_chaos(self, length=400):
        # 手动定义一个包含字母、数字、加号、斜杠和一些干扰字符的池子
        char_pool = string.ascii_letters + string.digits + "+/=" + "++//"
        result = ''.join(random.choice(char_pool) for _ in range(length))
        return result

    def get_token_yunzhonghe(self, username, password):
        """
        获取云台token
        :param username:
        :param password:
        :return:
        """
        # 登录接口地址
        url = "https://gateway.yunzhonghe.com/api/user/login/authskip"

        # 请求头
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        # 请求体（您提供的登录信息）
        payload = {
            "loginModeType": 1001,
            "username": username,
            "password": password
        }

        try:
            # 发送 POST 请求
            response = requests.post(url, headers=headers, json=payload)

            # 检查响应状态
            if response.status_code == 200:
                # 解析 JSON 响应
                result = response.json()['result']
                token = result.get('token') or result.get('data', {}).get('token')

                if token:
                    return True, token
                else:
                    return False, '未找到令牌'
            else:
                return False, "请求失败"

        except requests.exceptions.RequestException as e:
            return False, "请求异常"

    def get_shop_key(self, token):
        url = "https://gateway.yunzhonghe.com/api/operation/data/operation/create/auth?"
        headers = {
            'Authorization': 'Bearer ' + token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
        }
        params = {
            'authType': 1002,
            'id': 14630
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.json()['success']:
                return True, response.json()['result']
            else:
                return False, ""
        except Exception as e:
            return False, str(e)

    def get_token_shop(self, shop_key):
        url = "https://gateway.haoxiny.com/portal/auth/operation/login"
        headers = {
            'Authorization': f"Bearer {self.generate_custom_chaos}",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
        }
        params = {
            'sgin': shop_key,
            'jumpSource': ""
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.json()['success']:
                return True, response.json()['data']['token']
            else:
                return False, ""
        except Exception as e:
            return False, str(e)

    def file_upload(self, file_path, shop_key):
        import requests

        url = "https://gateway.haoxiny.com/portal/backstage/file/importOrder/orderImport"

        # 打开文件
        with open(file_path, "rb") as f:
            files = {
                "file": (
                    "2026-04-14-14_密文订单.xlsx",
                    f,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            }

            headers = {
                'Authorization': f"Bearer {shop_key}",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
            }

            response = requests.post(url, files=files, headers=headers)

            print(response.json())


    def main(self):
        status, token = self.get_token_yunzhonghe("", "")
        file_path = ""
        if status:
            status, shop_key = self.get_shop_key(token)
            if status:
                status, shop_token = self.get_token_shop(shop_key)
                if status:
                    self.file_upload(file_path, shop_key)
                    print(shop_token)
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

if __name__ == '__main__':
    upload_huice_order = uploadHuiceOrder()
    upload_huice_order.main()