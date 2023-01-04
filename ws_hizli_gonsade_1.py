import multiprocessing
import warnings

import numpy
from binance.exceptions import BinanceAPIException

warnings.simplefilter(action='ignore', category=FutureWarning)
import requests
from binance import ThreadedWebsocketManager
from json import loads
import traceback
import logging
import threading
# from binance.spot import Spot as Client
import json
import pandas as pd
import websocket
from binance.client import Client as Client_1
import asyncio
import binance
import sqlite3
import time
from datetime import datetime
import API_Config
import talib as ta
import numpy as np
import DB_transactions3
import Telebot_v1
from decimal import Decimal, ROUND_DOWN
# from threading import Thread
from multiprocessing import Process
from multiprocessing import Pool
import concurrent.futures

# ssl den doğacak hataları bertaraf etmek için
requests.packages.urllib3.disable_warnings()

DB_FILE = "TRADE3.DB"
con = sqlite3.connect(DB_FILE, timeout=10)
cursor = con.cursor()

v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales = 0, 0, 0, 0, 0, 0, 0, 0
v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, [], [], {}
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla = '2022', 0, '', '', '', '', 0
closes, highes, lowes, kesmeler, openes = [], [], [], [], []


def floor_step_size(quantity, stepSize):
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
    return floor_step_size(qty, stepSize)


# *****************************ALIM SATIM İŞLEMLERİ*********************************************************************

def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati, v_last_price_g, v_alim_miktar
    global v_client, v_alim_timestamp, v_alim_zamani, v_hizli_gonzales, v_ters_kesim

    if v_alim_var == 0:
        try:
            v_zip = 0
            if v_hizli_gonzales == 1:
                if v_test_prod == 'P':
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani = buy_coin(v_symbol, v_islem_tutar, v_kar_oran,
                                                                           v_zarar_oran)
                else:
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani = buy_coin_test(v_symbol, v_islem_tutar, v_kar_oran,
                                                                                v_zarar_oran, v_zip)

                v_alim_var = 1
            else:
                print('Alım için Uygun Emir Bulunamadı.!', v_symbol, datetime.now())
        except BinanceAPIException as e:
            print('Status code', str(e.status_code), v_symbol)
            print('Mesajı', str(e.message), v_symbol)
            # except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Alım tarafı  = ' + str(e.message) + '-' + \
                           str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj)

    elif v_alim_var == 1:
        current_timestamp = round(time.time() * 1000)
        v_satim_timestamp = current_timestamp / 1000
        try:
            v_son_fiyat = float(v_last_price_g)
            print(str(v_symbol), 'İçerde alım var.......!!', str(datetime.now())[0:19], 'Hedefi = ',
                  str(v_hedef_bid_global), 'Son Fiyat = ', str(v_last_price_g))
            """
            if float(v_last_price_g) > float(v_hedef_bid_global):
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani)
                v_alim_var = 0
                time.sleep(60)
            elif float(v_last_price_g) < float(v_hedef_ask_global):
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 2, v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 2, v_alim_zamani)
                v_alim_var = 0
                time.sleep(60)
            elif v_satim_timestamp >= v_alim_timestamp:
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 3, v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 3, v_alim_zamani)
                v_alim_var = 0
                time.sleep(60)
            """
            if v_ters_kesim == 1:
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            else:
                print('İçerde alım var ama henüz satılamadı...!- ', str(datetime.now())[0:19], v_symbol, ' - Hedefi = ',
                      str(v_hedef_bid_global), 'Son Fiyat = ', str(v_last_price_g))
        except BinanceAPIException as e:
            print('Status code', str(e.status_code), v_symbol)
            print('Mesajı', str(e.message), v_symbol)
            # except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Satım tarafı  = ' + str(e.message) + '-' + \
                           str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj)


