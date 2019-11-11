# -*- coding: utf-8 -*-
import os
import re
import time
import json
import operator
import requests
import collections
import urllib.request
import http.cookiejar as cookielib

from pprint import pprint
from opencc import OpenCC
from logger import logger
from fuzzywuzzy import fuzz
from utils import upload_to_imgur
from bs4 import BeautifulSoup as bs
from errors import (WenkuLoginError, WenkuGetMainPageError, EpubstSeachError,
                    NoSearchError)
from config.config import (WENKU_ACCOUNT, WENKU_PASSWORD)

loc = os.path.dirname(__file__)


class WENKUParser:
    def __init__(self):
        self.base_url = 'https://www.wenku8.net/index.php'
        self.login_url = 'https://www.wenku8.net/login.php'
        self.main_page = 'https://www.wenku8.net/book/{}.htm'
        self.search_url = 'https://www.wenku8.net/modules/article/search.php?searchtype=articlename&searchkey={}'
        self.download_url = 'http://dl.wenku8.com/packtxt.php?aid={}&vid={}&charset=big5'
        self.wenku_session = requests.Session()
        self.data = {}
        with open('config/data.json', 'r', encoding='utf8') as fp:
            self.data = json.load(fp)

    def login(self):
        # login into wenku
        postData = {
            'username': WENKU_ACCOUNT,
            'password': WENKU_PASSWORD,
            'usecookie': '315360000',
            'action': 'login'
        }
        self.wenku_session.cookies = cookielib.LWPCookieJar(
            filename=os.path.join(loc, 'config/cookie.txt'))
        try:
            # use cookie login
            self.wenku_session.cookies.load()
            resp = self.wenku_session.get(self.base_url)
            resp.encoding = 'gbk'
            soup = bs(resp.text, 'html.parser')
            not_login = soup.find('caption')
            if not_login:
                # use account logging
                if not WENKU_ACCOUNT or not WENKU_PASSWORD:
                    logger.error('You need to login wenku then you can search')
                    return -1
                resp = self.wenku_session.post(self.login_url, data=postData)
                resp.encoding = 'gbk'
                self.wenku_session.cookies.save()
            return 1
        except:
            raise WenkuLoginError

    def get_main_page(self, aid):
        try:
            url = self.main_page.format(aid)
            resp = requests.get(url=url)
            resp.encoding = 'gbk'
            soup = bs(resp.text, 'html.parser')
            title = soup.find('span').find('b').text
            author = soup.find('td', text=re.compile('小说作者')).text.replace(
                '小说作者：', '').strip()
            content_table_url = soup.find('a', text='小说目录')['href']
            cover_url = soup.find('img', src=re.compile(r's.jpg'))['src']
            # logger.info('Renew {} successful'.format(aid))
            return {
                str(aid): {
                    "title": title,
                    "author": author,
                    "cover_url": cover_url,
                    "content_table_url": content_table_url
                }
            }
        except:
            raise WenkuGetMainPageError

    def get_cover(self, aid, url):
        if str(aid) not in self.data['wenku']['cover']:
            try:
                logger.info('upoad to imgur')
                self.data['wenku']['cover'][str(aid)] = upload_to_imgur(url)
                with open('config/data.json', 'w', encoding='utf8') as fp:
                    json.dump(self.data, fp)
            except Exception as e:
                logger.warn(e)
                return 'https://avatars2.githubusercontent.com/u/33758217?s=460&v=4'
        return self.data['wenku']['cover'][str(aid)]

    def searcher(self, key):
        ret = []
        result = {}
        rating = 0
        key = OpenCC('tw2s').convert(key)
        for idx in self.data['wenku']['data'].keys():
            score = fuzz.partial_token_set_ratio(
                self.data['wenku']['data'][idx], key)
            if score > 50:
                result[idx] = score
        result = collections.OrderedDict(
            sorted(result.items(), key=operator.itemgetter(1), reverse=True))
        for idx in result:
            temp = self.data['wenku']['data'][idx]
            main_page = self.get_main_page(idx)[str(idx)]
            ret.append(
                dict({
                    'aid':
                    str(idx),
                    'title':
                    temp['title'],
                    'type':
                    'wenku',
                    'main_url':
                    main_page['content_table_url'].replace('http:', 'https:'),
                    'cover_url':
                    self.get_cover(idx, main_page['cover_url'])
                }))
        return ret


class EPUBSITEParser:
    def __init__(self):
        self.base_url = 'http://epubln.blogspot.com/'
        self.search_url = 'http://epubln.blogspot.com/search/'
        self.download_url = 'https://docs.google.com/uc?export=download'

    def searcher(self, key):
        rest = []
        try:
            resp = requests.get(url=self.search_url, params={'q': key})
            resp.encoding = 'utf-8'
            soup = bs(resp.text, 'html.parser')
            if '找不到與查詢字詞' in soup.find('h2', class_='pagetitle').text:
                raise NoSearchError
            else:
                results = soup.find_all('div', class_='post-outer')
                for result in results:
                    temp = result.find('a',
                                       rel='bookmark',
                                       title=re.compile(r'Permalink to'))
                    rest.append(
                        dict({
                            'aid':
                            temp['href'].replace(self.base_url,
                                                 '').replace('.html', ''),
                            'title':
                            temp['title'].replace('Permalink to ', ''),
                            'type':
                            'epubst',
                            'main_url':
                            temp['href'].replace('http:', 'https:'),
                            'cover_url':
                            result.find('img')['src'].replace(
                                'http:', 'https:')
                        }))
            return rest
        except NoSearchError:
            logger.error('No search result')
        except Exception as e:
            logger.debug(e)
            logger.error('Idk wtf happened')


if __name__ == '__main__':
    result = []
    [result.append(x) for x in WENKUParser().searcher('乙女')]
    [result.append(x) for x in EPUBSITEParser().searcher('無職')]
