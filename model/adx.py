# -*- coding:utf-8 -*-
import signal
import time
from selenium import webdriver
from login import WebOperation
from login import HandleException
from collections import defaultdict
from selenium.common.exceptions import WebDriverException

from utils import logger
from utils import write_csv_data
from utils import headers


class AdxModel(WebOperation):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.unit_ids = defaultdict(dict)
        self.result = defaultdict(list)
        super(AdxModel, self).__init__()

    def send_keys(self, element, value):
        try:
            element.send_keys(value)
            return True
        except WebDriverException as e:
            logger.error('send_keys,errinfo:{}'.format(e.message))
            return False

    @property
    def home_url(self):
        return 'https://www.google.com/adx/Main.html#INVENTORY/ListTagsPlace:mobile'

    @property
    def account_id(self):
        try:
            self.go_to_home_url()
            value = '//span[contains(text(),"Publisher ID: ")]'
            el = self.find_by_xpath(value)
            text = el.text.split(':')[1].strip()
            return text
        except Exception, e:
            logger.error('adx account id,errinfo:{}'.format(e.message))
            return None

    @HandleException.retry_count
    def go_to_home_url(self):
        try:
            if self.driver.current_url == self.home_url:
                return True
            self.driver.get(self.home_url)
            value = 'new-tag-button'
            el = self.find_by_id(value, timeout=30)
            if not el:
                raise Exception('adx find the new-tag-button failed')

            # ensure the page loading finished
            value = '//a[@class="gwt-Anchor"][@href="javascript:void(0)"]'
            els = self.find_by_xpath(value, timeout=50, multi=True)
            return True
        except Exception, e:
            logger.error(e.message)
            return False

    @HandleException.retry_count
    def login_website(self):
        return self.login_google(self.email, self.password)

    @HandleException.retry_count
    def get_units_id(self):
        data = dict()
        try:
            # get the all ad names,not consider the page bigger than one
            value = '//a[@class="gwt-Anchor"][@href="javascript:void(0)"]'
            els = self.find_by_xpath(value, timeout=50, multi=True)
            for el in els:
                unit_name = el.text
                unit_id = el.get_property('id')
                unit_id = unit_id.split('-')[-1]
                data[unit_name] = 'ca-mb-app-{account_id}/{unit_id}'.format(
                    account_id=self.account_id, unit_id=unit_id)
        except Exception, e:
            logger.error('adx get units id,errinfo:{}'.format(e.message))
        else:
            logger.error('adx get units id success')
        return data

    def get_all_units(self):
        try:
            self.go_to_home_url()
            value = '//a[@class="gwt-Anchor"][@href="javascript:void(0)"]'
            els = self.find_by_xpath(value, timeout=30, multi=True)
            data = dict()
            for el in els:
                link_name = el.text
                link_id = el.get_property('id')
                link_id = link_id.split('-')[-1]
                data[link_name] = link_id
            return data
        except Exception, e:
            logger.error('adx get unit id by names,errinfo:{}'.format(e.message))
            return dict()

    @HandleException.retry_count
    def create(self, ad_name):
        try:
            self.go_to_home_url()
            # find new buton and click
            value = 'new-tag-button'
            el = self.find_by_id(value)
            res = self.click(el)
            if not res:
                raise Exception('adx new tag button click failed')

            # input name
            value = 'name-textbox'
            el = self.find_by_id(value)
            res = self.send_keys(el, ad_name)
            if not res:
                raise Exception('adx input ad name failed')

            # click the save button
            value = '//div[contains(text(),"Save &")]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('adx save click failed')

            # find the name has already used
            value = '//div[contains(text(),"This name is already used")]'
            el = self.find_by_xpath(value, timeout=10)
            if el:
                raise Exception('the name is already used')
            else:
                value = '//div[@role="button"][contains(text(),"Close")]'
                el = self.find_by_xpath(value,timeout=20)
                res = self.click(el)
            return True
        except Exception, e:
            logger.error('adx create unit failed,errinfo:{}'.format(e.message))
            return False

    @HandleException.retry_count
    def get_exist_floor(self):
        # get the exist has set rule
        # return the list contains rules name
        rule_names = list()
        try:
            floor_url = 'https://www.google.com/adx/Main.html#RULES/PricingRuleListPlace:mobile'
            self.driver.get(floor_url)

            # load all the floors
            value = '//div/div[text()="Load All"]' # 不是简单的改造成新的,老的问题需要兼顾
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('adx not find load all button or other error')

            # find all the rule names
            value = '//div/a[contains(@id,"rule-link-")]'
            els = self.find_by_xpath(value, multi=True)
            rule_names = [el.text for el in els]
        except Exception, e:
            logger.error('adx get exist rules error,errinfo:{}'.format(e.message))
        return rule_names

    @HandleException.retry_count
    def create_floor(self, ad_name, floor=0.05):
        # create new floor for ad_name
        try:
            floor_url = 'https://www.google.com/adx/Main.html#RULES/PricingRuleListPlace:mobile'
            self.driver.get(floor_url)
            # find the create button
            value = 'add-new-rule-button'
            el = self.find_by_id(value)
            res = self.click(el)
            if not res:
                raise Exception('adx click add new rule button')

            # input the rule name
            value = 'rule-name'
            el = self.find_by_id(value)
            res = self.send_keys(el, ad_name)
            if not res:
                raise Exception('adx input name failed1')

            # filter the include ad name
            value = '//div/input[@type="text"]'
            els = self.find_by_xpath(value, multi=True)
            res = self.send_keys(els[1], ad_name)
            if not res:
                raise Exception('adx input name failed2')

            # make sure the ad_name is included
            value = '//div/button[contains(text(),"include")]'
            el = self.find_by_xpath(value)
            res = el.click() if el.text != 'include' else 'pass'
            if not res:
                raise Exception('adx click the include failed')

            # find the branded
            value = '//div/span[text()="Branded"]'
            els = self.find_by_xpath(value, multi=True)
            input_el = els[1].find_element_by_xpath('../input')
            res1 = self.click(input_el)
            res2 = self.send_keys(input_el, str(floor))
            if not all([res1, res2]):
                raise Exception('adx input floor failed1')

            # find the anonymous
            value = '//div/span[text()="Anonymous"]'
            els = self.find_by_xpath(value, multi=True)
            input_el = els[1].find_element_by_xpath('../input')
            res1 = self.click(input_el)
            res2 = self.send_keys(input_el, str(floor))
            if not all([res1, res2]):
                raise Exception('adx input floor failed2')

            # move mouse to other place
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(input_el)
            action.move_by_offset(100,100).click().perform()

            # find save button
            value = 'save-button'
            el = self.find_by_id(value)
            res = self.click(el)
            time.sleep(2)
            if not res:
                raise Exception('error in save button')
            return True
        except Exception, e:
            logger.error('adx create floor error,errinfo:{}'.format(e.message))
            return False

    @HandleException.retry_count
    def update_floor(self, ad_name, floor=0.05):
        # base on the ad_name and floor ,set floor
        value = ''
        try:
            floor_url = 'https://www.google.com/adx/Main.html#RULES/PricingRuleListPlace:mobile'
            self.driver.get(floor_url)
            # load all the rules
            value = '//div/div[text()="Load All"]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                logger.error('load all button failed')

            value = '//a[text()="%s"]' % ad_name
            el = self.find_by_xpath(value)
            edit = el.find_element_by_xpath('../../div/div[text()="Edit"]')

            # scroll page to make the element visible
            self.driver.execute_script("arguments[0].scrollIntoView(false);",edit)
            res = self.click(edit)
            if not res:
                raise Exception('adx update floor scroll failed')

            # input the ad name
            value = '//div/input[@type="text"]'
            els = self.find_by_xpath(value, timeout=60, multi=True)
            res = self.send_keys(els[1], ad_name)
            if not res:
                raise Exception('adx input ad name failed')

            # make sure the ad_name is include
            value = '//div/button[contains(text(),"include")]'
            el = self.find_by_xpath(value)
            res = self.click(el) if el.text == 'include' else 'pass'
            if not res:
                raise Exception('adx update floor click include failed')

            # find the branded
            value = '//div/span[text()="Branded"]'
            els = self.find_by_xpath(value, multi=True)
            el = els[1]
            input_el = el.find_element_by_xpath('../input')
            res1 = self.click(input_el)
            res2 = self.send_keys(input_el, str(floor))
            if not all([res1, res2]):
                raise Exception('adx update floor failed1')

            # find the anonymous
            # now has a bug,floor set invalid
            value = '//div/span[text()="Anonymous"]'
            els = self.find_by_xpath(value, multi=True)
            el = els[1]
            input_el = el.find_element_by_xpath('../input')
            res1 = self.click(input_el)
            res2 = self.send_keys(input_el, str(floor))
            if not all([res1, res2]):
                raise Exception('adx update floor failed2')

            # move mouse to other place
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(input_el)
            action.move_by_offset(100, 100).click().perform()

            # find save button
            value = 'save-button'
            el = self.find_by_id(value)
            self.driver.execute_script('window.scrollBy(-200,0)')
            res = self.click(el)
            if not res:
                raise Exception('adx update floor save button failed')
            return True
        except Exception,e:
            logger.error('adx set floor error,value:{},errinfo:{}'.format(value,e.message))

    def check_floor_status(self, task_id, unit_name, floor):
        try:
            obj = TaskModel.objects(id=task_id).get()
            items = obj.result.get('items',[])
            for item in items:
                if item.get('unit_name') == unit_name \
                        and item.get('floor') == floor:
                    return True
            return False
        except Exception, e:
            logger.error('adx check floor status failed,errinfo:{}'.format(e.message))
            return False

    def save_units_id(self, data):
        result = list()
        for name, unit_id in data.iteritems():
            temp = dict(zip(headers, [self.email, 'adx', name, unit_id]))
            result.append(temp)
        write_csv_data(result)

    def close(self):
        try:
            self.driver.quit()
            logger.info('adx close successfull')
        except Exception,e:
            logger.error('adx close driver failded,errinfo:{}'.format(e.message))
            self.driver.service.process.send_signal(signal.SIGTERM)

    def start(self, data=None):
        assert isinstance(data, dict)
        result = {}
        create_names = data.get('task') or []
        self.login_website()
        self.go_to_home_url()
        exist_names = self.get_all_units()
        un_create_names = list(set(create_names) - set(exist_names.keys()))
        for name in un_create_names:
            self.create(name)
        units = self.get_all_units()
        for name in create_names:
            result[name] = units.get(name)

        self.save_units_id(result)

    def set_floor(self, data=None):

        self.login_website()
        exist_floor = self.get_exist_floor()
        count = 0
        while not exist_floor and count < 3:
            time.sleep(5)
            exist_floor = self.get_exist_floor()

        tasks = data.get('task')
        for item in tasks:
            ad_name = item.get('ad_name')
            floor = item.get('floor')
            if ad_name not in exist_floor:
                self.create_floor(ad_name, floor)
            else:
                self.update_floor(ad_name, floor)
        logger.info('adx set floor finished')

