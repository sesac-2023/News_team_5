import scrapy

SUB_CATEGORIES = ['221', '224', '225', '7a5', '309']
SUB_CATEGORY_DICT = {
    '221': '연예가화제',
    '224': '방송·TV',
    '225': '드라마',
    '7a5': '뮤직',
    '309': '해외연예'
}

from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import traceback
from .modules.utils import make_query_dict

class EnterNewsSpider(scrapy.Spider):
    name = "enter_news"
    base_url = 'https://entertain.naver.com/now?'
    json_url = 'https://entertain.naver.com/now/page.json'
    ROOT_URL = 'https://entertain.naver.com/'
    stickers_url = 'https://news.like.naver.com/v1/search/contents?suppress_response_codes=true&callback=jQuery33107996074329902225_1669883087712&q=ENTERTAIN%5Bne_{}_{}%5D&isDuplication=false&cssIds=MULTI_MOBILE%2CSPORTS_MOBILE&_=1669883087713'

    def start_requests(self):
        for i in range(1, 31):
            for category in SUB_CATEGORIES:
                query_dict = {
                    'sid': category,
                    'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                    'page': str(1)
                }
                
                yield scrapy.FormRequest(url=self.json_url, callback=self.parse, formdata=query_dict, meta={
                    'query_dict': query_dict,
                    'original_data': [],
                })

    # body 데이터
    def parse(self, response):
        json_data = json.loads(response.text)
        sp = BeautifulSoup(json_data['newsListHtml'], 'html.parser')
        news_list = sp.select('li > a')
        if news_list == response.meta['original_data']:
            return
            
        query_dict = response.meta['query_dict']
        for a_tag in news_list:
            hrefs = a_tag.attrs['href']
            url = self.ROOT_URL + hrefs
        
            yield scrapy.Request(url=url, callback=self.parse_news, meta={
                'query_dict': query_dict
            })

        page = int(query_dict['page'])
        query_dict['page'] = str(page+1)
        yield scrapy.FormRequest(url=self.json_url, callback=self.parse, formdata=query_dict, meta={
            'query_dict': query_dict,
            'original_data': news_list,
        })

    def parse_news(self, response):
        try:
            major_category = '연예'
            sub_category = SUB_CATEGORY_DICT[response.meta['query_dict']['sid']]
            
            title = response.css('.end_tit::text').get().strip()
            press = response.css('.press_logo > img::attr(alt)').get()

            writed_at = response.css('.article_info > .author > em::text').get()
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


            photos = response.css('img[id^="img"]::attr(src)').getall()
            # content = response.css('#articeBody::text')
            sp = BeautifulSoup(response.body, 'html.parser')
            content = sp.select_one('#articeBody').text
            file_id = len(os.listdir('./enter_contents'))
            with open('./enter_contents/'+str(file_id)+'.txt', 'w', encoding='utf-8') as f:
                f.write(content.strip())
            url = response.url
            writer = response.css('.journalistcard_summary_name::text').get()
            sticker_names = response.css('.u_likeit_layer .u_likeit_list_name::text').getall()
            sticker_counts = response.css('.u_likeit_layer .u_likeit_list_count::text').getall()
            stickers = dict(zip(sticker_names, sticker_counts))
            
            # str(photos)
            data_list = ['네이버', major_category, sub_category, title.strip(), press, writer.replace('기자', '').strip() if writer else '',
                         writed_at.strftime('%Y-%m-%d %H:%M'), '', str(file_id)+'.txt', url, str(stickers)]
                
            queries = make_query_dict(url.split('?')[-1])
            oid = queries['oid']
            aid = queries['aid']
            yield scrapy.Request(url=self.stickers_url.format(oid, aid), callback=self.parse_stickers, meta={
                'data':data_list
            })

        except:
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
            with open('enter_metadata.tsv', 'a') as f:
                f.write('\t'.join(data_list) + '\n')

        except:
            traceback.print_exc()
            # 원래 url로 변경
            with open('error_urls', 'a') as f:
                f.write(response.url+'\n')