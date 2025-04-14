from csv import writer
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.afr.com/companies"

page = requests.get(url)

soup = BeautifulSoup(page.content, 'html.parser')
# sorted section for latest in AFR
# main = soup.find('main')
# section = main.find_all('section')

# scrapes afr news for data and writes to CSV file

# creates CSV file
with open('RawNews.csv', 'w', newline= '', encoding = 'utf8') as f:
# set up writer for CSV file
    writeFile = writer(f)
    header = ['Title','Description','Link','Date']
    writeFile.writerow(header)

    NewsStorysection = soup.find_all(attrs={"data-testid": "StoryTileBase"})
    for NSsection in NewsStorysection:
    # get image
    # imagesection = NSsection.find()
    # get Title
        StoryTitle = NSsection.find(attrs={"data-testid": "StoryTileHeadline-h3"})
        title = StoryTitle.get_text()
        print(title)
    # get Description
        StoryDesc = NSsection.find(attrs={"data-pb-type": "ab"})
        desc = StoryDesc.get_text()
        print(desc)
    # get Link
        link = StoryTitle.find('a', href = True)
        FinalLink = "https://www.afr.com" + link['href']
        print(FinalLink)
    # get datePosted
        StoryDate = NSsection.find(attrs={"data-testid": "StoryTile-Timestamp"})
        if StoryDate:
            Date = StoryDate.get_text(strip = True)
        else:
                Date = None
        print(Date)


        createRows = [title, desc, FinalLink, Date]
        writeFile.writerow(createRows)