# ****************************SATIM********************************
def sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip, v_alim_zamani):
    global v_alim_var
    try:
        order_sell = v_client.order_market_sell(symbol=v_symbol, quantity=float(v_alim_miktar))
        # v_son_fiyat = float(v_last_price_g)
        if order_sell['status'] == 'FILLED':
            print('success')
            p = 0
            i = len(order_sell['fills'])
            v_total_price = 0
            v_quantity_filled = 0
            for p in range(i):
                v_total_price = v_total_price + float(order_sell['fills'][p]['price']) * float(
                    order_sell['fills'][p]['qty'])
                v_quantity_filled = v_quantity_filled + float(order_sell['fills'][p]['qty'])

            v_satim_miktar = float(v_quantity_filled)  # float(order_buy['origQty'])
            v_satim_fiyati = float(v_total_price) / float(v_quantity_filled)
            v_son_fiyat = v_satim_fiyati
            quantity_filled = order_sell['fills'][0]['qty']
            v_times = order_sell['transactTime']
            v_times = v_times / 1000
            dt_v_trantime = datetime.fromtimestamp(float(v_times))
            v_satim_zamani = str(dt_v_trantime)  # str(datetime.now())[0:19]

            if float(v_satim_fiyati) > float(v_alim_fiyati):
                v_profit_oran = float(((float(v_satim_fiyati) - float(v_alim_fiyati)) * 100) / float(v_alim_fiyati))
                if v_tip == 3:
                    v_kisa_mes = 'KARLA KAPADI - '
                else:
                    v_kisa_mes = 'Karla Sattı..'

                v_oran_mesaj = '- Kar Oranı :'
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.8f}".format(float(v_alim_fiyati)) + '*' + \
                                   "{:.8f}".format(float(v_satim_fiyati)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani)
            else:
                v_profit_oran = float(((float(v_alim_fiyati) - float(v_satim_fiyati)) * 100) / float(v_alim_fiyati))
                if v_tip == 3:
                    v_kisa_mes = 'ZARARLA KAPADI.'
                else:
                    v_kisa_mes = 'Zararla Sattı..'

                v_oran_mesaj = '- Zarar Oranı :'
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.8f}".format(
                    float(v_alim_fiyati)) + '*' + "{:.8f}".format(float(v_satim_fiyati)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani)

            v_mess1 = v_kisa_mes + ' Hedefi : ' + "{:.8f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(
                v_symbol) + \
                      '- Alım Fiyatı :' + "{:.8f}".format(
                float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.8f}".format(float(v_satim_fiyati)) + \
                      str(v_oran_mesaj) + "{:.8f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(v_satim_zamani) + \
                      'Alım Zamanı : ' + str(v_alim_zamani)

            # ******************
            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
            v_alim_var = 0
            Telebot_v1.genel_alimlar(v_symbol, 'S')
            Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
        else:
            v_hata = 'SATIM işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!..   = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip, v_alim_zamani):
    global v_alim_var

    try:
        v_son_fiyat = float(v_last_price_g)
        v_satim_fiyati = v_son_fiyat
        v_satim_zamani = str(datetime.now())

        if float(v_satim_fiyati) > float(v_alim_fiyati):
            v_profit_oran = float(((float(v_satim_fiyati) - float(v_alim_fiyati)) * 100) / float(v_alim_fiyati))
            if v_tip == 3:
                v_kisa_mes = 'KARLA KAPADI - '
            else:
                v_kisa_mes = 'Karla Sattı..'

            v_oran_mesaj = '- Kar Oranı :'
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.8f}".format(float(v_alim_fiyati)) + '*' + \
                               "{:.8f}".format(float(v_satim_fiyati)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani)
        else:
            v_profit_oran = float(((float(v_alim_fiyati) - float(v_satim_fiyati)) * 100) / float(v_alim_fiyati))
            if v_tip == 3:
                v_kisa_mes = 'ZARARLA KAPADI.'
            else:
                v_kisa_mes = 'Zararla Sattı..'

            v_oran_mesaj = '- Zarar Oranı :'
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.8f}".format(
                float(v_alim_fiyati)) + '*' + "{:.8f}".format(float(v_satim_fiyati)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani)

        v_mess1 = v_kisa_mes + ' Hedefi : ' + "{:.8f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(
            v_symbol) + \
                  '- Alım Fiyatı :' + "{:.8f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.8f}".format(
            float(v_satim_fiyati)) + \
                  str(v_oran_mesaj) + "{:.8f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(v_satim_zamani) + \
                  'Alım Zamanı : ' + str(v_alim_zamani)

        Telebot_v1.mainma(v_mess1)
        Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
        v_alim_var = 0
        Telebot_v1.genel_alimlar(v_symbol, 'S')
        Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.11   = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def buy_coin(v_symbol, v_islem_tutar, v_kar_oran, v_zarar_oran):
    try:
        order_buy = v_client.order_market_buy(symbol=v_symbol, quoteOrderQty=float(v_islem_tutar))

        if order_buy['status'] == 'FILLED':
            print('success')
            p = 0
            i = len(order_buy['fills'])
            v_total_price = 0
            v_quantity_filled = 0

            for p in range(i):
                v_total_price = v_total_price + float(order_buy['fills'][p]['price']) * float(
                    order_buy['fills'][p]['qty'])
                v_quantity_filled = v_quantity_filled + float(order_buy['fills'][p]['qty'])

            v_alim_miktar = float(v_quantity_filled)  # float(order_buy['origQty'])
            v_alim_fiyati = float(v_total_price) / float(v_quantity_filled)
            v_son_fiyat = v_alim_fiyati

            # v_exqty = order_buy['executedQty']
            v_times = order_buy['transactTime']
            v_times = v_times / 1000
            # now = datetime.now()
            # timestamp = datetime.timestamp(now)
            dt_v_trantime = datetime.fromtimestamp(float(v_times))
            v_alim_zamani = str(dt_v_trantime)  # str(datetime.now())[0:19]
            v_hedef_bid = float(v_son_fiyat * v_kar_oran)
            v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
            v_hedef_bid_global = v_hedef_bid
            v_hedef_ask_global = v_hedef_ask

            current_timestamp = round(time.time() * 1000)
            v_alim_timestamp = (current_timestamp + (90000)) / 1000
            # v_alim_zamani = str(datetime.now())[0:19]
        else:
            v_hata = 'Alım işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata)

        v_mess = str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'Miktar = ' + '--' + "{:.1f}".format(float(v_alim_miktar)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.1f}".format(float(v_islem_tutar))
        # Telegram mesajo
        Telebot_v1.mainma(v_mess)
        Telebot_v1.genel_alimlar(v_symbol, 'A')
        v_sembolmik = v_symbol.replace("BUSD", "")
        v_alim_miktar = v_client.get_asset_balance(asset=v_sembolmik).get('free')
        v_alim_miktar = get_round_step_quantity(v_symbol, float(v_alim_miktar))

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, \
               v_alim_timestamp, v_alim_miktar, v_alim_fiyati, v_alim_zamani
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.. buy_coin  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ************************************************************ ************************TEST ALIM**********************/
def buy_coin_test(v_symbol, v_islem_tutar, v_kar_oran, v_zarar_oran, v_zip):
    global v_last_price_g, v_alim_zamani, v_alim_var
    try:
        v_son_fiyat = float(v_last_price_g)
        v_alim_zamani = str(datetime.now())
        v_alim_fiyati = v_son_fiyat
        v_hedef_bid = float(v_son_fiyat * v_kar_oran)
        v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
        v_hedef_bid_global = v_hedef_bid
        v_hedef_ask_global = v_hedef_ask
        current_timestamp = round(time.time() * 1000)
        v_alim_timestamp = (current_timestamp + (60000)) / 1000
        # v_alim_var = 1

        v_mess = str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.1f}".format(float(v_islem_tutar)) + '--' + \
                 'Zip=' + '--' + str(v_zip)
        # Telegram mesajo
        Telebot_v1.mainma(v_mess)
        Telebot_v1.genel_alimlar(v_symbol, 'A')

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, \
               v_alim_timestamp, v_alim_miktar, v_alim_fiyati, v_alim_zamani
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.. buy_coin_test  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def on_open_f(ws_front):
    global vn_front
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front, "id": 1}
    ws_front.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


