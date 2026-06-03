import os
import re
import pandas as pd
from openpyxl import Workbook, load_workbook

def col_to_list(file_path, sheet_name=None, col_name=None, col_index=None, drop_na=True):
    """
    读取 Excel 指定列 → list

    :param file_path:   Excel 文件路径
    :param sheet_name:  工作表名（None 表示第一个表）
    :param col_name:    列名（如 '姓名'），与 col_index 二选一
    :param col_index:   列序号（0 起始），与 col_name 二选一
    :param drop_na:      是否去掉 NaN / 空值
    :return:            list
    """
    df = pd.read_excel(file_path,sheet_name=sheet_name)

    # 二选一取列
    if col_name is not None:
        series = df[col_name]
    elif col_index is not None:
        series = df.iloc[:, col_index]
    else:
        raise ValueError('必须指定 col_name 或 col_index')

    if drop_na:
        series = series.dropna()

    return series.astype(str).tolist()

def create_excel(sheet_name: str, excel_path: str, col_names: list = None):
    """
    创建excel表格

    :param sheet_name:
    :param excel_path:
    :param col_names: 列名列表
    :return:
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(col_names)
    folder = os.path.dirname(excel_path)
    os.makedirs(folder, exist_ok = True)
    wb.save(excel_path)


def append_data_to_excel(data_list, file_path, col_idx_list):
    """将列表数据作为一行追加到Excel文件，并自动清洗非法控制字符"""

    def clean_value(v):
        """清洗非法字符，防止 IllegalCharacterError"""
        if isinstance(v, str):
            # 匹配 0x00-0x08, 0x0b-0x0c, 0x0e-0x1f 等非法控制字符并替换为空
            return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', v)
        return v

    # 检查文件是否存在
    if os.path.exists(file_path):
        wb = load_workbook(file_path)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active

    new_row = ws.max_row + 1

    # 处理多行嵌套列表情况
    if isinstance(data_list[0], list):
        for data in data_list:
            for col_idx, value in enumerate(data, 1):
                cell = ws.cell(row=new_row, column=col_idx)

                # 清洗数据
                safe_val = clean_value(value)

                if col_idx in col_idx_list:
                    cell.value = str(safe_val)  # 强制转换为字符串
                    cell.number_format = '@'  # 设置为文本格式
                else:
                    cell.value = safe_val
            new_row += 1
        print(f"✅ 已成功追加 {len(data_list)} 行数据")

    # 处理单行列表情况
    else:
        for col_idx, value in enumerate(data_list, 1):
            cell = ws.cell(row=new_row, column=col_idx)

            # 清洗数据
            safe_val = clean_value(value)

            if col_idx in col_idx_list:
                cell.value = str(safe_val)
                cell.number_format = '@'
            else:
                cell.value = safe_val
        print(f"✅ 第 {new_row} 行已写入")

    wb.save(file_path)

def append_status(code, status, excel_path, col_name, col_index):
    """在excel文件插入该订单处理状态（如果要插入状态单元格不为空则跳过）

    :param code: 用于查找对应行的订单编号
    :param status: 插入状态
    :param excel_path: excel路径
    :param col_name: 列名（在该列使用code查找对应订单的行）
    :param col_index: 插入在第几列
    """
    # 打开工作簿
    wb = load_workbook(excel_path)
    ws = wb.active

    order_col = None
    for cell in ws[1]:
        if cell.value == col_name:
            order_col = cell.column  # 列号，从 1 开始
            break
    if order_col is None:
        raise ValueError(f'找不到“{col_name}”列')

    target_row = None
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        if row[order_col - 1].value == code:  # 列号转 0 基索引
            target_row = row[0].row  # 记录行号
            break
    if target_row is None:
        raise ValueError(f'找不到订单 {code}')

    target_cell = ws.cell(row=target_row, column=col_index)
    if target_cell.value in (None, ''):
        target_cell.value = status
        print(f'已在第 {target_row} 行第 {col_index} 列写入“{status}”')
    else:
        print(f'第 {target_row} 行第 {col_index} 列已有数据，跳过写入')

    # 4. 保存文件
    wb.save(excel_path)

