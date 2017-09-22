# -*- coding:utf-8 -*-
import pprint

from selenium import webdriver

from admob import AdmobModel
from adx import AdxModel
from mopub import MopubModel
from utils import read_config
from utils import read_floor_config
from utils import logger

options = webdriver.ChromeOptions()
options.add_argument('--window-size=1920,1080')


def admob_create(data=None,operation='id'):
    try:
        assert isinstance(data,dict)
        config = data.get('platform',{}).get('admob')
        if not config:
            logger.info('admob do not have configuration info')
        for item in config:
            email = item.get('account', {}).get('email')
            password = item.get('account', {}).get('password')
            admob = AdmobModel(email=email, password=password)
            apps = item.get('app')
            try:
                if operation == 'floor':
                    # config = read_floor_config('./floor.yaml')
                    # temp_apps = config.get('vendor').get('admob')
                    admob.set_floor(apps)
                else:
                    admob.start(apps)
            except Exception,e:
                admob.close()
                logger.info('admob create some error')
                logger.info(e)
            else:
                admob.close()
    except Exception,e:
        logger.info('admob error')
        logger.info(e)



def adx_create(data=None,operation='id'):
    try:
        assert isinstance(data,dict)
        config = data.get('platform',{}).get('adx')
        if not config:
            logger.info('adx do not have configuration info')
        for item in config:
            email = item.get('account', {}).get('email')
            password = item.get('account', {}).get('password')
            adx = AdxModel(email=email, password=password)
            apps = item.get('app')
            try:
                if operation == 'floor':
                    # config = read_floor_config('./floor.yaml')
                    # temp_apps = config.get('vendor').get('adx')
                    adx.set_floor(apps)
                else:
                    adx.start(apps)
    
            except Exception,e:
                adx.close()
                logger.info('create adx id happens error')
                logger.info(e)
            else:
                adx.close()
    except Exception,e:
        logger.info('adx error')
        logger.info(e)



def mopub_create(data=None):
    try:
        assert isinstance(data,dict)
        config = data.get('platform',{}).get('mopub')
        if not config:
            logger.info('mopub do not have configuration info')
        for item in config:
            email = item.get('account',{}).get('email')
            password = item.get('account',{}).get('password')
            mopub = MopubModel(email,password)
            apps = item.get('app')
            try:
                mopub.start(apps)
            except Exception,e:
                mopub.close()
                logger.info('mopub create id happens error')
                logger.info(e)
            else:
                mopub.close()
    except Exception,e:
        logger.info('mopub error')
        logger.info(e)

    
def create_unit_id():
    try:
        data = read_config(path='data/account.yaml')
        admob_create(data)
        adx_create(data)
        mopub_create(data)
    except Exception,e:
        logger.info('create unit id')
        logger.info(e)


def set_floor():
    try:
        data = read_floor_config('data/floor.yaml')
        admob_create(data=data,operation='floor')
        adx_create(data=data,operation='floor')
    except Exception,e:
        logger.info('set floor')
        logger.info(e)


def main():
    create_unit_id()
    # set_floor()