# ***********************************************************************************************************************
def on_error_f(ws_front):
    print('Error olustu')


# ***********************************************************************************************************************
def on_close_f(ws_front):
    print('closed connection')


# ***********************************************************************************************************************
def on_message_f(ws_front, message):
    global v_last_price_g, v_open_price, closes, highes, lowes, openes, v_kesim, \
        v_ters_kesim, v_alim_var, v_hizli_gonzales, v_ziplama_oran, kesmeler
    # v_l_c_p, v_p_c_p2, v_1m_c, v_p_c_p3, v_3m_c, v_p_c_p5, v_5m_c = 0, 0, 0, 0, 0, 0, 0

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']
    # print('closes dizisi ik', v_symbol, closes, datetime.now())
    # print('Geldi', v_symbol, close, '-', open, '-', high, '-', low, '-', datetime.now())
    is_candle_closed = candle['x']

    x = ((float(close) - float(open)) / float(open)) * 100
    if x >= v_ziplama_oran:
        v_acil_al = 1
        v_acil_oran = x
    else:
        v_acil_al = 0
        v_acil_oran = 0

    # Normal işleyiş
    if is_candle_closed:  # or (v_acil_al == 1 and is_candle_closed == True):
        candle_islem(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran)

    # Acil alım
    if v_acil_al == 1 and is_candle_closed == False:
        if v_alim_var == 0 and v_hizli_gonzales != 1:
            candle_islem_acil_alim(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes,
                                   v_ziplama_oran)

    # Acil Satım
    if v_alim_var == 1 and is_candle_closed == False:
        candle_islem_satim(v_symbol, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran)


