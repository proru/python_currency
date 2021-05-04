from abc import ABC, abstractmethod
import asyncio
from aiohttp import web
import aiohttp
import datetime
import argparse
from typing import Awaitable, Callable
import traceback


class AbstractRest(ABC):

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
        self.logger = logger
        self.period = script_args.__dict__['period'] if script_args.__dict__.get('period') else 60
        self.currencies = [key for key, value in self.currency_data.items()]
        self.currencies.remove('rub')
        self.app = self.init_app()

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

    @abstractmethod
    async def control_data(self) -> None:
        pass

    @abstractmethod
    async def receive_data(self, session) -> None:
        pass

    @abstractmethod
    def init_app(self) -> app:
        pass

    async def start_server(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        self.logger.info("======= Serving on http://127.0.0.1:8080/ ======")
        print("======= Serving on http://127.0.0.1:8080/ ======")
        await asyncio.Event().wait()

    async def start_control_schedul(self):
        self.logger.info('start control data on changing')
        while True:
            try:
                await self.control_data()
            except Exception as ex:
                self.logger.error(traceback.format_exc())
            await asyncio.sleep(5 - datetime.datetime.now().second % 5)

    async def start_schedul(self):
        headers = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            self.logger.info('Start receiving data about currency schedule')
            while True:
                try:
                    await self.receive_data(session)
                except Exception as ex:
                    self.logger.error(traceback.format_exc())
                await asyncio.sleep(self.period - datetime.datetime.now().second % self.period)

    async def main(self):
        self.logger.info('Start event loop')
        await asyncio.gather(
            self.start_schedul(),
            self.start_server(),
            self.start_control_schedul(),
        )




