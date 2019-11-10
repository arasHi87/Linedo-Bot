from parsers import *
from pprint import pprint
from logger import logger
from linebot.models import (MessageAction, CarouselColumn, URIAction,
                            TextSendMessage, CarouselTemplate,
                            TemplateSendMessage, PostbackAction)

wenku8 = WENKUParser()
epubst = EPUBSITEParser()
search_result = {}


def searcher(key, st, ed):
    result = []
    temp = []
    if key not in search_result:
        [result.append(x) for x in wenku8.searcher(key)]
        [result.append(x) for x in epubst.searcher(key)]
        search_result[key] = result
    else:
        result = search_result[key]
    result_len = len(result)
    for i in range(st, min(result_len, ed + 1)):
        temp.append(
            CarouselColumn(
                thumbnail_image_url=result[i]['cover_url'],
                title=result[i]['type'],
                text=result[i]['title'],
                actions=[MessageAction(label='Surprise!', text='Surprise!')]))
    if result_len > ed + 1:
        temp[9] = CarouselColumn(
            thumbnail_image_url=
            'https://i.giphy.com/media/Nm8ZPAGOwZUQM/giphy.webp',
            title='Total result {}'.format(result_len),
            text='瀏覽下一頁 {} - {}'.format(ed + 1, min(result_len, ed + 9)),
            actions=[
                PostbackAction(label='show next page',
                               display_text='總共有{}個搜尋結果，現在正在預覽{} - {}'.format(
                                   result_len, ed + 1, min(result_len,
                                                           ed + 9)),
                               data='show {} {} {}'.format(
                                   key, ed, min(result_len, ed + 9)))
            ])
    return temp


def command(opt, client, event):
    if opt == 'author' or opt == '作者':
        template_message = TemplateSendMessage(
            alt_text='author',
            template=CarouselTemplate(columns=[
                CarouselColumn(
                    thumbnail_image_url=
                    'https://avatars2.githubusercontent.com/u/33758217?s=460&v=4',
                    title='作者',
                    text='arasHi87',
                    actions=[
                        MessageAction(label='Surprise!', text='Surprise!')
                    ]),
                CarouselColumn(
                    thumbnail_image_url=
                    'https://scontent-tpe1-1.xx.fbcdn.net/v/t1.0-9/74647587_111092293665052_7033169574681903104_o.jpg?_nc_cat=102&_nc_oc=AQluJKJ8qFV3PeoMjbbByUusf7Gw-x9d6u7TR_T_lvtp3mvOoN5RFX-y4-PN3zQkyMo&_nc_ht=scontent-tpe1-1.xx&oh=451f14474310c4c1f8fc6ce639dd5731&oe=5E51C17D',
                    title='官網',
                    text='lightdo',
                    actions=[
                        URIAction(label='點我前往', uri='https://fb.me/lightdo87')
                    ])
            ]))
        client.reply_message(event.reply_token, template_message)
    elif opt.startswith('search') or opt.startswith('搜尋'):
        key = opt.split(' ')[1]
        template_message = TemplateSendMessage(
            alt_text='result',
            template=CarouselTemplate(columns=searcher(key, 0, 9)))
        client.reply_message(event.reply_token, template_message)
    elif opt.startswith('show'):
        opt = opt.split(' ')
        key = opt[1]
        st = int(opt[2])
        ed = int(opt[3])
        template_message = TemplateSendMessage(
            alt_text='result',
            template=CarouselTemplate(columns=searcher(key, st, ed)))
        client.reply_message(event.reply_token, template_message)


if __name__ == '__main__':
    opt = input().strip()
    if opt.startswith('search') or opt.startswith('搜尋'):
        key = opt.split(' ')[1]
        wenku8.online_searcher(key)
