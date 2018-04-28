# -*- coding: utf-8 -*-
import os
import sys
import logging
import requests
import time
import datetime
import json
import copy
from get_cookie import *
from function import *
import cx_Oracle
from selenium.webdriver.common.action_chains import ActionChains #引入ActionChains鼠标操作类
from selenium.webdriver.common.keys import Keys

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
reload(sys)
sys.setdefaultencoding('utf-8')

proxies = {
  "http": "http://tj_user_5_2:111111@60.28.110.66:8899",
}

class BaiduCrawler:
    def __init__(self):
        self.bd_ip = 338
        self.bd_pv = 339
        self.bd_uv = 340

    ## 解析mip下趋势分析每个小时的数据
    def flow_trend_hour(self, browser):

        wait = ui.WebDriverWait(browser,120)
        results_item = {}
        try:
            ## 1,
            wait.until(lambda browser: browser.find_element_by_xpath("//tr[@id='site-summary-tr_10835307']/td[@class='table-index']/div/a"))
        except TimeoutException:
            logging.error('click mip.hc.360.com failed')
        browser.find_element_by_xpath("//tr[@id='site-summary-tr_10835307']/td[@class='table-index']/div/a").click()

        try:
            ## 2,
            wait.until(lambda browser: browser.find_element_by_xpath("//span[@class='trend']/a[@id='event-monitor-today']"))
        except TimeoutException:
            logging.error('click flow trend today failed')
        browser.find_element_by_xpath("//span[@class='trend']/a[@id='event-monitor-today']").click()

        ## 3, page_down
        ac = ActionChains(browser)
        ac.send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(2)
        bd_pv = browser.find_element_by_xpath("//tr[@id='table-tr_1']/td[@class='number group pv_count']/div[@class='td-content']")
        if bd_pv:
            pv = bd_pv.text.encode('utf-8').replace(',', '')
        bd_uv = browser.find_element_by_xpath("//tr[@id='table-tr_1']/td[@class='number visitor_count']/div[@class='td-content']")
        if bd_uv:
            uv = bd_uv.text.encode('utf-8').replace(',', '')
        bd_ip = browser.find_element_by_xpath("//tr[@id='table-tr_1']/td[@class='number ip_count']/div[@class='td-content']")
        if bd_ip:
            ip = bd_ip.text.encode('utf-8').replace(',', '')

        results_item = {'pv': pv, 'uv':uv, 'ip': ip}
        logging.info('[HOUR] results_item:%s \n', results_item)
        browser.quit()
        return results_item


    def flow_trend_days_and_yesterdayHour(self, browser, irsl_date_h, irsl_date):

        wait = ui.WebDriverWait(browser,120)
        results_item_hour = results_item_day = {}
        try:
            ## 1,
            wait.until(lambda browser: browser.find_element_by_xpath("//tr[@id='site-summary-tr_10835307']/td[@class='table-index']/div/a"))
        except TimeoutException:
            logging.error('click mip.hc.360.com failed')
        browser.find_element_by_xpath("//tr[@id='site-summary-tr_10835307']/td[@class='table-index']/div/a").click()

        try:
            ## 2,
            wait.until(lambda browser: browser.find_element_by_xpath("//span[@class='trend']/a[@id='event-monitor-yesterday']"))
        except TimeoutException:
            logging.error('click flow trend today failed')
        browser.find_element_by_xpath("//span[@class='trend']/a[@id='event-monitor-yesterday']").click()

        time.sleep(5)
        bd_pv = browser.find_element_by_xpath("//tr[@id='table-tr_0']/td[@class='number group pv_count']/div[@class='td-content']")
        if bd_pv:
            pv = bd_pv.text.encode('utf-8').replace(',', '')
        bd_uv = browser.find_element_by_xpath("//tr[@id='table-tr_0']/td[@class='number visitor_count']/div[@class='td-content']")
        if bd_uv:
            uv = bd_uv.text.encode('utf-8').replace(',', '')
        bd_ip = browser.find_element_by_xpath("//tr[@id='table-tr_0']/td[@class='number ip_count']/div[@class='td-content']")
        if bd_ip:
            ip = bd_ip.text.encode('utf-8').replace(',', '')

        results_item_hour = {'pv': pv, 'uv':uv, 'ip': ip}
        logging.info('[HOUR_DAY] results_item_hour:%s \n', results_item_hour)
        time.sleep(2)

        ## spider yesterday sum
        sum_pv_xpath = browser.find_element_by_xpath("//td[1]/div[@class='value summary-ellipsis']")
        if sum_pv_xpath:
            sum_pv = sum_pv_xpath.text.encode('utf-8').replace(',', '')
        sum_uv_xpath = browser.find_element_by_xpath("//td[2]/div[@class='value summary-ellipsis']")
        if sum_uv_xpath:
            sum_uv = sum_uv_xpath.text.encode('utf-8').replace(',', '')
        sum_ip_xpath = browser.find_element_by_xpath("//td[3]/div[@class='value summary-ellipsis']")
        if sum_ip_xpath:
            sum_ip = sum_ip_xpath.text.encode('utf-8').replace(',', '')

        results_item_day = {'pv': sum_pv, 'uv': sum_uv, 'ip': sum_ip}
        logging.info('[HOUR_DAY] results_item_day:%s \n', results_item_day)

        browser.quit()
        return (results_item_hour, results_item_day)

    def insert_oracle_days(self, results_days, irsl_date, cur, conn):
        try:
            sql_day = "insert into SJPT_REALTIME_STATIC_DAY(id, data_type, data_count, irsl_date) \
                            values(sjpt_realtime_day_seq.nextval, :1, :2, :3)"
            insert_items = []
            if 'ip' in results_days:
                insert_items.append([338, results_days['ip'], irsl_date])
            if 'pv' in results_days:
                insert_items.append([339, results_days['pv'], irsl_date])
            if 'uv' in results_days:
                insert_items.append([340, results_days['uv'], irsl_date])

            cur.executemany(sql_day, insert_items)
            conn.commit()
            logging.info('[DAY] insert_day succeed %s %s', irsl_date, results_days)
        except Exception, e:
            logging.warning('[DAY] insert_day error! %s %s', sql_day, str(e))

    def insert_oracle_hours(self, results_items, irsl_date_h, cur, conn):
        try:
            sql = "insert into SJPT_REALTIME_STATIC_HOUR(id, data_type, data_count, irsl_date_h) \
                    values(sjpt_realtime_seq.nextval, :1, :2, :3)"
            insert_items = []
            if 'ip' in results_items:
                insert_items.append([338, results_items['ip'], irsl_date_h])
            if 'pv' in results_items:
                insert_items.append([339, results_items['pv'], irsl_date_h])
            if 'uv' in results_items:
                insert_items.append([340, results_items['uv'], irsl_date_h])

            cur.executemany(sql, insert_items)
            conn.commit()
            logging.info('[HOUR] insert_hour succeed %s %s', irsl_date_h, results_items)
        except Exception, e:
            logging.warning('[HOUR] insert_hour error! %s %s', sql, str(e))

    def irsl_date_h(self):
        today = time.strftime('%Y-%m-%d')
        time_now = datetime.datetime.now()
        one_hour = datetime.timedelta(hours=1)
        irsl_h = time_now - one_hour
        foward_hour = str(irsl_h.hour)
        if len(foward_hour) == 1:
            foward_hour = '0' + foward_hour
        irsl_date_h = ''.join(today.split('-')) + foward_hour
        return irsl_date_h

    def irsl_date(self):
        ## yesterday time ex: 2018-04-10
        today = datetime.date.today()
        one = datetime.timedelta(days=1)
        yesterday = today - one
        yesterday = yesterday.strftime('%Y-%m-%d')
        ## yesterday time ex:20180410
        irsl_date = ''.join(yesterday.split('-'))

        ## yesterday 23:00-23:59 ex:2018041023
        time_now = datetime.datetime.now()
        one_hour = datetime.timedelta(hours=23)
        irsl_d = time_now + one_hour
        irsl_date_h = ''.join(yesterday.split('-')) + str(irsl_d.hour)

        return (irsl_date_h, irsl_date)

