import base64
import json
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization


# ==========================================
# 🛡️ 修正后的 RSA-OAEP 加密器
# ==========================================
class CsairEncryptor:
    @staticmethod
    def rsa_encrypt(plain_text, public_key_str):
        # 1. 补全 PEM 格式
        if "-----BEGIN PUBLIC KEY-----" not in public_key_str:
            pub_key = public_key_str.replace("\n", "").strip()
            public_key_str = f"-----BEGIN PUBLIC KEY-----\n{pub_key}\n-----END PUBLIC KEY-----"

        # 2. 加载公钥
        public_key = serialization.load_pem_public_key(public_key_str.encode())

        # 3. 执行 RSA-OAEP + SHA256 加密 (与前端 H0 函数完全对齐)
        encrypted_bytes = public_key.encrypt(
            plain_text.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted_bytes).decode('utf-8')


# ==========================================
# 🚀 完整生命周期请求客户端
# ==========================================
class CsairClient:
    def __init__(self):
        self.host = "https://coc.csair.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/xcoc/',
            'Origin': self.host,
            'Content-Type': 'application/json'
        })

    def execute_login_flow(self, username, password):
        try:
            # 1. 建立基础 Session 链接
            self.session.get(f"{self.host}/xcoc/", timeout=10)

            # 2. 获取验证码与公钥
            captcha_info = self.session.get(f"{self.host}/api/icoc-meal/sys/auth/captcha", timeout=10).json()["data"]
            public_key_str = self.session.get(f"{self.host}/api/icoc-meal/sys/auth/publicKey", timeout=10).json()[
                "data"]

            # 3. OCR 识别
            img_data = captcha_info['image'].split(",")[-1]
            img_bytes = base64.b64decode(img_data)
            with open("captcha.jpg", "wb") as f:
                f.write(img_bytes)

            captcha_code = self._ocr_identify(img_bytes)
            if not captcha_code: raise Exception("打码识别返回为空")

            # 4. 严谨拼接
            plain_text = f"{username};{password};{captcha_code};{captcha_info['key']}"
            print(f"👉 待加密明文: {plain_text}")

            # 5. 加密与投递
            login_str = CsairEncryptor.rsa_encrypt(plain_text, public_key_str)
            print(f"🔑 加密后串: {login_str}")

            resp = self.session.post(
                f"{self.host}/api/icoc-meal/sys/auth/login",
                json={"loginStr": login_str},
                timeout=15
            )

            response = self.session.get('https://coc.csair.com/stockManagerAction.do?method=showResult_supplier')
            print(response.text)

            print(f"📡 响应状态: {resp.status_code}")
            return resp.json()
        except Exception as e:
            print(f"❌ 流程异常: {e}")
            return None

    def _ocr_identify(self, img_bytes):
        ocr_url = ''
        resp = requests.post(ocr_url, params={'outPut': '{"验证码":"x"}'},
                             files={'file': ('c.jpg', img_bytes, 'image/jpeg')}, timeout=15)
        data = resp.json().get('data')
        if isinstance(data, str): data = json.loads(data)
        return data[0]['验证码'] if data else None


# ==========================================
# 🏁 测试入口
# ==========================================
if __name__ == "__main__":
    client = CsairClient()
    result = client.execute_login_flow("", "")
    print(json.dumps(result, indent=4, ensure_ascii=False))