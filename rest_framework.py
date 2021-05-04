import time
import random
import asyncio
from aiohttp import web
import requests
import aiohttp_debugtoolbar
import aiohttp
import itertools
from decimal import Decimal
import threading
import concurrent.futures
from aiohttp_debugtoolbar import toolbar_middleware_factory
import time, requests
import datetime
import xml.etree.ElementTree as ET
import sys
import argparse

import logging
from typing import Any, AsyncIterator, Awaitable, Callable, Dict
import traceback


class RestFrame:
    stack = []
    currencies = []
    currency_data = {}
    period = None
    app = None
    log_level = 'INFO'
    logger = None

    def __init__(self, list_currency, script_args, logger):
        self.currencies = list(filter(lambda x: x.startswith('--') and not x.startswith('--help'), list_currency))
        for key in self.currencies:
            self.currency_data[key.replace('-', '')] = {
                'prev_value': script_args.__dict__[key.replace('-', '')],
                'prev_rate': None,
                'current_value': script_args.__dict__[key.replace('-', '')],
                'current_rate': None,
            }
        if script_args.__dict__['debug'] in ('1', 'true', 'True', 'y', 'Y', 'N'):
            self.log_level = 'DEBUG'
        self.logger = logger
        self.period = script_args.__dict__['period']
        self.currencies = [key for key, value in self.currency_data.items()]
        self.currencies.remove('rub')
        self.app = self.init()

    @staticmethod
    def createParser(list_currency):
        parser = argparse.ArgumentParser(description='Process some integers.')
        if '--debug' in list_currency:
            list_currency.remove('--debug')
        if '--period' in list_currency:
            list_currency.remove('--period')
        for item in list_currency:
            if item.startswith('--') and not item.startswith('--help'):
                parser.add_argument(item, type=float)
        parser.add_argument('--debug')
        parser.add_argument('--period', type=int)
        return parser

    async def health(self, request):
        return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>", content_type='text/html')

    async def amount_get(self, request):
        txt = 'amount currencies'
        for key in self.currencies:
            txt = txt + ' / ' + key + ': ' + str(self.currency_data[key]['current_value'])
        txt = txt + '\ncurrencies rate'
        for key in self.currencies:
            txt = txt + ' / ' + 'rub-' + key + ': ' + str(round(float(self.currency_data[key]['current_rate']), 2))
        txt = txt + '\ncurrencies rate relation'
        combinations = list(itertools.combinations(self.currencies, r=2))
        for (keyf, keys) in combinations:
            txt = txt + ' / ' + keyf + '-' + keys + ' ' + \
                  str(round(float(self.currency_data[keyf]['current_rate']) / float(self.currency_data[keys]['current_rate']),2))
        txt = txt + '\nsum:'
        sum_rub = 0
        for key in self.currencies:
            sum_rub = sum_rub + float(self.currency_data[key]['current_rate']) * \
                      float(self.currency_data[key]['current_value'])
        sum_rub = round(sum_rub, 2)
        txt = txt + ' / ' + 'rub ' + str(sum_rub)
        for key in self.currencies:
            txt = txt + ' / ' + key + ' ' + str(round(sum_rub / float(self.currency_data[key]['current_rate']), 2))
        # txt = str([(key, value) for key, value in self.currency_data.items()])
        self.logger.debug('end handle request /amount/get')
        return web.Response(text=txt, content_type='text/plain')

    async def amount_set(self, request):
        try:
            data = await request.json()
            for key, value in data.items():
                self.currency_data[key]['prev_value'], self.currency_data[key]['current_value'] = \
                    self.currency_data[key]['current_value'], value
            txt = str([(key, value) for key, value in self.currency_data.items()])
        except Exception as e:
            self.logger.debug(request + 'handled request /amount/get')
        return web.Response(text=txt, content_type='text/plain')

    async def modify_currency(self, request):
        data = await request.json()
        for key, value in data.items():
            self.currency_data[key]['prev_value'], self.currency_data[key]['current_value'] = \
                self.currency_data[key]['current_value'], value + self.currency_data[key]['current_value']
        txt = str([(key, value) for key, value in self.currency_data.items()])
        self.logger.debug('handle request ' + str(request))
        return web.Response(text=txt, content_type='text/plain')

    async def set_currency(self, request):
        name = request.match_info.get('name', 'usd')
        txt = "Hello, {}".format(name)
        data = await request.json()
        for key, value in data.items():
            self.currency_data[key] = value
        return web.Response(text=txt)

    async def get_currency(self, request):
        name = request.match_info.get('name', 'usd')
        txt = "Currency rate: {} {}".format(name, self.currency_data[name]['current_rate'])
        return web.Response(text=txt)

    async def control_data(self):
        self.logger.info('Check changing data value or rates')
        print_now = False
        for key in self.currencies:
            if self.currency_data[key]['current_rate'] != self.currency_data[key]['prev_rate'] or \
                    self.currency_data[key]['current_value'] != self.currency_data[key]['prev_value']:
                self.currency_data[key]['prev_value'] = self.currency_data[key]['current_value']
                print_now = True
        if print_now:
            response = await self.amount_get(request=None)
            self.logger.debug(response.body.decode("utf-8"))
            print(response.body.decode("utf-8"))

    async def send_request_to_data(self, session):
        self.logger.info('Update data about currencies rate')
        async with session.get(url="https://www.cbr-xml-daily.ru/daily_utf8.xml", ) as response:
            string_xml = await response.text()
        root = ET.fromstring(string_xml)
        for key in self.currencies:
            self.currency_data[key]['prev_rate'], self.currency_data[key]['current_rate'] = \
                self.currency_data[key]['current_rate'], root.findall(".*[CharCode='" + key.upper() + "']/Value")[0].text.replace(",", ".")

    async def start_schedul(self):
        headers = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                self.logger.info('Start receiving data about currency schedule')
                await self.send_request_to_data(session)
            except Exception as ex:
                self.logger.error(traceback.format_exc())
            while True:
                try:
                    await self.send_request_to_data(session)
                except Exception as ex:
                    self.logger.error(traceback.format_exc())
                await asyncio.sleep(self.period - datetime.datetime.now().second % self.period)

    async def start_control_schedul(self):
        self.logger.info('start control data on changing')
        await asyncio.sleep(10)
        while True:
            await asyncio.sleep(5 - datetime.datetime.now().second % 5)
            try:
                await self.control_data()
            except Exception as ex:
                self.logger.error(traceback.format_exc())

    @web.middleware
    async def error_middleware(self, request: web.Request, handler: Callable[[web.Request], Awaitable[web.StreamResponse]],) -> web.StreamResponse:
        try:
            self.logger.info(request)
            return await handler(request)
        except web.HTTPException:
            self.logger.error(traceback.format_exc())
        except asyncio.CancelledError:
            self.logger.error(traceback.format_exc())
        except Exception as ex:
            self.logger.error(traceback.format_exc())

    def init(self):
        app = web.Application(middlewares=[self.error_middleware])
        app.router.add_get("/", self.health)
        app.router.add_get("/amount/get", self.amount_get)
        app.router.add_post("/amount/set", self.amount_set)
        app.router.add_get("/{name}/get", self.get_currency)
        app.router.add_post("/{name}/set", self.set_currency)
        app.router.add_post("/modify", self.modify_currency)
        aiohttp_debugtoolbar.setup(app)
        return app

    async def start_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        self.logger.info("======= Serving on http://127.0.0.1:8080/ ======")
        print("======= Serving on http://127.0.0.1:8080/ ======")
        await asyncio.Event().wait()

    async def main(self):
        self.logger.info('Start event loop')
        await asyncio.gather(
            self.start_schedul(),
            self.start_server(),
            self.start_control_schedul(),
            # web._run_app(self.app, port=8000),
        )


def configure_log(log_level='DEBUG'):
    logfile = './logs/log_'+str(datetime.date.today())+'.log'
    log = logging.getLogger("my_log")
    log.setLevel(logging.__dict__[log_level])
    FH = logging.FileHandler(logfile)
    basic_formater = logging.Formatter('%(asctime)s : [%(levelname)s] : %(message)s')
    FH.setFormatter(basic_formater)
    log.addHandler(FH)
    return log


if __name__ == "__main__":
    logger = configure_log()
    list_currency = sys.argv[1:]
    parser = RestFrame.createParser(list_currency=list_currency)
    script_args = parser.parse_args(sys.argv[1:])
    if script_args.__dict__['debug'] in ('1', 'true', 'True', 'y', 'Y', 'N'):
        logger = configure_log('DEBUG')
    rest_obj = RestFrame(list_currency=list_currency, script_args=script_args, logger=logger)
    asyncio.run(rest_obj.main())
    logger.info("Script Completed")
