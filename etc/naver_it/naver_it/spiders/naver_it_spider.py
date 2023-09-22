import scrapy


class NaverItSpiderSpider(scrapy.Spider):
    name = "naver_it_spider"
    start_urls = ["http://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=105&sid2=731"]

    def parse(self, response):
        print(response)
        # pass
