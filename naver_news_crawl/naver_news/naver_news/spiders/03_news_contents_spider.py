from pathlib import Path
import datetime as dt
import pandas as pd
import re
import pickle
import requests
import json
from urllib.parse import urlparse, parse_qs

import scrapy

## 각 기사 데이터 크롤링
classified = {
            731: '모바일',
            226: '인터넷/SNS',
            227: '통신/뉴미디어',
            230: 'IT 일반',
            732: '보안/해킹',
            283: '컴퓨터',
            229: '게임/리뷰',
            228: '과학 일반',
        }
# 댓글 기본 주소
comment_base_url = 'https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json'
# 댓글 url 쿼리 json 추출 key list
comment_key_list = ['commentNo','contents','userIdNo','userName', 'regTime', 'modTime', 'sympathyCount', 'antipathyCount']
# 스티커 기본 주소
sticker_base_url = 'https://news.like.naver.com/v1/search/contents'
# sticker_dict = {
#     "touched": "공감백배",
#     "warm": "훈훈해요",
#     "analytical": "분석탁월",
#     "like": "좋아요",
#     "sad": "슬퍼요",
#     "want": "후속기사원해요",
#     "recommend": "후속강추",
#     "angry": "화나요",
#     "useful": "쏠쏠정보",
#     "wow": "흥미진진"
# }
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ko',
}
to_wirte = []

class QuotesSpider(scrapy.Spider):
    name = "contents"

    def start_requests(self):
        with open('total_news_url.txt', encoding='utf_8') as f:
            urls_classes = [_.split('\t') for _ in f.read().split('\n')[:-1]]

        for url_class in urls_classes:
            url, class__ = url_class
            yield scrapy.Request(url=url, headers=headers, callback=self.parse, cb_kwargs={'class__': int(class__)})
        
        # pickle로 바이너리 저장
        with open('total_news_data.pkl', 'wb') as f:
            pickle.dump(to_wirte, f)

    def parse(self, response, class__):
        # 기사 본문 등 추출
        d = str(response.css('div.newsct_wrapper').getall())
        기자, 언론사 = d.split('Copyright ⓒ ')
        언론사 = 언론사.split('. All rights reserved. ')[0]
        try: 기자 = 기자.split('<span class="byline_s">')[1].split('</span>')[0]
        except: 기자 = 'null'
        제목 = d.split('media_end_head_title')[1].split('span>')[1][:-2]
        입력일시 = d.split('"media_end_head_info_datestamp_time _ARTICLE_DATE_TIME" data-date-time="')[1]
        수정일시 = 입력일시.split('data-modify-date-time="')[1][:19] if '_ARTICLE_MODIFY_DATE_TIME' in 입력일시 else 'null'
        입력일시 = 입력일시[:19]
        소주제 = classified.get(class__)
        소주제_id = class__
        기사_url = response.url
        사이트 = 'Naver' if classified.get(class__) else 'Daum'
        본문 = response.css('div.newsct_article article.go_trans::text').getall()

        ## sticker와 comment 추출
        # 기사의 id 쿼리값
        id_1 = response.url[39:42]
        id_2 = response.url[43:-8]

        # sticker 코드
        # sticker에 필요한 params
        params = {'suppress_response_codes': 'true',
                'callback': 'jQuery33108878292007524402_1694786068691',
                'q': f'JOURNALIST[78818(period)]|NEWS[ne_{id_1}_{id_2}]',
                'isDuplication': 'false',
                'cssIds': 'MULTI_MOBILE,NEWS_MOBILE',
                '_': '1694786068692'}
        # 전체 sticker 딕셔너리
        sticker_dict = {"touched": 0, "warm": 0, "analytical": 0, "like": 0, "sad": 0, "want": 0, "recommend": 0, "angry": 0, "useful": 0, "wow": 0}
        # 기사의 sticker 값 추출 및 update
        sticker = requests.get(sticker_base_url, params=params, headers=headers).text
        sticker = json.loads(sticker[sticker.find('(')+1:-2])
        sticker_dict.update({reaction['reactionType']: reaction['count'] for reaction in sticker['contents'][1]['reactions']})

        # comment 코드
        # commnet url로 response 변경. 임의 변수에 url 저장해도 동일함.
        response._set_url('article/comment'.join(response.url.split('article')))
        headers['Referer'] = response.url
        params = {'ticket': 'news',
                'templateId': 'default_politics',
                'pool': 'cbox5',
                '_cv': '20230912182421',
                '_callback': 'jQuery33105087127982071216_1694783152409',
                'lang': 'ko',
                'country': 'KR',
                'objectId': f'news{id_1},{id_2}',
                'categoryId': '',
                'pageSize': '9999',
                'indexSize': '9999',
                'groupId': '',
                'listType': 'OBJECT',
                'pageType': 'more',
                'page': '99',
                'initialize': 'true',
                'followSize': '5',
                'userType': '',
                'useAltSort': 'true',
                'replyPageSize': '9999',
                'sort': 'new',
                'includeAllStatus': 'true',
                '_': '1694783152411'}
        
        comment = requests.get(comment_base_url, params=params, headers=headers).text
        comment = [[_[__] for __ in comment_key_list] for _ in json.loads(comment[comment.find('(')+1:-2])['result']['commentList']]

        to_wirte.append([언론사, 기자, 제목, 입력일시, 수정일시, 소주제, 소주제_id, 기사_url, 사이트, 본문, comment, sticker_dict])
        
        df = pd.DataFrame(to_wirte, columns=['언론사', '기자', '제목', '입력일시', '수정일시', '소주제', '소주제_id', '기사_url', '사이트', '본문', 'comment', 'sticker_dict'])

        # 데이터프레임을 CSV 파일로 저장
        df.to_csv('total_news_data.csv', index=False, encoding='utf-8-sig')  # index=False를 설정하여 인덱스 열을 저장하지 않습니다. 인코딩은 'utf-8-sig'로 지정하여 한글이 깨지지 않도록 합니다.