import multiprocessing
import time
import random
from aiohttp import web
import requests
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory

import time, requests
import datetime
import xml.etree.ElementTree as ET

import sys
import argparse


async def health(request):
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')


async def get_crypto_info(request):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false&sparkline=false"
    response = requests.get(url)
    if response.status_code in [200, 201]:
        return web.Response(text=response.text, contenaioservert_type='application/json')
    else:
        return web.Response(text=str({"status": "failure", "status_code": response.status_code}))


async def hello(request):
    print(request)
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')


async def get_currency(request):
    name = request.match_info.get('name', "Anonymous")
    txt = "Hello, {}".format(name)
    return web.Response(text=txt)
    # return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
    #                     content_type='text/html')


async def amount_get(request):
    print(request)
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')


async def amount_set(request):
    print(request)
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')


async def modify_currency(request):
    print(request)
    return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
                        content_type='text/html')


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
    currencies = []
    currency_data = {}
    period = None

    def __init__(self, list_currency):
        for item in list_currency:
            if not item.startswith('--') or item.startswith('--help'):
                list_currency.remove(item)
        for key in list_currency:
            self.currency_data[key.replace('-', '').upper()] = {
                'prev_value': None,
                'prev_rate': None,
                'current_value': None,
                'current_rate': None
            }
        self.currencies = [key for key, value in self.currency_data.items()]
        self.currencies.remove('RUB')
        print(self.currencies)

    async def get_currency(self, request):
        name = request.match_info.get('name', "Anonymous")
        txt = "Hello, {} {}, {}".format(name, self.currency_data[name.upper()]['current_rate'], name.upper())
        print(self.currency_data)
        return web.Response(text=txt)
        # return web.Response(text="<h1> Async Rest API using aiohttp : Health OK </h1>",
        #                     content_type='text/html')

    def send_post(self):
        response = requests.get("https://www.cbr-xml-daily.ru/daily_utf8.xml")
        string_xml = response.content
        root = ET.fromstring(string_xml)
        # print('USD', root.findall(".*[CharCode='USD']/Value")[0].text, 'EUR',
        #       root.findall(".*[CharCode='EUR']/Value")[0].text)
        for key in self.currencies:
            self.currency_data[key]['prev_rate'], self.currency_data[key]['current_rate'] = \
                self.currency_data[key]['current_rate'], root.findall(".*[CharCode='" + key + "']/Value")[0].text
            print('print ', key, self.currency_data[key]['current_rate'])

    def start_schedul(self):
        while True:
            self.send_post()
            time.sleep(5 - datetime.datetime.now().second % 5)

    async def init(self):
        app = web.Application()
        app.router.add_get("/", health)
        app.router.add_get("/hello", hello)
        app.router.add_post("/v1/crypto/info", get_crypto_info)
        app.router.add_get("/amount/get", amount_get)
        app.router.add_post("/amount/set", amount_set)
        app.router.add_get("/{name}/get", self.get_currency)
        app.router.add_post("/modify", modify_currency)
        aiohttp_debugtoolbar.setup(app)
        return app

    def start_server(self):
        application = self.init()
        web.run_app(application, port=8000)


if __name__ == "__main__":
    # list_currency = ['usd', 'rub', 'eur']
    list_currency = sys.argv[1:]
    parser = createParser(list_currency=list_currency)
    script_args = parser.parse_args(sys.argv[1:])
    print(script_args)
    print(parser)
    rest_obj = RestFrame(list_currency=list_currency)

    aioserver = multiprocessing.Process(name='my_server', target=rest_obj.start_server)
    script_control = multiprocessing.Process(name='start_script', target=rest_obj.start_schedul)
    aioserver.start()
    script_control.start()
    print('all start')
    # aioserver = multiprocessing.Process(name='my_server', target=start_server)