# *********************************************************************************************
def candle_islem_satim(v_symbol, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales

    time.sleep(2)
    # Alım var SATIM prosedürü
    v_ema_cross_up, v_ema_cross_down, v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_30m_c, v_45m_c, v_60m_c, \
    ema_artik, v_10m_c,v_120m_c = check_exist_ema_second(v_symbol, openes, closes, highes, lowes, 5, 20)

    if v_ema_cross_down == 1 or (float(openes[-1]) > float(closes[-1]) and float(closes[-1]) > float(v_last_price_g)):
        v_ters_kesim = 1
        vm1 = 'Acil Satım Yapılacak...!..  = ' + str(v_symbol) + str(datetime.now()) + '*' + str(float(closes[-1])) \
              + '*' + str(openes[-1]) + '*' + str(v_last_price_g)
        Telebot_v1.mainma(vm1)
    else:
        print('İçerde alım var fakat satılamadı  ', v_symbol, datetime.now())
        v_ters_kesim = 0


# **********************************************************************************************************************
def candle_islem(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales
    v_toplam = 0

    time.sleep(2.333)
    closes.append(close)
    highes.append(high)
    lowes.append(low)
    openes.append(open)
    #

    if v_alim_var == 0:
        v_ema_cross_up, v_ema_cross_down, v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_30m_c, v_45m_c, v_60m_c, \
        ema_artik, v_10m_c, v_120m_c = check_exist_ema_second(v_symbol, openes, closes, highes, lowes, 10, 30)

        if v_ema_cross_up == 1:
            kesmeler.append(1)
        else:
            kesmeler.append(0)

        # Son 5 dk içinde kesme varsa
        if len(kesmeler) > 15:
            kesmeler.pop(0)

        for i in range(len(kesmeler)):
            v_toplam = v_toplam + int(kesmeler[-i - 1])

        if v_1m_c > 30:
            v_hata_mesaj = 'HATAA..  = ' + str(v_symbol) + ' Fiyat=' + \
                           str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                           'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj)
        # v_ema_cross_up==1 and close > float(v_15m_c) and close > float(v_30m_c) and close > float(v_45m_c) and close > float(v_60m_c):
        if v_1m_c > v_ziplama_oran and close > float(v_3m_c) and close > float(v_5m_c) and (
                v_toplam >= 1 or ema_artik == 1) and \
                close > float(v_10m_c) and close > float(v_15m_c) and close > float(v_30m_c) and close > float(
            v_45m_c) and close > float(v_60m_c) and close > float(v_120m_c):
            # EKSTRA KONTROL
            if float(v_last_price_g) < float(close):
                v_hata_mesaj = 'Eksiye Gidiş Başlamıştı girmedim....  = ' + str(v_symbol) + ' Fiyat=' + \
                               str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                               'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
                Telebot_v1.mainma(v_hata_mesaj)
                v_hizli_gonzales = 0
            else:
                v_hizli_gonzales = 1
                v_hata_mesaj = 'Hızlı Artan Var..  = ' + str(v_symbol) + ' Fiyat=' + \
                               str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                               'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
                Telebot_v1.mainma(v_hata_mesaj)
        else:
            print('Değişim Anormal Yok= ', v_symbol, datetime.now())
            v_hizli_gonzales = 0
    else:
        # SATIM prosedürü
        v_ema_cross_up, v_ema_cross_down, v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_30m_c, v_45m_c, v_60m_c, \
        ema_artik, v_10m_c , v_120m_c = check_exist_ema_second(v_symbol, openes, closes, highes, lowes, 5, 20)

        # Alım yaptıktan sonraki ilk kırmızı mum var mı ? ve de kapanışın altına siyat indi mi bu 3 sn içinde
        # bunu ilk kırmızı mum sonrası düşüş trendi devam ediyor mu yoksa kandırma mumu mu bunu anlamak için
        # kapanış değeri altına düştü ise, düşüş devam ediyordur. Çıkmalısın..Yoksa kapanıştan yüksek bir anlık fiyat
        # yeşillenmenin başladığını gösterir. çıkma bekle.. Acil satım prosedürü bundan sonra devreye girsin.
        # Taki diğer mum kapanışı olana kadar.
        # ***************NEGATİF MUM************         En son kapanışın da aşağısına inerse son fiyat çık
        if v_ema_cross_down == 1 or (
                float(openes[-1]) > float(closes[-1]) and float(closes[-1]) > float(v_last_price_g)):
            v_ters_kesim = 1
            vm1 = 'Çık!..  = ' + str(v_symbol) + str(datetime.now())
            # Telebot_v1.mainma(vm1)
        else:
            print('İçerde alım var fakat satılamadı  ', v_symbol, datetime.now())
            v_ters_kesim = 0

    if len(closes) > 500:
        closes.pop(0)
        highes.pop(0)
        lowes.pop(0)
        openes.pop(0)


# *********************************************
def candle_islem_acil_alim(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales
    v_toplam = 0

    # if v_acil_al == 0:
    time.sleep(2.333)
    closes.append(close)
    highes.append(high)
    lowes.append(low)
    openes.append(open)

    v_ema_cross_up, v_ema_cross_down, v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_30m_c, v_45m_c, v_60m_c, \
    ema_artik, v_10m_c,v_120m_c = check_exist_ema_second(v_symbol, openes, closes, highes, lowes, 10, 30)

    for i in range(len(kesmeler)):
        v_toplam = v_toplam + int(kesmeler[-i - 1])

    # v_ema_cross_up==1 and close > float(v_15m_c) and close > float(v_30m_c) and close > float(v_45m_c) and close > float(v_60m_c):
    if v_1m_c > v_ziplama_oran and close > float(v_3m_c) and close > float(v_5m_c) and (
            v_toplam >= 1 or ema_artik == 1) and \
            close > float(v_10m_c) and close > float(v_15m_c) and close > float(v_30m_c) and close > float(
        v_45m_c) and close > float(v_60m_c) and close > float(v_120m_c) :
        # EKSTRA KONTROL
        if float(v_last_price_g) < float(close):
            v_hata_mesaj = 'Acil...Eksiye Gidiş Başlamıştı girmedim....  = ' + str(v_symbol) + ' Fiyat=' + \
                           str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                           'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj)
            v_hizli_gonzales = 0
        else:
            if v_hizli_gonzales != 1:
                v_hizli_gonzales = 1
                v_hata_mesaj = 'Acil...Hızlı Artan Var..  = ' + str(v_symbol) + ' Fiyat=' + \
                               str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                               'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
                Telebot_v1.mainma(v_hata_mesaj)
    else:

        print('Değişim Anormal Yok= ', v_symbol, datetime.now())
        v_hizli_gonzales = 0

    # Aciliyet nedeniyle geçici eklenen değerleri geri kaldır. Çünkü zaten mum kapanışında eklenecek.
    closes.pop()
    highes.pop()
    lowes.pop()
    openes.pop()


# ******************************************************************************************************
def check_exist_ema_second(v_symbol, open, close, high, low, v_kisa, v_uzun):
    # klines = v_cli.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
    # close = [float(entry[4]) for entry in klines]
    # high = [float(entry[2]) for entry in klines]
    # low = [float(entry[3]) for entry in klines]
    v_uz = len(close)
    v_len = len(close)
    v_l_c_p_c = close[-1]
    v_l_c_p_o = open[-1]
    v_l_c_p = ((float(v_l_c_p_c) - float(v_l_c_p_o)) / float(v_l_c_p_o)) * 100

    # v_l_c_p = float(v_l_c_p_c) - float(v_l_c_p_o)

    if v_uz < 2:
        print('Oluşmamış Değer var. T3', str(v_symbol))
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    else:
        v_last_closing_price = close[-1]
        v_previous_closing_price = close[-2]
        close_array = np.asarray(close)
        close_finished = close_array[:-1]
        high_array = np.asarray(high)
        high_finished = high_array[:-1]
        low_array = np.asarray(low)
        low_finished = low_array[:-1]

        # ******************    EMA -Eski usul kapanmış
        ema5k = ta.EMA(close_finished, int(v_kisa))
        ema20k = ta.EMA(close_finished, int(v_uzun))
        last_ema5k = ema5k[-1]
        last_ema20k = ema20k[-1]
        previous_ema5k = ema5k[-2]
        previous_ema20k = ema20k[-2]
        v_cross_up_ema = previous_ema20k > previous_ema5k and last_ema5k > last_ema20k
        v_cross_down_ema = previous_ema20k < previous_ema5k and last_ema5k < last_ema20k

        if v_cross_up_ema == True:
            ema_cross_upk = 1
        else:
            ema_cross_upk = 0

        if v_cross_down_ema == True:
            ema_cross_downk = 1
        else:
            ema_cross_downk = 0

        if last_ema20k >= last_ema5k:
            ema_artik = 0
        else:
            ema_artik = 1
        # ********************************************
        if v_len < 2:
            return ema_cross_upk, ema_cross_downk, 0, 0, 0, 0, 0, 0, 0, ema_artik, 0, 0
        else:
            v_p_c_p2 = close[-2]
            # v_1m_c = float(((v_l_c_p - v_p_c_p2) * 100) / v_p_c_p2)
            v_1m_c = v_l_c_p  # float(((v_l_c_p - v_p_c_p2) * 100) / v_p_c_p2)

        if v_len < 4:
            return ema_cross_upk, ema_cross_downk, v_1m_c, 0, 0, 0, 0, 0, 0, ema_artik, 0, 0
        else:
            v_p_c_p3 = close[-3]
            # v_3m_c = float(((v_l_c_p - v_p_c_p3) * 100) / v_p_c_p3)
        if v_len < 6:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, 0, 0, 0,0,0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, 0, 0, 0, 0, 0, ema_artik, 0, 0
        else:
            v_p_c_p5 = close[-5]
            # v_5m_c = float(((v_l_c_p - v_p_c_p5) * 100) / v_p_c_p5)

        if v_len < 11:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, v_5m_c, 0, 0,0,0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, 0, 0, 0, 0, ema_artik, 0, 0
        else:
            v_p_c_p10 = close[-10]
            # v_15m_c = float(((v_l_c_p - v_p_c_p15) * 100) / v_p_c_p15)

        if v_len < 16:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, v_5m_c, 0, 0,0,0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, 0, 0, 0, 0, ema_artik, v_p_c_p10, 0
        else:
            v_p_c_p15 = close[-15]
            # v_15m_c = float(((v_l_c_p - v_p_c_p15) * 100) / v_p_c_p15)

        if v_len < 31:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, v_5m_c, v_15m_c, 0,0,0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, v_p_c_p15, 0, 0, 0, ema_artik, v_p_c_p10, 0
        else:
            v_p_c_p30 = close[-30]
            # v_30m_c = float(((v_l_c_p - v_p_c_p30) * 100) / v_p_c_p30)

        if v_len < 46:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_30m_c,0,0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, v_p_c_p15, v_p_c_p30, 0, 0, ema_artik, v_p_c_p10, 0
        else:
            v_p_c_p45 = close[-45]
            # v_45m_c = float(((v_l_c_p - v_p_c_p45) * 100) / v_p_c_p45)

        if v_len < 61:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, v_5m_c, v_15m_c,v_30m_c,v_45m_c, 0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, v_p_c_p15, v_p_c_p30, v_p_c_p45, 0, ema_artik, v_p_c_p10, 0
        else:
            v_p_c_p60 = close[-60]

        if v_len < 121:
            # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c, v_5m_c, v_15m_c,v_30m_c,v_45m_c, 0
            return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, v_p_c_p15, v_p_c_p30, v_p_c_p45, 0, ema_artik, v_p_c_p10, 0
        else:
            v_p_c_p120 = close[-120]
            # v_60m_c = float(((v_l_c_p - v_p_c_p60) * 100) / v_p_c_p60)

        # return ema_cross_upk, ema_cross_downk, ema_cross_up, ema_cross_down, ema_arti, ema_artik, \
        #        v_last_closing_price, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, \
        #        v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p
        # return ema_cross_upk, ema_cross_downk, v_1m_c, v_3m_c,v_5m_c, v_15m_c,v_60m_c
        return ema_cross_upk, ema_cross_downk, v_1m_c, v_p_c_p3, v_p_c_p5, v_p_c_p15, \
               v_p_c_p30, v_p_c_p45, v_p_c_p60, ema_artik, v_p_c_p10, v_p_c_p120

        """
        # ***************EMA -Burada nan değerler vardı. Satarken Online EMA
        ema5 = ta.EMA(close_array, 5)
        ema20 = ta.EMA(close_array, 20)
        ema5 = ema5[~np.isnan(ema5)]
        ema20 = ema20[~np.isnan(ema20)]
        last_ema5 = ema5[-1]
        last_ema20 = ema20[-1]
        previous_ema5 = ema5[-2]
        previous_ema20 = ema20[-2]
        ema_cross_up = previous_ema20 > previous_ema5 and last_ema5 > last_ema20
        ema_cross_down = previous_ema20 < previous_ema5 and last_ema5 < last_ema20
        if last_ema20 >= last_ema5:
            ema_arti = 0
        else:
            ema_arti = 1
        # if  ema_cross_up ==True:
        #    print('Bekleeee')
        # ****************************** STOCH RSI
        stochasticRsiF, stochasticRsiS = generateStochasticRSI(close_array, timeperiod=14)
        if v_stoc_hesaplama == 55:  # or stochasticRsiF==0:
            stoc_cross_up = False
            stoc_cross_down = False
            stoc_arti = 0
        else:
            last_stochasticRsiF = stochasticRsiF[-1]
            last_stochasticRsiS = stochasticRsiS[-1]
            previous_stochasticRsiF = stochasticRsiF[-2]
            previous_stochasticRsiS = stochasticRsiS[-2]
            stoc_cross_up = previous_stochasticRsiF < previous_stochasticRsiS and last_stochasticRsiS < last_stochasticRsiF
            stoc_cross_down = previous_stochasticRsiF > previous_stochasticRsiS and last_stochasticRsiS > last_stochasticRsiF
            if last_stochasticRsiF >= last_stochasticRsiS:
                stoc_arti = 1
            else:
                stoc_arti = 0
        # *********************************    ADX
        # plus di ve minus di değerleri bir önceki çubuğun değerlerini alıyor.Güncellemeyi yeni 1 dk başladıktan sonra yapıyor
        adx = ta.ADX(high_finished, low_finished, close_finished, timeperiod=14)
        plus_di = ta.PLUS_DI(high_finished, low_finished, close_finished, timeperiod=14)
        minus_di = ta.MINUS_DI(high_finished, low_finished, close_finished, timeperiod=14)
        # last_adx = adx[-1]
        last_plus_di = plus_di[-1]
        last_minus_di = minus_di[-1]
        previous_plus_di = plus_di[-2]
        previous_minus_di = minus_di[-2]
        adx_cross_up = previous_plus_di < previous_minus_di and last_minus_di < last_plus_di
        if last_plus_di >= last_minus_di:
            adx_arti = 1
        else:
            adx_arti = 0
        adx_cross_down = previous_plus_di > previous_minus_di and last_minus_di > last_plus_di
        """


# ***********************************************************************************************************************
def son_fiyat_getir(msg):
    global v_sembol_islenen, v_last_price_g
    # print('Fiyat', float(price[v_symbol]))
    if msg['e'] != 'error':
        v_last_price_g = float(msg['c'])
        # print('Fiyat', float(v_last_price_g),datetime.now())
    else:
        v_last_price_g = 0
        vmesaj = 'Hata - Son fiyat sıfır!..btc_pairs_trade  = ' + str(v_sembol_islenen)
        Telebot_v1.mainma(vmesaj)
    # print('Fiyat', v_last_price_g,datetime.now())
    if v_last_price_g == 0:
        time.sleep(0.1)


# ***********************************************************************************************************************
def socket_thread_front(v_symbol, v_inter):
    global vn_front, ws_front_g, v_sembol_islenen
    # v_symbol = v_symbol.lower()
    v_sembol_islenen = v_symbol
    bsm = ThreadedWebsocketManager(api_key=API_Config.API_KEY, api_secret=API_Config.API_SECRET)
    bsm.start()
    bsm.start_symbol_ticker_socket(symbol=v_symbol, callback=son_fiyat_getir)
    bsm.join(1.99)
    # print('fff')


# ***********************************************************************************************************************
# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter):
    global vn_front, ws_front_g
    v_symbol = v_symbol.lower()
    v_sembol_deg1 = f'[{v_symbol}@kline_{v_inter}]'  # <symbol>@kline_<interval>
    # v_sembol_deg1 = f'[{v_symbol}@miniTicker]'  # <symbol>@miniTicker
    v_sembol_deg5 = v_sembol_deg1.replace("[", "")
    v_sembol_deg5 = v_sembol_deg5.replace("]", "")
    vn_front = [v_sembol_deg5]
    socket_f = 'wss://stream.binance.com:9443/ws'
    ws_front = websocket.WebSocketApp(socket_f, on_message=on_message_f, on_open=on_open_f, on_close=on_close_f)
    wst = threading.Thread(target=ws_front.run_forever)
    wst.start()
    wst.join(2)


# ***********************************************************************************************************************
def dosyalari_temizle():
    open("Alinanlar.txt", 'w').close()
    open("Satilanlar.txt", 'w').close()


# ***********************************************************************************************************************
def dosya_aktar():
    global v_dosya_coin
    # #
    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write()
    DB_transactions3.high_oran_coin()
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open('Sembol3.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_symbol = line

            v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
            v_ema_arti_3m, v_3m_sonfiyat, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, v_1m_c, \
            v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p = check_exist(v_symbol, '1m', 500, v_client)
            # time.sleep(0.33)
            # if adx_arti == 1 and stoc_arti==1 and v_3m_c>0 and v_15m_c>0 and v_60m_c> 0:
            if 1 == 1:  # v_3m_c > 0 and v_ema_arti_3m == 1:
                if i <= 40:
                    v_dosya_coin.append(line)
                    print('Dosyaya eklenen Coin..: ', line, i, '**', datetime.now())
                else:
                    print('Devamı...Dosyaya eklenen Coin..: ', line, i, datetime.now())
                i += 1
            else:
                print('Dosyaya Uygun Değil .: ', line, i, datetime.now())
    dosya.close()
    print('Dosya Tamamlandı', v_dosya_coin)

    # ***************Temizlik***********************
    with open('sabikalilar.txt', 'r') as dosya_sabika:
        i = 0
        for line in dosya_sabika.read().splitlines():
            if (line in v_dosya_coin):
                v_dosya_coin.remove(line)
    dosya_sabika.close()
    print('Sabıkalılar Temizlendi.', v_dosya_coin)


# ***********************************************************************************************************************
def run_frontdata(v_sem, v_int):
    try:
        get_first_set_of_closes(v_sem, v_int)
        # EMA, ADX gibi indikatörleri sn likte oluşturmak için kline lı kullanım..Yenileme 2 sn. Ama her sn veri geliyor.
        socket_front(v_sem, v_int)
        # Son fiyatı almak için. Sn lik data yenileme
        socket_thread_front(v_sem, v_int)
        # time.sleep(2)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_sem)
        print('Mesajı', str(e.message), v_sem)
        # except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..run_frontdata  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_sem) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def get_snapshot(v_sembol, v_limit):
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())


# ***********************************************************************************************************************
def main_islem(v_sembol_g, v_limit_g, v_inter_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
               v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran):
    print('Başladı ', v_sembol_g, datetime.now())
    try:
        # time.sleep(1.333)
        run_frontdata(v_sembol_g, v_inter_g)
        time.sleep(0.33)
        islem(v_sembol_g, v_limit_g, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_ziplama_oran)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_sembol_g)
        print('Mesajı', str(e.message), v_sembol_g)
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem  = ' + str(e.message) + '-' + str(e.status_code) + '-' + str(
            v_sembol_g) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def islem(v_sembol_g, v_limit_g, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_zip):
    global v_last_price_g, v_open_price, v_alim_var, v_ziplama_oran
    v_ziplama_oran = float(v_zip)
    v_on_zaman = ''
    # time.sleep(1.66)
    try:
        while (True):
            v_zaman = str(datetime.now())[0:16]
            v_kota_doldu = icerdeki_alinan()
            if v_kota_doldu >= 15:
                if v_on_zaman != v_zaman:
                    v_mesajx = 'İçerde alım var. Kota dolduğu için yeni alım yapılamıyor!!!...' + str(datetime.now())
                    Telebot_v1.mainma(v_mesajx)
                    v_on_zaman = v_zaman

                if v_alim_var == 1:
                    time.sleep(0.01)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                     v_zarar_oran, v_test_prod)
            else:
                if v_alim_var == 0:
                    time.sleep(0.01)
                    if v_last_price_g != 0:
                        print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, datetime.now())

                        whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                         v_zarar_oran, v_test_prod)
                else:
                    time.sleep(0.01)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                     v_zarar_oran, v_test_prod)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_sembol_g)
        print('Mesajı', str(e.message), v_sembol_g)
        # except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_sembol_g) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def icerdeki_alinan():
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open("Satilanlar.txt", "r").readlines())
    genel_alimlar = len(open("Alinanlar.txt", "r").readlines())
    v_icerde = int(genel_alimlar) - int(genel_satimlar)
    return v_icerde


