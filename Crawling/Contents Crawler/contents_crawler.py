# 먼저 해당 라이브러리를 받아옵니다.
import requests
from bs4 import BeautifulSoup
import json
import re
import sys
import time, random


def get_news(n_url):
    news_detail = []
    print(n_url)
    breq = requests.get(n_url)
    bsoup = BeautifulSoup(breq.content, 'html.parser')

    # html 파싱
    title = bsoup.select('h3#articleTitle')[0].text
    news_detail.append(title)

    # 날짜 파싱
    pdate = bsoup.select('.t11')[0].get_text()[:11]
    news_detail.append(pdate)

    # 기사 본문 크롤링
    _text = bsoup.select('#articleBodyContents')[0].get_text().replace('\n', " ")
    btext = _text.replace("// flash 오류를 우회하기 위한 함수 추가 function _flash_removeCallback() {}", "")
    news_detail.append(btext.strip())

    # 신문사 크롤링
    pcompany = bsoup.select('#footer address')[0].a.get_text()
    news_detail.append(pcompany)

    return news_detail


# 쿼리에 검색어를 입력하고 검색 시작날짜부터 끝 날짜까지를 입력합니다.
query = input("검색어를 입력하세요 :  ")  # url 인코딩 에러는 encoding parse.quote(query)
s_date = input("시작날짜를 입력하세요 ex)2010.01.01 :  ")
e_date = input("종료날짜를 입력하세요 ex)2018.04.20 :  ")
s_from = s_date.replace(".", "")
e_to = e_date.replace(".", "")
page = 1

# 저장 경로를 입력합니다.
f = open("/Users/jungyulyang/programming/Project_ThematicInvest/Data/" + query + '테스트파일0430.txt', 'w', encoding='utf-8')

# 최대 몇개까지 크롤링을 할찌 숫자를 입력합니다. 크롤링 순서는 최신기사 순서로 크롤링 됩니다.
while page < 1000:

    print(page)

    url = "https://search.naver.com/search.naver?where=news&query=" + query + "&sort=1&ds=" + s_date + "&de=" + e_date + "&nso=so%3Ar%2Cp%3Afrom" + s_from + "to" + e_to + "%2Ca%3A&start=" + str(
        page)
    # header 추가
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    }
    req = requests.get(url, headers=header)
    print(url)
    cont = req.content
    soup = BeautifulSoup(cont, 'html.parser')
    # print(soup)

    for urls in soup.select("._sp_each_url"):
        try:
            # print(urls["href"])
            if urls["href"].startswith("https://news.naver.com"):
                # print(urls["href"])
                news_detail = get_news(urls["href"])
                # pdate, pcompany, title, btext
                f.write("{}\t{}\t{}\t{}\n".format(news_detail[1], news_detail[3], news_detail[0],
                                                  news_detail[2]))  # new style
        except Exception as e:
            print(e)
            continue
    page += 10
f.close()