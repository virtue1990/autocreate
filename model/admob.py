# -*- coding:utf-8 -*-
import signal
import time
from login import WebOperation
from login import HandleException
from selenium import webdriver
from collections import defaultdict
from utils import logger 
from utils import headers
from utils import write_csv_data


class AdmobModel(WebOperation):
    def __init__(self, email, password):
        self.unit_ids = defaultdict(dict)
        self.email = email
        self.password = password
        super(AdmobModel, self).__init__()

    @property
    def ad_map(self):
        """
        return the ad type collection
        """
        data = {
            'Banner': 'Banner',
            'MediumRectangle': 'Banner',
            'Interstitial': 'Interstitial',
            'RewardedVideo': 'Rewarded video',
            'NativeExpress': 'Native',
            'Native': 'Native'
        }
        return data

    @property
    def home_url(self):
        return 'https://apps.admob.com/#monetize/app:view/id={}'

    @property
    def create_url(self):
        return 'https://apps.admob.com/#monetize/app:create/id={}'

    @property
    def account_id(self):
        account_id = self.__dict__.get('account_id')
        if account_id:
            return account_id
        try:
            # get the account id from web page
            value = '//li[contains(text(),"Publisher ID: ")]'
            el = self.find_by_xpath(value)
            text = el.text.split(':')[1].strip()
            self.__dict__['account_id'] = text
            return text
        except Exception, e:
            logger.error('admob get account_id error,errorinfo:{}'.format(e.message))
            return ''

    def get_all_units(self):
        # now only can get the first page,if
        # have more than one page,not found the method

        self.driver.get(self.home_url.format(self.app_id))
        try:
            data = dict()
            while 1:
                value = '//div[contains(text(),"Ad unit ID")]'
                els = self.find_by_xpath(value, timeout=30, multi=True)
                unit_ids = [el.text.split(':')[1].strip() for el in els]

                value = '//div/a[@href="javascript:;"][@id]'
                els = self.find_by_xpath(value, timeout=30, multi=True)
                unit_names = [el.text for el in els]

                temp = dict(zip(unit_names[1:], unit_ids))
                data.update(temp)

                res = self.turn_page()
                if not res:
                    break
            return data
        except Exception, e:
            logger.error('admob get units error,errinfo:{}'.format(e.message))
            return {}

    @HandleException.retry_count
    def login_website(self):
        return self.login_google(self.email, self.password)

    @HandleException.retry_count
    def create(self, app_id, ad_type, ad_name):
        self.driver.get(self.home_url.format(app_id))
        try:
            # click the button
            value = '//div[contains(text(),"New ad unit")]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob new ad unit click failed')

            # select the ad type
            ad_type = self.ad_map.get(ad_type)
            value = '//div[text()="{}"]'.format(ad_type)
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob select ad type failed')

            # find the input box
            value = '//div/input[@type="text"][@class="gwt-TextBox"][@maxlength="80"]'
            els = self.find_by_xpath(value, multi=True)
            res = self.send_keys(els[-1], ad_name)
            if not res:
                raise Exception('admob input name failed')

            # click save button
            value = '//div[text()="Save"]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob save failed')

            # get the ad unit id
            value = '//span[contains(text(),"ca-app-{}")]'.format(self.account_id)
            el = self.find_by_xpath(value, timeout=30)
            self.unit_ids[app_id][ad_name] = el.text

            # click the Done button
            value = '//div[text()="Finished"]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob done click failed')
            return True
        except Exception, e:
            logger.error('create,errinfo:{}'.format(e.message))
            return False

    @HandleException.retry_count
    def create_native_advanced_unit_id(self, app_id, ad_name):
        try:
            self.driver.get(self.home_url.format(app_id))
            # click the new add unit button
            value = '//div[contains(text(),"New ad unit")]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob new ad unit click failed')

            # click the Native ad type
            ad_type = 'Native'
            value = '//div[text()="{}"]'.format(ad_type)
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob select ad type failed')

            # switch to the native advanced
            value = '//a[contains(text(),"Switch to Native Ads Advanced")]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('admob switch to native ads advanced faild')

            # find the input box
            value = '//div/input[@type="text"][@class="gwt-TextBox"][@maxlength="80"]'
            els = self.find_by_xpath(value, timeout=30, multi=True)
            res = self.send_keys(els[-1], ad_name)
            if not res:
                raise Exception('admob input name faild')

            # click save button
            value = '//div[text()="Save"]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob save failed')

            # get the ad unit id
            value = '//span[contains(text(),"ca-app-{}")]'.format(self.account_id)
            el = self.find_by_xpath(value)
            self.unit_ids[app_id][ad_name] = el.text

            # click the Done button
            value = '//div[text()="Finished"]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob finished click failed')
            return True
        except Exception, e:
            logger.error('create_native_advanced_unit_id,errinfo:{}'.format(e.message))
            return False

    @HandleException.retry_count
    def create_native_unit_id(self, app_id, ad_name):
        try:
            self.driver.get(self.home_url.format(app_id))
            # click the new add unit button
            value = '//div[contains(text(),"New ad unit")]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('admob new ad unit click failed')

            # click the Native ad type
            ad_type = 'Native'
            value = '//div[text()="{}"]'.format(ad_type)
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('admob select ad type failed')

            # select the ad type size
            value = '//div[contains(text(),"Small")]'
            el = self.find_by_xpath(value)
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(el)
            action.move_by_offset(0, -40).click().perform()

            # select the ad type template
            value = '//div[contains(text(),"Template ID: S001")]'
            el = self.find_by_xpath(value)
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(el)
            action.move_by_offset(0, -20).click().perform()

            # need enouht time to validate the config
            time.sleep(5)
            value = '//div[contains(text(),"Validate style")]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                logger.error('admob validate failed, later click save may be succeed')

            # find the input box
            value = '//div/input[@type="text"][@class="gwt-TextBox"][@maxlength="80"]'
            els = self.find_by_xpath(value, multi=True)
            res = self.send_keys(els[-1], ad_name)
            if not res:
                raise Exception('admob input ad name failed')

            # click save button
            value = '//div[text()="Save"]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob save failed')

            # get the ad unit id
            value = '//span[contains(text(),"ca-app-{}")]'.format(self.account_id)
            el = self.find_by_xpath(value)
            self.unit_ids[app_id][ad_name] = el.text

            # click the Done button
            value = '//div[text()="Finished"]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('admob done click failed')
            return True
        except Exception, e:
            logger.error('admob create_native_unit_id,errinfo:{}'.format(e.message))
            return False

    @HandleException.retry_count
    def update_floor(self, unit_id, floor=0.05):
        try:
            # go to the app url
            home_url = self.home_url.format(self.app_id)
            self.driver.get(home_url)
            value = '//div/a[contains(text(),"1 ad source")]'
            el = self.find_by_xpath(value, timeout=15)

            # base on the unit_id create url
            special_id = unit_id.split('/')[1]
            app_id_url = 'https://apps.admob.com/#monetize/adunit:mediate/id={}'.format(special_id)
            self.driver.get(app_id_url)

            # click the AdMob Network
            value = '//span/a[contains(text(),"AdMob Network")]'
            el = self.find_by_xpath(value)
            res = self.click(el)
            if not res:
                raise Exception('admob update floor admob network click failed')


            # find the input Enable eCPM floor
            info = "Enable eCPM floor for the AdMob Network"
            value = '//div[contains(text(),"%s")]' % info
            el = self.find_by_xpath(value)

            value = '../../div/div[@role="checkbox"]'
            check = el.find_element_by_xpath(value)
            if check.get_attribute('aria-checked') == 'false':
                check.click()

            input = el.find_element_by_xpath('./div/div/div/input')
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(input).perform()
            action.double_click().perform()
            action.send_keys(str(floor)).perform()

            # find continue button
            time.sleep(1)
            value = '//div[contains(text(),"Continue")]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob click continue button failed')

            # find save button
            value = '//div/div[contains(text(),"Save")]'
            el = self.find_by_xpath(value, timeout=30)
            action = webdriver.ActionChains(self.driver)
            action.move_to_element(el).click().perform()

            # finish
            # click the cancel button for quickly redirect the web
            time.sleep(2)
            value = '//div/div[contains(text(),"Cancel")]'
            el = self.find_by_xpath(value, timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('admob click cancel button failed')

            return True
        except Exception, e:
            logger.error('admob update floor failed,errinfo:{}'.format(e.message))
            return False

    def turn_page(self):
        # turn on the page when the unit ids bigger than one
        try:
            home_url = self.home_url.format(self.app_id)
            cur_url = self.driver.current_url
            if home_url != cur_url:
                self.driver.get(self.home_url.format(self.app_id))
            value = '//div[contains(text(),"Ad units")]'
            el = self.find_by_xpath(value)
            num = int(el.text.split('(')[1].split(')')[0])
            if num > 15:
                value = '//div/b[contains(text(),"-")]'
                el = self.find_by_xpath(value)
                temp_num = int(el.text.split('-')[1])
                if temp_num < num:
                    value = '//div/b[text()=%s]' % num
                    self.driver.execute_script("window.scrollBy(100,500)")
                    el = self.find_by_xpath(value)
                    action = webdriver.ActionChains(self.driver)
                    action.move_to_element(el)
                    action.move_by_offset(70, 0).click().perform()
                    return True
        except Exception, e:
            logger.error('admob turn page failed,errinfo:{}'.format(e.message))
            return False

    def turn_page_by_id(self):
        # turn the page when the unit ids bigger than one
        # this method not be possible ,because distinct page has different id
        try:
            value = 'gwt-uid-139'
            el = self.find_by_id(value)
            if el and el.get_attribute('disabled'):
                return False
            el.click() if el else ''
            return True
        except Exception,e:
            logger.error('admob turn page by id,errinfo:{}'.format(e.message))
            return False

    def check_floor_status(self, task_id, app_id, unit_id, floor):
        try:
            obj = TaskModel.objects(id=task_id).get()
            items = obj.result.get('items',[])
            for item in items:
                if item.get('app_id') == app_id \
                        and item.get('unit_id') == unit_id \
                        and item.get('floor') == floor:
                    return True
            return False
        except Exception, e:
            logger.error('admob check floor status failed,errinfo:{}'.format(e.message))
            return False

    def close(self):
        try:
            self.driver.quit()
            logger.info('admob close successfull')
        except Exception, e:
            logger.error('admob close driver failded,errinfo:{}'.format(e.message))
            self.driver.service.process.send_signal(signal.SIGTERM)

    def save_units_id(self, data):
        result = list()
        for app_id, units in data.iteritems():
            for name, unit_id in units.iteritems():
                temp = dict(zip(headers, [self.email, 'admob', name, unit_id]))
                result.append(temp)
        write_csv_data(result)

    def start(self, data):
        assert isinstance(data,list)
        self.login_website()
        for item in data:
            self.app_id = item.get('app_id')
            all_units = self.get_all_units()
            logger.info('admob all_units')
            logger.info(all_units)
            for name in item.get('task'):
                if not name or name in all_units.keys():
                    logger.info('admob task has one empty or exists')
                    continue
                try:
                    ad_type = name.split(' ')[2]
                    if ad_type.lower() == 'nativeexpress':
                        res = self.create_native_unit_id(self.app_id,name)
                    elif ad_type.lower() == 'native':
                        res = self.create_native_advanced_unit_id(self.app_id,name)
                    else:
                        res = self.create(self.app_id, ad_type, name)

                    if not res:
                        raise Exception('create unit id failed')
                except Exception,e:
                    logger.info(e.message)

        self.save_units_id(self.unit_ids)

    def set_floor(self, data):
        assert isinstance(data, list)
        self.login_website()
        for item in data:
            self.app_id = item.get('app_id')
            unit_id_list = item.get('task')
            for item in unit_id_list:
                if not item :
                    continue
                unit_id = item.get('unit_id')
                floor = item.get('floor')
                self.update_floor(unit_id, floor)
            logger.info('admob app_id %s create ' % self.app_id)