# ***********************************************************************************************************************
def alinan_satilan_esitmi():
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open("Satilanlar.txt", "r").readlines())
    genel_alimlar = len(open("Alinanlar.txt", "r").readlines())
    if genel_satimlar == genel_alimlar:
        return 1
    else:
        return 0


# ***********************************************************************************************************************
def generateStochasticRSI(close_array, timeperiod):
    global v_stoc_hesaplama
    v_stoc_hesaplama = 5
    # 1) ilk aşama rsi değerini hesaplıyoruz.
    rsi = ta.RSI(close_array, timeperiod=timeperiod)
    # 2) ikinci aşamada rsi arrayinden sıfırları kaldırıyoruz.
    rsi = rsi[~np.isnan(rsi)]
    # 3) üçüncü aşamada ise ta-lib stoch metodunu uyguluyoruz.
    # print('uzunn',len(rsi))
    if len(rsi) < 3:
        print('uzunn', len(rsi))
        v_stoc_hesaplama = 55
        return 0, 0
    else:
        stochrsif, stochrsis = ta.STOCH(rsi, rsi, rsi, fastk_period=14, slowk_period=3, slowd_period=3)
    # print(' Değerler = ',stochrsif, stochrsis)
    return stochrsif, stochrsis


# ****************************************************EMA ve V_Client **************************************************
def get_first_set_of_closes(v_symbol, v_inter):
    global closes, highes, lowes, openes, v_dosya_coin
    try:
        if v_inter == '1m':
            v_sure = "5 hour ago UTC"
        elif v_inter == '3m':
            v_sure = "15 hour ago UTC"
        elif v_inter == '1s':
            v_sure = "5 minute ago UTC"
        for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
            closes.append(float(kline[4]))
            highes.append(float(kline[2]))
            lowes.append(float(kline[3]))
            openes.append(float(kline[1]))

    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def check_exist(v_symbol, v_interval, v_limit, v_cli):
    klines = v_cli.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
    close = [float(entry[4]) for entry in klines]
    high = [float(entry[2]) for entry in klines]
    low = [float(entry[3]) for entry in klines]

    v_uz = len(close)
    v_len = len(close)
    v_l_c_p = close[-1]

    if v_uz < 2:
        print('Oluşmamış Değer var. T3', str(v_symbol), str(v_interval))
        return False, False, False, False, 0, 0, 0, False, False, 0, 0, 0, 0, 0, 0, 0
    else:
        v_last_closing_price = close[-1]
        v_previous_closing_price = close[-2]
        close_array = np.asarray(close)
        close_finished = close_array[:-1]
        high_array = np.asarray(high)
        high_finished = high_array[:-1]
        low_array = np.asarray(low)
        low_finished = low_array[:-1]

        # ******************    EMA -Eski usul kapanmış
        ema5k = ta.EMA(close_finished, 5)
        ema20k = ta.EMA(close_finished, 20)
        last_ema5k = ema5k[-1]
        last_ema20k = ema20k[-1]
        previous_ema5k = ema5k[-2]
        previous_ema20k = ema20k[-2]
        ema_cross_upk = previous_ema20k > previous_ema5k and last_ema5k > last_ema20k
        ema_cross_downk = previous_ema20k < previous_ema5k and last_ema5k < last_ema20k
        if last_ema20k >= last_ema5k:
            ema_artik = 0
        else:
            ema_artik = 1

        # ***************EMA -Burada nan değerler vardı. Satarken Online EMA
        ema5 = ta.EMA(close_array, 5)
        ema20 = ta.EMA(close_array, 20)
        ema5 = ema5[~np.isnan(ema5)]
        ema20 = ema20[~np.isnan(ema20)]
        last_ema5 = ema5[-1]
        last_ema20 = ema20[-1]
        previous_ema5 = ema5[-2]
        previous_ema20 = ema20[-2]
        ema_cross_up = previous_ema20 > previous_ema5 and last_ema5 > last_ema20
        ema_cross_down = previous_ema20 < previous_ema5 and last_ema5 < last_ema20
        if last_ema20 >= last_ema5:
            ema_arti = 0
        else:
            ema_arti = 1
        # if  ema_cross_up ==True:
        #    print('Bekleeee')
        # ****************************** STOCH RSI
        stochasticRsiF, stochasticRsiS = generateStochasticRSI(close_array, timeperiod=14)
        if v_stoc_hesaplama == 55:  # or stochasticRsiF==0:
            stoc_cross_up = False
            stoc_cross_down = False
            stoc_arti = 0
        else:
            last_stochasticRsiF = stochasticRsiF[-1]
            last_stochasticRsiS = stochasticRsiS[-1]
            previous_stochasticRsiF = stochasticRsiF[-2]
            previous_stochasticRsiS = stochasticRsiS[-2]
            stoc_cross_up = previous_stochasticRsiF < previous_stochasticRsiS and last_stochasticRsiS < last_stochasticRsiF
            stoc_cross_down = previous_stochasticRsiF > previous_stochasticRsiS and last_stochasticRsiS > last_stochasticRsiF
            if last_stochasticRsiF >= last_stochasticRsiS:
                stoc_arti = 1
            else:
                stoc_arti = 0
        # *********************************    ADX
        # plus di ve minus di değerleri bir önceki çubuğun değerlerini alıyor.Güncellemeyi yeni 1 dk başladıktan sonra yapıyor !!!!!!!!!!!!!!!!!!!!!!!1
        adx = ta.ADX(high_finished, low_finished, close_finished, timeperiod=14)
        plus_di = ta.PLUS_DI(high_finished, low_finished, close_finished, timeperiod=14)
        minus_di = ta.MINUS_DI(high_finished, low_finished, close_finished, timeperiod=14)
        # last_adx = adx[-1]
        last_plus_di = plus_di[-1]
        last_minus_di = minus_di[-1]
        previous_plus_di = plus_di[-2]
        previous_minus_di = minus_di[-2]
        adx_cross_up = previous_plus_di < previous_minus_di and last_minus_di < last_plus_di
        if last_plus_di >= last_minus_di:
            adx_arti = 1
        else:
            adx_arti = 0
        adx_cross_down = previous_plus_di > previous_minus_di and last_minus_di > last_plus_di

        if v_len < 2:
            return 0, 0, 0, 0, 0
        else:
            v_p_c_p2 = close[-2]
            v_1m_c = float(((v_l_c_p - v_p_c_p2) * 100) / v_p_c_p2)

        if v_len < 4:
            return v_1m_c, 0, 0, 0, 0
        else:
            v_p_c_p3 = close[-3]
            v_3m_c = float(((v_l_c_p - v_p_c_p3) * 100) / v_p_c_p3)

        if v_len < 6:
            return v_1m_c, v_3m_c, 0, 0, 0
        else:
            v_p_c_p5 = close[-5]
            v_5m_c = float(((v_l_c_p - v_p_c_p5) * 100) / v_p_c_p5)

        if v_len < 16:
            return v_1m_c, v_3m_c, v_5m_c, 0, 0
        else:
            v_p_c_p15 = close[-15]
            v_15m_c = float(((v_l_c_p - v_p_c_p15) * 100) / v_p_c_p15)

        if v_len < 61:
            return v_1m_c, v_3m_c, v_5m_c, v_15m_c, 0
        else:
            v_p_c_p60 = close[-60]
            v_60m_c = float(((v_l_c_p - v_p_c_p60) * 100) / v_p_c_p60)

        return ema_cross_upk, ema_cross_downk, ema_cross_up, ema_cross_down, ema_arti, ema_artik, \
               v_last_closing_price, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, \
               v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p


