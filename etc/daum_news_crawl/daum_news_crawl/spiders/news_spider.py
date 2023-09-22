import scrapy
import os
import re
import traceback
from datetime import datetime, timedelta
import requests

class SocietySpider(scrapy.Spider):
    name = "digital"

    CATEGORIES = {
        ('IT', 'digital') : {
            '인터넷': 'internet',
            '과학': 'science',
            '게임': 'game',
            '휴대폰통신': 'it',
            'IT기기': 'device',
            '통신_모바일': 'mobile',
            '소프트웨어': 'software',
            'Tech일반': 'others',
        },
    }

    URL_FORMAT = 'https://news.daum.net/breakingnews/{}/{}?page={}&regDate={}'
    def start_requests(self):
        start_date = datetime(2023, 6, 1)
        end_date = datetime(2023, 9, 13)
        dates = [start_date]
        while True:
            start_date = start_date + timedelta(days=1)
            dates.append(start_date)
            if start_date == end_date:
                break

        for main_ctg in self.CATEGORIES:
            main_name, main_id = main_ctg
            for sub_name, sub_id in self.CATEGORIES[main_ctg].items():
                for date in dates:
                    target_url = self.URL_FORMAT.format(main_id, sub_id, 1, date.strftime('%Y%m%d'))

                    yield scrapy.Request(url=target_url, callback=self.parse_url, meta={
                        'page': 1, 'urls': [], 'main_category': main_name, 'sub_category': sub_name})

    def parse_url(self, response):
        # 페이지 체크
        urls = response.css('.list_news2 a.link_thumb::attr(href)').getall()
        cps = response.css('.info_news::text').getall()

        if response.meta.pop('urls') == urls:
            return
        
        for i, url in enumerate(urls):
            yield scrapy.Request(url=url, callback=self.parse, meta={**response.meta, 'cp': cps[i]})

        # 다음페이지
        page = response.meta.pop('page')
        target_url = re.sub('page\=\d+', f'page={page+1}', response.url)
        yield scrapy.Request(url=target_url, callback=self.parse_url, meta={**response.meta, 'page': page+1, 'urls':urls})

    def parse(self, response):
        try:
            title = response.css('.tit_view::text').get().strip()
            content = response.css('.article_view')[0].xpath('string(.)').extract()[0].strip()
            infos = response.css('.info_view .txt_info')
            if len(infos) == 1:
                writer = ''
                writed_at = infos[0].css('.num_date::text').get()
            else:
                writer = response.css('.info_view .txt_info::text').get()
                writed_at = infos[1].css('.num_date::text').get()
            
            news_id = response.url.split('/')[-1]
            folder_path = './news_contents/'
            os.makedirs(folder_path, exist_ok=True)

            with open(os.path.join(folder_path, news_id+'.txt'), 'w', encoding='utf-8') as f:
                f.write(content)


            # 스티커
            news_url = f'https://v.daum.net/v/{news_id}'
            r = requests.get(news_url)
            idx = r.text.find('data-client-id')
            client_id = r.text[idx:idx+100].split()[0].split('"')[-2]

            token_url = "https://alex.daum.net/oauth/token?grant_type=alex_credentials&client_id={}".format(client_id)
            r = requests.get(token_url, headers = {'referer': news_url})
            auth = 'Bearer ' + r.json()['access_token']

            r = requests.get(f'https://action.daum.net/apis/v1/reactions/home?itemKey={news_id}', headers={
                'User-Agent': 'Mozilla/5.0',
                'Authorization': auth
            })

            stickers = r.json()['item']['stats']
            # 언론사, 수정일자
            datas = ['다음', response.meta.pop('main_category'), response.meta.pop('sub_category'),
                title, response.meta['cp'], writer, writed_at, '', news_url, news_id, str(stickers)]

            with open('./metadata.tsv', 'a', encoding='utf-8') as f:
                f.write('\t'.join(map(str,datas)) + '\n')

        except:
            traceback.print_exc()
            with open('error_urls', 'a') as f:
                f.write(response.url+'\n')