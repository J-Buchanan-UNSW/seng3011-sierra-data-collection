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
    findName = "None"
    findTscore = "None"
    findEscore = "None"
    findSscore = "None"
    findGscore = "None"
    # entirepageFinders
    ESGContainer = soup.find('main', {"id": "nimbus-app"})
    CompanyDetails = soup.find('section', {"data-testid": "quote-hdr"})

    # Controversy = soup.find('section', {"data-testid": "esg-controversy"})
    # print(Controversy.get_text(strip = True))
    # subFinders
    CompanyName = CompanyDetails.find('h1')
    findName = CompanyName.get_text(strip = True)
    print(findName)
    MainScoring = ESGContainer.find('section', {"data-testid": "esg-cards"})
    if MainScoring:
        # get total esg score
        TotalEsgScore = MainScoring.find('section',{"data-testid": "TOTAL_ESG_SCORE"})

        if TotalEsgScore:
            findTscore = TotalEsgScore.find('h4').get_text(strip = True)
            print(findTscore)
        else:
            print("none")
        # get Environmental esg score
        EnvironmentalScore = MainScoring.find('section',{"data-testid": "ENVIRONMENTAL_SCORE"})
        if EnvironmentalScore:
            findEscore = EnvironmentalScore.find('h4').get_text(strip = True)
            print(findEscore)
        else:
            print("none")
        # get Social esg score
        SocialScore = MainScoring.find('section',{"data-testid": "SOCIAL_SCORE"})
        if SocialScore:
            findSscore = SocialScore.find('h4').get_text(strip = True)
            print(findSscore)
        else:
            print("none")
        # get Governance esg score
        GovernanceScore = MainScoring.find('section',{"data-testid": "GOVERNANCE_SCORE"})
        if GovernanceScore:
            findGscore = GovernanceScore.find('h4').get_text(strip = True)
            print(findGscore)
        else:
            print("none")
    else:
        print("No Sustainability Available")
    createRows = [findName, findTscore, findEscore, findSscore, findGscore]
    writeFile.writerow(createRows)

chrome_prefs = {
    "profile.default_content_setting_values": {
        "images": 2,
        "stylesheet": 2,
        "fonts": 2,
        "plugins": 2,
        "notifications": 2
    }
}

options = Options()
options.add_experimental_option("prefs", chrome_prefs)
options.add_argument('--headless=new')
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=100x100")

# initialize a web driver instance to control a Chrome window
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=options
)

# when conveted to lambda needs change

with open('Tickers.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    with open('RawNews.csv', 'w', newline= '', encoding = 'utf8') as f:
# set up writer for CSV file
        writeFile = writer(f)
        header = ['CompanyName','TotalScore','EnvironmentalScore','SocialScore','GovernanceScore']
        writeFile.writerow(header)
        for row in reader:
            if row:
                ticker = row[0].strip()
                scrape_stock(driver, ticker)


# close the browser and free up the resources
driver.quit()
