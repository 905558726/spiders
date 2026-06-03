import re
import json
import requests
from gmssl import sm2

class TobaccoLogin:
    def __init__(self):
        self.public_key_hex = "0469bcea2b69bd7b1b80fbcf6242181fe9da54958f6a7633f99402eeeeee59df1d0c3ed58fc9c9247e268089fd45c9bfd7e56dd0e2750c8f1d3fef5a44f8975c15"
        self.session = requests.Session()
        self.base_url = "https://bid.tobacco.com.cn/cas/login"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://cgjy.tobacco.com.cn/',
        }
        self.params = {
            'role': 'mall',
            'mallType': 'B',
            'service': 'https://login.dzsc.tobacco.com.cn/open/token/authentication?login_type=tobacco&portal_type=outer',
            'callbackUrl': 'https://login.dzsc.tobacco.com.cn/open/token/authentication?login_type=tobacco&portal_type=outer',
        }

    def encrypt_password(self, password):
        sm2_crypt = sm2.CryptSM2(
            public_key=self.public_key_hex,
            private_key=None,
            mode=1
        )
        data = password.encode('utf-8')
        enc_data = sm2_crypt.encrypt(data)
        res_hex = enc_data.hex()
        return "04" + res_hex

    def get_and_identify_captcha(self):
        captcha_res = self.session.get('https://bid.tobacco.com.cn/cas/captch', headers=self.headers)

        ocr_url = 'https://bigdata-gateway.yunzhonghe.com/api/goods/skip/img/local/identify'
        files = {'file': ('captcha.jpg', captcha_res.content, 'image/jpeg')}
        params = {'outPut': '{"验证码":"x"}'}

        try:
            resp = requests.post(ocr_url, params=params, files=files)
            if resp.json().get('success'):
                data = json.loads(resp.json()['data'])
                return data[0]['验证码']
        except Exception as e:
            print(f"验证码识别异常: {e}")
        return None

    def login_tobacco(self, username, encrypted_password, captcha):

        base_url = "https://bid.tobacco.com.cn/cas/login"
        params = {
            "role": "mall",
            "mallType": "B",
            "service": "https://login.dzsc.tobacco.com.cn/open/token/authentication?login_type=tobacco&portal_type=outer",
            "callbackUrl": "https://login.dzsc.tobacco.com.cn/open/token/authentication?login_type=tobacco&portal_type=outer"
        }
        session = requests.Session()

        try:
            response = session.get(base_url, params=params, headers=self.headers)
            lt = re.search(r'name="lt" value="(.*?)"', response.text).group(1)
            execution = re.search(r'name="execution" value="(.*?)"', response.text).group(1)
            data = {
                "loginIdentity": "B",
                "username": username,
                "password": encrypted_password,
                "captcha": captcha,
                "lt": lt,
                "type": "1",
                "execution": execution,
                "_eventId": "submit",
                "submit": ""
            }
            login_res = session.post(base_url, params=params, data=data, headers=self.headers, allow_redirects=True)
            open('result.txt', 'wb').write(login_res.content)
            if "登录失败" in login_res.text or "验证码错误" in login_res.text:
                print("登录可能失败，请检查返回内容。")
                return False, login_res.text

            print("登录请求已发送，请检查 session 或重定向结果。")
            return True, session

        except Exception as e:
            print(f"程序异常: {e}")
            return False, None

    def main_login(self, username, password):
        try:
            resp = self.session.get(self.base_url, params=self.params, headers=self.headers)

            lt_match = re.search(r'name="lt" value="(.*?)"', resp.text)
            exe_match = re.search(r'name="execution" value="(.*?)"', resp.text)

            if not lt_match or not exe_match:
                print("未能在页面中找到 lt 或 execution")
                return

            lt = lt_match.group(1)
            execution = exe_match.group(1)

            captcha = self.get_and_identify_captcha()
            print(f"识别到的验证码: {captcha}")

            data = {
                "loginIdentity": "B",
                "username": username,
                "password": self.encrypt_password(password),
                "captcha": captcha,
                "lt": lt,
                "type": "1",
                "execution": execution,
                "_eventId": "submit",
                "submit": ""
            }

            login_res = self.session.post(self.base_url, params=self.params, data=data, headers=self.headers,
                                          allow_redirects=True)

            if "登录失败" in login_res.text or "验证码错误" in login_res.text:
                print("登录失败，详细信息见 result.txt")
                with open('result.txt', 'w', encoding='utf-8') as f:
                    f.write(login_res.text)
            elif "个人中心" in login_res.text or "我的" in login_res.text or login_res.status_code == 200:
                print("登录成功！")
                print("当前有效 Cookies:", self.session.cookies.get_dict())
                return self.session.cookies.get_dict()
            else:
                print("结果未知，请检查响应内容")

        except Exception as e:
            print(f"登录执行异常: {e}")



if __name__ == '__main__':
    tobacco_login = TobaccoLogin()
    cookies = tobacco_login.main_login("", "")
    print(cookies)

