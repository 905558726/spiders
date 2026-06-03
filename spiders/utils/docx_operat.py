import os
import re
from PIL import Image
from docx import Document
from docx.shared import Cm
import utils.excel_operat as excel

TP_PATTERN = re.compile(r'TP\d+')
IMG_EXT = ('.png', '.jpg', '.jpeg')

def build_img_dict(img_dir: str) -> dict:
    """遍历文件夹，生成 单据号->绝对路径 的字典"""
    mp = {}
    for root, _, files in os.walk(img_dir):
        for f in files:
            name, ext = os.path.splitext(f)
            if ext.lower() in IMG_EXT and TP_PATTERN.fullmatch(name):
                mp[name] = os.path.join(root, f)
    print(f'[INFO] 共扫描到 {len(mp)} 张可用图片')
    return mp


def find_tp_in_paragraph(p):
    """找到订单编号位置"""
    text = p.text.strip()
    m = TP_PATTERN.search(text)
    return m.group(0) if m else None


def insert_picture_after_paragraph(doc, p, img_path, width_cm=15):
    """
    在段落 p 后面插入一张居中图片，等比例缩放为 15 cm 宽
    """
    # 1. 新建段落并挂到 XML 后面
    new_p = doc.add_paragraph()
    p._p.addnext(new_p._p)
    new_p.alignment = 1          # 居中

    # 2. 用 PIL 读原图，计算缩放比例
    with Image.open(img_path) as im:
        px_w, px_h = im.size

    # 3. 插入图片（指定宽高即可等比例）
    run = new_p.add_run()
    run.add_picture(img_path, width=Cm(width_cm))


def insert_images(word_path: str, img_dir: str, excel_path: str, col: str):
    """
    在word文档查找订单号（TP开头）

    :param word_path: word文档路径
    :param img_dir: 图片存放文件夹位置
    :param excel_path: 用于修改状态excel路径
    :param col: 用于查询行号的列
    :return:
    """
    img_dict = build_img_dict(img_dir)
    if not img_dict:
        print('[WARN] 文件夹内未找到任何 TPxxxx 图片')
        return

    doc = Document(word_path)
    tasks = []          # (paragraph, img_path)

    for p in doc.paragraphs:
        tp = find_tp_in_paragraph(p)
        try:
            if tp and tp in img_dict:
                tasks.append((p, img_dict[tp]))
                excel.append_status(tp, '插入成功', excel_path, col, 3)
            elif tp and tp not in img_dict:
                print(f'[WARN] 缺失图片：{tp}')
                excel.append_status(tp, '插入失败', excel_path, col, 3)
        except Exception as e:
            excel.append_status(tp, '插入异常', excel_path, col, 3)



    # 倒序插入，避免段落错位
    for p, img_path in reversed(tasks):
        insert_picture_after_paragraph(doc, p, img_path)

    doc.save(word_path)
    print(f'[INFO] 处理完成，已保存：{word_path}')