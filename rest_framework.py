import asyncio
from aiohttp import web
import aiohttp_debugtoolbar
import itertools
import datetime
import xml.etree.ElementTree as ET
import sys
from abstract_module import AbstractRest
import logging
import traceback


class RestFrame(AbstractRest):

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
        txt = txt + '\n'+'-'*140
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
            self.logger.error(traceback.format_exc())
        self.logger.debug(str(request) + 'handled request /amount/get')
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
                self.currency_data[key]['prev_rate'] = self.currency_data[key]['current_rate']
                print_now = True
        if print_now:
            response = await self.amount_get(request=None)
            self.logger.debug(response.body.decode("utf-8"))
            print(response.body.decode("utf-8"))

    async def receive_data(self, session):
        self.logger.info('Update data about currencies rate')
        async with session.get(url="https://www.cbr-xml-daily.ru/daily_utf8.xml", ) as response:
            string_xml = await response.text()
        root = ET.fromstring(string_xml)
        for key in self.currencies:
            self.currency_data[key]['prev_rate'], self.currency_data[key]['current_rate'] = \
                self.currency_data[key]['current_rate'], root.findall(".*[CharCode='" + key.upper() + "']/Value")[0].text.replace(",", ".")


    def init_app(self):
        app = web.Application(middlewares=[self.error_middleware])
        app.router.add_get("/", self.health)
        app.router.add_get("/amount/get", self.amount_get)
        app.router.add_post("/amount/set", self.amount_set)
        app.router.add_get("/{name}/get", self.get_currency)
        app.router.add_post("/{name}/set", self.set_currency)
        app.router.add_post("/modify", self.modify_currency)
        aiohttp_debugtoolbar.setup(app)
        return app


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
    try:
        asyncio.run(rest_obj.main())
    except KeyboardInterrupt as ex:
        rest_obj.logger.info('Stop event loop end script')
    except Exception as e:
        rest_obj.logger.error(traceback.format_exc())
    logger.info("Script completed")
    print('Script completed')