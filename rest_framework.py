import multiprocessing
import time
import random
import asyncio
from aiohttp import web
import requests
import aiohttp_debugtoolbar
import aiohttp
import threading
import concurrent.futures

from aiohttp_debugtoolbar import toolbar_middleware_factory

import time, requests
import datetime
import xml.etree.ElementTree as ET

import sys
import argparse


async def health(request):
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>", content_type='text/html')


async def get_crypto_info(request):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
    response = requests.get(url)
    if response.status_code in [200, 201]:
        return web.Response(text=response.text, contenaioservert_type='application/json')
    else:
        return web.Response(text=str({"status": "failure", "status_code": response.status_code}))


async def hello(request):
    print(request)
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>", content_type='text/html')


async def get_currency(request):
    name = request.match_info.get('name', "Anonymous")
    txt = "Hello, {}".format(name)
    return web.Response(text=txt)
    # return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>", content_type='text/html')


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


class RestFrame:
    stack = []
    currencies = []
    currency_data = {}
    period = None
    app = None

    def __init__(self, list_currency, script_args):
        # for item in list_currency:
        #     if not item.startswith('--') or item.startswith('--help'):
        #         list_currency.remove(item)
        # list_currency.append('--help')
        self.currencies = list(filter(lambda x: x.startswith('--') and not x.startswith('--help'), list_currency))
        for key in self.currencies:
            self.currency_data[key.replace('-', '')] = {
                'prev_value': None,
                'prev_rate': None,
                'current_value': script_args.__dict__[key.replace('-', '')],
                'current_rate': None,
            }
        self.period = script_args.__dict__['period']
        self.currencies = [key for key, value in self.currency_data.items()]
        self.currencies.remove('rub')
        self.app = self.init()

    # rub: 100
    # usd: 200
    # eur: 300
    #
    # rub - usd: 65.5
    # rub - eur: 73.4
    # usd - eur: 1.12
    #
    # sum: 35220.0
    # rub / 537.52
    # usd / 479.93
    # eur
    async def amount_get(self, request):
        txt = str([(key, value) for key, value in self.currency_data.items()])
        return web.Response(text=txt, content_type='text/plain')

    async def amount_set(self, request):
        data = await request.json()
        for key, value in data.items():
            self.currency_data[key]['prev_value'], self.currency_data[key]['current_value'] = \
                self.currency_data[key]['current_value'], value
        txt = str([(key, value) for key, value in self.currency_data.items()])
        return web.Response(text=txt, content_type='text/plain')

    async def modify_currency(self, request):
        data = await request.json()
        for key, value in data.items():
            self.currency_data[key]['prev_value'], self.currency_data[key]['current_value'] = \
                self.currency_data[key]['current_value'], value + self.currency_data[key]['current_value']
        txt = str([(key, value) for key, value in self.currency_data.items()])
        return web.Response(text=txt, content_type='text/plain')

    async def set_currency(self, request):
        name = request.match_info.get('name', "Anonymous")
        txt = "Hello, {}".format(name)
        data = await request.json()
        # self.currency_data['current_rate'] = data['current_data']
        # self.currency_data['prev_rate'] = data['prev_data']
        for key, value in data.items():
            self.currency_data[key] = value
        return web.Response(text=txt)

    async def get_currency(self, request):
        name = request.match_info.get('name', "Anonymous")
        txt = "Hello, {} {}, {}".format(name, self.currency_data[name]['current_rate'], name)
        return web.Response(text=txt)
        # return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>", content_type='text/html')

    def send_post(self):
        response = requests.get("https://www.cbr-xml-daily.ru/daily_utf8.xml")
        string_xml = response.content
        root = ET.fromstring(string_xml)
        # print('USD', root.findall(".*[CharCode='USD']/Value")[0].text, 'EUR',
        #       root.findall(".*[CharCode='EUR']/Value")[0].text)
        for key in self.currencies:
            self.currency_data[key]['prev_rate'], self.currency_data[key]['current_rate'] = \
                self.currency_data[key]['current_rate'], root.findall(".*[CharCode='" + key.upper() + "']/Value")[
                    0].text
            print('print ', key, self.currency_data[key]['current_rate'], datetime.datetime.now())

    async def start_schedul(self):
        while True:
            self.send_post()
            # print(self.currency_data)
            # time.sleep(10 - datetime.datetime.now().second % 10)
            # await asyncio.sleep(1)
            await asyncio.sleep(self.period - datetime.datetime.now().second % self.period)

    def init(self):
        app = web.Application()
        app.router.add_get("/", health)
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
        print("======= Serving on http://127.0.0.1:8080/ ======")
        # pause here for very long time by serving HTTP requests and
        # waiting for keyboard interruption
        await asyncio.Event().wait()

    async def main(self):
        await asyncio.gather(
            self.start_schedul(),
            self.start_server(),
            # web._run_app(self.app, port=8000),
        )


if __name__ == "__main__":
    # list_currency = ['usd', 'rub', 'eur']
    list_currency = sys.argv[1:]
    parser = createParser(list_currency=list_currency)
    script_args = parser.parse_args(sys.argv[1:])
    print(script_args.__dict__.items())
    print(list_currency)
    rest_obj = RestFrame(list_currency=list_currency, script_args=script_args)
    asyncio.run(rest_obj.main())
    print('all start')
