from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException
import sys
import csv
from csv import writer
import requests
from bs4 import BeautifulSoup
import re





def scrape_stock(driver, ticker_symbol):
    # build the URL of the target page
    url = f'https://finance.yahoo.com/quote/{ticker_symbol}/sustainability/'

    # visit the target page
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    with open('RawNews.csv', 'w', newline= '', encoding = 'utf8') as f:
# set up writer for CSV file
        writeFile = writer(f)
        header = ['TotalScore','EnvironmentalScore','SocialScore','GovernanceScore']
        writeFile.writerow(header)
        print('none')
        # with open("page_source.html", "w", encoding="utf-8") as file:
        #     file.write(driver.page_source)
        ESGContainer = soup.find('main', {"id": "nimbus-app"})
        MainScoring = ESGContainer.find('section', {"data-testid": "esg-cards"})
        TotalEsgScore = MainScoring.find('section',{"data-testid": "TOTAL_ESG_SCORE"})

        if TotalEsgScore:
            findTscore = TotalEsgScore.find('h4').get_text(strip = True)
            print(findTscore)
        else:
            findTscore = None
            print("none")
        EnvironmentalScore = MainScoring.find('section',{"data-testid": "ENVIRONMENTAL_SCORE"})
        if EnvironmentalScore:
            findEscore = EnvironmentalScore.find('h4').get_text(strip = True)
            print(findEscore)
        else:
            findEscore = None
            print("none")
        SocialScore = MainScoring.find('section',{"data-testid": "SOCIAL_SCORE"})
        if SocialScore:
            findSscore = SocialScore.find('h4').get_text(strip = True)
            print(findSscore)
        else:
            findSscore = None
            print("none")
        GovernanceScore = MainScoring.find('section',{"data-testid": "GOVERNANCE_SCORE"})
        if GovernanceScore:
            findGscore = GovernanceScore.find('h4').get_text(strip = True)
            print(findGscore)
        else:
            findGscore = None
            print("none")
        createRows = [findTscore, findEscore, findSscore, findGscore]
        writeFile.writerow(createRows)

# if there are no CLI parameters
if len(sys.argv) <= 1:
    print('Ticker symbol CLI argument missing!')
    sys.exit(2)

options = Options()
options.add_argument('--headless=new')
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=800x600")

# initialize a web driver instance to control a Chrome window
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=options
)

# scraping all market securities
for ticker_symbol in sys.argv[1:]:
    scrape_stock(driver, ticker_symbol)
# close the browser and free up the resources
driver.quit()
