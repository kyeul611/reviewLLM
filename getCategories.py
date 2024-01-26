'''
네이버와 쿠팡의 카테고리 정보를 수집하는 크롤러
카테고리 탭을 순회하며 카테고리 이름과 값을 수집하여 mongoDB에 저장함.

수집한 데이터는 어떤 형식으로 저장할까?

# 현재 저장 방식
{
    "Naver":{
        
        대분류:{
            id: 값,
            중분류:{
                ID: 값,
                소분류: {ID: 값},
                소분류: {ID: 값},
                소분류: {ID: 값},
                소분류: {ID: 값},
            },
            중분류:{
                ID: 값,
                소분류: {ID: 값},
                소분류: {ID: 값},
                소분류: {ID: 값},
                소분류: {ID: 값},
            },
        },
    }
}

# 변경할 저장 방식

{
    "collection_name" : "Naver",
    "데이터" : [
        {
            레벨: 대분류,
            이름: 카테고리 이름
            ID: 값,
            데이터: [
                {
                레벨: 중분류,
                이름: 카테고리 이름
                ID: 값,
                데이터:[
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    ]
                },
                {
                레벨: 중분류,
                이름: 카테고리 이름
                ID: 값,
                데이터:[
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    ]
                }
            ]
        },
        {
            레벨: 대분류,
            이름: 카테고리 이름
            ID: 값,
            데이터: [
                {
                레벨: 중분류,
                이름: 카테고리 이름
                ID: 값,
                데이터:[
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    ]
                },
                {
                레벨: 중분류,
                이름: 카테고리 이름
                ID: 값,
                데이터:[
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    {레벨: 소분류, 이름: 카테고리 이름, ID: 값},
                    ]
                }
            ]
        }
    ]
}

'''

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

import chromedriver_autoinstaller

from pymongo import MongoClient
import json

import time
import re
from tqdm import tqdm
from dotenv import dotenv_values

import concurrent.futures

chromedriver_autoinstaller.install()

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


def saveData(config, name, data):
    '''
    데이터를 받아 "name" collection에 data를 저장하는 메서드
    '''
    mongodb_client = MongoClient(config['MONGODB_ATLAS'])
    db = mongodb_client.reviewLLM_db
    collection = db[name]
    # result = collection.insert_many(data).inserted_ids
    for row in data:
        result = collection.insert_one(row).inserted_id
        if result:
            print(f"{list(row)[0]} => {result}")
    
    mongodb_client.close()

def getNaverCate():
    '''
    네이버 쇼핑 페이지에 접근한 후, 카테고리를 순회하며 ID값을 수집함
    '''

    def getNaverIDvalue(href):
        '''
        href에서 카테고리 ID를 추출하는 함수
        '''
        cat_id = int(re.search(r'catId=(\d+)', href).group(1))

        return cat_id

    category_data = []

    driver = raiseChromeDriver()
    url = 'https://shopping.naver.com/home'
    driver.get(url)

    # 카테고리 탭 클릭
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, '_categoryButton_category_3_5ml'))
    ).click()
    
    # 메인 카테고리 태그들이 로딩되고 나면 원소 찾기
    main_category = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, '_categoryLayer_main_category_2A7mb'))
    )
    # 메인카테고리 li 태그들
    main_li_list = main_category.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME') 
    
    # 메인 카테고리 순회
    for main_li_tag in tqdm(main_li_list, desc="네이버 카테고리 수집"):
        main_categories = {}
        # time.sleep(0.1)

        actions = ActionChains(driver)
        actions.move_to_element(main_li_tag).perform()

        # 메인 카테고리 ID값 찾기
        main_a_tag = main_li_tag.find_element(By.CSS_SELECTOR, 'a')
        main_href = main_a_tag.get_attribute('href')
        main_categories['ID'] = getNaverIDvalue(main_href)

        # 중간 카테고리 태그들 찾기
        middle_category = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, '_categoryLayer_middle_category_2g2zY'))
        )
        middle_li_list = middle_category.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME')
        
        # 중간 카테고리 순회
        for middle_li_tag in tqdm(middle_li_list, desc=f"   {main_li_tag.text} 항목 수집 중", leave=False):
            middle_categories = {}    
            
            # time.sleep(0.1)
            actions = ActionChains(driver)
            actions.move_to_element(middle_li_tag).perform()

            # 중간 카테고리 ID값 저장
            middle_a_tag = middle_li_tag.find_element(By.CSS_SELECTOR, 'a')
            middle_href = middle_a_tag.get_attribute('href')
            middle_categories["ID"] = getNaverIDvalue(middle_href) 


            # 하위 카테고리가 있는 경우 데이터를 수집한다.
            try:
                sub_category = driver.find_element(By.CLASS_NAME, '_categoryLayer_subclass_1K649')
            except NoSuchElementException:
                continue

            subclass_list = sub_category.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME')
            
            # 하위 카테고리 순회
            for sub_li in subclass_list:
                sub_categoris = {} # 하위 카테고리 값들을 저장할 임시 변수
                # 하위 카테고리 ID값 찾기
                try:
                    a_tag = WebDriverWait(sub_li, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                    )

                    sub_href = a_tag.get_attribute('href')
                    sub_categoris["ID"] = getNaverIDvalue(sub_href)
                    
                    # 중간 카테고리에 하위 카테고리 저장
                    middle_categories[sub_li.text] = sub_categoris
                
                except StaleElementReferenceException:
                    print(sub_li)
                    print(sub_li.get_property("attributes"))
                    print(a_tag)
                    print(a_tag.get_property("attributes"))
                    exit()

           
            main_categories[middle_li_tag.text] = middle_categories
        # category_data[main_li_tag.text]=main_categories
        category_data.append({main_li_tag.text:main_categories})
    return "Naver", category_data

