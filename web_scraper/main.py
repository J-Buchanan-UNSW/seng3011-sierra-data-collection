# base selenium headless setup and tutorial by https://github.com/wbytedev/wbyte-selenium-lambda/blob/main/src/Dockerfile

import logging
import json

from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
import csv
from bs4 import BeautifulSoup
import boto3
from io import StringIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# setup headlessbrowser to bypass javascript when scraping
def initialise_driver():
    chrome_prefs = {

    "profile.default_content_setting_values": {
        "images": 2,
        "stylesheet": 2,
        "fonts": 2,
        "plugins": 2,
        "notifications": 2
    }
}
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-pipe")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-path=/tmp")
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    return driver
# scraper logic
def scrape_stock(driver, ticker_symbol):

        # build the URL of the target page
    url = f'https://finance.yahoo.com/quote/{ticker_symbol}/sustainability/'

    # visit the target page
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    findName = ""
    findTscore = ""
    findEscore = ""
    findSscore = ""
    findGscore = ""
    # entirepageFinders
    ESGContainer = soup.find('main', {"id": "nimbus-app"})
    CompanyDetails = soup.find('section', {"data-testid": "quote-hdr"})

    # subFinders
    if CompanyDetails:

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
    else:
        print("corrosponding company for ticker not found")
    # driver.quit()
    return [findName, findTscore, findEscore, findSscore, findGscore]


def lambda_handler(event, context):
    driver = initialise_driver()

    # Constants
    upload_prefix = "esgScoreCSV/"
    upload_filename = "CompanyScores"

    # AWS S3 Client
    s3_client = boto3.client("s3")

    print("🚀 Starting CSV processing...")
    print("📩 Event received:", json.dumps(event))

    # Retrieve bucket name and file key
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    print(f"🗂 File detected: s3://{bucket}/{key}")

    # Download CSV from S3
    print("📥 Fetching CSV from S3...")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    file_content = response["Body"].read().decode("utf-8")

    # Load CSV into DataFrame
    print("📊 Loading cleaned CSV into DataFrame...")

    tickerbuffer = StringIO(file_content)
    tickerread = csv.reader(tickerbuffer)

    scrapeddatabuffer = StringIO()
    scrapeddatawrite = csv.writer(scrapeddatabuffer)
    header = ['CompanyName','TotalScore','EnvironmentalScore','SocialScore','GovernanceScore']
    scrapeddatawrite.writerow(header)

    for row in tickerread:
        if row:
            ticker = row[0].strip()
            scrapedreturns = scrape_stock(driver, ticker)
            scrapeddatawrite.writerow(scrapedreturns)

    # Save final scraped CSV to S3
    scrapeddatabuffer.seek(0)
    s3_client.put_object(
        Bucket=bucket,
        Key = f"{upload_prefix}{upload_filename}.csv",
        Body=scrapeddatabuffer.getvalue(),
    )

    print(f"Successfully processed and uploaded to {upload_prefix}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "Success"}),
    }