if __name__ == '__main__':
    
    dirname = os.path.split(os.path.abspath(sys.argv[0]))[0]
    log_file = dirname + '/logs/baidu_tongji_hours.log'
    logInit(log_file, logging.INFO, True, 0)
    
    logging.info('[BAIDU_TONGJI] start fetch baidu tongji date ')

    crawler = BaiduCrawler()

    spider_hour = spider_day = False
    while True:
        db_oracle_str = 'behavior/iSo1gO2HoMe@192.168.245.31:7783/behaviorlog1'
        conn = cx_Oracle.connect(db_oracle_str)
        cur = conn.cursor()
        if time.strftime('%H:%M') == '00:20':
            if spider_day:
                time.sleep(60)
                continue
            browser = get_baidu_tongji_cookie("spiderhc360", "HCsearch2014", '18210607604')
            time.sleep(2)
            irsl_date_h, irsl_date = crawler.irsl_date()
            results_items_hour, results_items_day = crawler.flow_trend_days_and_yesterdayHour(browser, irsl_date_h, irsl_date)
            crawler.insert_oracle_hours(results_items_hour,irsl_date_h, cur, conn)
            time.sleep(2)
            crawler.insert_oracle_days(results_items_day, irsl_date, cur, conn)
            logging.info('[HOUR_DAY] end fetch baidu tongji date')
            spider_day = True
            continue
        elif datetime.datetime.now().minute == 20:
            if spider_hour:
                time.sleep(60)
                continue
            browser = get_baidu_tongji_cookie("spiderhc360", "HCsearch2014", '18210607604')
            time.sleep(2)
            irsl_date_h = crawler.irsl_date_h()
            results_items = crawler.flow_trend_hour(browser)
            crawler.insert_oracle_hours(results_items, irsl_date_h, cur, conn)
            logging.info('[HOUR] end fetch baidu tongji date')
            cur.close()
            conn.close()
            spider_hour = True
            continue
        else:
            spider_hour = False
            spider_day = False
            logging.info('[BAIDU_TONGJI] no time to spider')
        conn.close()
        time.sleep(60)
