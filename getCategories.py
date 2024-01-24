'''
네이버와 쿠팡의 카테고리 정보를 수집하는 크롤러
카테고리 탭을 순회하며 카테고리 이름과 값을 수집하여 mongoDB에 저장함.

수집한 데이터는 어떤 형식으로 저장할까?
    {
        "Naver":{
            {
                대분류:[
                    {"중분류/소분류":ID값},
                    {"중분류/소분류":ID값},
                    {"중분류/소분류":ID값},
                ],
                대분류:[
                    {"중분류/소분류":ID값},
                    {"중분류/소분류":ID값},
                    {"중분류/소분류":ID값},
                ],
            }
        },

    Naver = [
        

    ]
        
        ## 또는 

        "Coupang":[
            {"대분류/중분류/소분류":ID값},
            {"대분류/중분류/소분류":ID값}
        ]
    }
    


'''

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import chromedriver_autoinstaller

from pymongo import MongoClient
import json

import time
import re
from dotenv import dotenv_values

import concurrent.futures

chromedriver_autoinstaller.install()

def raiseChromeDriver():
    '''
    크롬 드라이버 구동
    '''
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options = Options()

    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={user_agent}")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def saveData(config, name, data):
    '''
    데이터를 받아 "name" collection에 data를 저장하는 메서드
    '''
    mongodb_client = MongoClient(config['MONGODB_ATLAS'])
    db = mongodb_client.reviewLLM_db
    collection = db[name]
    result = collection.update_one(data, upsert=True)
    if result.upserted_id:
        print(result.upserted_id)
    
    mongodb_client.close()


def getNaverCate():
    '''
    네이버 쇼핑 페이지에 접근한 후, 카테고리를 순회하며 ID값을 수집함
    '''
    category_data = {}

    driver = raiseChromeDriver()
    url = 'https://shopping.naver.com/home'
    driver.get(url)

    # 카테고리 탭 클릭
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, '_categoryButton_category_3_5ml'))
    )
    element.click()
        
    main_categories = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, '_categoryLayer_main_category_2A7mb'))
    )
    # main_categories = driver.find_element(By.CLASS_NAME, '_categoryLayer_main_category_2A7mb')
    main_li_list = main_categories.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME') 
    for main_li_tag in main_li_list:
        # time.sleep(0.1)

        # 메인 카테고리 저장
        main_category = main_li_tag.text
        category_data[main_category] = []

        actions = ActionChains(driver)
        actions.move_to_element(main_li_tag).perform()
        middle_categories = driver.find_element(By.CLASS_NAME, '_categoryLayer_middle_category_2g2zY')
        middle_li_list = middle_categories.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME')
    
        for middle_li_tag in middle_li_list:
            # time.sleep(0.1)
            actions = ActionChains(driver)
            actions.move_to_element(middle_li_tag).perform()
            try:
                subclass = driver.find_element(By.CLASS_NAME, '_categoryLayer_subclass_1K649')
                subclass_list = subclass.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME')
                for sub_li in subclass_list:
                    a_tag = WebDriverWait(sub_li, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                    )
                    try:
                        href = a_tag.get_attribute('href')
                        cat_id = re.search(r'catId=(\d+)', href).group(1)
                    except:
                        print(a_tag.get_attribute("exampleId"))
                        exit()
                    # save to dictionary
                    rest_data = f"{middle_li_tag.text}-{sub_li.text}"
                    
                    category_data[main_category].append({rest_data : int(cat_id)})
            
            # 하위 카테고리가 없는 항목은 중위 카테고리 정보만 가져온다.
            except NoSuchElementException:
                a_tag = WebDriverWait(middle_li_tag, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                    )
                href = a_tag.get_attribute('href')
                
                cat_id = re.search(r'catId=(\d+)', href).group(1)
                rest_data = f"{middle_li_tag.text}"

                category_data[main_category].append({rest_data : int(cat_id)})
    
        # result = json.dumps(category_data[main_li_tag.text], indent=2, ensure_ascii=False)
        # print(result)
    return "Naver", category_data

def getCoupangCate():
    '''
    쿠팡 페이지에 접근한 후, 카테고리를 순회하며 ID값을 수집함
    '''
    category_data = {}
    
    driver = raiseChromeDriver()
    url = 'https://www.coupang.com/'
    driver.get(url)

    # 카테고리 탭에 마우스 올려서 메인 카테고리 불러오기
    category_btn = driver.find_element(By.CLASS_NAME, 'category-btn')
    action = ActionChains(driver)
    action.move_to_element(category_btn).perform()

    # 메인 카테고리 정보 가져오기
    main_categories = driver.find_element(By.CLASS_NAME, 'category-layer')
    main_li_list = main_categories.find_elements(By.CSS_SELECTOR, 'ul.menu > li')
    for main_li_tag in main_li_list:
        main_category = main_li_tag.text
        category_data[main_category] = []

        action = ActionChains(driver)
        action.move_to_element(main_li_tag).perform()

        middle_li_list = main_li_tag.find_elements(By.CLASS_NAME, 'second-depth-list')
        for middle_li_tag in middle_li_list:

            action = ActionChains(driver)
            action.move_to_element(middle_li_tag).perform()
            middle_category = middle_li_tag.find_element(By.CSS_SELECTOR, 'a')
            try:
                sub_li_list = middle_li_tag.find_elements(By.CSS_SELECTOR, 'li')
                for sub_li in sub_li_list:
                    a_tag = WebDriverWait(sub_li, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                    )
                    href = a_tag.get_attribute('href')
                    cat_id = re.search(r'/(\d+)$', href).group(1)

                    # save to dictionary
                    
                    rest_data = f"{middle_category.text}-{sub_li.text}"
                    category_data[main_category].append({rest_data:int(cat_id)})

            except NoSuchElementException:
                a_tag = WebDriverWait(middle_li_tag, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                )
                href = a_tag.get_attribute('href')
                cat_id = re.search(r'/(\d+)$', href).group(1)
                rest_data = f"{middle_category.text}"

                category_data[main_category].append({rest_data: int(cat_id)})

    result = json.dumps(category_data, indent=2, ensure_ascii=False)
    print(result)
    return "Coupang", category_data

        

if __name__=="__main__":

    config = dotenv_values(".env")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        # future1 = executor.submit(getNaverCate)
        future2 = executor.submit(getCoupangCate)
        
        future2.result()

        # for future in concurrent.futures.as_completed([future1, future2]):
        #     try:
        #         name, data = future.result()
        #         saveData(config, name, data)
            
        #     except Exception as e:
        #         print(e)