def getCoupangCate():
    '''
    쿠팡 페이지에 접근한 후, 카테고리를 순회하며 ID값을 수집함
    '''
    def getCoupangIDvalue(href):
        '''
        href에서 카테고리 ID를 추출하는 함수
        '''
        try:
            cat_id = int(re.search(r'/(\d+)$', href).group(1))
        except AttributeError:
            cat_id = None

        return cat_id

    category_data = []
    
    driver = raiseChromeDriver()
    url = 'https://www.coupang.com/'
    driver.get(url)

    time.sleep(2)

    # 카테고리 탭에 마우스 올려서 메인 카테고리 불러오기
    category_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.category-btn'))
    )

    # category_btn = driver.find_element(By.CLASS_NAME, 'category-btn')
    action = ActionChains(driver)
    action.move_to_element(category_btn).perform()

    # 메인 카테고리 정보 가져오기
    main_category = driver.find_element(By.CLASS_NAME, 'category-layer')
    main_li_list = main_category.find_elements(By.CSS_SELECTOR, 'ul.menu > li')

    # 메인 카테고리 순회
    for main_li_tag in tqdm(main_li_list, desc="쿠팡 카테고리 수집"):
        main_categories = {}

        # main_category 이름
        main_text = main_li_tag.find_element(By.CSS_SELECTOR, 'a').text

        action = ActionChains(driver)
        action.move_to_element(main_li_tag).perform()

        # 메인 카테고리 ID값 찾기
        main_a_tag = main_li_tag.find_element(By.CSS_SELECTOR, 'a')
        main_href = main_a_tag.get_attribute('href')
        main_categories["ID"] = getCoupangIDvalue(main_href)

        middle_li_list = main_li_tag.find_elements(By.CLASS_NAME, 'second-depth-list')

        # 중간 카테고리 순회
        for middle_li_tag in tqdm(middle_li_list, desc=f"    {main_text} 항목 수집 중", leave=False):
            middle_categories = {}

            # 중간 카테고리 이름
            middle_text = middle_li_tag.find_element(By.CSS_SELECTOR, 'a').text

            action = ActionChains(driver)
            action.move_to_element(middle_li_tag).perform()
            
            # 중간 카테고리 ID값 저장
            middle_a_tag = middle_li_tag.find_element(By.CSS_SELECTOR, 'a')
            middle_href = middle_a_tag.get_attribute('href')
            middle_categories['ID'] = getCoupangIDvalue(middle_href)


            # 하위 카테고리가 있는 경우 데이터를 수집함
            try:
                sub_li_list = middle_li_tag.find_elements(By.CSS_SELECTOR, 'li')
            except NoSuchElementException:
                continue

            for sub_li in sub_li_list:
                sub_categories = {} # 하위 카테고리 값들을 저장할 임시 변수

                a_tag = WebDriverWait(sub_li, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                )
                sub_href = a_tag.get_attribute('href')
                sub_categories['ID'] = getCoupangIDvalue(sub_href)
            
            main_categories[middle_text] = middle_categories
        category_data.append({main_text:main_categories})

    return "Coupang", category_data
   

if __name__=="__main__":

    config = dotenv_values(".env")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        future1 = executor.submit(getNaverCate)
        future2 = executor.submit(getCoupangCate)

        for future in concurrent.futures.as_completed([future1, future2]):
            try:
                name, data = future.result()
                saveData(config, name, data)
            
            except Exception as e:
                print(e)

