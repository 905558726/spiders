import json


def python_to_java_json(obj):
    """
    将Python对象转换为符合Java标准的JSON字符串
    - 双引号
    - None转换为空字符串
    - True/False转换为true/false
    """

    def convert_value(value):
        if value is None:
            return ""
        elif isinstance(value, bool):
            return value  # JSON中的true/false
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            return value
        elif isinstance(value, list):
            return [convert_value(item) for item in value]
        elif isinstance(value, dict):
            return {key: convert_value(val) for key, val in value.items()}
        else:
            return str(value)

    # 先递归转换值，然后序列化为JSON
    converted_obj = convert_value(obj)
    return json.dumps(converted_obj, ensure_ascii=False, separators=(',', ':'))
