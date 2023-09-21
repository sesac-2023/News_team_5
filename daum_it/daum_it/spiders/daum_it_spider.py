import scrapy
from daum_it.items import DaumItItem
from datetime import datetime, timedelta



class DaumItSpiderSpider(scrapy.Spider):
    name = "daum_it_spider"

    # 날짜 범위 설정 (현재 날짜부터 이전 3개월까지)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    # 카테고리 목록 설정
    category_list = ["internet", "science", "game", "it", "device", "mobile", "software", "others"]

    #start_urls = ["http://news.daum.net//breakingnews/digital?regDate=20230904"]

    def start_requests(self):
        
        for category in self.category_list:
            # 날짜 범위 내의 날짜를 반복
            current_date = self.start_date
            while current_date <= self.end_date:
                formatted_date = current_date.strftime("%Y%m%d")
                for page_num in range(1, 11):  # 페이지 번호를 조절하세요 (1부터 10까지)
                    url = f"https://news.daum.net/breakingnews/digital/{category}?page={page_num}&regDate={formatted_date}"
                    yield scrapy.Request(url, callback=self.parse)

                # 다음 날짜로 이동
                current_date += timedelta(days=1)


    def parse(self, response):
        # global URL
        
        for i in range(1,16):
            URL = response.xpath(f'//*[@id="mArticle"]/div[3]/ul/li[{i}]/div/strong/a/@href')[0].extract()
            yield scrapy.Request(URL,callback=self.parse_page_content1)
            #print(URL,i)
            # div = response.xpath(f'//*[@id="mArticle"]/div[3]/ul/li[{i}]')

            # if (URL !=[]): #i가 비어있지않다면
            #     href = div.xpath('./div/strong/a/@href')
            #     url = response.urljoin(href[0].extract())
            #     print(url)

    def parse_page_content1(self,response): #세부항목들안으로 들어가는 함수
        item = DaumItItem()

        item['Title'] = response.xpath('//*[@id="mArticle"]/div[1]/h3/text()')[0].extract()
        item['Date'] = response.xpath('//*[@id="mArticle"]/div[1]/div[1]/span[2]/span/text()')[0].extract()
        #item['수정일시']
        item['Media'] = response.xpath('//*[@id="kakaoServiceLogo"]/text()')[0].extract()
        item['Content_URL'] = response.url 
        item['Contents'] = response.xpath('//*[@id="mArticle"]/div[2]/div[2]/section/p/text()').getall()
        item['Pressname'] = response.xpath('//*[@id="mArticle"]/div[1]/div[1]/span[1]/text()')[0].extract()
        #item['Category'] = category
        #item['React]
        return item
    

# import requests
# from bs4 import BeautifulSoup
# url = "https://action.daum.net/apis/v1/reactions/home?itemKey={'news_id'}"
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
#     "Referer": "https://v.daum.net/v/{'news_id'}",
#     "Origin": "https://v.daum.net",
#     "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmb3J1bV9rZXkiOiJuZXdzIiwidXNlcl92aWV3Ijp7ImlkIjo5OTIxODQzMywiaWNvbiI6Imh0dHBzOi8vdDEuZGF1bWNkbi5uZXQvcHJvZmlsZS9McDhKZEs4R2VwdzAiLCJwcm92aWRlcklkIjoiREFVTSIsImRpc3BsYXlOYW1lIjoi7JeU7KCkIn0sImdyYW50X3R5cGUiOiJhbGV4X2NyZWRlbnRpYWxzIiwic2NvcGUiOltdLCJleHAiOjE2OTQ3MTc2NzgsImF1dGhvcml0aWVzIjpbIlJPTEVfSU5URUdSQVRFRCIsIlJPTEVfREFVTSIsIlJPTEVfSURFTlRJRklFRCIsIlJPTEVfVVNFUiJdLCJqdGkiOiI4Y2Q4MmFhZi1kNGIzLTQ0MmItYmIzMi00M2NlNDkxNGNmZjMiLCJmb3J1bV9pZCI6LTk5LCJjbGllbnRfaWQiOiIyNkJYQXZLbnk1V0Y1WjA5bHI1azc3WTgifQ.nP_UCBbXZOMYwiLLLJF4RBxBnsbGDj5-9gL4Ia0aRjI"
# }
# response = requests.get(url,headers=headers, )
# data = response.json()
# print("LIKE:", data["item"]["stats"]["LIKE"])
# print("DISLIKE:", data["item"]["stats"]["DISLIKE"])
# print("GREAT:", data["item"]["stats"]["GREAT"])
# print("SAD:", data["item"]["stats"]["SAD"])
# print("ABSURD:", data["item"]["stats"]["ABSURD"])
# print("ANGRY:", data["item"]["stats"]["ANGRY"])
# print("RECOMMEND:", data["item"]["stats"]["RECOMMEND"])
# print("IMPRESS:", data["item"]["stats"]["IMPRESS"]) 