# ***********************************************************************************************************************
def parametre_ata():
    # v_inter_g = '1s'
    v_inter_g = '3m'
    v_limit_g = 100
    v_in_g = '1000ms'
    v_islem_tutar = 20
    v_mod = 'S'
    v_test_prod = 'T'
    v_ziplama_oran = 0.5

    if v_mod == 'S':
        v_volume_fark_oran = 0.03  # İlgili bid veya ask satırının tüm tablodaki volume oranı
        v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
        v_kar_oran = 1.01
        v_zarar_oran = 0.99
        minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz
    elif v_mod == 'B':
        v_volume_fark_oran = 0.05  # İlgili bid veya ask satırının tüm tablodaki volume oranı
        v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
        v_kar_oran = 1.005
        v_zarar_oran = 0.995
        minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz
    else:
        v_volume_fark_oran = 0.05  # İlgili bid veya ask satırının tüm tablodaki volume oranı
        v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
        v_kar_oran = 1.003
        v_zarar_oran = 0.995
        minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz

    return v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
           v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran


# ***************************************************
def degiskenleri_basa_al():
    global v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales
    global v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook
    global v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla
    global closes, highes, lowes, openes, kesmeler

    v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales = 0, 0, 0, 0, 0, 0, 0, 0
    v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, [], [], {}
    v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
    v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla = '2022', 0, '', '', '', '', 0
    closes, highes, lowes, openes, kesmeler = [], [], [], [], []


