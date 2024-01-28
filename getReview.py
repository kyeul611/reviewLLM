from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException, NoSuchAttributeException

import chromedriver_autoinstaller

import re
import json
import time

import itertools

chromedriver_autoinstaller()


def raiseChromeDriver():
    '''
    크롬 드라이버 구동
    '''
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options = Options()

    # options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={user_agent}")
    # options.add_argument("--headless")
    options.add_argument("--blink-settings=imagesEnabled=false")

    driver = webdriver.Chrome(options=options)
    return driver


def scroll_down(driver, iter=max):
        '''
        동적 웹 페이지의 모든 컨텐츠를 로드하기 위해 스크롤을 내리는 메서드
        iter: 내리는 횟수
        '''
        if iter == max:
            last_position = 0
            while True:
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                current_position = driver.execute_script("return window.pageYOffset;")

                if current_position == last_position:
                    break
                else:
                    last_position = current_position
                
                time.sleep(0.75)

        else:
            for _ in range(iter):
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(0.75)

def write_log():
    '''
    로그 기록용 함수
    '''
    pass

class CrawlingNaver:
    def __init__(self):
        self.driver = raiseChromeDriver()

    def getProdUrls(self, category_id):
        for page_num in itertools.count(1, 1):
            url = f"https://search.shopping.naver.com/search/category/{category_id}?adQuery&pagingIndex={page_num}&pagingSize=40&productSet=checkout&sort=review_rel&viewType=list"
        





class CrawlingCoupang:

    def __init__(self):
        self.driver = raiseChromeDriver()