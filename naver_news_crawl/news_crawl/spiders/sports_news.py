import scrapy

SUB_CATEGORIES = ['kfootball', 'kbaseball', 'wbaseball', 'wfootball', 'basketball', 'volleyball', 'golf', 'general']
SUB_CATEGORY_DICT = {
    'kfootball': '축구',
    'kbaseball': '야구',
    'wbaseball': '해외야구',
    'wfootball': '해외축구',
    'basketball': '농구',
    'volleyball': '배구',
    'golf': '골프',
    'general': '일반',
}

def make_query(query:dict):
    return '&'.join([k+'='+str(v) for k, v in query.items()])

import json

from datetime import datetime, timedelta
import os
import traceback
from bs4 import BeautifulSoup

class NaverNewsSpider(scrapy.Spider):
    name = "sports_news"
    base_url = 'https://sports.news.naver.com/{}/news/list?isphoto=N&'
    stickers_url = 'https://news.like.naver.com/v1/search/contents?suppress_response_codes=true&callback=jQuery33107996074329902225_1669883087712&q=SPORTS%5Bne_{}_{}%5D&isDuplication=false&cssIds=MULTI_MOBILE%2CSPORTS_MOBILE&_=1669883087713'

    def start_requests(self):
        for i in range(1, 31):
            target_date = (datetime.today() - timedelta(days=i)).strftime('%Y%m%d')

            query_dict = {
                'date': target_date,
                'page': 1
            }

            for sub_cate in SUB_CATEGORIES:
                url = self.base_url.format(sub_cate) + make_query(query_dict)

                yield scrapy.Request(url=url, callback=self.parse, meta={
                    'query_dict': query_dict,
                    'sub_category': sub_cate
                })

    def parse(self, response):
        json_data = json.loads(response.text)
        sub_category = response.meta['sub_category']

        for li in json_data['list']:
            oid = li['oid'] # 언론사
            aid = li['aid'] # 아티클 아이디
            url = f'https://sports.news.naver.com/{sub_category}/news/read?oid={oid}&aid={aid}'
            # 뉴스기사 크롤링
            yield scrapy.Request(url=url, headers={
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
                }, callback=self.parse_news, meta={
                'sub_category': sub_category,
                'oid': oid,
                'aid': aid,
            })

        if json_data['totalPages'] == json_data['page']:
            return
        else:
            query_dict = response.meta['query_dict']
            query_dict['page'] = str(json_data['page']+1)
            url = self.base_url.format(sub_category) + make_query(query_dict)
            
            # 다음페이지 크롤링
            yield scrapy.Request(url=url, callback=self.parse, meta={
                'query_dict': query_dict,
                'sub_category': sub_category
            }) 

    # 뉴스기사 상세정보 크롤링
    def parse_news(self, response):
        try:
            sp = BeautifulSoup(response.body, 'html.parser')

            my_data = []

            title = sp.select_one('.content_area .title')
            if not title:
                title = sp.select_one('#title_area')
            
            
            writer = sp.select_one('.reporter_info .name')
            if not writer:
                writer = sp.select_one('.media_end_head_journalist_name')

            content = sp.select_one('#dic_area')
            if not content:
                content = sp.select_one('#newsEndContents').text
                content = content[:content.index('기사제공')]
            else:
                content = content.text
            
            file_id = len(os.listdir('./sports_contents'))
            with open('./sports_contents/'+str(file_id)+'.txt', 'w', encoding='utf-8') as f:
                f.write(content.strip())

            photos = response.css('.end_photo_org img::attr(src)').getall()
            if not photos:
                photos = response.css('img[id^="img"]::attr(data-src)').getall()

            sticker_names = response.css('.u_likeit_layer .u_likeit_list_name::text').getall()
            sticker_counts = response.css('.u_likeit_layer .u_likeit_list_count::text').getall()
            stickers = dict(zip(sticker_names, sticker_counts))
            press = response.css('#pressLogo img::attr(alt)').get()
            press = press if press else ''

            url = response.url
            major_category = '스포츠'
            sub_category = SUB_CATEGORY_DICT[response.meta['sub_category']]
            # 날짜 변환 오전, 오후
            writed_at = response.css('.news_headline .info span::text').get()
            
            if not writed_at:
                writed_at = response.css('._ARTICLE_DATE_TIME::text').get().strip()
            else:
                writed_at = writed_at.replace('기사입력', '').strip()

            hour_split = writed_at.split(':')
            front_text = hour_split[0].split()
            date_text = ' '.join(front_text[:-1])
            hour_text = front_text[-1]

            if '오후' in writed_at:
                hour = int(hour_text) + 12
                minutes = hour_split[-1]
                if hour == 24:
                    date_text = date_text.replace('오후', '오전')
                    hour = 0
                    writed_at = datetime.strptime(date_text + ' ' + str(hour).zfill(2) + ':' + minutes, '%Y.%m.%d. 오전 %H:%M')
                else:
                    writed_at = datetime.strptime(date_text + ' ' + str(hour) + ':' + minutes, '%Y.%m.%d. 오후 %H:%M')
            else:
                if int(hour_text) == 12:
                    writed_at = writed_at.replace('12:', '00:')
                writed_at = datetime.strptime(writed_at, '%Y.%m.%d. 오전 %H:%M')

            data_list = [major_category, sub_category, writed_at.strftime('%Y-%m-%d %H:%M'), 
                            title.text.strip(), str(file_id)+'.txt', url, str(photos), writer.text.replace('기자', '').strip() if writer else '', press, str(stickers)]

            oid = response.meta['oid']
            aid = response.meta['aid']
            yield scrapy.Request(url=self.stickers_url.format(oid, aid), callback=self.parse_stickers, meta={
                'data':data_list
            })

        except Exception as e:
            traceback.print_exc()
            with open('error_urls', 'a') as f:
                f.write(response.url+'\n')
    
    def parse_stickers(self, response):
        try:
            r = response.text
            start_index = r.index('(')+1
            data = json.loads(r[start_index:-2])

            data_list = response.meta['data']
            stickers = json.loads(data_list[-1].replace('\'', '"'))
            stickers.update(
                {reaction['reactionTypeCode']['description'].strip(): reaction['count'] for reaction in data['contents'][0]['reactions']}
            )
            data_list[-1] = str(stickers)
            with open('sports_metadata.tsv', 'a') as f:
                f.write('\t'.join(data_list) + '\n')

        except:
            traceback.print_exc()
            # 원래 url로 변경
            with open('error_urls', 'a') as f:
                f.write(response.url+'\n')
            