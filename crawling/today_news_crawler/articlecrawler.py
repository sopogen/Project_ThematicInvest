#!/usr/bin/env python
# -*- coding: utf-8, euc-kr -*-

from time import sleep
from bs4 import BeautifulSoup
from multiprocessing import Process
from exceptions import *
from articleparser import ArticleParser
from writer import Writer
import os
import platform
import calendar
import requests
import re
from datetime import date, timedelta
import pymysql
import datetime
import concurrent
import json


from pyarrow import csv, parquet
from s3fs import S3FileSystem


class ArticleCrawler(object):
    def __init__(self):
        self.categories = {'정치': 100, '경제': 101, '사회': 102, '생활문화': 103, '세계': 104, 'IT과학': 105, '오피니언': 110}
        self.selected_categories = []
        self.date = {'year': 0, 'month': 0, 'day': 0}
        self.user_operating_system = str(platform.system())

    def set_category(self, *args):
        for key in args:
            if self.categories.get(key) is None:
                raise InvalidCategory(key)
        self.selected_categories = args

    def set_date_range(self, year, month, day):
        args = [year, month, day]
        if month < 1 or month > 12:
            raise InvalidMonth(month)
        if day < 1 or day > 31:
            raise InvalidDay(day)
        for key, date in zip(self.date, args):
            self.date[key] = date
        print(self.date)

    @staticmethod
    def make_news_page_url(category_url, year, month, day):
        made_urls = []
        if len(str(month)) == 1:
            month = "0" + str(month)
        if len(str(day)) == 1:
            day = "0" + str(day)
        url = category_url + str(year) + str(month) + str(day)
        print(url)
        totalpage = ArticleParser.find_news_totalpage(url + "&page=10000")
        for page in range(1, totalpage + 1):
            made_urls.append(url + "&page=" + str(page))

        return made_urls

    @staticmethod
    def get_url_data(url, max_tries=10):
        remaining_tries = int(max_tries)
        while remaining_tries > 0:
            try:
                return requests.get(url)
            except ConnectionError:
                sleep(60)
            remaining_tries = remaining_tries - 1
        raise ResponseTimeout()

    def crawling(self, category_name):
        # Multi Process PID
        print(category_name + " PID: " + str(os.getpid()))

        writer = Writer(category_name=category_name, date=self.date)
        wcsv = writer.get_writer_csv()
        wcsv.writerow(["date", "category", "company", "headline", "sentence", "content_url", "image_url"])

        # 기사 URL 형식
        url = "http://news.naver.com/main/list.nhn?mode=LSD&mid=sec&sid1=" + str(
            self.categories.get(category_name)) + "&date="

        # start_year년 start_month월 ~ end_year의 end_month 날짜까지 기사를 수집합니다.
        day_urls = self.make_news_page_url(url, self.date['year'], self.date['month'], self.date['day'])
        print(category_name + " Urls are generated")
        print("The crawler starts")
        
        for URL in day_urls:

            regex = re.compile("date=(\\d+)")

            news_date = regex.findall(URL)[0]
            
            request = self.get_url_data(URL)

            document = BeautifulSoup(request.content, 'html.parser')

            # html - newsflash_body - type06_headline, type06
            # 각 페이지에 있는 기사들 가져오기
            post_temp = document.select('.newsflash_body .type06_headline li dl')
            post_temp.extend(document.select('.newsflash_body .type06 li dl'))

            # 각 페이지에 있는 기사들의 url 저장
            post = []
            for line in post_temp:
                post.append(line.a.get('href'))  # 해당되는 page에서 모든 기사들의 URL을 post 리스트에 넣음
            del post_temp

            for content_url in post:  # 기사 URL
                # 크롤링 대기 시간
                sleep(0.01)

                # 기사 HTML 가져옴
                request_content = self.get_url_data(content_url)
                try:
                    document_content = BeautifulSoup(request_content.content, 'html.parser')
                except:
                    continue


                try:
                    # 기사 제목 가져옴
                    tag_headline = document_content.find_all('h3', {'id': 'articleTitle'}, {'class': 'tts_head'})
                    text_headline = ''  # 뉴스 기사 제목 초기화
                    text_headline = text_headline + ArticleParser.clear_headline(
                        str(tag_headline[0].find_all(text=True)))
                    if not text_headline:  # 공백일 경우 기사 제외 처리
                        continue

                    # 기사 본문 가져옴
                    tag_content = document_content.find_all('div', {'id': 'articleBodyContents'})
                    text_sentence = ''  # 뉴스 기사 본문 초기화
                    text_sentence = text_sentence + ArticleParser.clear_content(str(tag_content[0].find_all(text=True)))
                    if not text_sentence:  # 공백일 경우 기사 제외 처리
                        continue

                    # 기사 언론사 가져옴
                    tag_company = document_content.find_all('meta', {'property': 'me2:category1'})
                    text_company = ''  # 언론사 초기화
                    text_company = text_company + str(tag_company[0].get('content'))
                    if not text_company:  # 공백일 경우 기사 제외 처리
                        continue

                    # 기사 이미지 가져옴
                    image_url = document_content.find('span', {'class':'end_photo_org'}).find('img')['src']
                    if not image_url:
                        continue

                    # CSV 작성
                    wcsv = writer.get_writer_csv()
                    wcsv.writerow([news_date, category_name, text_company, text_headline, text_sentence, content_url, image_url])
                    
                    del text_company, text_sentence, text_headline
                    del tag_company
                    del tag_content, tag_headline
                    del image_url
                    del request_content, document_content

                    
                except Exception:  # UnicodeEncodeError ..
                    # wcsv.writerow([ex, content_url])
                    del request_content, document_content
                    pass

        
        print(category_name + "crawler finished")    
        writer.close()
    
    def date_loader(self):
        today = date.today()
        numbers = re.findall("\d+", str(today))
        today_year = int(numbers[0])
        today_month = int(numbers[1])
        today_day = int(numbers[2])
        print(today_year, today_month, today_day)

        return today_year, today_month, today_day

    def start(self):
        # MultiProcess 크롤링 시작
        for category_name in self.selected_categories:
            proc = Process(target=self.crawling, args=(category_name,))
            proc.start()

            
if __name__ == "__main__":
    
    Crawler = ArticleCrawler()
    Crawler.set_category("사회", "생활문화", "IT과학")
    today_year, today_month, today_day = Crawler.date_loader()
    Crawler.set_date_range(today_year, today_month, today_day)
    Crawler.start()









