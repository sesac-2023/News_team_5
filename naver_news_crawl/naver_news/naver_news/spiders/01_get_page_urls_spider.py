from pathlib import Path
import datetime as dt
import pandas as pd

import scrapy

## 날짜별 소주제별 기사 페이지 url 크롤링
class QuotesSpider(scrapy.Spider):
    name = "page_url"

    def start_requests(self):
        # 'https://news.naver.com/main/list.naver?mode=LS2D&sid2=231&sid1=104&mid=shm&date=20230913&page=1'   # 아시아/호주
        # 'https://news.naver.com/main/list.naver?mode=LS2D&sid2=232&sid1=104&mid=shm&date=20230913&page=1'   # 미국/중남미
        # 'https://news.naver.com/main/list.naver?mode=LS2D&sid2=233&sid1=104&mid=shm&date=20230913&page=1'   # 유럽
        # 'https://news.naver.com/main/list.naver?mode=LS2D&sid2=234&sid1=104&mid=shm&date=20230913&page=1'   # 중동/아프리카
        # 'https://news.naver.com/main/list.naver?mode=LS2D&sid2=322&sid1=104&mid=shm&date=20230913&page=1'   # 세계 일반
        
        # 소주제 확인용 딕셔너리
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
        base = 'https://news.naver.com/main/list.naver?mode=LS2D&sid2={}&sid1=105&mid=shm&date={}&page={}'
        6
        # 크롤링 날짜 지정 및 리스트 생성
        first_day = '2023-06-13'
        END_DAY = '2023-09-13'
        date_list = pd.date_range(first_day, END_DAY, freq='d')[::-1]
        date_list = [t_day.strftime('%Y%m%d') for t_day in date_list]

        # url 리스트 생성
        urls = [base.format(target_class, target_day, 99999) for target_day in date_list for target_class in classified.keys()]
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        last_page = int(response.css('td.content div.content div.paging strong::text').get())
        base = response.url[:-5]
        new_urls = [base+str(_) for _ in range(last_page,0,-1)]
        with open('total_url.txt', 'a', encoding='utf_8') as f:
	        for url in new_urls:
                    f.write(url+'\n')