# ***********************************************************************************************************************
if __name__ == '__main__':
    v_dosya_coin = []
    v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
    v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran = parametre_ata()

    try:
        while True:
            # usdtBalance = v_client.get_asset_balance(asset='BUSD').get('free')
            vm = 'İlk Başladı.........' + str(datetime.now())
            Telebot_v1.mainma(vm)
            print(vm)
            while True:
                print('Başladı.........', datetime.now())
                dosyalari_temizle()
                dosya_aktar()
                degiskenleri_basa_al()

                # Eğer uygun coin bulamadıysan yeniden başa dön
                if len(v_dosya_coin) < 1:
                    v_maxw = 1
                    break
                else:
                    v_maxw = len(v_dosya_coin)

                with concurrent.futures.ProcessPoolExecutor(max_workers=v_maxw) as executer:
                    results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g, v_islem_tutar,
                                               v_volume_fark_oran, v_oran, v_kar_oran,
                                               v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran) for p
                               in
                               range(len(v_dosya_coin))]
                    # print('Başla.', results)
                    while True:
                        time.sleep(1800)
                        v_esit = alinan_satilan_esitmi()
                        # v_esit =0
                        if v_esit == 1:
                            active = multiprocessing.active_children()
                            for child in active:
                                child.terminate()
                                # block until all children have closed
                            for child in active:
                                child.join()
                            # report active children
                            active = multiprocessing.active_children()
                            print(f'Active Children: {len(active)}')
                            v_m = 'Tüm Processler Kapatıldı...Yeniden başlanacak = ' + str(datetime.now())
                            print('Tüm Processler Kapatıldı...Yeniden başlanacak = ')
                            Telebot_v1.mainma(v_m)
                            break
                        else:
                            v_m = 'İçerde alım olduğundan yenileyemedi.....' + str(datetime.now())
                            Telebot_v1.mainma(v_m)

                print('Çalışmaya başladılar...SON')
    except BinanceAPIException as e:
        print('Status code', str(e.status_code))
        print('Mesajı', str(e.message))
        # except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
