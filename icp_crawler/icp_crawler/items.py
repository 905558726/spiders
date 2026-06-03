# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class IcpCrawlerItem(scrapy.Item):
    # 核心主体与域名信息
    unit_name = scrapy.Field()  # 企业/单位名称 (例如: 北京百度网讯科技有限公司)
    nature_name = scrapy.Field()  # 单位性质 (例如: 企业 / 个人)
    domain = scrapy.Field()  # 备案域名 (例如: baidu.com)
    domain_id = scrapy.Field()  # 域名内部ID

    # 许可证/备案号信息
    main_licence = scrapy.Field()  # 主体备案号 (例如: 京ICP证030173号)
    service_licence = scrapy.Field()  # 网站/服务备案号 (例如: 京ICP证030173号-1)

    # 系统内部ID
    main_id = scrapy.Field()  # 主体ID

    # 更新时间
    update_time = scrapy.Field()  # 备案更新时间 (例如: 2019-05-16 16:06:21)
