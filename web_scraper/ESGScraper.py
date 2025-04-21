from csv import writer
import requests
from bs4 import BeautifulSoup
import re

import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider

class YahooFinanceSpider(scrapy.Spider):
    name = "yahoo_finance"

    def start_requests(self):
        urls = [
            'https://finance.yahoo.com/quote/AAPL/sustainability/',
        ]
        for url in urls:
            yield SplashRequest(url, self.parse, args={'wait': 2})
    custom_settings = {
    'SPLASH_URL': 'http://localhost:8050',
    'DOWNLOADER_MIDDLEWARES': {
        'scrapy_splash.SplashCookiesMiddleware': 723,
        'scrapy_splash.SplashMiddleware': 725,
        'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    },
    'SPIDER_MIDDLEWARES': {
        'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
    },
    'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
    'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',

    'DEFAULT_REQUEST_HEADERS': {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

    def parse(self, response):
            print("Status:", response.status)
            print("Body:", response.text[:500])
            print("none")
            ESGContainer = response.find('div', {"id": "nimbus-app"})
            MainScoring = ESGContainer.find(attrs={"data-testid": "esg-cards"})
            TotalEsgScore = MainScoring.find(attrs={"data-testid": "TOTAL_ESG_SCORE"})
            if TotalEsgScore:
                # TotalEsgScore = TotalEsgScore.get_text(strip = True)
                findTscore = TotalEsgScore.find('h3')
                title = findTscore.get_text(strip = True)
                print(title)
                print("none")
            else:
                TotalEsgScore = None
                print("none")
process = CrawlerProcess()
process.crawl(YahooFinanceSpider)  # Register the spider for crawling
process.start()  # Start the crawl process

# url = "https://finance.yahoo.com/quote/LDZA.SG/sustainability/"

# page = requests.get(url)

# soup = BeautifulSoup(page.content, 'html.parser')
# # sorted section for latest in AFR
# # main = soup.find('main')
# # section = main.find_all('section')

# # scrapes afr news for data and writes to CSV file

# # creates CSV file
# with open('RawNews.csv', 'w', newline= '', encoding = 'utf8') as f:
# # set up writer for CSV file
#     writeFile = writer(f)
#     header = ['TotalEsgScore','EnviromentScore', 'SocialScore','GovernanceScore']
#     writeFile.writerow(header)

#     ESGContainer = soup.find('div', {"id": "nimbus-app"})
#     # for NSsection in ESGContainer:
#     # get image
#     # imagesection = NSsection.find()
#     # get Title
#     MainScoring = soup.find(attrs={"data-testid": "esg-cards"})
#     totalEsgScore = soup.find(attrs={"data-testid": "TOTAL_ESG_SCORE"})
#     if totalEsgScore:
#         TotalEsgScore = totalEsgScore.get_text(strip = True)
#         title = totalEsgScore.get_text()
#         print(title)
#     else:
#         TotalEsgScore = None
#         print("none")

#     # title = StoryTitle.get_text()
#     # print(title)

#     # # get Description
#     #     StoryDesc = NSsection.find(attrs={"data-pb-type": "ab"})
#     #     desc = StoryDesc.get_text()
#     #     print(desc)
#     # # get Link
#     #     link = StoryTitle.find('a', href = True)
#     #     FinalLink = "https://www.afr.com" + link['href']
#     #     print(FinalLink)
#     # # get datePosted
#     #     StoryDate = NSsection.find(attrs={"data-testid": "StoryTile-Timestamp"})
#     #     if StoryDate:
#     #         Date = StoryDate.get_text(strip = True)
#     #     else:
#     #             Date = None
#     #     print(Date)


#         createRows = ['TotalEsgScore','EnviromentScore', 'SocialScore','GovernanceScore']
#         writeFile.writerow(createRows)


