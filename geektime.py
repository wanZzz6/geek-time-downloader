# encoding: utf-
import logging
import random
import time
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

import requests

from render import CommentHtmlRender
from utils import *

logger = logging.getLogger()


def _get_default_headers():
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) '
                      'AppleWebKit/537.36 (KHTML, like Gecko)Chrome/81.0.4044.122 Safari/537.36'
    }


class ApiQueryError(Exception):
    pass


DOWNLOAD_HISTORY_FILE = 'download_history.txt'


class GeekTime:
    def __init__(self, phone: str = '', password: str = '', cookie: str = '', is_jump_exist: bool = True,
                 is_request_delay: bool = True):
        """
        @param phone: phone number
        @param password: password
        @param cookie: 不用账号密码，从浏览器复制 cookie 字符串过来也行
        @param is_jump_exist: 是否跳过之前下载过的
        @param is_request_delay: 是否请求之间添加随机延迟
        """
        self.is_request_delay = bool(is_request_delay)
        self.is_jump_exist = bool(is_jump_exist)
        assert cookie or phone and password
        self.phone = phone
        self.password = password
        self._session = requests.Session()
        self._session.headers.update(**_get_default_headers())
        cookie and self.set_cookie(cookie)
        self._already_download = set()
        self._load_history()

        self.products = []

        self.comment_render = CommentHtmlRender()
        # TODO

    def _load_history(self):
        if not Path(DOWNLOAD_HISTORY_FILE).exists():
            return
        with open(DOWNLOAD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                self._already_download.add(i.strip().split('-', 1)[0])

    def _dump_record(self, article_id: str, article_title: str):
        write_file(DOWNLOAD_HISTORY_FILE, '{}-{}\n'.format(article_id, article_title), 'a')
        self._already_download.add(article_id)

    def has_download(self, article_id: str):
        return str(article_id).strip() in self._already_download

    def set_cookie(self, cookie: str):
        tmp = {i.strip().split('=')[0]: i.strip().split('=')[1] for i in cookie.split(';')}
        self._session.cookies.update(tmp)
        self.check_cookie()

    def request(self, url: str, method='post', **kwargs) -> dict:
        """请求极客时间的接口，返回的都是 json 格式，没有使用高效的异步方式，且加了随机延迟，是怕频繁访问被限制

        @param url:
        @param method:
        @return: dict
        """
        logger.info(">>> {} {} {}".format(method.upper().center(5), url, kwargs))
        self.is_request_delay and time.sleep(random.random() * 2)
        parse_ret = urlparse(url)
        headers = {
            'Host': parse_ret[1],
            'Origin': '{}://{}'.format(parse_ret[0], parse_ret[1])
        }
        resp = self._session.request(method, url, headers=headers, **kwargs)
        logger.info('<<< {}'.format(resp))
        assert resp.status_code < 400, "请求失败 {}".format(resp.text)
        try:
            data = resp.json()
            assert data.get('code') == 0
            return data
        except Exception as e:
            logger.error('接口返回json异常: {}'.format(resp.text))
            raise ApiQueryError

    # ############################################################################
    def check_cookie(self):
        try:
            self.fetch_user_products('c1', False)
            logger.info('cookie 有效')
        except AssertionError:
            raise ApiQueryError('cookie 已过期') from None
        except UnicodeEncodeError:
            raise Exception('cookie 中不能有非ascii范围内的字符')

    def login(self) -> None:
        """login"""
        logger.info('正在登录')
        path = 'https://account.geekbang.org/account/ticket/login'
        param = {
            'country': 86,
            'cellphone': self.phone,
            'password': self.password,
            'captcha': '',
            'remember': 1,
            'platform': 3,
            'appid': 1,
            'source': ''
        }

        self.request(path, json=param)
        logger.info('登录成功')

    def fetch_column_info(self, pid: int, with_chapters=True):
        path = 'https://time.geekbang.org/serv/v3/column/info'
        param = {
            "product_id": pid,
            "with_recommend_article": True
        }
        data = self.request(path, json=param)['data']
        return {
            'id': data['id'],
            'title': data['title'],
            'type': data['type'],
            'chapters': self.fetch_column_chapter(data['id']) if with_chapters else {}
        }

    def fetch_user_products(self, type_: str = '', with_chapters=True) -> list:
        """获取当前用户课程列表

        @param type_: 课程类型： c1 专栏课  c3 视频课，空表示全部类型
        @param with_chapters: 是否查询章节信息
        @return: 课程信息 eg:  [{'title': '消息队列高手课', 'id': 100032301, 'type': 'c1', 'chapters: {}}]
        """
        logger.info('获取用户课程列表')
        path = 'https://time.geekbang.org/serv/v3/learn/product'
        param = {
            'desc': True,
            'expire': 1,
            'last_learn': 0,
            'learn_status': 0,
            'prev': 0,
            'size': 100,
            'sort': 1,
            'type': type_,
            'with_learn_count': 1
        }

        data1 = self.request(path, json=param)['data']['products']
        logger.info('成功获取用户课程列表 type:{} Total: {}'.format(type_, len(data1)))
        data = []
        for item in data1:
            data.append({
                'title': item['title'],
                'id': item['id'],
                'type': item['type'],
                'chapters': self.fetch_column_chapter(item['id']) if with_chapters else {}
            })

        return data

    def fetch_all_available_column(self) -> list:
        """获取全部可看的专栏"""
        path = 'https://time.geekbang.org/serv/v1/column/label_skus'

        param = {
            "label_id": 0,
            "type": 1  # 0全部，1 专栏，3视频课
        }

        data = self.request(path, json=param)['data']['list']
        return [i['column_sku'] for i in data if i['had_sub']]

    def fetch_column_chapter(self, cid) -> dict:
        """获取专栏章节信息
        @return eg: {'1466': '开篇词(2讲)', '1467': '基础篇(4讲)'}
        """
        logger.info('获取文章章节信息 cid:%s', cid)
        path = 'https://time.geekbang.org/serv/v1/chapters'
        param = {
            'cid': cid
        }
        data = self.request(path, json=param)['data']
        logger.info('成功获取章节信息 cid:%s  %s', cid, data)

        return {item['id']: "{}-{}({}讲)".format(index + 1, item['title'], item['article_count']) for index, item in
                enumerate(data)}

    def fetch_column_articles(self, cid: str):
        """获取专栏所有文章 id 和名称
        @param cid: 专栏id
        @return eg: [{'id': 245166, 'title': '开篇词丨学习正则，我们到底要学什么？'},
                     {'id': 245256, 'title': '导读 | 余晟：我是怎么学习和使用正则的？'}]
        """
        logger.info('获取专栏所有文章信息')
        path = 'https://time.geekbang.org/serv/v1/column/articles'
        param = {
            'cid': cid,
            'order': 'earliest',
            'prev': 0,
            'size': 500,
            'sample': False
        }

        data = self.request(path, json=param)['data']['list']
        logger.info("成功获取专栏所有文章信息  cid: %s", cid)

        return [{'id': i['id'], 'title': i['article_title']} for i in data]

    def fetch_comments(self, aid: Union[int, str], num: int = 40) -> list:
        """
        获取评论信息
        @param aid: 文章id
        @param num: 评论数
        @return:
        """
        path = 'https://time.geekbang.org/serv/v1/comments'
        # 该接口按时间先后升序每次返回20条数据
        param = {
            "aid": aid,
            "prev": 0
        }
        keys = ['comment_content', 'comment_ctime', 'user_name', 'score']
        comments = []
        total = 0
        while total < num:
            logger.info('获取评论信息  aid: %s  page: %d', aid, (total // 20) + 1)
            data = self.request(path, json=param)['data']
            tmp = []
            for comment in data['list']:
                comment_detail = {key: comment[key] for key in keys}
                # 展开更多讨论区
                if comment['discussion_count'] == 1:
                    if comment_detail.get('replies'):
                        comment_detail['replies'] = self._format_root_reply(comment['replies'])
                    else:
                        comment_detail['replies'] = self._sub_comments(comment['id'], 1)
                elif comment['discussion_count'] > 1:
                    comment_detail['replies'] = self._sub_comments(
                        comment['id'], comment['discussion_count'])
                tmp.append(comment_detail)

            comments.extend(tmp)
            if not data['page']['more'] or len(tmp) == 0:
                break
            num += len(tmp)
            param['prev'] = tmp[-1]['score']
        return comments

    @classmethod
    def _format_root_reply(cls, replies: list) -> list:
        return [{'comment_content': reply['content'], 'comment_ctime': reply['ctime'], 'user_name': reply['user_name']}
                for reply in replies]

    def _sub_comments(self, comment_id, num=10) -> list:
        logger.info('获取评论讨论区：  comment_id： %s', comment_id)
        path = 'https://time.geekbang.org/serv/discussion/v1/root_list'
        data = {
            "use_likes_order": True,
            "target_id": comment_id,
            "target_type": 1,
            "page_type": 1,
            "prev": 1,
            "size": num
        }
        data = self.request(path, json=data)['data']['list']

        return [self._format_sub_comments(item) for item in data]

    def _format_sub_comments(self, data) -> dict:
        tmp = {}
        try:
            tmp['user_name'] = data['author']['nickname']
            tmp['comment_content'] = data['discussion']['discussion_content']
            tmp['comment_ctime'] = data['discussion']['ctime']
            tmp['replies'] = [self._format_sub_comments(
                item) for item in data.get('child_discussions', [])]
        except Exception as e:
            logger.error(e, exc_info=True)
        return tmp

    def fetch_article_detail(self, article_id: Union[int, str]) -> dict:
        """文章详情"""
        logger.info(f'获取文章详情 article id: {article_id}')

        path = 'https://time.geekbang.org/serv/v1/article'
        param = {
            'id': article_id,
            'include_neighbors': True,
            'is_freelyread': True
        }

        data = self.request(path, json=param)['data']
        logger.info(f'成功获取文章详情 article id: {article_id}')
        keys = ['id', 'product_id', 'article_title', 'article_content',
                'audio_download_url', 'audio_download_url', 'chapter_id', 'cid', 'comment_count', 'product_type',
                'article_cover']

        return {k: data.get(k) for k in keys}

    def _save_article(self, product: dict, article_detail: dict, file_type='.md', offline_pic=False,
                      offline_audio=True, comments_num=20):
        """
        # TODO md文件 写入评论数据
        @param product: 专栏信息
        @param article_detail: 文章信息
        @param file_type: 文件后缀
        @param offline_pic: 是否将文章中图片保存到本地
        @param offline_audio: 是否将音频下载到本地
        @param comments_num: 保存评论数，前 n条
        @return:
        """
        logger.info('开始保存文件 aid:%s %s', article_detail['id'], article_detail['article_title'])
        if comments_num > 0 or file_type != '.md':
            file_type = '.html'
        # 如果有章节信息，则按章节分目录保存
        dir_name = Path(product['title'].strip().replace('/', '')).joinpath(
            product['chapters'].get(article_detail['chapter_id'], '/'))
        dir_path = mkdir(dir_name)
        # 去除文件名中非法字符
        file_name = check_filename(article_detail['article_title'])
        file_path = dir_path.resolve().joinpath(file_name).with_suffix(file_type)

        audio_uri = article_detail['audio_download_url']

        if offline_audio and audio_uri:
            audio_file = dir_path.resolve().joinpath(file_name).with_suffix('.mp3')
            logger.info('开始下载音频 - %s - %s', article_detail['article_title'], audio_uri)
            download_audio(audio_uri, audio_file, article_detail.get('article_cover'))
            logger.info('下载音频成功 - %s', audio_file)
            # 相对地址
            audio_uri = './{}'.format(audio_file.name)
        if offline_pic:
            # TODO 下载离线图片
            pass
        comment_html = ''
        if comments_num > 0:
            logger.info('获取文章评论...')
            try:
                comments = self.fetch_comments(article_detail['id'], comments_num)
                logger.info('共获取到评论：{}'.format(len(comments)))
            except Exception:
                logger.error('获取评论失败', exc_info=True)
            else:
                comment_html = self.comment_render.render(comments)

        content = f"""
<h1>{article_detail['article_title']}</h1>
<img src="{article_detail.get('article_cover')}" style="zoom: 67%;" />
<br>
<br>
"""
        if audio_uri:
            content += f'<audio title="{file_name}" src="{audio_uri}" controls="controls"></audio>'
        content += f"""
<br>
{article_detail['article_content']}
<br>
<br>

{comment_html}
"""

        write_file(file_path, content)
        self._dump_record(article_detail['id'], file_name)

    # ################################# 常用下载接口 ####################################

    def download_column(self, product: dict, file_type='.md', offline_pic=False, offline_audio=True,
                        comments_num=20):
        """下载专栏"""
        logger.info(' 开始下载专栏：pid:%s  %s '.center(66, '#'), product['id'], product['title'], )
        start = time.time()
        articles = self.fetch_column_articles(product['id'])
        for article in articles:
            self._download_article(product, article, file_type, offline_pic, offline_audio, comments_num)
            logger.info('-' * 100)
        logger.info(' 专栏下载完成，文章数：%d，耗时：%.1fs '.center(66, '#'), len(articles), (time.time() - start))

    def _download_article(self, product: dict, article: dict, file_type='.md', offline_pic=False, offline_audio=True,
                          comments_num=20):
        if self.is_jump_exist and self.has_download(article['id']):
            logger.info('跳过已下载的文章 aid:%s  %s', article['id'], article['title'])
            return
        logger.info('下载文章 aid:%s  %s', article['id'], article['title'])
        article_detail = self.fetch_article_detail(article['id'])
        self._save_article(product, article_detail, file_type, offline_pic, offline_audio, comments_num)

    def download_article_by_aid(self, aid: Union[str, int], file_type='.md', offline_pic=False, offline_audio=True,
                                comments_num=20):
        logger.info('下载单个专栏文章：%s', aid)
        article_detail = self.fetch_article_detail(aid)
        product = self.fetch_column_info(article_detail['product_id'])
        self._save_article(product, article_detail, file_type, offline_pic, offline_audio, comments_num)
        logger.info('成功下载单个文章： aid:%s %s - %s', aid, product['title'], article_detail['article_title'])

    def download_my_products(self, type_: str = 'c1', file_type='.md', offline_pic=False, offline_audio=True,
                             comments_num=20):
        """
        下载当前用户的所有课程
        @param type_: 课程类型： c1 专栏课  c3 视频课，空表示全部类型
        @param file_type: 保存文件类型： md、html
        @param offline_pic: 下载图片
        @param offline_audio: 下载音频
        @param comments_num: 每篇文章保存的评论数
        """
        my_products = self.fetch_user_products(type_, False)
        for product in my_products:
            self.download_column(product, file_type, offline_pic, offline_audio, comments_num)
