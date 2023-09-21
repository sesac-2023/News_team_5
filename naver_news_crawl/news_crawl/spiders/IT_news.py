import scrapy
from datetime import datetime, timedelta
import time
import json
import traceback, os

SUB_CATEGORIES = ['731', '226', '227', '230', '732', '283', '229', '228']
SUB_CATEGORY_DICT = {
    '731': '모바일',
    '226': '인터넷/SNS',
    '227': '통신/뉴미디어',
    '230': 'IT 일반',
    '732': '보안/해킹',
    '283': '컴퓨터',
    '229': '게임/리뷰',
    '228': '과학 일반',
}

BASE_URL = 'https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid2={}&sid1=102&date={}&page={}'

class ITNewsSpider(scrapy.Spider):
    name = "IT_news"

    def start_requests(self):
        urls = []

        for sid2 in SUB_CATEGORIES:
            date = datetime(2023, 9, 13).strftime('%Y%m%d')
            try: 
                url = BASE_URL.format(sid2, date, 1)
                urls.append([url,sid2])
            except Exception as e:
                print(e)

        for url,sid2 in urls:
            yield scrapy.Request(url=url, callback=self.news_list, cb_kwargs={
                'sid2': sid2,
                'date': date,
                'page': 1
            }, meta={
                'urls': []
            })
    
    def news_list(self, response, sid2, date, page):
        detail_urls = response.css('li > dl > dt:first-child > a::attr(href)').getall()
        
        # 페이지 끝에 도달했으면,
        if response.meta['urls'] == detail_urls:
            date = datetime.strptime(date, '%Y%m%d')
            date -= timedelta(days=1)
            if date < datetime(2023, 7, 14):
                return
            
            date = date.strftime('%Y%m%d')
        else:
            for detail_url in detail_urls:
                yield scrapy.Request(url=detail_url, callback=self.news_detail, cb_kwargs={
                    'sid2': sid2
                })

        yield scrapy.Request(url=BASE_URL.format(sid2, date, page+1), 
                             callback=self.news_list, cb_kwargs={
                                 'sid2': sid2, 
                                 'date': date,
                                 'page': page+1
                            }, meta={
                                'urls': detail_urls
                            })
        
    def news_detail(self, response, sid2):
        # 뉴스 컨텐츠 수집
        title = response.css('#title_area > span::text').get()
        if title is not None:
            title = title.strip()
        writed_at = response.css('._ARTICLE_DATE_TIME::text').get()
        if writed_at is not None:
            writed_at = writed_at.strip()
        writed_at = self.change_dt(writed_at)
        updated_at = response.css('._ARTICLE_MODIFY_DATE_TIME::text').get() #.strip()
        updated_at = self.change_dt(updated_at)
        
        content = response.xpath('//*[@id="contents"]/text()')
        if content:
            content = response.xpath('//*[@id="dic_area"]/text()').extract()    
            content = '\n'.join([''.join(content[i].strip()) for i in range(len(content))])
        else:
            content = response.xpath('//*[@id="contents"]/text()').extract()
            content = '\n'.join([''.join(content[i].strip()) for i in range(len(content))])

        sticker_names = response.css('.u_likeit_layer .u_likeit_list_name::text').getall()
        sticker_counts = response.css('.u_likeit_layer .u_likeit_list_count::text').getall()
        stickers = dict(zip(sticker_names, sticker_counts))
        file_id = len(os.listdir('./news_contents'))
        if not os.path.exists('./news_contents'):
            os.makedirs('./news_contents')
        with open('./news_contents/'+str(file_id)+'.txt', 'w', encoding='utf-8') as f:
            f.write(content.strip())
        url = response.url
        oid = response.url.split('/')[-2]
        aid = response.url.split('/')[-1].split('?')[0]

        press = response.css('.media_end_head_top_logo > img::attr(alt)').get()
        writer = response.css('.media_end_head_journalist_name::text').get()

        data_list = ['네이버', 'IT', SUB_CATEGORY_DICT[sid2], title, press,
             writer.replace('기자', '').strip() if writer is not None else '',
             writed_at, updated_at, str(file_id), url, str(stickers)]
        # yield 댓글
        comment_url = f'https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=view_it_m1&pool=cbox5&_cv=20230912182421&_callback=jQuery331020756992294701737_1694678830776&lang=ko&country=KR&objectId=news{oid}%2C{aid}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=1&initialize=true&followSize=5&userType=&useAltSort=true&replyPageSize=20&sort=FAVORITE&includeAllStatus=true&_=1694948327657'
        yield scrapy.Request(comment_url, callback=self.comments, headers={
            'Referer': f'https://n.news.naver.com/mnews/ranking/article/comment/{oid}/{aid}?sid=102'
        }, meta={
            'url': url,
            'oid': oid,
            'aid': aid
        })

        # yield 스티커
        # https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=default_world&pool=cbox5&_cv=20230912182421&_callback=jQuery33103811823674354218_1694679844371&lang=ko&country=KR&objectId=news056%2C0011565765&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=1&initialize=true&followSize=5&userType=&useAltSort=true&replyPageSize=20&sort=FAVORITE&includeAllStatus=true&_=1694679844373
        # 'https://news.like.naver.com/v1/search/contents?suppress_response_codes=true&q=JOURNALIST%7CNEWS%5Bne_{0}%5D&isDuplication=false'
        sticker_url = f'https://news.like.naver.com/v1/search/contents?suppress_response_codes=true&q=JOURNALIST%7CNEWS%5Bne_{oid}_{aid}%5D&isDuplication=false'
        yield scrapy.Request(url=sticker_url, callback=self.stickers, meta={
            'data': data_list
        })

    
    def change_dt(self, writed_at):
        if not writed_at:
            return ''

        # 날짜 변환 오전, 오후
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

        return writed_at.strftime('%Y-%m-%d %H:%M')

    def stickers(self, response):
        try:
            # r = response.text
            # start_index = r.index('(')+1
            data = json.loads(response.text)
            data_list = response.meta['data']
            stickers = json.loads(data_list[-1].replace('\'', '"'))
            stickers.update(
                {reaction['reactionTypeCode']['description'].strip(): reaction['count'] 
                 for reaction in data['contents'][0]['reactions']}
            )
            data_list[-1] = str(stickers)
            with open('./news_comments.tsv', 'a', encoding='utf-8') as f:
                f.write('\t'.join(data_list) + '\n')


        except:
            traceback.print_exc()
            # 원래 url로 변경
            with open('error_urls', 'a') as f:
                f.write(response.url+'\n')

    def comments(self, response):
        original_url = response.meta['url']
        oid = response.meta['oid']
        aid = response.meta['aid']
        comments = json.loads('('.join(response.text.split('(')[1:])[:-2])
        data_text = '\n'.join(['\t'.join([original_url, comment['commentNo'], comment['userIdNo'], comment['userName'], comment['contents'].replace('\n', ' '), 
                            datetime.strptime(comment['regTime'], '%Y-%m-%dT%H:%M:%S+0900').strftime('%Y-%m-%d %H:%M')]) 
                            for comment in comments['result']['commentList'] if comment['userIdNo']])

        with open('./news_comments.tsv', 'a', encoding='utf-8') as f:
            f.write(data_text+'\xa0' if data_text else '')

        if comments['result']['pageModel']['page'] == comments['result']['pageModel']['lastPage']:
            return
        
        mp_prev = comments['result']['morePage']['prev']
        mp_next = comments['result']['morePage']['next']
        page = comments['result']['pageModel']['page'] + 1
        current = comments['result']['commentList'][-1]['commentNo']
        try:
            prev = response.meta['prev']
        except:
            prev = comments['result']['commentList'][0]['commentNo']

        tsp = int(time.time() * 1000)
        url = f'https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&templateId=default_world&pool=cbox5&_cv=20230912182421&_callback=jQuery33103811823674354218_1694679844371&lang=ko&country=KR&objectId=news{oid}%2C{aid}&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page={page}&currentPage={page-1}&refresh=false&sort=FAVORITE&current={current}&prev={prev}&moreParam.direction=next&moreParam.prev={mp_prev}&moreParam.next={mp_next}&includeAllStatus=true&_={tsp}'
        yield scrapy.Request(url=url, headers={
            'Referer': f'https://n.news.naver.com/mnews/ranking/article/comment/{oid}/{aid}?sid=102'
        }, meta={'url': original_url, 'oid': oid, 'aid': aid, 'prev': prev}, callback=self.comments)


