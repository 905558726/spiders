import json
from itemadapter import ItemAdapter


class IcpCrawlerPipeline:

    def open_spider(self, spider):
        """当爬虫启动时执行，初始化并打开 JSON 文件"""
        # 创建或清空名为 beian_results.json 的文件，指定编码为 utf-8
        self.file = open('beian_results.json', 'w', encoding='utf-8')
        # 写入 JSON 数组的开头符号
        self.file.write("[\n")
        # 用于标记是否是第一条数据，用来优雅地处理逗号
        self.first_item = True

    def process_item(self, item, spider):
        """每当 Spider yield 一个 item 时，该方法会被自动调用"""
        # 将 Scrapy Item 转换为标准的 Python 字典
        item_dict = ItemAdapter(item).asdict()

        # 将字典转换为 JSON 字符串，ensure_ascii=False 保证中文正常显示
        line = json.dumps(item_dict, ensure_ascii=False, indent=4)

        # 为了生成标准的 JSON 数组，从第二条数据开始，每一条前面加个逗号和换行
        if not self.first_item:
            self.file.write(",\n")
        else:
            self.first_item = False

        # 写入文件
        self.file.write(line)

        # 必须返回 item，以便后续的其他管道（如果有的话）继续处理
        return item

    def close_spider(self, spider):
        """当爬虫关闭时执行，收尾并关闭文件"""
        # 写入 JSON 数组的结尾符号
        self.file.write("\n]")
        # 释放文件资源
        self.file.close()