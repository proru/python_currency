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
    stack = []
    currencies = []
    currency_data = {}
    period = None
    app = None

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
        self.app = self.init()

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
        txt = "Hello, {} {}, {}".format(name, self.currency_data[name.upper()]['current_rate'], name.upper())
        # print(self.currency_data)
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

    async def start_schedul(self):
        while True:
            self.send_post()
            # print(self.currency_data)
            # time.sleep(10 - datetime.datetime.now().second % 10)
            # await asyncio.sleep(1)
            await asyncio.sleep(5 - datetime.datetime.now().second % 5)

    def init(self):
        app = web.Application()
        app.router.add_get("/", health)
        app.router.add_get("/hello", hello)
        app.router.add_post("/v1/crypto/info", get_crypto_info)
        app.router.add_get("/amount/get", amount_get)
        app.router.add_post("/amount/set", amount_set)
        app.router.add_get("/{name}/get", self.get_currency)
        app.router.add_post("/{name}/set", self.set_currency)
        app.router.add_post("/modify", modify_currency)
        aiohttp_debugtoolbar.setup(app)
        return app

    async def start_server(self):
        # runner = web.AppRunner(self.app)
        # await runner.setup()
        # site = web.TCPSite(runner, 'localhost', 8080)
        # await site.start()
        # # wait for finish signal
        # await runner.cleanup()
        web._run_app(self.app, port=8000)

    async def main(self):
        # Schedule three calls *concurrently*:
        # runner = aiohttp.web.AppRunner(self.app)
        # await runner.setup()
        # site = aiohttp.web.TCPSite(runner, host='localhost', port=8000)
        # await site.start()
        # # wait forever
        # await asyncio.Event().wait()
        await asyncio.gather(
            self.start_schedul(),
            web._run_app(self.app, port=8000),
        )

    # async def run(self):
    #     self.stack.append(self.start_schedul)
    #     self.stack.append(self.start_server)
    #     while True:
    #         task = self.stack.pop()
    #         await task()
    #         task = self.stack.pop()
    #         await task()
    #         self.stack.append(self.start_schedul)
    #         self.stack.append(self.start_server)
    #         # self.stack.append(self.start_server)
    #         print('11')
    #         await asyncio.sleep(1)


# async def main():
#     loop = asyncio.get_running_loop()
#
#     ## Options:
#
#     # 2. Run in a custom thread pool:
#     with concurrent.futures.ThreadPoolExecutor() as pool:
#         result = await loop.run_in_executor(pool, blocking_io)
#         print('custom thread pool', result)


if __name__ == "__main__":
    # list_currency = ['usd', 'rub', 'eur']
    list_currency = sys.argv[1:]
    parser = createParser(list_currency=list_currency)
    script_args = parser.parse_args(sys.argv[1:])
    print(script_args)
    print(parser)
    rest_obj = RestFrame(list_currency=list_currency)

    asyncio.run(rest_obj.main())
    # rest_obj.start_server()
    # loop = asyncio.get_event_loop()
    # runner = aiohttp.web.AppRunner(rest_obj.app)
    # loop.run_until_complete(runner.setup())
    # # here you can specify the listen address and port
    # site = aiohttp.web.TCPSite(runner, 'localhost', 8000)
    # loop.run_until_complete(site.start())
    # broadcast_data = loop.create_future()
    #
    # async def broadcast():
    #     global broadcast_data
    #     while True:
    #         broadcast_data.set_result(datetime.datetime.now())
    #         broadcast_data = loop.create_future()
    #         print(broadcast_data)
    #         await asyncio.sleep(1)
    #
    #
    # loop.create_task(broadcast())
    # loop = asyncio.get_running_loop()
    # try:
    #     asyncio.ensure_future(rest_obj.start_schedul())
    #     # asyncio.ensure_future(rest_obj.start_server())
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     print("Closing Loop")
    #     loop.close()
    # running_loop = asyncio.get_event_loop()
    #
    # asyncio.(rest_obj.run(), loop=running_loop)

    # aioserver = multiprocessing.Process(name='my_server', target=rest_obj.start_server)
    # aioserver = threading.Thread(name='my_server', target=rest_obj.start_server)
    # # script_control = multiprocessing.Process(name='start_script', target=rest_obj.start_schedul)
    # script_control = threading.Thread(name='start_script', target=rest_obj.start_schedul)
    # aioserver.start()
    # script_control.start()
    print('all start')
    # aioserver = multiprocessing.Process(name='my_server', target=start_server)
