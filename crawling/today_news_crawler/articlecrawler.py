#!/usr/bin/env python
# -*- coding: utf-8, euc-kr -*-

from time import sleep
from bs4 import BeautifulSoup
from multiprocessing import Process
from exceptions import *
import json
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

import pyarrow as pa
from pyarrow import csv, parquet
from s3fs.core import S3FileSystem, aiobotocore

from schema import generate_schema
from utils import BackOff, loading_time

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
        wcsv.writerow(["date", "time", "category", "company", "author", "headline", "sentence", "content_url", "image_url"])
        

        # 기사 URL 형식
        url = "http://news.naver.com/main/list.nhn?mode=LSD&mid=sec&sid1=" + str(
            self.categories.get(category_name)) + "&date="

        # start_year년 start_month월 ~ end_year의 end_month 날짜까지 기사를 수집합니다.
        day_urls = self.make_news_page_url(url, self.date['year'], self.date['month'], self.date['day'])
        print(category_name + " Urls are generated")
        print("The crawler starts")

        with concurrent.futures.ThreadPoolExecutor() as pool:
            futureWorkers = []
            for URL in day_urls:
                futureWorkers.append(pool.submit(
                    self.get_page_and_write_row,
                    category_name,
                    writer,
                    URL,
                ))
            for future in concurrent.futures.as_completed(futureWorkers):
                print(future.result())
        writer.close()


    def get_page_and_write_row(self, category_name, writer, URL):
        news_date = self.get_date_from_URL(URL)

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
                text_headline = self.get_headline_from_document(document_content)
                # 기사 본문 가져옴
                text_sentence = self.get_sentence_from_document(document_content)
                # 기사 언론사 가져옴
                text_company = self.get_company_from_document(document_content)
                # 기사 이미지 가져옴
                image_url = self.get_imgURL_from_document(document_content)
                # 기사 시간 가져옴
                news_time = self.get_time_from_document(document_content)
                # 기자 가져옴
                author_name = self.find_author(text_sentence)

                # CSV 작성
                wcsv = writer.get_writer_csv()
                wcsv.writerow([news_date, news_time, category_name, text_company, author_name, text_headline, text_sentence, content_url, image_url])
                
                del text_company, text_sentence, text_headline
                del image_url
                del request_content, document_content
                return("DONE")
                
            except Exception as e:  # UnicodeEncodeError ..
                # wcsv.writerow([ex, content_url])
                del request_content, document_content
                return(f"ERROR : {e}")

    def date_loader(self):
        with open("/Users/jungyulyang/programming/hell-news/config/credential.json") as json_file:
            json_data = json.load(json_file)

        db = pymysql.connect(
            user = json_data['user'],
            passwd = json_data['passwd'],
            host = json_data['host'],
            charset = json_data['charset']
        )

        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute('USE news_crawling')

        sql = "select dates from only_date"
        cursor.execute(sql)
        rows = cursor.fetchall()
        sql_data = str(rows[0])

        numbers = re.findall("\d+", sql_data)
        sql_year = int(numbers[0])
        sql_month = int(numbers[1])
        sql_day = int(numbers[2])

        sql = "delete from only_date limit 1"
        cursor.execute(sql)
        db.commit()

        return sql_year, sql_month, sql_day


    def start(self):
        # MultiProcess 크롤링 시작
        with concurrent.futures.ProcessPoolExecutor() as process:
            futureWorkers = []
            for category_name in self.selected_categories:
                futureWorkers.append(process.submit(
                    self.crawling,
                    category_name
                ))
            for future in concurrent.futures.as_completed(futureWorkers):
                print(future.result())

    def get_date_from_URL(self, URL):
        regex = re.compile("date=(\\d+)")
        news_date = regex.findall(URL)[0]
        return news_date

    def get_headline_from_document(self, document):
        tag_headline = document.find_all('h3', {'id': 'articleTitle'}, {'class': 'tts_head'})
        text_headline = ''  # 뉴스 기사 제목 초기화
        text_headline = text_headline + ArticleParser.clear_headline(
            str(tag_headline[0].find_all(text=True)))
        if not text_headline:  # 공백일 경우 기사 제외 처리
            return None
        return text_headline

    def get_sentence_from_document(self, document):
        tag_content = document.find_all('div', {'id': 'articleBodyContents'})
        text_sentence = ''  # 뉴스 기사 본문 초기화
        text_sentence = text_sentence + ArticleParser.clear_content(str(tag_content[0].find_all(text=True)))
        if not text_sentence or len(text_sentence) < 500:  # 공백일 경우 기사 제외 처리
            return None
        return text_sentence
    
    def get_company_from_document(self, document):
        tag_company = document.find_all('meta', {'property': 'me2:category1'})
        text_company = ''  # 언론사 초기화
        text_company = text_company + str(tag_company[0].get('content'))
        if not text_company:  # 공백일 경우 기사 제외 처리
            return None
        return text_company
    
    def get_imgURL_from_document(self, document):
        image_url = document.find('span', {'class':'end_photo_org'}).find('img')['src']
        if not image_url:
            return None
        return image_url

    def get_time_from_document(self, document):
        tag_time = document.find('span', {'class':'t11'}).text.split(" ")[1:]
        news_time = " ".join(tag_time)
        if not news_time:
            return None
        return news_time
    
    def find_author(self, company_string):
        company_list = company_string.split(" ")
        front = 0
        back = len(company_list)-1
        while front <= back:
            if company_list[front] == '기자' or company_list[back] == '기자':
                author_name = company_list[front-1]
                if len(author_name) != 3 :
                    return None
                else:
                    return author_name
                    break

            front += 1
            back -= 1
        
        return None

    def today_date_loader(self):
        today = date.today()
        numbers = re.findall("\d+", str(today))
        today_year = int(numbers[0])
        today_month = int(numbers[1])
        today_day = int(numbers[2])
        print(today_year, today_month, today_day)

        return today_year, today_month, today_day
            
if __name__ == "__main__":
    Crawler = ArticleCrawler()
    Crawler.set_category("정치", "경제", "사회", "생활문화", "IT과학")

    # 날짜 하나씩 불러올때
    # sql_year, sql_month, sql_day = Crawler.date_loader()
    # Crawler.set_date_range(sql_year, sql_month, sql_day)

    #오늘 날짜
    today_year, today_month, today_day = Crawler.today_date_loader()
    Crawler.set_date_range(today_year, today_month, today_day)

    # 날짜 설정
    # Crawler.set_date_range(2020, 8, 15)

    Crawler.start()
    