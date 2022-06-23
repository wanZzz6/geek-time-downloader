# encoding: utf-8
import logging
import yaml
from utils import load_yaml, dump_yaml

from geektime import GeekTime

logging.basicConfig(
    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    level=logging.INFO
)
handler = logging.FileHandler(filename='geek_crawler.log', mode='a', encoding='utf-8')
logging.root.addHandler(handler)

logger = logging.getLogger()


def demo1():
    """下载一个专栏"""
    pid = 100053301
    product = geek.fetch_column_info(pid, True)
    geek.download_column(product, 'html', comments_num=40)


def demo2():
    """下载单个专栏文章"""
    aid = 245214
    geek.download_article_by_aid(aid)


def demo3():
    """遍历所有可用的专栏并下载，按课程最新发布顺序"""
    product_ids = geek.fetch_all_available_column()
    for pid in product_ids:
        product = geek.fetch_column_info(pid, True)
        geek.download_column(product, 'html', comments_num=40)
        logger.info('#' * 100)


def demo4():
    """下载当前用户 ‘我的课程’ 中的所有专栏"""
    geek.download_my_products('c1')


if __name__ == '__main__':
    cookie = """
    gksskpitn=9f6824f4-2fbe-4fde-914a-a64f009080f8; Hm_lvt_59c4ff31a9ee6263811b23eb921a5083=1655426621; Hm_lvt_022f847c4e3acd44d4a2481d9187f1e6=1655426621; LF_ID=1655426621478-6672934-806037; _ga=GA1.2.1195576613.1655426622; GCID=2202ec2-e4a2191-6df9357-a1ec642; GRID=2202ec2-e4a2191-6df9357-a1ec642; GCESS=BgEIJPMjAAAAAAAIAQMEBACNJwAMAQEHBAMTpE0GBM5nQXgDBNtjsGICBNtjsGIJAQELAgYADQEBCgQAAAAABQQAAAAA; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%222356004%22%2C%22first_id%22%3A%221818081378caee-0ab06881ca7b788-714e2d2d-1881600-1818081378dcc7%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E5%BC%95%E8%8D%90%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Faccount.geekbang.com%2F%22%2C%22%24latest_landing_page%22%3A%22https%3A%2F%2Ftime.geekbang.org%2Fcolumn%2Farticle%2F262354%3Fcid%3D100053301%22%7D%2C%22%24device_id%22%3A%221816f1d9f9b37a-0265b29a5f606e2-714e2d28-1881600-1816f1d9f9ccb6%22%7D; _gid=GA1.2.1958634363.1655829197; Hm_lpvt_59c4ff31a9ee6263811b23eb921a5083=1655871115; Hm_lpvt_022f847c4e3acd44d4a2481d9187f1e6=1655871115; gk_process_ev={%22count%22:24%2C%22utime%22:1655728076101%2C%22referrer%22:%22https://time.geekbang.org/dashboard/course%22%2C%22referrerTarget%22:%22%22%2C%22target%22:%22%22}; SERVERID=3431a294a18c59fc8f5805662e2bd51e|1655879230|1655864434
    """
    geek = GeekTime(cookie=cookie, is_jump_exist=True,)
    # 或者
    # cellphone = '188xxxxxxxxxxx'
    # pwd = '123456'
    # geek_crawler =
    # GeekTime(cellphone, pwd)
    demo3()
