import io
import cv2
import base64
import asyncio
import numpy as np
from uuid import uuid4
import PIL.Image as Image

class GetImgInfo:
    def __init__(self, session, token):
        """
        :param session: 传入外部统一维护、带有加速乐 Cookie (__jsluid_s) 的 requests.Session 实例
        :param token: 传入最新通过 /api/auth 接口获取到的 params.bussiness 字符串
        """
        self.session = session
        self.token = token

    async def get_img_info(self):
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
            'clientUid': f'point-{str(uuid4())}',
        }
        url = 'https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/getCheckImagePoint'
        response = await self.session.post(
            url,
            headers=headers,
            json=json_data,
            timeout=10
        )
        return response.json()['params']

    @staticmethod
    def save_image_to_cache(base64_data):
        try:
            if "base64," in base64_data:
                base64_data = base64_data.split("base64,")[1]
            else:
                base64_data = base64_data.strip()
            np_arr = np.frombuffer(base64.b64decode(base64_data), np.uint8)
            img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img_cv is None:
                raise ValueError("Base64 解码失败！")
            lower_bgr = np.array([170, 170, 170])
            upper_bgr = np.array([220, 220, 220])
            img_bin = cv2.inRange(img_cv, lower_bgr, upper_bgr)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            img_bin = cv2.morphologyEx(img_bin, cv2.MORPH_CLOSE, kernel)
            # cv2.imwrite("binary_result.png", img_bin)
            # cv2.imwrite("original.png", img_cv)
            return img_bin
        except Exception as e:
            print(f"Error saving image: {e}")

    def get_small_img_info(self, base64_data):
        if "base64," in base64_data:
            base64_data = base64_data.split("base64,")[1]
        else:
            base64_data = base64_data.strip()
        try:
            img_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Base64 解码失败: {e}")
        try:
            img_mem = io.BytesIO(img_bytes)
            img = Image.open(img_mem)
        except Exception as e:
            raise ValueError(f"无法读取图片数据: {e}")
        width, height = img.size
        return width, height

    def img_handle(self, result):
        small_image = result['smallImage']
        big_image = result['bigImage']
        small_img_width, small_img_height = self.get_small_img_info(small_image)
        big_img_bin = self.save_image_to_cache(big_image)
        contours, _ = cv2.findContours(big_img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_x = 0
        min_diff = float('inf')
        target_found = False
        tolerance = 15

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            diff_w = abs(w - small_img_width)
            diff_h = abs(h - small_img_height)
            if diff_w <= tolerance and diff_h <= tolerance:
                total_diff = diff_w + diff_h
                if total_diff < min_diff:
                    min_diff = total_diff
                    best_x = x
                    target_found = True

        if target_found:
            return best_x
        else:
            return None


    async def main(self):
        result = await self.get_img_info()
        value = self.img_handle(result)
        return result['uuid'], value
