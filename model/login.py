# -*- coding:utf-8 -*-
import time
from functools import wraps
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from utils import get_driver
from utils import logger


class WebOperation(object):
    def __init__(self):
        self.driver = get_driver()

    def click(self, element):
        try:
            time.sleep(1)
            element.click()
            return True
        except TimeoutException,e:
            logger.error('click timeout,errinfo:{}'.format(e.message))
            return True
        except WebDriverException as e:
            logger.error('click,errinfo:{}'.format(e.message))
            return False

    def send_keys(self, element, value):
        try:
            element.clear()
            element.send_keys(value)
            return True
        except WebDriverException as e:
            logger.error('send_keys,errinfo:{}'.format(e.message))
            return False

    def find_by_xpath(self, value, timeout=100, multi=False):
        try:
            method = 'xpath'
            if multi:
                # visibility_of_all_elements_located method always timeout
                # so use any at first, second use presence_of_all_elements_located
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_any_elements_located((method, value))
                )

                els = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((method, value))
                )
                return els
            else:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((method, value))
                )
                return el
        except TimeoutException:
            template = ("Waited for element to appear for {sec} seconds, ",
                        "but {type}:{target} didn't appear.")
            msg = "".join(template).format(sec=timeout, type=method, target=value)
            logger.error('find by xpath,errinfo:{}'.format(msg))
            return False
        except Exception, e:
            logger.error('find by xpath,errinfo:{}'.format(e.message))
            return False

    def find_by_id(self, value, timeout=100):
        try:
            method = 'id'
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((method, value))
            )
            return el

        except TimeoutException:
            template = ("Waited for element to appear for {sec} seconds, ",
                        "but {type}:{target} didn't appear.")
            msg = "".join(template).format(sec=timeout, type=method, target=value)
            logger.error('find by id,errinfo:{}'.format(msg))
            return False
        except Exception, e:
            logger.error('find by id,errinfo:{}'.format(e.message))
            return False

    def find_by_name(self, value, timeout=100, multi=False):
        try:
            method = 'name'
            if multi:
                # visibility_of_all_elements_located method always timeout
                # so use any at first, second use presence_of_all_elements_located
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_any_elements_located((method, value))
                )

                els = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((method, value))
                )
                return els
            else:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((method, value))
                )
                return el
        except TimeoutException:
            template = ("Waited for element to appear for {sec} seconds, ",
                        "but {type}:{target} didn't appear.")
            msg = "".join(template).format(sec=timeout, type=method, target=value)
            logger.error('find by name,errinfo:{}'.format(msg))
            return False
        except Exception, e:
            logger.error('find by name,errinfo:{}'.format(e.message))
            return False

    def find_by_link_text(self, value, timeout=100, multi=False):
        try:
            method = 'link_text'
            if multi:
                # visibility_of_all_elements_located method always timeout
                # so use any at first, second use presence_of_all_elements_located
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_any_elements_located((method, value))
                )

                els = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((method, value))
                )
                return els
            else:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((method, value))
                )
                return el
        except TimeoutException:
            template = ("Waited for element to appear for {sec} seconds, ",
                        "but {type}:{target} didn't appear.")
            msg = "".join(template).format(sec=timeout, type=method, target=value)
            logger.error('find by link_text,errinfo:{}'.format(msg))
            return False
        except Exception, e:
            logger.error('find by link_text,errinfo:{}'.format(e.message))
            return False

    def login_google(self, email, password):
        self.url = 'https://accounts.google.com/signin/v2/identifier'
        try:
            if not all([email, password]):
                logger.error('email {email}, password {password}'
                              .format(email=email, password=password))
                raise Exception('email or password is None')
            self.driver.get(self.url)

            # input email
            el = self.find_by_id('identifierId', timeout=20)
            res = self.send_keys(el, email)
            if not res:
                raise Exception('google login_website input email failed')

            # click email next
            el = self.find_by_id('identifierNext',timeout=20)
            res = self.click(el)
            if not res:
                raise Exception('google login_website click email next failed')

            # input password
            el = self.find_by_name('password', timeout=30)
            res = self.send_keys(el, password)
            if not res:
                raise Exception('google login_website input password failed')

            # click email next
            el = self.find_by_id('passwordNext', timeout=30)
            res = self.click(el)
            if not res:
                raise Exception('google login_website click password next failed')

            # make sure login_website success
            value = '//h1[contains(text(),"My Account")]'
            el = self.find_by_xpath(value)
            if not el:
                raise Exception('google login_website failed ,can not find the flag')
            return True

        except Exception, e:
            logger.error('login_website google failed,errinfo:{}'.format(e.message))
            return False


class HandleException(object):
    @classmethod
    def retry_count(cls, func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            count = 0
            status = False
            while not status and count < 3:
                count += 1
                status = func(*args, **kwargs)
            return status
        return decorated_function

