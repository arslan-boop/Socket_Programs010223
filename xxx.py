# from binance.spot import Spot as Client
import math
from decimal import Decimal as D, ROUND_DOWN, ROUND_UP
import decimal
import pandas as pd
import websocket
from binance.client import Client as Client_1, AsyncClient
import asyncio
from binance.exceptions import BinanceAPIException
import sqlite3
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
import math
from typing import Union
from binance.helpers import round_step_size
import API_Config
import json
import Telebot_v1
from binance import ThreadedWebsocketManager

api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)

minQty = 0
maxQty = 0
stepSize = 0
closes = []

def floor_step_size(quantity):
    step_size_dec = Decimal(str(stepSize))
    return float(int(Decimal(str(quantity)) / step_size_dec) * step_size_dec)


def get_round_step_quantity(v_symbol, qty):
    info = v_client.get_symbol_info(v_symbol)
    for x in info["filters"]:
        if x["filterType"] == "LOT_SIZE":
            minQty = float(x["minQty"])
            maxQty = float(x["maxQty"])
            stepSize = x["stepSize"]
    if qty < minQty:
        qty = minQty
    return floor_step_size(qty)


def get_quantity(asset):
    balance = get_balance(asset=asset)
    balance = float(balance) * 0.4
    quantity = get_round_step_quantity(float(balance))
    return quantity


def get_balance(asset) -> str:
    balance = v_client.get_asset_balance(asset=asset)
    return balance['free']


def buy(v_symbol, v_quantity, v_asset):
    v_client.order_market_buy(symbol=v_symbol, quoteOrderQty=get_quantity(v_asset))
    # v_client.order_market_buy(symbol=v_symbol, quoteOrderQty=get_quantity(Config.QUOTE_ASSET))


def sell(v_symbol, v_asset):
    v_client.order_market_sell(symbol=v_symbol, quantity=get_quantity(v_asset))

def handle_socket_message(msg):
        print(f"message type: {msg['e']}")
        print(msg)
def get_first_set_of_closes(v_symbol):
        for kline in v_client.get_historical_klines(v_symbol, v_client.KLINE_INTERVAL_1MINUTE, "1 hour ago UTC"):
            closes.append(float(kline[4]))

def mainx():
    try:
        symbol = 'BNBBTC'
        twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
        # start is required to initialise its internal loop
        get_first_set_of_closes(symbol)
        twm.start()
        twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)
        twm.join()
    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
    #
    # # multiple sockets can be started
    # twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)
    #
    # # or a multiplex socket can be started like this
    # # see Binance docs for stream names
    # streams = ['bnbbtc@miniTicker', 'bnbbtc@bookTicker']
    # twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
    #twm.join(2)

    #Stop Individual Stream
    # depth_stream_name = twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)
    # # some time later
    # twm.stop_socket(depth_stream_name)

    #Stop All Streams
    #twm.stop()

if __name__ == '__main__':
    try:
        #mainx()
        # get latest price from Binance API
        btc_price = v_client.get_symbol_ticker(symbol="BTCUSDT")
        # print full output (dictionary)
        print(btc_price)

        v_symbol = 'BEAMUSDT'
        usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
        usdtBalance = get_balance('USDT')

        while True:
            usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='BTC').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='AVAX').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='DOGE').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')

            print('İlk Başladı.........', usdtBalance, '-', datetime.now())
        #
        # print('Bakiye = ', usdtBalance)
        # islem_tutar = float(usdtBalance) * 0.4
        # islem_tutar = float(round(islem_tutar, 8))
        # print('İşlem tutar = ', islem_tutar)
        #
        # # account = v_client.get_account()
        # # order_buy = v_client.order_market_buy(symbol=v_symbol, quantity=float(islem_tutar))
        # time.sleep(3)
        # miktar = v_client.get_asset_balance(asset='PSG').get('free')
        # # order_sell = v_client.order_market_sell(symbol='PSGUSDT', quantity=avaxBalance)
        # print('Alınan Miktar', miktar)

    except BinanceAPIException as e:
        print(e.status_code)
        print(e.message)
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(e.status_code) + '-' + str(e.message) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
