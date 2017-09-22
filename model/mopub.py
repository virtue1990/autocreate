# -*- coding:utf-8 -*-
import time
import signal
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from login import WebOperation
from login import HandleException
from collections import defaultdict
from selenium.common.exceptions import WebDriverException
from utils import logger
from utils import headers
from utils import write_csv_data


class MopubModel(WebOperation):
    def __init__(self, email, password):
        super(MopubModel, self).__init__()
        self.email = email
        self.password = password
        self.result = defaultdict(list)
        self.init_config()

    def init_config(self):
        self.vendor_name = 'mopub'
        self.url = 'https://app.mopub.com/inventory/'

    @HandleException.retry_count
    def login_website(self, username, password):
        try:
            self.driver.get(self.url)
            # input the email
            value = 'id_username'
            el = self.find_by_id(value)
            res = self.send_keys(el, username)
            if not res:
                raise Exception('mopub login input username error')

            # input the password
            value = 'id_password'
            el = self.find_by_id(value)
            res = self.send_keys(el, password)
            if not res:
                raise Exception('mopub login input password error')

            # click the login button
            value = 'login-submit'
            el = self.find_by_id(value)
            res = self.click(el)
            if not res:
                raise Exception('mopub login submit failed')
            return True
        except Exception, e:
            logger.error('mopub login,errinfo:{}'.format(e.message))
            return False

    @HandleException.retry_count
    def delete_all(self):
        self.go_to_app_url(self.app_id)
        value = '//td[@class="name"]/a'
        success_count = 0
        els = self.find_by_xpath(value, multi=True)
        if not els:
            logger.info('app %s has wrong or is empty' % self.app_id)
            return True
        length = len(els)
        for _ in range(length):
            try:
                self.go_to_app_url(self.app_id)
                value = '//td[@class="name"]/a'
                el = self.find_by_xpath(value)
                try:
                    link_url = el.get_attribute('href')
                    self.driver.get(link_url)
                except Exception, e:
                    logger.error('mopub delete all,errinfo:{}'.format(e.message))
                    raise Exception('mopub find one ad click failed')

                # find the edit button
                value = 'dashboard-apps-editAdUnitButton'
                el = self.find_by_id(value)
                res = self.click(el)
                if not res:
                    raise Exception('mopub edit button click failed')

                # find the delete button
                try:
                    value = '//button[@href="#delete-modal"]'
                    el = self.find_by_xpath(value)
                    action = webdriver.ActionChains(self.driver)
                    action.move_to_element(el).perform()
                    action.move_by_offset(0, -5).click().perform()
                except Exception, e:
                    logger.error(e)
                    raise Exception('mopub click delete button faild')

                # confirm the delete button
                try:
                    value = 'confirm-delete-button'
                    el = self.find_by_id(value)
                    action = webdriver.ActionChains(self.driver)
                    action.move_to_element(el).click().perform()
                except Exception, e:
                    logger.error(e)
                    raise Exception('moput click confirm delete button failid')
            except Exception, e:
                logger.error('mopub delete error,errinfo:{}'.format(e.message))
            else:
                success_count += 1
        logger.info('success count,count:{}'.format(success_count))
        return True

    def get_unit_type_index(self, ad_type):
        ad_map = {
            'Fullscreen': 0,
            'Medium': 1,
            'Banner': 2,
            'Custom': 3,
            'Native': 4,
            'RewardedVideo': 5,
        }
        return ad_map.get(ad_type, 1)

    @HandleException.retry_count
    def create(self, ad_type, ad_name):
        try:
            # find create button and click
            value = 'dashboard-apps-addAdUnitButton'
            el = self.find_by_id(value, timeout=20)
            res = self.click(el)
            if not res:
                logger.error('mopub can not find the create button')
                el = self.find_by_id(value, timeout=20)
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                except Exception, e:
                    raise Exception('mopub can not click the create button')

            # find option by index,the last one
            try:
                value = '//select[@id="adunit-device_format-field"][@name="format"]'
                index = self.get_unit_type_index(ad_type)
                el = self.find_by_xpath(value)
                action = Select(el)
                action.select_by_index(index)
            except WebDriverException, e:
                raise Exception('mopub select the ad type faild')

            # input ad_name
            try:
                value = 'adunit-name-field'
                el = self.find_by_id(value, timeout=30)
                el.clear()
                el.send_keys(ad_name)
                action = webdriver.ActionChains(self.driver)
                action.move_to_element(el).perform()
                action.move_by_offset(40, 50).click().perform()
            except Exception, e:
                raise Exception('mopub input username failed')

            # click the save button
            value = 'adunit-form-modal-submit'
            el = self.find_by_id(value)
            self.driver.execute_script("arguments[0].click();", el)
            time.sleep(5)  # wait for click succeed
        except Exception, e:
            logger.error('mopub adunit-form-modal-submit,errinfo:{}'.format(e.message))
            self.go_to_app_url(self.app_id)
            return False
        else:
            self.go_to_app_url(self.app_id)
            value = 'dashboard-apps-addAdUnitButton'
            el = self.find_by_id(value)
            if not el:
                logger.error('mopub end dashboard-apps-addAdUnitButton not find')
            logger.info('mopub create id success')
            return True

    @HandleException.retry_count
    def go_to_app_url(self, app_id):
        url = '/'.join([self.url.strip('/'),'app',app_id])
        try:
            self.driver.get(url)
            value = 'dashboard-apps-addAdUnitButton'
            el = self.find_by_id(value, timeout=30)
            if not el:
                raise Exception('mopub go to home url failed')
            return True
        except Exception, e:
            logger.error('mopub go to app_url error,errinfo:{}'.format(e.message))
            return False

    def go_to_home_url(self):
        try:
            self.driver.get(self.url)
        except Exception, e:
            logger.error('mopub app go home url error,errinfo:{}'.format(e.message))

    @HandleException.retry_count
    def get_unit_id_by_name(self, names=None):
        data = dict()
        self.go_to_app_url(self.app_id)
        for name in names:
            els = self.find_by_link_text(name, multi=True, timeout=30)
            for el in els:
                temp = el.get_attribute('href')
                app_unid = temp.split('key=')[1].strip()
                data[app_unid] = name
        logger.info('mopub print the ids,{}'.format(data))
        return data

    @HandleException.retry_count
    def get_apps_id(self):
        data = dict()
        try:
            self.driver.get(self.url)
            value = '//div/a[contains(@href,"/app?key")]'
            els = self.find_by_xpath(value, multi=True)
            for el in els:
                name = el.text
                href = el.get_attribute('href')
                app_id = href.split('key=')[1]
                data[app_id] = name
        except Exception, e:
            logger.error('mopub get apps id some error,errinfo:{}'.format(e.message))
        else:
            logger.info('mopub get apps id success,{}'.format(data))
        return data

    def get_all_units(self):
        data = dict()
        try:
            value = '//td[@class="name"]/a[contains(@href,"/ad-unit?key=")]'
            els = self.find_by_xpath(value, timeout=30, multi=True)
            for el in els:
                href = el.get_attribute('href')
                unit_id = href.split('key=')[1]
                unit_name = el.text
                data[unit_name] = unit_id
        except Exception, e:
            logger.error('mopub get units id error,errinfo:{}'.format(e.message))
        else:
            logger.info('mopub get units id success')
        return data

    def close(self):
        try:
            self.driver.quit()
            logger.info('mopub close successfull')
        except Exception, e:
            logger.error('mopub close driver failded,errinfo:{}'.format(e.message))
            self.driver.service.process.send_signal(signal.SIGTERM)

    def start(self, data):
        assert isinstance(data, list)
        self.login_website(self.email, self.password)
        result_data = dict()
        for item in data:
            self.app_id = item.get('app_id')
            self.go_to_app_url(self.app_id)
            pre_data = self.get_all_units()
            tasks = item.get('task') or []
            new_names = []
            for task in tasks:
                if not task or task in pre_data.keys():
                    continue
                ad_type = task.split(' ')[2]
                res = self.create(ad_type, task)
                if not res:
                    self.create(ad_type, task)
                new_names.append(task)
            aft_data = self.get_all_units()
            temp_result = {name: aft_data.get(name) for name in tasks}
            result_data.update(temp_result)
        self.save_units_id(result_data)

    def delete(self, data):
        assert isinstance(data, list)
        self.login_website(self.email, self.password)
        for item in data:
            self.app_id = item.get('app_id')
            self.go_to_app_url(self.app_id)
            self.delete_all()
        return True

    def save_units_id(self, data):
        result = list()
        for name, unit_id in data.iteritems():
            temp = dict(zip(headers, [self.email, self.vendor_name, name, unit_id]))
            result.append(temp)
        write_csv_data(result)

