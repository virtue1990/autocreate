# -*- coding:utf-8 -*-
import csv
import yaml
import os
import logging 
logging.basicConfig(filename='autocreate.log',filemode='w',level=logging.DEBUG)
logger = logging

headers = ['account', 'platform', 'adunit', 'id']


from selenium import webdriver

def get_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    return driver

def read_config(path=''):
    try:
        if not path:
            raise Exception('path can not be None')
        with open(path, 'r') as f:
            data = yaml.load(f.read())

        return data
    except Exception, e:
        logger.info(e)
        return None


def read_floor_config(path=''):
    try:
        if not path:
            raise Exception('floor path can not be None')
        with open(path,'r') as f:
            data = yaml.load(f.read())
        return data
    except Exception,e:
        logger.info(e)
        return None

def write_csv_header(columns=None, file_name=''):
    try:
        temp_headers = columns if columns else headers
        file_name = file_name if file_name else 'id.csv'

        with open(file_name, 'w+') as f:
            f_csv = csv.DictWriter(f, temp_headers)
            f_csv.writeheader()
        logger.info('write headers success')
        return True
    except Exception, e:
        logger.info('write headers failed')
        logger.info(e)
        return False


def write_csv_data(data=None, path=''):
    """
    :param
        data contains the need info
        [
        {
            'account': 'ads.blowfire',
            'platform': 'adx',
            'adunit': 'Test_A [GA Native TestforAdmob]',
            'id': 'xxxxx'
        },
        ...
        ]
    """
    try:
        if not data:
            raise Exception('the params data is None')
        if not path:
            path = 'id.csv'
        if not os.path.exists(path):
            write_csv_header(file_name=path)
        temp_headers = data[0].keys()
        with open(path, 'a+') as f:
            f_csv = csv.DictWriter(f, temp_headers)
            f_csv.writerows(data)
        return True
    except Exception, e:
        logger.info('write data failed')
        logger.info(e)
        return False
