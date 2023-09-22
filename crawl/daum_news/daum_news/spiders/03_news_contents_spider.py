from pathlib import Path
import datetime as dt
import pandas as pd
import re
import pickle
import requests
import json

import scrapy

## 각 기사 데이터 크롤링
classified_e = {'internet': '인터넷', 'science': '과학', 'game': '게임', 'it': '휴대폰통신', 'device': 'IT기기', 'mobile': '통신_모바일', 'software': '소프트웨어', 'others': 'Tech일반'}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmb3J1bV9rZXkiOiJuZXdzIiwiZ3JhbnRfdHlwZSI6ImFsZXhfY3JlZGVudGlhbHMiLCJzY29wZSI6W10sImV4cCI6MTY5NTAzOTc0MSwiYXV0aG9yaXRpZXMiOlsiUk9MRV9DTElFTlQiXSwianRpIjoiZjI3NTVkNTEtNjlkOS00NDViLWI3ZmQtNGFkZTEzYmJkYmFiIiwiZm9ydW1faWQiOi05OSwiY2xpZW50X2lkIjoiMjZCWEF2S255NVdGNVowOWxyNWs3N1k4In0.E1jUzWOXVH4odHjn3D9VbVa6tPD8NTEcYQn0ePBOPOk'
}
base_sticker = 'https://action.daum.net/apis/v1/reactions/home?itemKey='
to_wirte = []

class QuotesSpider(scrapy.Spider):
    name = "contents"

    def start_requests(self):
        
        with open('total_news_url.txt', encoding='utf_8') as f:
            urls_classes = [_.split('\t') for _ in f.read().split('\n')[:-1]]
        # idx = int(__file__[-5:-3])
        # idx_list = [i for i in range(0,len(urls_classes), int(len(urls_classes)/10))][:-1]+[len(urls_classes)]
        # urls_classes = urls_classes[idx_list[idx]+idx_list[idx]]

        # scrapy가 마지막 작업은 실패해도 완료하여 해당 개수만큼 뒷부분 url 추가
        for url_class in urls_classes+urls_classes[-33:]:
            url, class__, agency = url_class
            yield scrapy.Request(url=url, headers=headers, callback=self.parse, cb_kwargs={'class__': class__, 'agency': agency})

        # pickle로 바이너리 저장
        # with open(f'total_news_data_{idx}.pkl', 'wb') as f:
        with open(f'total_news_data.pkl', 'wb') as f:
            pickle.dump(to_wirte, f)

    def parse(self, response, class__, agency):
        d = str(response.css('article.box_view').getall())
        제목 = d.split('<h3 class="tit_view" data-translation=')[1].split('</h3>')[0].split('>')[1]
        기자 = d.split('<span class="txt_info">')[1].split('</span>')[0]
        입력일시 = d.split('<span class="num_date">')[1].split('</span>')[0]
        수정일시 = 'null'
        소주제_id = str(classified_e.get(class__))
        기사_url = response.url
        사이트 = 'Daum' if classified_e.get(class__) else 'Naver'
        본문 = ''.join(response.css('div.news_view.fs_type1 div.article_view section p::text').getall()).strip()
        언론사 = agency
        소주제 = class__
        스티커 = json.loads(requests.get(base_sticker+기사_url[21:], headers=headers).text)['item']['stats']

        to_wirte.append([언론사, 기자, 제목, 입력일시, 수정일시, 소주제, 소주제_id, 기사_url, 사이트, 본문, 스티커])
    
    def closed(self, reason):
        # 스파이더가 종료될 때 호출되는 메서드
        # to_wirte 리스트를 파일로 저장
        with open('total_news_data.pkl', 'wb') as f:
            pickle.dump(to_wirte, f)