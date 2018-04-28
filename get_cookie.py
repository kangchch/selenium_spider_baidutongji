# -*- coding: utf-8 -*-

from ctypes import *
import sys
import os
import hashlib
import binascii
import random
import sys
import requests
import time
from selenium import webdriver
from ctypes import *
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient,DESCENDING
from PIL import Image
from selenium.webdriver.chrome.options import Options
import logging
import traceback
import selenium.webdriver.support.ui as ui
import pymongo
import datetime
from pic_recognise import PicRecognise
from  proxy import proxy

reload(sys)
sys.setdefaultencoding('utf-8')

pic_vcode_name = os.path.join(os.path.dirname(__file__), 'image', 'vcode.jpg')   #测试图片文件
pic_ab_name = os.path.join(os.path.dirname(__file__), 'image', 'ab.jpg')

proxy = proxy('chrome')
def init_browser(browser_type):
    pass

def browser_quit(browser):
    try:
        if browser:
            pid = browser.service.process.pid
            os.kill(pid, 9)
    except Exception, e:
        pass
    finally:
        browser  = None

def isLogin(browser):
    try:
        time.sleep(1)
        wait = WebDriverWait(browser, 10)
        element = wait.until(EC.presence_of_element_located(
            (By.ID, 'ErrorTip')))
        print 'Login Failed';
        return False
    except NoSuchElementException:
        print 'Login Successful';
        return True
    except TimeoutException:
        print 'Login Successful';
        return True

def get_baidu_tongji_cookie(username, passwd, phone):
    while True:
        # browser = proxy.get_new_webdriver_with_proxy()
        browser = webdriver.Chrome()
        browser.maximize_window()
        wait = ui.WebDriverWait(browser,120)

        try:
            ## 0. open login page
            browser.get("https://tongji.baidu.com/web/welcome/login")
            source = browser.page_source
            if source.find(u'您所请求的网址（URL）无法获取') > 0:
                browser.quit()
                time.sleep(5)
                continue
            wait.until(lambda browser: browser.find_element_by_xpath("//div[@class='r homepage-header-user-info']/a[@id='login']"))
            break
        except Exception, e:
            logging.warning("open chrom error:%s" %(str(e)))
            browser.quit()
            time.sleep(10)
            continue
        

    try:
        ## 1. input username and password
        browser.find_element_by_xpath("//div[@class='r homepage-header-user-info']/a[@id='login']").click()
        # browser.find_element_by_xpath("//input[@id='UserName']").send_keys("searchhc360")
        # browser.find_element_by_xpath("//input[@id='Password']").send_keys("HCsearch2014")
        browser.find_element_by_xpath("//input[@id='UserName']").send_keys(username)
        browser.find_element_by_xpath("//input[@id='Password']").send_keys(passwd)

        ## 2. save vcode pic
        browser.save_screenshot(pic_ab_name)
        page = browser.find_element_by_xpath('//*[@id="cas_code"]')
        location = page.location
        size = page.size
        rangle=(int(location['x']),int(location['y']),int(location['x']+size['width']),int(location['y']+size['height']))
        i=Image.open(pic_ab_name)
        frame4=i.crop(rangle)
        frame4.save(pic_vcode_name)
        logging.info('[get_baidu_tongji_cookie] 1. vcode cut complete.')

        ## 3. recognize vcode by call api
        logging.info('[get_baidu_tongji_cookie] 2. vcode recognise before.')
        pr = PicRecognise()
        vcode = pr.PicRecognise(pic_vcode_name)
        # vcode = raw_input('Please input captcha:')
        logging.info('[get_baidu_tongji_cookie] 3. vcode recognise after. %s', vcode)

        ## 4. submit and wait next page
        browser.find_element_by_xpath("//input[@id='Valicode']").send_keys(vcode)
        time.sleep(1)
        browser.find_element_by_xpath("//input[@id='Submit']").click()
        logging.info('[get_baidu_tongji_cookie] 4. vcode submit after.')

        while(not isLogin(browser)):
            browser.find_element_by_xpath("//input[@id='Password']").send_keys(passwd)

            ## 2. save vcode pic
            browser.save_screenshot(pic_ab_name)
            page = browser.find_element_by_xpath('//*[@id="cas_code"]')
            location = page.location
            size = page.size
            rangle=(int(location['x']),int(location['y']),int(location['x']+size['width']),int(location['y']+size['height']))
            i=Image.open(pic_ab_name)
            frame4=i.crop(rangle)
            frame4.save(pic_vcode_name)
            logging.info('[get_baidu_tongji_cookie] 1. vcode cut complete.')

            ## 3. recognize vcode by call api
            logging.info('[get_baidu_tongji_cookie] 2. vcode recognise before.')
            pr = PicRecognise()
            vcode = pr.PicRecognise(pic_vcode_name)
            # vcode = raw_input('Please input captcha:')
            logging.info('[get_baidu_tongji_cookie] 3. vcode recognise after. %s', vcode)

            ## 4. submit and wait next page
            browser.find_element_by_xpath("//input[@id='Valicode']").send_keys(vcode)
            time.sleep(1)
            browser.find_element_by_xpath("//input[@id='Submit']").click()
            logging.info('[get_baidu_tongji_cookie] 4. vcode submit after.')

        try:
            wait.until(lambda browser: browser.find_element_by_xpath('''//*[@id="QuestionSelect"]|//*[@id='site-summary']/table'''))
        except TimeoutException:
            logging.error('[get_baidu_tongji_cookie] vcode auth failed!')
            if browser.current_url.find('cas.baidu.com/?action=login') > 0:
                browser.quit()
                return ''


        try:
            ## 4.1 phone authorize if need
            ui.Select(browser.find_element_by_xpath("//*[@id='QuestionSelect']")).select_by_value('100000000')
            browser.find_element_by_xpath("//*[@id='QuestionInput']").send_keys(phone)
            browser.find_element_by_xpath("//*[@id='uc-sec-confirm-btn']").click()
            logging.info('[get_baidu_tongji_cookie] 5. need phone auth.')
        except NoSuchElementException, e:
            logging.info('[get_baidu_tongji_cookie] 5. not need phone auth.')

        ## 5. login
        try:
            wait.until(lambda browser: browser.find_element_by_xpath("//*[@id='site-summary']/table"))
        except TimeoutException:
            logging.error('[get_baidu_tongji_cookie] after auth failed!')
            browser_quit(browser)
        # cookie = browser.execute_script('return document.cookie')
        # logging.info('[get_baidu_tongji_cookie] 6. login succeed. \n %s \n', cookie)
        return browser
    except Exception, e:
        logging.error('[get_baidu_tongji_cookie] error! \n%s', str(traceback.print_exc()))
        browser_quit(browser)

if __name__ == '__main__':
    get_baidu_tongji_cookie("searchhc360", "HCsearch2014", '18210607604')
