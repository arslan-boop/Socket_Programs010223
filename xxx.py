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


def floor_step_size(quantity,stepSize):
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
    return floor_step_size(qty,stepSize)


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


if __name__ == '__main__':

    try:
        v_symbol = 'AVAXUSDT'
        print(datetime.now())
        usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
        islem_tutar = 20 #float(usdtBalance) * 0.4
        v_tip=2
        #Alım
        if v_tip == 1 :
            order = v_client.order_market_buy(symbol=v_symbol, quoteOrderQty=float(islem_tutar))
            if order['status'] == 'FILLED':
                print('success')
                price = order['fills'][0]['price']
                quantity_filled = order['fills'][0]['qty']
                v_orqty = order['origQty']
                v_exqty = order['executedQty']
                v_times = order['transactTime']
                v_times = v_times/1000
                now = datetime.now()
                timestamp = datetime.timestamp(now)
                dt_v_trantime = datetime.fromtimestamp(float(v_times))
                current_timestamp = round(time.time() * 1000)
                current_timestamp = current_timestamp /1000
                dt_current = datetime.fromtimestamp(current_timestamp)
                print('price ' + price, ' qty ' + quantity_filled)

                v_total_price = 0
                v_quantity_filled = 0
                p = 0
                i = len(order['fills'])
                for p in range(i):
                    v_total_price = v_total_price + float(order['fills'][p]['price']) * float(order['fills'][p]['qty'])
                    v_quantity_filled = v_quantity_filled + float(order['fills'][p]['qty'])

                v_alim_miktar = float(v_quantity_filled)  # float(order_buy['origQty'])
                v_alim_fiyati = float(v_total_price) / float(v_quantity_filled)
                print('Alım fiyat ve miktar', str(v_alim_miktar), str(v_alim_fiyati))

        elif v_tip==2:
            v_sembolmik = v_symbol.replace("USDT","")
            miktar = v_client.get_asset_balance(asset=v_sembolmik).get('free')
            miktar = get_round_step_quantity(v_symbol, float(miktar))
            print('Yuvarlanmış miktar', miktar, datetime.now())

            #Satım
            order = v_client.order_market_sell(symbol=v_symbol, quantity=float(miktar))
            print('SAlınan Miktar',order,datetime.now())
            if order['status'] == 'FILLED':
                print('success')
                price = order['fills'][0]['price']
                quantity_filled = order['fills'][0]['qty']
                v_orqty = order['origQty']
                v_exqty = order['executedQty']
                v_times = order['transactTime']
                v_times = v_times / 1000
                now = datetime.now()
                timestamp = datetime.timestamp(now)
                dt_v_trantime = datetime.fromtimestamp(float(v_times))
                current_timestamp = round(time.time() * 1000)
                current_timestamp = current_timestamp / 1000
                dt_current = datetime.fromtimestamp(current_timestamp)
                print('price ' + price, ' qty ' + quantity_filled)

                v_total_price = 0
                v_quantity_filled = 0
                p=0
                i = len(order['fills'])
                for p in range(i):
                    v_total_price = v_total_price + float(order['fills'][p]['price']) * float(
                        order['fills'][p]['qty'])
                    v_quantity_filled = v_quantity_filled + float(order['fills'][p]['qty'])

                v_alim_miktar = float(v_quantity_filled)  # float(order_buy['origQty'])
                v_alim_fiyati = float(v_total_price) / float(v_quantity_filled)
                print('Alım fiyat ve miktar',str(v_alim_miktar),str(v_alim_fiyati))
        else:
            # get trades
            trades = v_client.get_my_trades(symbol=v_symbol)
            print(trades)

    except BinanceAPIException as e:
        print(e.status_code)
        print(e.message)
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(e.status_code) + '-' + str(e.message) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
"""
order = client.order_market_buy(symbol=symbol,quantity=0.2)
    #pprint.pprint(order)
    if order['status'] == 'FILLED':
      print('success')
      price = order['fills'][0]['price']
      quantity_filled = order['fills'][0]['qty']
      print('price ' + price, ' qty '+ quantity_filled)
  except Exception as e:
    print(e)
    """