import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import csv
from articleparser import ArticleParser


def get_news_title(n_url):
    breq = requests.get(n_url)
    bsoup = BeautifulSoup(breq.content, 'html.parser')

    get_title_raw = bsoup.select('h3#articleTitle')[0].text  # 대괄호는  h3#articleTitle 인 것중 첫번째 그룹만 가져오겠다.
    get_title = ''
    get_title = get_title + ArticleParser.clear_headline(get_title_raw)

    if not get_title:
        return None

    return get_title

def get_news_content(n_url):
    breq = requests.get(n_url)
    bsoup = BeautifulSoup(breq.content, 'html.parser')
    
    _text = bsoup.select('#articleBodyContents')[0].get_text().replace('\n', " ")
    btext = _text.replace("// flash 오류를 우회하기 위한 함수 추가 function _flash_removeCallback() {}", "")

    get_content = ''
    get_content = get_content + ArticleParser.clear_content(btext)

    if not get_content:
        return None

    return get_content


def crawler(query): 
    page = 1
    maxpage = 3991  # 11= 2페이지 21=3페이지 31=4페이지  ...81=9페이지 , 91=10페이지, 101=11페이지
    f = open(RESULT_PATH + "%s.csv" % str(query), 'w', encoding='utf-8', newline="")
    writer = csv.writer(f)
    writer.writerow(["title", "contents"])

    while page < maxpage:
        print(page)

        url = "https://search.naver.com/search.naver?where=news&query=" + query + "&sm=tab_pge&sort=0&start=" + str(page)
        print(url)
        req = requests.get(url)
        cont = req.content
        soup = BeautifulSoup(cont, 'html.parser')
        # print(soup)

        for urls in soup.select("._sp_each_url"):
            try:    
                if urls["href"].startswith("https://news.naver.com"):
                    news_title = get_news_title(urls["href"])
                    print(news_title)

                    news_content = get_news_content(urls["href"])
                    print(news_content)

                    if len(news_content) > 500:
                        writer.writerow([news_title, news_content])
                    else:
                        continue
                    

            except Exception as e:
                print(e)
                continue
        page += 10


if __name__ == "__main__":
    RESULT_PATH = '/Users/jungyulyang/programming/Project_ThematicInvest/Data/theme_news_data/'
    query = input("원하는 검색어를 입력하세요: ")
    # query = "5G"
    crawler(query)
