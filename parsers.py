import os
import re
import time
import json
import requests
import collections
import urllib.request
import http.cookiejar as cookielib

from pprint import pprint
from opencc import OpenCC
from logger import logger
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
        self.wenku_cover = {}
        with open('config/data.json', 'r', encoding='utf8') as fp:
            self.wenku_cover = json.load(fp)

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
        if str(aid) not in self.wenku_cover:
            try:
                self.wenku_cover['wenku'][str(aid)] = upload_to_imgur(url)
                with open('config/data.json', 'w', encoding='utf8') as fp:
                    json.dump(self.wenku_cover, fp)
            except Exception as e:
                logger.warn(e)
                return 'https://avatars2.githubusercontent.com/u/33758217?s=460&v=4'
        return self.wenku_cover['wenku'][str(aid)]

    def searcher(self, key):
        result = []
        try:
            self.login()
            key = OpenCC('tw2s').convert(key)
            resp = self.wenku_session.get(url=self.search_url.format(
                requests.utils.quote(key, encoding='gbk')))
            resp.encoding = 'gbk'
            soup = bs(resp.text, 'html.parser')

            # get search result
            if soup.find('caption', text=re.compile('搜索结果')):
                # multi search result
                max_page = int(soup.find('a', class_='last').text)
                for i in range(2, max_page + 2):
                    novels = soup.find_all('a', text=re.compile(key))
                    # self.get_main_page(aid)[str(aid)]['cover_url']
                    for novel in novels:
                        aid = re.findall(r'[/][0-9]+',
                                         novel['href'])[0].replace('/', '')
                        result.append(
                            dict({
                                'aid':
                                aid,
                                'title':
                                novel.text,
                                'type':
                                'wenku',
                                'cover_url':
                                self.get_cover(aid, self.get_main_page(aid)[str(aid)]['cover_url'])
                            }))
                    if (i == max_page + 1):
                        return result
                    time.sleep(5)
                    url = self.search_url.format(
                        requests.utils.quote(
                            key, encoding='gbk')) + '&page=' + str(i)
                    resp = self.wenku_session.get(url=url)
                    resp.encoding = 'gbk'
                    soup = bs(resp.text, 'html.parser')
            else:
                # singal search
                aid = re.findall(r'=[0-9]+',
                                 soup.find('a',
                                           text='加入书架')['href'])[0].replace(
                                               '=', '')
                temp = self.get_main_page(aid)[str(aid)]
                title = temp['title']
                result.append(
                    dict({
                        'aid':
                        str(aid),
                        'title':
                        title,
                        'type':
                        'wenku',
                        'cover_url':
                        self.get_cover(aid, self.get_main_page(aid)[str(aid)]['cover_url'])
                    }))
            return result
        except WenkuLoginError:
            logger.error('Fail to login wenku8, try later')
        except WenkuGetMainPageError:
            logger.error(
                'Fail to get main page, plese check your payload and try later'
            )


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
    # WENKUParser().get_main_page(34)
    EPUBSITEParser().searcher('乙女')
