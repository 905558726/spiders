import json
import urllib.parse
from datetime import datetime, timedelta

import requests
import re
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class GwmsCrawler:
    def __init__(self, username, password):
        self.base_url = "http://47.97.186.218:9090"
        self.session = requests.Session()
        self.last_error = ""  # 用于存放失败原因
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/Gwms_YZH/main.jsf"
        }
        # 预设公钥
        self.pub_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCixoHVGxcBhLFbsg4gntuvzzxhTywcJXco7IkSQwA6aq+BuVR4Pl62DgvdPGeG6OmIc3jOm/G5WnC7HyLLpnYKXGxeoHLBM1J5J1Yxc2fQlPBt0Bx+ig611j+YUQ0ta2tjauz+E5T/yaU6nOX0Y0LWzmCEDD1c72OmcO/K8fqfGwIDAQAB"
        self.username = username
        self.password = password
        self.cookies = {}

    def _encrypt(self, text):
        """RSA 加密"""
        try:
            key = f"-----BEGIN PUBLIC KEY-----\n{self.pub_key}\n-----END PUBLIC KEY-----"
            pub = RSA.importKey(key)
            cipher = PKCS1_v1_5.new(pub)
            return base64.b64encode(cipher.encrypt(text.encode())).decode()
        except Exception as e:
            self.last_error = f"加密失败: {str(e)}"
            return None

    def get_cookies(self):
        """获取当前会话的 Cookie 字典"""
        return self.session.cookies.get_dict()

    def login(self):
        """
        登录接口
        :return: True (登录成功) / False (登录失败)
        """
        login_page_url = f"{self.base_url}/Gwms_YZH/main.jsf"

        try:
            # 1. 获取 ViewState
            r1 = self.session.get(login_page_url, headers=self.headers, timeout=10)
            vs_match = re.search(r'id="javax\.faces\.ViewState" value="(.*?)"', r1.text)
            if not vs_match:
                self.last_error = "无法从页面提取 ViewState 状态码"
                return False

            view_state = vs_match.group(1)

            # 2. 构建加密密码
            enc_password = self._encrypt(self.password)
            if not enc_password: return False

            # 3. 构造请求载荷
            payload = {
                'form1': 'form1',
                'form1:uszw': '',
                'form1:nv_userid': self.username,
                'form1:passWord': enc_password,
                'form1:smsCode2': '1',
                'form1:smsCode': '',
                'form1:selectid': '1',
                'form1:archive': 'false',
                'form1:loginBtn': '登 录 ',
                'form1:available_flag': 'true',
                'form1:hosturl': self.base_url,
                'form1:msg': '系统授权通过,有效期更新至:2026-08-18,有效期剩余:126天!',
                'form1:resultMsg': '',
                'form1:smsCodeMsg': '',
                'form1:machineID': '00-00-00-00-00-00-00-E0',
                'javax.faces.ViewState': view_state
            }

            # 4. 提交登录
            r2 = self.session.post(login_page_url, data=payload, headers=self.headers, timeout=15)

            # 5. 验证是否包含登录成功的特征（主页通常包含退出系统或用户名）
            if "退出系统" in r2.text or "G.usid" in r2.text:
                self.cookies = self.get_cookies()
                return True
            else:
                if "验证码" in r2.text:
                    self.last_error = "服务器要求输入验证码"
                elif "用户名或密码" in r2.text:
                    self.last_error = "账号或密码错误"
                else:
                    self.last_error = "未知错误：页面未跳转至主页"
                return False

        except Exception as e:
            self.last_error = f"网络请求异常: {str(e)}"
            return False

    def search_order(self):

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'http://47.97.186.218:9090',
            'Referer': 'http://47.97.186.218:9090/Gwms_YZH/pages/views/ordercount/ordercount.html?v=1702888714605?ch_moduleid=ordercount&url=/pages/views/ordercount/ordercount.html?v=1702888714605&isAll=0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'selected-customer': 'yzherqi',
            'selected-system': 'cangyun',
        }
        now = datetime.now()
        start_time = (now - timedelta(days=2)).strftime('%Y-%m-%d')
        end_time = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        querykey = self.generate_query_param(start_time, end_time)
        data = {
            'page': '1',
            'limit': '50',
            'moduleCode': 'ordercount',
            'rowid': '1078358030335086592',
            'querykey': querykey,
            'functions': 'funcMainList',
        }

        response = requests.post(
            'http://47.97.186.218:9090/Gwms_YZH/mvc/customize/public/search',
            cookies=self.cookies,
            headers=headers,
            data=data,
            verify=False,
        )

        print(response.text)

    def generate_query_param(self, start_date, end_date):
        # 1. 构造原始字典
        data = [
            {"ge_o_crdt": f"{start_date} 00:00:00"},
            {"le_o_crdt": f"{end_date} 00:00:00"}
        ]

        # 2. 转为 JSON 并进行两次 URL 编码 (模拟 JSF 行为)
        json_str = json.dumps(data)
        double_encoded_json = urllib.parse.quote(urllib.parse.quote(json_str))

        # 3. Base64 编码
        b64_str = base64.b64encode(double_encoded_json.encode()).decode()

        # 4. 最后加在 ABCD@ 和 @ABCD 之间
        final_param = f"ABCD@{b64_str}@ABCD"
        return final_param

# --- 执行入口 ---
if __name__ == "__main__":
    USER = ""
    PASS = ""
    crawler = GwmsCrawler(USER, PASS)

    print(f"[*] 正在尝试登录用户: {USER}...")

    if crawler.login():
        crawler.search_order()

    else:
        print(f"[-] 失败原因: {crawler.last_error}")