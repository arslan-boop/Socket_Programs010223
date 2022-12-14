# from binance.spot import Spot as Client
import pandas as pd
import websocket
from binance.client import Client as Client_1, AsyncClient
import asyncio
from binance.exceptions import BinanceAPIException
import sqlite3
import time
from datetime import datetime
import API_Config
import json

v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)

api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'


async def macin():
    quantity = '0.000001'
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret, testnet=True)

    try:
        market_res = await client.order_market_sell(symbol='BTCUSDT', quantity=quantity)
    except BinanceAPIException as e:
        print(e)
    else:
        print(json.dumps(market_res, indent=2))

    await client.close_connection()


if __name__ == '__main__':
    try:
        usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')

        order_buy = v_client.order_market_buy(symbol='BTCUSDT', quantity=float(usdtBalance))
        order_sell = v_client.order_market_sell(symbol='BTCUSDT', quantity=btcBalance)

        # order_buy = Client.order_market_buy(symbol='BTCUSDT', quantity= < yourquantity >, quoteOrderQty = my_USDT_position)
        # order_sell = Client.order_market_sell(symbol='BTCUSDT', quantity= < yourquantity >, quoteOrderQty = my_BTC_position)

        # *******************************************************************

        # use param quoteOrderQty instead of param quantity when buying
        order_buy = v_client.order_market_buy(symbol='BTCUSDT', quoteOrderQty=usdtBalance)
        ##Some time later##
        btcBalance = v_client.get_asset_balance(asset='BTC').get('free')
        # use param quantity instead of param quoteOrderQty when selling
        order_sell = v_client.order_market_sell(symbol='BTCUSDT', quantity=btcBalance)

        # buy_order = v_client.order_market_buy(symbol=v_symbol, quantity=100)
        while True:
            print('İlk Başladı.........', usdtBalance, datetime.now())

    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
