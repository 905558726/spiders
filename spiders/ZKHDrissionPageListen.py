import os
import re

import aiohttp
import asyncio
import uuid
import json
import time
import queue
import shutil
import random
import requests
import threading
import pyautogui
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from DrissionPage import ChromiumPage, ChromiumOptions


class ZKHDrissionPage:

    def __init__(self):
        self.code_result = []

        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

        self.insert_max_try = 3

        self.page_dict = {}

        self.si_ye_cao_url = 'http://proxy.siyetian.com/apis_get.html?token='

        self.status_dict = {}

        self.fifo_queue = queue.Queue()

        self.is_listen = True

    def human_scroll(self, page, min_times, max_times):
        """
        模拟人类分段向下滚动页面
        """
        # 随机滚动 3 到 6 次
        scroll_times = random.randint(min_times, max_times)

        for _ in range(scroll_times):
            # 随机产生每次滚动的像素距离（模仿用力大或小）
            px = random.randint(500, 800)
            # 模拟滚动动作
            page.scroll.down(px)

            # 关键：滚动后的随机停顿，模拟人眼阅读
            time.sleep(random.uniform(0.8, 2.0))

            # 偶尔向上微调一下，模拟人翻过头了往回拉
            if random.random() > 0.8:
                page.scroll.up(random.randint(50, 150))
                time.sleep(random.uniform(0.5, 1.0))

    def solve_aliyun_slider(self, page):
        # 1. 定位元素
        slider = page.ele('#aliyunCaptcha-sliding-slider')
        track = page.ele('#aliyunCaptcha-sliding-text-box')

        # 2. 获取屏幕绝对坐标 (x, y)
        # screen_location 返回的是元素左上角的屏幕坐标
        slider_rect = slider.rect.screen_location
        track_width = track.rect.size[0]

        # 计算滑块中心点作为起始点
        start_x = slider_rect[0] + slider.rect.size[0] / 2
        start_y = slider_rect[1] + slider.rect.size[1] / 2

        # 3. 移动鼠标到滑块并按下
        pyautogui.moveTo(start_x, start_y, duration=random.uniform(0.3, 0.5))
        pyautogui.mouseDown()

        current_x = start_x
        target_x = start_x + track_width

        # 4. 模拟真人滑动轨迹 (模拟加速度与减速)
        while current_x < target_x:
            remaining = target_x - current_x

            if remaining > track_width * 0.3:
                # 前期快速滑动
                step = random.randint(15, 35)
            elif remaining > 10:
                # 后期减速，增加微小抖动
                step = random.randint(3, 8)
            else:
                # 最后冲刺
                step = remaining if remaining > 0 else 0

            current_x += step
            # 增加 Y 轴微小偏移，模拟人手抖动
            offset_y = random.randint(-2, 2)

            # 使用 pyautogui 移动到绝对坐标
            # tween 可以设置移动渐变函数，使其更平滑
            pyautogui.moveTo(current_x, start_y + offset_y, duration=random.uniform(0.01, 0.03))

            if current_x >= target_x:
                break

        # 5. 稍微回弹或微调 (阿里验证码经常检测精准度)
        pyautogui.moveRel(random.randint(-3, 1), random.randint(-1, 1), duration=0.1)

        # 6. 松开鼠标
        time.sleep(random.uniform(0.2, 0.4))
        pyautogui.mouseUp()

    def get_miss_block(self, page):
        with open(r'E:\python\spider\resource\html.txt', 'w', encoding='utf-8') as f:
            f.write(page.html)
            # 1. 尝试获取 iframe，增加超时判断
            try:
                # 使用 css 选择器配合模糊匹配 src
                iframe = page.get_frame('tag:iframe@src^https://turing.captcha.qcloud.com', timeout=3)
            except Exception:
                print("未找到腾讯验证码 iframe")
                return None
            if not iframe:
                return None
            # 2. 在 iframe 内部查找背景图
            # 腾讯验证码背景图通常是 #slideBg
            bg_ele = iframe.ele('#slideBg', timeout=1)
            if bg_ele:
                # 腾讯的背景图有时在 style 里，有时在 src 里
                style_str = bg_ele.attr('style')
                if style_str:
                    # 兼容处理 &quot;
                    clean_style = style_str.replace('&quot;', '"')
                    match = re.search(r'url\("?(.*?)"?\)', clean_style)
                    if match:
                        img_url = match.group(1)
                        # 腾讯的图片 URL 可能是相对路径或带协议
                        return img_url if img_url.startswith('http') else f"https:{img_url}"
                # 如果 style 里没有，尝试找 src (部分版本)
                src = bg_ele.attr('src')
                if src: return src
            return None


    def web_operate(self, url = "https://www.zkh.com/list/c-11003798.html", category_info = ("照明", "灯具配件", "其他灯具配件"), current_page=1):
        self.status_dict[category_info[2]] = False
        first_run = True
        last_btn_text = 1
        page = None
        for i in range(10):
            try:
                refresh_times = 0
                while True:
                    co = ChromiumOptions()
                    co.set_proxy(self.si_ye_cao())
                    page = ChromiumPage(co)
                    page.get(url)
                    page.set.window.max()
                    time.sleep(3)
                    if page.ele('text:无法访问此网站', timeout=1) or page.ele('text:未连接到互联网', timeout=1):
                        page.quit()
                    if page.ele('text:抱歉，没有找到相关商品', timeout=1) and refresh_times <= 3:
                        refresh_times += 1
                        page.refresh(True)
                    else:
                        break
                try:
                    close_span = page.ele(".ant-modal-close-x")
                    if close_span:
                        close_span.click()
                except Exception as e:
                    pass
                while True:
                    if "安全验证-震坤行" in page.title:
                        print(self.get_miss_block(page))
                    elif "验证" in page.title:
                        self.solve_aliyun_slider(page)
                        time.sleep(3)
                    else:
                        break
                while True:
                    if page.ele('text:无法访问此网站', timeout=1) or page.ele('text:未连接到互联网', timeout=1):
                        page.quit()
                        co = ChromiumOptions()
                        co.set_proxy(self.si_ye_cao())
                        page = ChromiumPage(co)
                        page.get(url)
                        page.set.window.max()
                        time.sleep(3)
                    else:
                        break
                try:
                    close_span = page.ele(".ant-modal-close-x")
                    if close_span:
                        close_span.click()
                except Exception as e:
                    pass
                try:
                    last_btn_text = int(page.ele('.pagination-page-total').text)
                except Exception as e:
                    pass
                print(last_btn_text)
                self.is_listen = True
                threading.Thread(target=self.capture_zkh_continuous, args=(page, category_info,)).start()
                page.ele('@@tag()=a@@text():销量').click()
                for page_num in range (current_page, last_btn_text + 1):
                    refresh_times = 0
                    while True:
                        if page.ele('text:无法访问此网站', timeout=1) or page.ele('text:未连接到互联网', timeout=1):
                            raise "代理IP失效"
                        if page.ele('text:抱歉，没有找到相关商品', timeout=1) and refresh_times <= 3:
                            refresh_times += 1
                            page.refresh(True)
                        else:
                            break
                    tmp_count = 0
                    if current_page != 1 and not first_run:
                        self.human_scroll(page, 7, 10)
                        if last_btn_text >= current_page:
                            input_box = page.ele('.zxfinput')
                            ok_btn = page.ele('.zxfokbtn')
                            if input_box:
                                input_box.scroll.to_see()
                                input_box.click()
                                input_box.input(str(current_page), clear=True)
                                page.run_js("""
                                    var el = arguments[0];
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                    el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Enter' }));
                                """, input_box)
                                time.sleep(0.5)
                                if ok_btn:
                                    ok_btn.click()
                    while True:
                        self.human_scroll(page, 7, 10)
                        first_run = True
                        time.sleep(random.uniform(0.8, 2.0))
                        html_text = page.html
                        pattern = re.compile(r'goods-item-wrap-new')
                        count = len(pattern.findall(html_text))
                        if tmp_count ==  count or count == 60:
                            page.wait(3)
                            # open(r'E:\python\spider\resource\html.txt', 'w', encoding='utf-8').write(html_text)
                            soup = BeautifulSoup(html_text, 'lxml')
                            links = []
                            for a in soup.find_all('a', href=True):
                                href = a['href']
                                if '/item/' in href:
                                    full_url = f"https://www.zkh.com{href}" if href.startswith('/') else href
                                    links.append(full_url)
                            unique_links = list(set(links))
                            print(f"共提取到 {len(unique_links)} 个商品链接")
                            if len(unique_links) == 0 and refresh_times <= 3:
                                page.refresh(True)
                            elif len(unique_links) != 0:
                                current_page += 1
                            break
                        else:
                            tmp_count = count

                    if last_btn_text >= current_page:
                        input_box = page.ele('.zxfinput')
                        ok_btn = page.ele('.zxfokbtn')
                        if input_box:
                            input_box.scroll.to_see()
                            input_box.click()
                            input_box.input(str(current_page), clear=True)
                            page.run_js("""
                                var el = arguments[0];
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                                el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Enter' }));
                            """, input_box)
                            time.sleep(0.5)
                            if ok_btn:
                                ok_btn.click()

                self.is_listen = False
                time.sleep(3)
                return True
            except Exception as e:
                print(e)
                current_page -= 1
                self.is_listen = False
                if page:
                    page.quit()
                time.sleep(3)
        return False



    def capture_zkh_continuous(self, page, category_info):
        """
        page: ChromiumPage 实例
        target_count: 本次操作预期捕获的数据包数量
        """
        target_url = '/servezkhApi/search/product/pc'

        page.listen.start(target_url)

        while True:
            if self.is_listen:
                res = page.listen.wait(timeout=1)
                if res:
                    raw_body = res.response.body

                    # 1. 确保 body 是字典类型
                    if isinstance(raw_body, str):
                        try:
                            body_dict = json.loads(raw_body)
                        except json.JSONDecodeError:
                            print("错误：无法将响应体解析为 JSON 格式")
                            body_dict = {}
                    else:
                        body_dict = raw_body
                    try:
                        if body_dict:
                            content = body_dict.get('result', {}).get('page', {}).get('content', [])
                            for item in content:
                                result = {
                                    "categoryName1": category_info[0], "categoryName2": category_info[1],
                                    "categoryName3": category_info[2], "page": 1,
                                    "html": json.dumps(item, ensure_ascii=False, separators=(',', ':'))
                                }
                                asyncio.run(self.insert_db(result))
                    except Exception as e:
                        print(e)
            else:
                break

    async def insert_db(self, data):
        url = "http://121.37.229.249:2039/goods/capture/zkh/html"
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        for try_time in range(self.insert_max_try):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        json_data = await resp.json()
                        return json_data.get('success', False)
            except Exception:
                if try_time == self.insert_max_try - 1: return False
                await asyncio.sleep(1)
        return False

    def si_ye_cao(self):
        try:
            response = requests.get(self.si_ye_cao_url)
            proxy_ip = response.text.strip()
            if not proxy_ip or proxy_ip.startswith('{'):
                print(f"获取IP异常：{proxy_ip}")
                time.sleep(2)
                return self.si_ye_cao()
            return 'http://' + str(proxy_ip)
        except requests.exceptions.RequestException as e:
            time.sleep(2)
            return self.si_ye_cao()
        except Exception as e:
            time.sleep(2)
            return self.si_ye_cao()

    def safe_read_excel(self, excel_path, **kwargs):
        """安全读取 Excel 文件，自动处理常见问题"""
        try:
            file_ext = Path(excel_path).suffix.lower()

            # 默认将"抓取状态"列设为字符串类型
            default_dtype = {"抓取状态": str}

            # 如果调用者没有指定dtype，则使用默认值
            if 'dtype' not in kwargs:
                kwargs['dtype'] = default_dtype
            else:
                # 合并调用者的dtype和默认dtype
                kwargs['dtype'] = {**default_dtype, **kwargs['dtype']}

            if file_ext == '.xlsx':
                return pd.read_excel(excel_path, engine='openpyxl', **kwargs)
            elif file_ext == '.xls':
                return pd.read_excel(excel_path, engine='xlrd', **kwargs)
            else:
                return pd.read_excel(excel_path, engine='openpyxl', **kwargs)
        except Exception as e:
            print(f"读取 Excel 文件失败: {e}")
            raise

    def safe_write_excel(self, df, excel_path, **kwargs):
        """安全写入 Excel 文件，使用临时文件避免损坏"""
        try:
            # 创建临时文件路径（使用随机名称但保持正确扩展名）
            file_dir = Path(excel_path).parent
            file_stem = Path(excel_path).stem
            file_ext = Path(excel_path).suffix

            # 临时文件使用随机名称，但保持正确的扩展名（如：震坤行分类信息_a1b2c3.xlsx）
            temp_filename = f"{file_stem}_{uuid.uuid4().hex[:8]}{file_ext}"
            temp_path = str(file_dir / temp_filename)
            backup_path = str(file_dir / f"{file_stem}{file_ext}.bak")

            # 选择合适的引擎
            engine = 'openpyxl' if file_ext.lower() == '.xlsx' else 'xlrd'

            # 如果原文件存在，先备份
            if os.path.exists(excel_path):
                shutil.copy2(excel_path, backup_path)
                print(f"✓ 已创建备份: {backup_path}")

            # 写入临时文件（使用正确的扩展名）
            df.to_excel(temp_path, index=False, engine=engine, **kwargs)
            print(f"✓ 临时文件写入成功: {temp_path}")

            # 原子性替换原文件
            if os.path.exists(excel_path):
                os.remove(excel_path)
            os.rename(temp_path, excel_path)
            print(f"✓ 文件更新成功: {excel_path}")

            # 删除备份文件
            if os.path.exists(backup_path):
                os.remove(backup_path)

            return True
        except Exception as e:
            print(f"✗ 写入 Excel 文件失败: {e}")
            # 如果有备份，恢复备份
            backup_path = str(Path(excel_path).parent / f"{Path(excel_path).stem}{Path(excel_path).suffix}.bak")
            if os.path.exists(backup_path):
                if os.path.exists(excel_path):
                    os.remove(excel_path)
                os.rename(backup_path, excel_path)
                print(f"✓ 已从备份恢复文件: {excel_path}")
            raise

    def get_category_info(self, excel_path):
        """获取Excel中的分类信息"""
        try:
            df = self.safe_read_excel(excel_path)
            info_dict = {}
            col_name = df.columns.tolist()

            if "抓取状态" not in col_name:
                df["抓取状态"] = ""
                # 确保"抓取状态"列为字符串类型
                df["抓取状态"] = df["抓取状态"].fillna("").astype(str)
                self.safe_write_excel(df, excel_path)
                # 重新读取以确保类型正确
                df = self.safe_read_excel(excel_path)

            # 确保所有现有"抓取状态"值都转换为字符串
            df["抓取状态"] = df["抓取状态"].fillna("").astype(str)

            for index, row in df.iterrows():
                if row["抓取状态"] != "已完成":
                    category_01 = row["一级分类名"]
                    category_02 = row["二级分类名"]
                    category_03 = row["三级分类名"]
                    category_id_03 = row["三级分类id"]
                    info_dict[category_id_03] = (category_01, category_02, category_03)

            return info_dict
        except Exception as e:
            print(f"获取分类信息失败: {e}")
            raise

    def main(self):
        folder_path = r'E:\python\spider\resource\104'

        # 筛选Excel文件
        excel_files = []
        for file in os.listdir(folder_path):

            if file.endswith('.xlsx') or file.endswith('.xls'):
                excel_files.append(file)

        for excel_name in excel_files:
            excel_path = os.path.join(folder_path, excel_name)
            completed_indices = []
            try:
                info_dict = self.get_category_info(excel_path)
                for key, value in info_dict.items():
                    try:
                        url = f"https://www.zkh.com/list/c-{key}.html"
                        flag = self.web_operate(url, value)
                        if flag:
                            self.code_result = []
                            df = self.safe_read_excel(excel_path)
                            index_to_update = df[df['三级分类id'] == key].index
                            if len(index_to_update) > 0:
                                completed_indices.append((index_to_update[0], key))
                            df.loc[index_to_update, "抓取状态"] = "已完成"
                            self.safe_write_excel(df, excel_path)
                        print(f"{key}: {flag}")
                    except Exception as e:
                        print(f"处理分类 {key} 时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

            except Exception as e:
                print(f"主函数执行出错: {e}")
                import traceback
                traceback.print_exc()

            finally:
                try:
                    if completed_indices:
                        df = self.safe_read_excel(excel_path)
                        for idx, category_id in completed_indices:
                            df.loc[idx, "抓取状态"] = "已完成"
                        self.safe_write_excel(df, excel_path)
                        print(f"✓ 最终更新了 {len(completed_indices)} 个分类状态")
                except Exception as e:
                    print(f"finally 块执行出错: {e}")
                    import traceback
                    traceback.print_exc()

if __name__ == '__main__':
    zkh_spider = ZKHDrissionPage()
    zkh_spider.main()