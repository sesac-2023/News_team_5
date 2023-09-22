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
            urls = f.read().split('\n')[:-1]
        
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        d = response.css('div.content div.list_body ul.type06_headline dl dt a').extract()
        d.extend(response.css('div.content div.list_body ul.type06 dl dt a').extract())
        d = list(set([_.split('"')[1] for _ in d if 'a href' in _]))
        # 소주제 적재용 변수
        target_class = response.url.split('sid')[1][2:5]

        with open('total_news_url.txt', 'a', encoding='utf_8') as f:
	        for _ in d:
                    f.write(_+'\t'+target_class+'\n')