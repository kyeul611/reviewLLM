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
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options = Options()

    options.add_argument("--start-maximized")
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
    collection.insert_one(data)

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
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, '_categoryButton_category_3_5ml'))
        )
        element.click()
    except Exception as e:
        print(e)
        
    main_categories = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, '_categoryLayer_main_category_2A7mb'))
    )[0]
    # main_categories = driver.find_element(By.CLASS_NAME, '_categoryLayer_main_category_2A7mb')
    main_li_list = main_categories.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME') 
    for i, main_li_tag in enumerate(main_li_list):
        # time.sleep(0.1)
        print(i, main_li_tag.text)

        # 메인 카테고리 저장
        category_data[main_li_tag.text] = []

        actions = ActionChains(driver)
        actions.move_to_element(main_li_tag).perform()
        middle_categories = driver.find_element(By.CLASS_NAME, '_categoryLayer_middle_category_2g2zY')
        middle_li_list = middle_categories.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME')
    
        for j, middle_li_tag in enumerate(middle_li_list):
            # time.sleep(0.1)
            print("     ", j, middle_li_tag.text)

            actions = ActionChains(driver)
            actions.move_to_element(middle_li_tag).perform()

            try:
                subclass = driver.find_element(By.CLASS_NAME, '_categoryLayer_subclass_1K649')
                subclass_list = subclass.find_elements(By.CLASS_NAME, '_categoryLayer_list_34UME')
                
                for sub_li in subclass_list:
                    # a_tag = sub_li.find_element(By.CSS_SELECTOR, 'a')
                    # a_tag = sub_li.find_element(By.CLASS_NAME, '_categoryLayer_link_2sZdW')
                    a_tag = WebDriverWait(sub_li, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a'))
                    )[0]
                    try:
                        href = a_tag.get_attribute('href')
                        cat_id = re.search(r'catId=(\d+)', href).group(1)
                    except:
                        print(a_tag.get_attribute("outerHTML"))
                        exit()
                    # save to dictionary
                    main_category = main_li_tag.text
                    rest_data = f"{middle_li_tag.text}/{sub_li.text}"
                    
                    category_data[main_category].append({rest_data : int(cat_id)})

                
            except NoSuchElementException as e:
                # a_tag = middle_li_tag.find_element(By.CSS_SELECTOR, "a")
                # a_tag = middle_li_tag.find_element(By.CLASS_NAME, '_categoryLayer_link_2sZdW')
                a_tag = WebDriverWait(middle_li_tag, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a'))
                    )[0]
                href = a_tag.get_attribute('href')
                cat_id = re.search(r'catId=(\d+)', href).group(1)

                category_data[main_category].append({rest_data : int(cat_id)})

    return "Naver", category_data

def getCoupangCate():
    
    driver = raiseChromeDriver()
    url = 'https://www.coupang.com/'
    driver.get(url)
    


if __name__=="__main__":
    config = dotenv_values(".env")

    # pass
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future1 = executor.submit(getNaverCate)
        future2 = executor.submit(getCoupangCate)
        

        for future in concurrent.futures.as_completed([future1, future2]):
            try:
                name, data = future.result()
                saveData(name, data)
            
            except Exception as e:
                print(e)

