import scrapy


class DaumItItem(scrapy.Item):
    Title = scrapy.Field() #기사제목
    Date = scrapy.Field() #작성일시
    Media = scrapy.Field() #언론사
    Content_URL = scrapy.Field() #기사 URL
    Contents = scrapy.Field()
    Pressname = scrapy.Field()
    # Img = scrapy.Field()
    # Reacts = scrapy.Field()
    # URL = scrapy.Field()
    # pass


    #사이트구분, 언론사, 기사제목, 작성자(기자), 작성일시, 수정일시, 소주제(세부 카테고리)ㅣlist로 넣기[], 기사URL, 기사본문,스티커, 댓글, 댓글작성자, 댓글 작성일시(시간까지), 좋아요, 싫어요
