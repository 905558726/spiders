import time
import base64
import asyncio
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class GetToken:
    def __init__(self, session):
        self.session = session
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://beian.miit.gov.cn',
            'Referer': 'https://beian.miit.gov.cn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        self.aes_key = 'abcdefgabcdefg12'.encode('utf-8')
        self.md5_salt = 'test'
        self.client_uid = 'test'

    def encrypt_aes(self, plain_text: str) -> str:
        """对应前端 v.encrypt: AES-128-ECB 加密"""
        cipher = AES.new(self.aes_key, AES.MODE_ECB)
        padded_data = pad(plain_text.encode('utf-8'), AES.block_size, style='pkcs7')
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_aes(self, cipher_text_base64: str) -> str:
        """对应前端 v.decrypt: AES-128-ECB 解密"""
        cipher = AES.new(self.aes_key, AES.MODE_ECB)
        encrypted_bytes = base64.b64decode(cipher_text_base64)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted_bytes, AES.block_size, style='pkcs7').decode('utf-8')

    def password_hex(self, password: str) -> str:
        """对应前端 v.passwordHex: 登录密码的 MD5"""
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    def generate_auth_key(self, timestamp: int) -> str:
        """对应前端 w.authKey: 核心注册鉴权密文生成"""
        source_str = f"{self.client_uid}{self.md5_salt}{timestamp}"
        return hashlib.md5(source_str.encode('utf-8')).hexdigest()

    async def get_token(self):

        timestamp = int(time.time() * 1000)

        data = {
            'authKey': self.generate_auth_key(timestamp),
            'timeStamp': timestamp,
        }

        response = await self.session.post(
            'https://hlwicpfwc.miit.gov.cn/icpproject_query/api/auth',
            headers=self.headers,
            data=data,
            timeout=10
        )

        params = response.json()['params']

        return params['refresh'], params['bussiness']

    async def main(self):

        return await self.get_token()

