from pathlib import Path
import datetime as dt
import pandas as pd
import re

import scrapy

## 날짜별 소주제별 각 기사 url 크롤링
class QuotesSpider(scrapy.Spider):
    name = "news_url"

    def start_requests(self):
        with open('total_url.txt', encoding='utf_8') as f:
            urls = f.read().split('\n')
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        d = response.css('div.box_etc ul.list_news2 li').extract()
        new_url = list(zip([_.split('<a href="')[1].split('"')[0] for _ in d], [_.split('<span class="info_news">')[1].split('<span class="txt_bar">')[0] for _ in d]))
        
        # 소주제 적재용 변수
        target_class = response.url[43:].split('?')[0]

        with open('total_news_url.txt', 'a', encoding='utf_8') as f:
	        for url, agency in new_url:
                    f.write(url+'\t'+target_class+'\t'+agency+'\n')