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

api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)

minQty = 0
maxQty = 0
stepSize = 0


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


def round_down(self, coin, number):
    info = self.client.get_symbol_info('%sUSDT' % coin)
    step_size = [float(_['stepSize']) for _ in info['filters'] if _['filterType'] == 'LOT_SIZE'][0]
    step_size = '%.8f' % step_size
    step_size = step_size.rstrip('0')
    decimals = len(step_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


# to get a lot size
def getLotSize(self):
    info = self.apiCall(lambda: self.client.get_symbol_info(self.pair))
    lotSize = float(info['filters'][2]['minQty'])
    return lotSize

def round_step_size(quantity: Union[float, Decimal], step_size: Union[float, Decimal]) -> float:
    if step_size == 1.0:
        return math.floor(quantity)
    elif step_size < 1.0:
        return Decimal(f'{quantity}').quantize(Decimal(f'{step_size}'), rounding=ROUND_DOWN)

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
    balance = float(balance)*0.4
    quantity = get_round_step_quantity(float(balance))
    return quantity

def get_balance(asset) -> str:
    balance = v_client.get_asset_balance(asset=asset)
    return balance['free']

def buy(v_symbol, v_quantity,v_asset):
    v_client.order_market_buy(symbol=v_symbol, quoteOrderQty=get_quantity(v_asset))
    #v_client.order_market_buy(symbol=v_symbol, quoteOrderQty=get_quantity(Config.QUOTE_ASSET))

def sell(v_symbol,v_asset):
    v_client.order_market_sell(symbol=v_symbol, quantity=get_quantity(v_asset))


if __name__ == '__main__':

    try:
        v_symbol = 'BEAMUSDT'
        usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
        usdtBalance = get_balance('USDT')
        print('Bakiye = ', usdtBalance)
        islem_tutar = float(usdtBalance) * 0.4
        islem_tutar = float(round(islem_tutar, 8))
        print('İşlem tutar = ', islem_tutar)

        # quantity = float(round(quantity, 6))
        # decimal_count = 4
        # quantity = f"{float(value):.{decimal_count}f}"

        # account = v_client.get_account()
        order_buy = v_client.order_market_buy(symbol=v_symbol, quantity=float(islem_tutar))
        # order_buy = v_client.order_market_buy(symbol=v_symbol, quantity=float(usdtBalance),quoteOrderQty=float(usdtBalance))
        # Some time later##
        time.sleep(3)
        miktar = v_client.get_asset_balance(asset='PSG').get('free')
        # order_sell = v_client.order_market_sell(symbol='PSGUSDT', quantity=avaxBalance)
        print('Alınan Miktar', miktar)
        print('son')

    except BinanceAPIException as e:
        print(e.status_code)
        print(e.message)
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(e.status_code) + '-' + str(e.message) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)

        # info = v_client.get_symbol_info(v_symbol)
        # print(info)
        # #v_in = info['filters'][2]['minQty']
        # print(info['filters'][1]['minQty'])
        # print('son')
        # #info = client.get_symbol_info(symbol=pair)
        # price_filter = float(info['filters'][0]['tickSize'])
        # lotSize = float(info['filters'][1]['minQty'])
        #
        # ticker = v_client.get_symbol_ticker(symbol=v_symbol)
        # price = float(ticker['price'])

        # order_buy = v_client.order_market_buy(symbol=v_symbol, quantity=float(usdtBalance))
        # order_buy = v_client.order_market_buy(symbol=v_symbol, quantity=float(usdtBalance),quoteOrderQty=float(usdtBalance))
        # order_buy = v_client.order_market_buy(symbol=v_symbol, quantity=float(usdtBalance),   quoteOrderQty=float(usdtBalance))

        # order_sell = v_client.order_market_sell(symbol='AVAXUSDT', quantity=btcBalance)
        # print('order', order_buy)

        # buy_quantity = round(buy_amount * 0.999, len(str(lotsize).split('.')[1]))

        # CurrencyRoundNum = int(math.Abs(math.Log10(stepSize)))
        # PriceRoundNum = int(math.Abs(math.Log10(tickSize)))

        # price = D.from_float(price).quantize(D(str(price_filter)))
        # minimum = float(info['filters'][1]['minQty'])  # 'minQty'
        # quant = D.from_float(usdtBalance).quantize(D(str(minimum)))  # if quantity >= 10.3/price
        # print('quan', str(quant))

        # while True:
        #     usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
        #     print('İlk Başladı.........', usdtBalance, '-', str(avaxBalance), datetime.now())

        # buy_order = v_client.order_market_buy(symbol=v_symbol, quantity=100)

        # except Exception as exp:
        #     v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + '-'+ str(exp.sta str(datetime.now())
        #     Telebot_v1.mainma(v_hata_mesaj)

        """
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

        # For spot trading
        res = client.get_exchange_info()          # Return rate limits and list of symbols
        res = client.get_symbol_info(symbol)      # Return information about a symbol
        res = client.get_symbol_ticker(**params)  # Latest price for a symbol or symbols
        res = client.get_account(**params)        # Get current account information
        res = client.get_asset_balance(asset, **params) # Get current asset balance
        res = client.get_avg_price(**params)      # Current average price for a symbol
        res = client.create_order(**params)       # Send in a new order


        # For futures trading 
        res = client.futures_account(**params)    # get futures account information
        res = client.futures_account_balance(**params) # returns futures account balance    
        res = client.futures_exchange_info()      # return rate limits and list of symbols for future
        res = client.futures_create_order(**params) # Send in a new futures order 

        # make a test order first. This will raise an exception if the order is incorrect.
            order = client.create_test_order(
                symbol='BNBBTC',
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=100,
                price='0.00001')
            # actual order
            order = client.create_order(
                symbol='BNBBTC',
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=100,
                price='0.00001')
        # To cancel order
        result = client.cancel_order(symbol='BNBBTC',orderId='orderId')
        # Get order status
        order = client.get_order(symbol='BNBBTC', orderId='orderId')
        # Get all open orders
        orders = client.get_open_orders(symbol='BNBBTC')
        # Get all orders
        orders = client.get_all_orders(symbol='BNBBTC')

        try:
            client.get_all_orders()
        except BinanceAPIException as e:
            print e.status_code
            print e.message

***************************************
"filters": [
    {
        "filterType": "PRICE_FILTER",
        "minPrice": "0.01000000",
        "maxPrice": "1000000.00000000",
        "tickSize": "0.01000000"
    },
    {
        "filterType": "PERCENT_PRICE",
        "multiplierUp": "5",
        "multiplierDown": "0.2",
        "avgPriceMins": 5
    },
    {
        "filterType": "LOT_SIZE",
        "minQty": "0.00001000",
        "maxQty": "9000.00000000",
        "stepSize": "0.00001000"
    },
    {
        "filterType": "MIN_NOTIONAL",
        "minNotional": "10.00000000",
        "applyToMarket": true,
        "avgPriceMins": 5
    },
    {
        "filterType": "ICEBERG_PARTS",
        "limit": 10
    },
    {
        "filterType": "MARKET_LOT_SIZE",
        "minQty": "0.00000000",
        "maxQty": "282.39806510",
        "stepSize": "0.00000000"
    },
    {
        "filterType": "TRAILING_DELTA",
        "minTrailingAboveDelta": 10,
        "maxTrailingAboveDelta": 2000,
        "minTrailingBelowDelta": 10,
        "maxTrailingBelowDelta": 2000
    },
    {
        "filterType": "MAX_NUM_ORDERS",
        "maxNumOrders": 200
    },
    {
        "filterType": "MAX_NUM_ALGO_ORDERS",
        "maxNumAlgoOrders": 5
    }
]
        """
