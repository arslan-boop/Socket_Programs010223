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

v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales = 0, 0, 0, 0, 0, 0, 0, 0
v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, [], [], {}
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla = '2022', 0, '', '', '', '', 0
closes, highes, lowes, kesmeler, openes = [], [], [], [], []
v_dosya_alinan,v_dosya_satilan,v_dosya_sembol,v_dosya_sabika,\
v_dosya_parametre,v_dosya_acilsat,v_dosya_genelbuy,v_dosya_sonuc= '', '','', '', '', '','', ''


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

def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_bakiye,v_program_tip):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati, v_last_price_g, v_alim_miktar
    global v_client, v_alim_timestamp, v_alim_zamani, v_hizli_gonzales, v_ters_kesim

    if v_alim_var == 0:
        try:
            v_zip = 0
            if v_hizli_gonzales == 1:  # Alım yap denmiş demektir.
                # # Program çalışırken parametrelerde değişiklik ihtiyacı olursa online yapmak için eklendi.
                # v_inter_g1, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
                # v_zarar_oran1, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye = parametre_ata()

                if v_test_prod == 'P':
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani = buy_coin(v_symbol, v_islem_tutar, v_kar_oran,
                                                                           v_zarar_oran, v_zip, v_bakiye,v_program_tip)
                else:
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani = buy_coin_test(v_symbol, v_islem_tutar, v_kar_oran,
                                                                                v_zarar_oran, v_zip, v_bakiye,v_program_tip)

                v_alim_var = 1
                v_hizli_gonzales = 0
            else:
                # print('')
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

            # # Program çalışırken parametrelerde değişiklik ihtiyacı olursa online yapmak için eklendi.
            # v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
            # v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye = parametre_ata()

            # Acil Satım emri varsa
            v_acilsat = acil_satim(v_symbol)

            # ******************************************************Belirlenen kar sağlandıysa
            if float(v_last_price_g) > float(v_hedef_bid_global):
                v_satim_sebeb = 'Kar Hedefine Ulasti'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani,v_satim_sebeb,v_program_tip)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani,v_satim_sebeb,v_program_tip)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            # ********************************************************Belirlenen zararın altına indiyse
            elif float(v_last_price_g) < float(v_hedef_ask_global):
                v_satim_sebeb = 'Zarar Seviyesinin Altina Dustu'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 2, v_alim_zamani,v_satim_sebeb,v_program_tip)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 2, v_alim_zamani,v_satim_sebeb,v_program_tip)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            # **********************************************************İlgili süre dolduysa
            elif (v_satim_timestamp >= v_alim_timestamp) and float(v_alim_fiyati) >= float(v_last_price_g):
                v_satim_sebeb = 'Uyusuk Cıktı'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 3, v_alim_zamani,v_satim_sebeb,v_program_tip)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 3, v_alim_zamani,v_satim_sebeb,v_program_tip)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            # ***********************************************************2.mum da eksiye döndüyse
            elif v_ters_kesim == 1:  # Satım koşulları gerçekleşmiş.
                v_satim_sebeb = '2.mum Kırmızıya Dondu'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani,v_satim_sebeb,v_program_tip)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani,v_satim_sebeb,v_program_tip)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            # ************************************************************** Acil satım yapılacaksa (manuel müdahale)
            elif v_acilsat == 1:  # Satım koşulları gerçekleşmiş.
                v_satim_sebeb = 'Acil Satimi Istendi.'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani,v_satim_sebeb,v_program_tip)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani,v_satim_sebeb,v_program_tip)
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
def sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip, v_alim_zamani,v_satim_sebeb,v_program_tip):
    global v_alim_var,v_dosya_sabika,v_dosya_genelbuy,v_dosya_alinan,v_dosya_satilan,v_dosya_sabika,v_dosya_sonuc
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
                    v_kisa_mes = 'KARLA KAPADI - '+str(v_satim_sebeb)
                else:
                    v_kisa_mes = 'Karla Sattı..'+str(v_satim_sebeb)

                v_oran_mesaj = '- Kar Oranı :'
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.8f}".format(float(v_alim_fiyati)) + '*' + \
                                   "{:.8f}".format(float(v_satim_fiyati)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani) + '*' + str(
                    v_alim_zamani)
            else:
                v_profit_oran = float(((float(v_alim_fiyati) - float(v_satim_fiyati)) * 100) / float(v_alim_fiyati))
                if v_tip == 3:
                    v_kisa_mes = 'ZARARLA KAPADI.'+str(v_satim_sebeb)
                else:
                    v_kisa_mes = 'Zararla Sattı..'+str(v_satim_sebeb)

                v_oran_mesaj = '- Zarar Oranı :'
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.8f}".format(
                    float(v_alim_fiyati)) + '*' + "{:.8f}".format(float(v_satim_fiyati)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + \
                                   str(v_satim_zamani) + '*' + str(v_alim_zamani)

            v_mess1 = 'Program Tipi = '+str(v_program_tip)+ v_kisa_mes + ' Hedefi : ' + "{:.8f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                      '- Alım Fiyatı :' + "{:.8f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.8f}".format(float(v_satim_fiyati)) + \
                      str(v_oran_mesaj) + "{:.8f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(v_satim_zamani) + \
                      'Alım Zamanı : ' + str(v_alim_zamani)

            # ******Alınanı 4 saat boyunca bir daha girme******
            Telebot_v1.sabikali_yap(v_symbol,v_dosya_sabika)

            # ******************
            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj,v_dosya_sonuc)
            v_alim_var = 0
            Telebot_v1.genel_alimlar(v_symbol, 'S',v_dosya_genelbuy,v_dosya_alinan,v_dosya_satilan,v_dosya_sabika)
            Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)

        else:
            v_hata = 'SATIM işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.sell_coin.   = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip, v_alim_zamani,v_satim_sebeb,v_program_tip):
    global v_alim_var2

    try:
        v_son_fiyat = float(v_last_price_g)
        v_satim_fiyati = v_son_fiyat
        v_satim_zamani = str(datetime.now())

        if float(v_satim_fiyati) > float(v_alim_fiyati):
            v_profit_oran = float(((float(v_satim_fiyati) - float(v_alim_fiyati)) * 100) / float(v_alim_fiyati))
            if v_tip == 3:
                v_kisa_mes = 'KARLA KAPADI - '+str(v_satim_sebeb)
            else:
                v_kisa_mes = 'Karla Sattı..'+str(v_satim_sebeb)

            v_oran_mesaj = '- Kar Oranı :'
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.8f}".format(float(v_alim_fiyati)) + '*' + \
                               "{:.8f}".format(float(v_satim_fiyati)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani) + '*' + str(
                v_alim_zamani)
        else:
            v_profit_oran = float(((float(v_alim_fiyati) - float(v_satim_fiyati)) * 100) / float(v_alim_fiyati))
            if v_tip == 3:
                v_kisa_mes = 'ZARARLA KAPADI.'+str(v_satim_sebeb)
            else:
                v_kisa_mes = 'Zararla Sattı..'+str(v_satim_sebeb)

            v_oran_mesaj = '- Zarar Oranı :'
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.8f}".format(
                float(v_alim_fiyati)) + '*' + "{:.8f}".format(float(v_satim_fiyati)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + \
                               str(v_satim_zamani) + '*' + str(v_alim_zamani)

        # ******Alınanı 4 saat boyunca bir daha girme******
        Telebot_v1.sabikali_yap(v_symbol, v_dosya_sabika)

        v_mess1 = 'Program Tipi = '+str(v_program_tip)+  v_kisa_mes + ' Hedefi : ' + "{:.8f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                  '- Alım Fiyatı :' + "{:.8f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.8f}".format(float(v_satim_fiyati)) + \
                  str(v_oran_mesaj) + "{:.8f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(v_satim_zamani) + \
                  'Alım Zamanı : ' + str(v_alim_zamani)



        # ******************
        Telebot_v1.mainma(v_mess1)
        Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj, v_dosya_sonuc)
        v_alim_var = 0
        Telebot_v1.genel_alimlar(v_symbol, 'S', v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika)
        Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)

    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.11   = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def buy_coin(v_symbol, v_islem_tutar, v_kar_oran, v_zarar_oran, v_zip, v_bakiye,v_program_tip):
    global  v_dosya_genelbuy,v_dosya_alinan,v_dosya_satilan,v_dosya_sabika
    try:
        # bakiye_kontrol(v_bakiye)

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
            v_alim_timestamp = (current_timestamp + (480000)) / 1000
            # v_alim_zamani = str(datetime.now())[0:19]
        else:
            v_hata = 'Alım işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata)

        v_mess = 'Program Tipi = '+str(v_program_tip)+ str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'Miktar = ' + '--' + "{:.1f}".format(float(v_alim_miktar)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.1f}".format(float(v_islem_tutar)) + '--' + \
                 'Zip=' + '--' + str(v_zip)
        # Telegram mesajo
        Telebot_v1.mainma(v_mess)
        Telebot_v1.genel_alimlar(v_symbol, 'A',v_dosya_genelbuy,v_dosya_alinan,v_dosya_satilan,v_dosya_sabika)
        v_sembolmik = v_symbol.replace("BUSD", "")
        v_alim_miktar = v_client.get_asset_balance(asset=v_sembolmik).get('free')
        v_alim_miktar = get_round_step_quantity(v_symbol, float(v_alim_miktar))

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, \
               v_alim_timestamp, v_alim_miktar, v_alim_fiyati, v_alim_zamani


    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Alırken  Hata Oluştu!!.. buy_coin  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ************************************************************ ************************TEST ALIM**********************/
def buy_coin_test(v_symbol, v_islem_tutar, v_kar_oran, v_zarar_oran, v_zip, v_bakiye,v_program_tip):
    global v_last_price_g, v_alim_zamani, v_alim_var,v_dosya_genelbuy,v_dosya_alinan,v_dosya_satilan,v_dosya_sabika
    try:
        # bakiye_kontrol(v_bakiye)

        v_son_fiyat = float(v_last_price_g)
        v_alim_zamani = str(datetime.now())
        v_alim_fiyati = v_son_fiyat
        v_hedef_bid = float(v_son_fiyat * v_kar_oran)
        v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
        v_hedef_bid_global = v_hedef_bid
        v_hedef_ask_global = v_hedef_ask
        current_timestamp = round(time.time() * 1000)
        v_alim_timestamp = (current_timestamp + (480000)) / 1000
        # v_alim_var = 1

        v_mess = 'Program Tipi = '+str(v_program_tip)+str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.1f}".format(float(v_islem_tutar)) + '--' + \
                 'Zip=' + '--' + str(v_zip)
        # Telegram mesajo
        Telebot_v1.mainma(v_mess)
        Telebot_v1.genel_alimlar(v_symbol, 'A',v_dosya_genelbuy,v_dosya_alinan,v_dosya_satilan,v_dosya_sabika)

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
        v_ters_kesim, v_alim_var, v_hizli_gonzales, v_ziplama_oran, kesmeler, v_alim_zamani, v_mum_sayisi, v_dalga_oran
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
        # v_m = str(v_symbol) + '*' + 'Acil_Al..Oran' + '*' + "{:.2f}".format(float(x)) + '*' + str(datetime.now())
        # Telebot_v1.analiz_islem_log(v_m, v_symbol)
        v_acil_al = 1
        v_acil_oran = x
    else:
        v_acil_al = 0
        v_acil_oran = 0

    # *************************Normal işleyiş
    if is_candle_closed:  # or (v_acil_al == 1 and is_candle_closed == True):
        candle_islem(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                     v_mum_sayisi, v_dalga_oran)
        # v_m = str(v_symbol) + '*' + 'Normal_Kapanış' + '*' + str(open) + '*' + str(close) + '*' + "{:.2f}".format(
        #     float(x)) + '*' + str(datetime.now())
        # Telebot_v1.analiz_islem_log(v_m, v_symbol)

    # ************************Acil alım
    if v_acil_al == 1 and is_candle_closed == False:
        if v_alim_var == 0 and v_hizli_gonzales != 1:
            candle_islem_acil_alim(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes,
                                   v_ziplama_oran, v_mum_sayisi, v_dalga_oran)
            # v_m = str(v_symbol) + '*' + 'Acil Al' + '*' + str(open) + '*' + str(close) + '*' + str(v_ziplama_oran) + '*' + \
            #         "{:.2f}".format(float(x)) + '*' + str(datetime.now())
            # Telebot_v1.analiz_islem_log(v_m, v_symbol)

    # ************************* Acil Satım
    v_altime = str(v_alim_zamani)[0:16]
    v_sattime = str(datetime.now())[0:16]

    # Aynı dk içinde satmaya çalışma alındıysa
    if v_altime != v_sattime:
        if v_alim_var == 1 and is_candle_closed == False and v_ters_kesim == 0:
            candle_acil_satim(v_symbol, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                              v_dalga_oran)
            # v_m = str(v_symbol) + '*' + 'Acil SAT' + '*' + str(open) + '*' + str(close) + '*' + \
            #       "{:.2f}".format(float(x)) + '*' + str(datetime.now())
            # Telebot_v1.analiz_islem_log(v_m, v_symbol)


# *********************************************************************************************
def candle_acil_satim(v_symbol, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran, v_dalga_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales
    try:
        time.sleep(2.66)
        closes.append(close)
        highes.append(high)
        lowes.append(low)
        openes.append(open)

        if float(openes[-1]) > float(closes[-1]) and float(openes[-2]) > float(closes[-2]):
            v_ters_kesim = 1
            vm1 = 'Acil Satım Yapılacak...!..  = ' + str(v_symbol) + str(datetime.now()) + '*' + str(float(closes[-1])) \
                  + '*' + str(openes[-1]) + '*' + str(v_last_price_g)
            Telebot_v1.mainma(vm1)
        else:
            print('İçerde alım var fakat satılamadı  ', v_symbol, datetime.now())
            v_ters_kesim = 0

        closes.pop()
        highes.pop()
        lowes.pop()
        openes.pop()

    except BinanceAPIException as e:
        print('Status code', str(e.status_code))
        print('Mesajı', str(e.message))
        # except Exception as exp:
        v_hata_mesaj = 'Hata candle_acil_satim!..  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# **********************************************************************************************************************
def candle_islem(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                 v_mum_sayisi, v_dalga_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales
    v_toplam = 0
    try:
        closes.append(close)
        highes.append(high)
        lowes.append(low)
        openes.append(open)
        # time.sleep(2.333)

        if v_alim_var == 0:
            v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes,
                                                                                 lowes, 10, 30)
            v_girme, v_1m_c = check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, 2,
                                                 v_ziplama_oran)

            if v_ema_cross_up == 1:
                kesmeler.append(1)
            else:
                kesmeler.append(0)

            # Son 5 dk içinde kesme varsa
            if len(kesmeler) > 15:
                kesmeler.pop(0)

            v_toplam = int(sum(kesmeler))
            #
            # v_m = str(v_symbol) + '*' + 'Normal Kapanış İşlemde ..Alım tarafı' + '*' + str(v_girme) + '*' + str(v_1m_c) + \
            #       '*' + str(ema_artik) + '*' + str(v_ziplama_oran) + '*' + str(v_toplam) + '*' + str(datetime.now())
            # Telebot_v1.analiz_islem_log(v_m, v_symbol)

            if v_1m_c > v_ziplama_oran and v_girme == 0 and (v_toplam >= 1 or ema_artik == 1):
                v_hizli_gonzales = 1
                v_hata_mesaj = 'Hızlı Artan Var..  = ' + str(v_symbol) + ' Fiyat=' + \
                               str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                               'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
                Telebot_v1.mainma(v_hata_mesaj)
                # time.sleep(1)
            else:
                print('Değişim Anormal Yok= ', v_symbol, datetime.now())
                v_hizli_gonzales = 0
        else:
            time.sleep(2.333)
            # v_m = str(v_symbol) + '*' + 'Normal Kapanış İşlemde ..Satım tarafı' + '*' + \
            #       str(float(closes[-1])) + '*' + str(float(openes[-1])) + '*' + str(float(v_last_price_g)) + '*' + str(
            #     datetime.now())
            # Telebot_v1.analiz_islem_log(v_m, v_symbol)

            if float(openes[-1]) > float(closes[-1]) and float(closes[-1]) > float(v_last_price_g):
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

    except BinanceAPIException as e:
        print('Status code', str(e.status_code))
        print('Mesajı', str(e.message))
        # except Exception as exp:
        v_hata_mesaj = 'Hata candle_islem_acil_alim!..  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# *********************************************
def candle_islem_acil_alim(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                           v_mum_sayisi, v_dalga_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales
    v_toplam = 0
    try:
        # time.sleep(2.333)
        closes.append(close)
        highes.append(high)
        lowes.append(low)
        openes.append(open)

        v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes, lowes,
                                                                             10, 30)
        v_girme, v_1m_c = check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, 2,
                                             v_ziplama_oran)

        if v_ema_cross_up == 1:
            kesmeler.append(1)
        else:
            kesmeler.append(0)
            # Son 5 dk içinde kesme varsa
        if len(kesmeler) > 15:
            kesmeler.pop(0)

        v_toplam = int(sum(kesmeler))

        # v_m = str(v_symbol) + '*' + 'Acile Geldi' + '*' + str(v_girme) + '*' + str(v_1m_c) + \
        #       '*' + str(ema_artik) + '*' + str(v_ziplama_oran) + '*' + str(v_toplam) + '*' + str(datetime.now())
        # Telebot_v1.analiz_islem_log(v_m, v_symbol)

        if v_1m_c > v_ziplama_oran and v_girme == 0 and (v_toplam >= 1 or ema_artik == 1):
            v_hizli_gonzales = 1
            v_hata_mesaj = 'Acil...Hızlı Artan Var..  = ' + str(v_symbol) + ' Fiyat=' + \
                           str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                           'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj)
            # time.sleep(1)
        else:
            # v_m = str(v_symbol) + '*' + 'Acile Geldi Ama almadı' + '*' + str(v_girme) + '*' + str(v_1m_c) + \
            #       '*' + str(ema_artik) + '*' + str(v_ziplama_oran) + '*' + str(v_toplam) + '*' + str(datetime.now())
            # Telebot_v1.analiz_islem_log(v_m, v_symbol)

            print('Acil Alımı Durumu Olışmadı.... ', v_symbol, datetime.now())
            # v_hata_mesaj = 'Acil...Hızlı Artan Var..AMA ALMADIIII  = ' + str(v_symbol) + ' Fiyat=' + \
            #                str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) \
            #                +'Girme='+ str(v_girme) +'Toplam=' + str(v_toplam) + 'EMA=' +str(ema_artik)+\
            #                'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
            # Telebot_v1.mainma(v_hata_mesaj)
            # time.sleep(1)
            v_hizli_gonzales = 0

        # Aciliyet nedeniyle geçici eklenen değerleri geri kaldır. Çünkü zaten mum kapanışında eklenecek.
        closes.pop()
        highes.pop()
        lowes.pop()
        openes.pop()
        kesmeler.pop()

    except BinanceAPIException as e:
        print('Status code', str(e.status_code))
        print('Mesajı', str(e.message))
        # except Exception as exp:
        v_hata_mesaj = 'Hata candle_islem_acil_alim!..  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
    #
    # except Exception as exp:
    #     v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
    #     Telebot_v1.mainma(v_hata_mesaj)


# ************************
def check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, v_ilk_kontrol,
                       v_ziplama_oran):
    global v_dosya_sabika
    v_girme = 0
    v_close = closes[-1]
    v_open = openes[-1]
    v_artim_oran = ((float(v_close) - float(v_open)) / float(v_open)) * 100

    if len(closes) < int(v_mum_sayisi):
        v_say = len(closes)
    else:
        v_say = int(v_mum_sayisi)

    if v_ilk_kontrol == 1:
        v_min = float(closes[-1])
        v_max = float(closes[-1])
    else:
        v_min = float(closes[-2])
        v_max = float(closes[-2])

    for i in range(1, v_say):
        # print(closes[-i-1], v_l_c_p_c)
        if float(closes[-i - 1]) > v_max:
            v_max = float(closes[-i - 1])
        if float(closes[-i - 1]) < v_min:
            v_min = float(closes[-i - 1])
        # Son mum belirlenen aralıktaki en yüksek mum değilse girme
        if v_ilk_kontrol != 1:
            if float(closes[-i - 1]) > float(v_close):
                v_girme = v_girme + 1

    # v= str(v_symbol) +'Girme ilk kontrol=' + str(closes[-i - 1]) + 'Prev=' + str(v_close) + str(v_girme)+ 'Zaman=' + str(datetime.now())
    # Telebot_v1.mainma(v)

    # En yüksek mum kapanışının üstünde zıplama oran kadar yükselti olsun
    if v_ilk_kontrol != 1:
        if float(v_close) - float(v_max) < float(v_ziplama_oran):
            v_girme = v_girme + 1

    # print('MinMax', v_min, v_max, v_girme)
    v_dalgalanma_oran = ((float(v_max) - float(v_min)) / float(v_min)) * 100

    # Son mumdan öncekilerde mumlar arası dalgalanma belirlenen orandan büyükse bu yakın zamanda çıkmıştır
    # veya testre piyasası yine alma
    if float(v_dalgalanma_oran) > v_dalga_oran:
        v_girme = v_girme + 1

    # v =str(v_symbol) + 'Girme dalga=' + str(v_dalgalanma_oran) + 'Prev=' + str(v_close) + str(v_girme) + 'Zaman=' + str(datetime.now())
    # Telebot_v1.mainma(v)

    # Yakın zamanda alınmış bir mumsa sabıkalıdır yine alma. 4 saat ceza süresi
    # dolmadıysa alma

    with open(v_dosya_sabika, 'r') as dosya_sabika:
        for line in dosya_sabika.read().splitlines():
            aciklama = line
            s = aciklama.split("*")
            current_timestamp = round(time.time() * 1000)
            v_current_timestamp = (current_timestamp) / 1000
            v_current_timestamp = int(v_current_timestamp)

            if str(s[0]) == v_symbol and float(v_current_timestamp) < float(s[1]):
                v_girme = v_girme + 1
    # v = str(v_symbol) +'Girme sabıka=' +  'Prev=' + str(v_close) + 'Girme = '+str(v_girme) + 'Oran='+ str(v_artim_oran)+ 'Zaman=' + str(datetime.now())
    # Telebot_v1.mainma(v)
    # print('Girme 3', v_girme)

    return v_girme, v_artim_oran


# ***************EMA CHECK
def check_exist_ema_second(v_symbol, open, close, high, low, v_kisa, v_uzun):
    v_uz = len(close)
    if v_uz < 2:
        print('Oluşmamış Değer var. T3', str(v_symbol))
        return 0, 0, 0, 0
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

        return ema_cross_upk, ema_cross_downk, ema_artik


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
    bsm.join(0.66)
    # print('fff')


# ***********************************************************************************************************************
# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter, v_zam, v_dalga_or):
    global vn_front, ws_front_g, v_mum_sayisi, v_dalga_oran
    v_mum_sayisi = int(v_zam)
    v_dalga_oran = float(v_dalga_or)
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
    global v_dosya_alinan,v_dosya_satilan
    open(v_dosya_alinan, 'w').close()
    open(v_dosya_satilan, 'w').close()
    # open("sabikalilar.txt", 'w').close()


def uygun_olmayani_temizle(v_symbol, v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran):
    global openes, closes, highes, lowes
    get_first_set_of_closes(v_symbol, v_inter_g)
    # v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes, lowes, 10,30)
    v_girme, v_artim_oran = check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, 1,
                                               v_ziplama_oran)

    with open(v_dosya_sabika, 'r') as dosya_sabika:
        for line in dosya_sabika.read().splitlines():
            aciklama = line
            s = aciklama.split("*")
            current_timestamp = round(time.time() * 1000)
            v_current_timestamp = (current_timestamp) / 1000
            v_current_timestamp = int(v_current_timestamp)

            if str(s[0]) == v_symbol and float(v_current_timestamp) < float(s[1]):
                v_girme = v_girme + 1
    # v = str(v_symbol) +'Girme sabıka=' +  'Prev=' + str(v_close) + 'Girme = '+str(v_girme) + 'Oran='+ str(v_artim_oran)+ 'Zaman=' + str(datetime.now())
    # Telebot_v1.mainma(v)
    dosya_sabika.close()

    return v_girme


# ***********************************************************************************************************************
def dosya_aktar(v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran,v_program_tip):
    global v_dosya_coin,v_dosya_sembol,v_dosya_sabika
    # #
    DB_transactions3.database_baglan(v_program_tip)

    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write(v_dosya_sembol)
    DB_transactions3.high_oran_coin()
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open(v_dosya_sembol, 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_symbol = line

            # Uygun olmayanları listeden çıkar. Dalgalanma bandı dışındaki ve sabıkalıları temizler
            v_girme = uygun_olmayani_temizle(v_symbol, v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran)

            if v_girme == 0:  # v_3m_c > 0 and v_ema_arti_3m == 1:
                if i < 55:
                    v_dosya_coin.append(line)
                    print('Dosyaya eklenen Coin..: ', line, i, '**', datetime.now())
                else:
                    print('Devamı...Dosyaya eklenen Coin..: ', line, i, datetime.now())
                i += 1
            else:
                print('Dosyaya Uygun Değil .: ', line, i, datetime.now())
    dosya.close()
    print('Dosya Tamamlandı', v_dosya_coin)

    # # ***************Temizlik***********************
    # with open(v_dosya_sabika, 'r') as dosya_sabika:
    #     i = 0
    #     for line in dosya_sabika.read().splitlines():
    #         aciklama = line
    #         s = aciklama.split("*")
    #         if (s[0] in v_dosya_coin):
    #             v_dosya_coin.remove(s[0])
    # dosya_sabika.close()
    # print('Sabıkalılar Temizlendi.', v_dosya_coin)

    # Telebot_v1.genel_alimlar('BTCBUSD', 'S')


# ***********************************************************************************************************************
def run_frontdata(v_sem, v_int, v_mum_sayisi, v_dalga_oran):
    try:
        get_first_set_of_closes(v_sem, v_int)
        # EMA, ADX gibi indikatörleri sn likte oluşturmak için kline lı kullanım..Yenileme 2 sn. Ama her sn veri geliyor.
        socket_front(v_sem, v_int, v_mum_sayisi, v_dalga_oran)
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
               v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye,v_program_tip):
    print('Başladı ', v_sembol_g, datetime.now())
    try:
        # time.sleep(1.333)
        dosya_parametre_ata(v_program_tip)
        run_frontdata(v_sembol_g, v_inter_g, v_mum_sayisi, v_dalga_oran)
        time.sleep(0.33)
        islem(v_sembol_g, v_limit_g, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_ziplama_oran, v_bakiye,v_program_tip)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_sembol_g)
        print('Mesajı', str(e.message), v_sembol_g)
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem  = ' + str(e.message) + '-' + str(e.status_code) + '-' + str(
            v_sembol_g) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def islem(v_sembol_g, v_limit_g, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_zip, v_bakiye,v_program_tip):
    global v_last_price_g, v_open_price, v_alim_var, v_ziplama_oran
    v_ziplama_oran = float(v_zip)
    v_on_zaman = ''
    # time.sleep(1.66)
    try:
        while (True):
            v_tt = str(datetime.now())[0:16]
            v_kota_doldu = icerdeki_alinan()
            if v_kota_doldu >= 15:
                if v_on_zaman != v_tt:
                    v_mesajx = 'İçerde alım var. Kota dolduğu için yeni alım yapılamıyor!!!...' + str(datetime.now())
                    Telebot_v1.mainma(v_mesajx)
                    v_on_zaman = v_tt

                if v_alim_var == 1:
                    time.sleep(0.1)
                    # time.sleep(2)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                     v_zarar_oran, v_test_prod, v_bakiye,v_program_tip)
            else:
                if v_alim_var == 0:
                    time.sleep(0.1)
                    # time.sleep(2)
                    if v_last_price_g != 0:
                        # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, datetime.now())

                        whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                         v_zarar_oran, v_test_prod, v_bakiye,v_program_tip)
                else:
                    time.sleep(0.1)
                    # time.sleep(2)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                     v_zarar_oran, v_test_prod, v_bakiye,v_program_tip)
    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_sembol_g)
        print('Mesajı', str(e.message), v_sembol_g)
        # except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_sembol_g) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***********************************************************************************************************************
def icerdeki_alinan():
    global  v_dosya_satilan,  v_dosya_alinan
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open(v_dosya_satilan, "r").readlines())
    genel_alimlar = len(open(v_dosya_alinan, "r").readlines())
    v_icerde = int(genel_alimlar) - int(genel_satimlar)
    return v_icerde


# ***********************************************************************************************************************
def alinan_satilan_esitmi():
    global v_dosya_satilan, v_dosya_alinan
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open(v_dosya_satilan, "r").readlines())
    genel_alimlar = len(open(v_dosya_alinan, "r").readlines())
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
    global closes, highes, lowes, openes, v_dosya_coin, kesmeler
    try:
        i = 0
        if v_inter == '1m':
            v_sure = "9 hour ago UTC"
            v_son_15 = 520
        elif v_inter == '3m':
            v_sure = "20 hour ago UTC"
            v_son_15 = 350
        elif v_inter == '1s':
            v_sure = "15 minute ago UTC"
            v_son_15 = 850
        for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
            closes.append(float(kline[4]))
            highes.append(float(kline[2]))
            lowes.append(float(kline[3]))
            openes.append(float(kline[1]))
            i = i + 1
            # Kesmelerin ilk 15 sini doldur
            # print('son',len(closes))
            if i >= v_son_15:
                v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes,
                                                                                     lowes, 10, 30)
                if v_ema_cross_up == 1:
                    kesmeler.append(1)
                else:
                    kesmeler.append(0)

                if len(kesmeler) > 15:
                    kesmeler.pop(0)

        # print('kesmeler',kesmeler, sum(kesmeler) )

    except BinanceAPIException as e:
        print('Status code', str(e.status_code), v_symbol)
        print('Mesajı', str(e.message), v_symbol)
        # except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(e.message) + '-' + \
                       str(e.status_code) + '-' + str(v_symbol) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


def dosyadan_parametreleri_oku():
    global  v_dosya_parametre
    with open(v_dosya_parametre, 'r') as dosya:
        i = 1
        for line in dosya.read().splitlines():
            aciklama = line
            s = aciklama.split("*")
            if i == 1:
                v_inter_g = str(s[1])
            elif i == 2:
                v_limit_g = int(s[1])
            elif i == 3:
                v_in_g = str(s[1])
            elif i == 4:
                v_islem_tutar = float(s[1])
            elif i == 5:
                v_mod = str(s[1])
            elif i == 6:
                v_test_prod = str(s[1])
            elif i == 7:
                v_ziplama_oran = float(s[1])
            elif i == 8:
                v_mum_sayisi = int(s[1])
            elif i == 9:
                v_dalga_oran = float(s[1])
            elif i == 10:
                v_bakiye = float(s[1])
            elif i == 11:
                v_volume_fark_oran = float(s[1])
            elif i == 12:
                v_oran = float(s[1])
            elif i == 13:
                v_kar_oran = float(s[1])
            elif i == 14:
                v_zarar_oran = float(s[1])
            elif i == 15:
                minVolumePerc = float(s[1])
            i = i + 1

        dosya.close()
        print('Parametreler Yüklendi.', v_dosya_coin)
    return v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_mod, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye, \
           v_volume_fark_oran, v_oran, v_kar_oran, v_zarar_oran, minVolumePerc


# ***********************************************************************************************************************
def acil_satim(v_symbol):
    global v_dosya_acilsat
    v_satilacak = 0
    with open(v_dosya_acilsat, 'r') as dosya:
        for line in dosya.read().splitlines():
            if v_symbol == line:
                v_satilacak = 1
    return v_satilacak


# ***********************************************************************************************************************

def dosya_parametre_ata(program_tip):
    global v_dosya_alinan, v_dosya_satilan, v_dosya_sembol, \
        v_dosya_sabika, v_dosya_parametre, v_dosya_acilsat,v_dosya_genelbuy,v_dosya_sonuc
    if program_tip==1:
       v_dosya_alinan="DOSYALAR/Alinanlar.txt"
       v_dosya_satilan="DOSYALAR/Satilanlar.txt"
       v_dosya_sembol='DOSYALAR/Sembol3.txt'
       v_dosya_sabika='DOSYALAR/sabikalilar.txt'
       v_dosya_parametre='DOSYALAR/parametreler.txt'
       v_dosya_acilsat='DOSYALAR/acil_sat.txt'
       v_dosya_genelbuy="DOSYALAR/genel_buy.txt"
       v_dosya_sonuc="DOSYALAR/Sonuc.txt"
    elif program_tip == 2:
        v_dosya_alinan = "DOSYALAR/Alinanlar1.txt"
        v_dosya_satilan = "DOSYALAR/Satilanlar1.txt"
        v_dosya_sembol = 'DOSYALAR/Sembol31.txt'
        v_dosya_sabika = 'DOSYALAR/sabikalilar1.txt'
        v_dosya_parametre = 'DOSYALAR/parametreler1.txt'
        v_dosya_acilsat = 'DOSYALAR/acil_sat1.txt'
        v_dosya_genelbuy = "DOSYALAR/genel_buy1.txt"
        v_dosya_sonuc = "DOSYALAR/Sonuc1.txt"

def parametre_ata():
    # ********Dosyadan parametreleri oku
    v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_mod, v_test_prod, \
    v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye, \
    v_volume_fark_oran, v_oran, v_kar_oran, v_zarar_oran, minVolumePerc = dosyadan_parametreleri_oku()

    return v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
           v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye


# ***************************************************
def degiskenleri_basa_al():
    global v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales
    global v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook
    global v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla
    global closes, highes, lowes, openes, kesmeler
    global  v_dosya_alinan,v_dosya_satilan,v_dosya_sembol,v_dosya_sabika,v_dosya_parametre,v_dosya_acilsat,v_dosya_genelbuy,v_dosya_sonuc

    v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales = 0, 0, 0, 0, 0, 0, 0, 0
    v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, [], [], {}
    v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
    v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla = '2022', 0, '', '', '', '', 0
    closes, highes, lowes, openes, kesmeler = [], [], [], [], []
    v_dosya_alinan,v_dosya_satilan,v_dosya_sembol,v_dosya_sabika,v_dosya_parametre,v_dosya_acilsat,v_dosya_genelbuy,v_dosya_sonuc= '', '','', '', '', '','', ''

# *******************************************************************
def bakiye_kontrol(v_bakiye):
    usdtBalance = v_client.get_asset_balance(asset='BUSD').get('free')

    if float(usdtBalance) < float(v_bakiye):
        vm = 'Bakiye Yetersiz............' + str(usdtBalance) + str(datetime.now())
        Telebot_v1.mainma(vm)
        while True:
            print('Bakiye Yetersiz...', datetime.now())

def db_baglan():
    global  program_tip, con, cursor
    if program_tip ==1:
        DB_FILE = "../TRADE3.DB"
    else:
        DB_FILE = "../TRADE31.DB"

    con = sqlite3.connect(DB_FILE, timeout=10)
    cursor = con.cursor()
# ***********************************************************************************************************************
if __name__ == '__main__':
    global program_tip
    program_tip =2
    db_baglan()
    v_dosya_coin = []
    dosya_parametre_ata(program_tip)

    try:
        while True:
            v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
            v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye = parametre_ata()

            # Belirlenen bakiyenin altındaysa işlem yapma
            bakiye_kontrol(v_bakiye)

            vm = 'Program Tipi = '+str(program_tip)+'İlk Başladı.........' + str(datetime.now())
            Telebot_v1.mainma(vm)
            print(vm)
            while True:
                print('Başladı.........', datetime.now())
                dosyalari_temizle()
                dosya_aktar(v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran,program_tip)
                degiskenleri_basa_al()

                vm = 'Program Tipi = '+str(program_tip)+'İşlem Yapacağı Coinler........' + str(len(v_dosya_coin)) + '-' + str(v_dosya_coin) + '-' + str(datetime.now())
                Telebot_v1.mainma(vm)

                # Eğer uygun coin bulamadıysan yeniden başa dön
                if len(v_dosya_coin) < 1:
                    v_maxw = 1
                    break
                else:
                    v_maxw = len(v_dosya_coin)

                with concurrent.futures.ProcessPoolExecutor(max_workers=v_maxw) as executer:
                    results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g, v_islem_tutar,
                                               v_volume_fark_oran, v_oran, v_kar_oran,
                                               v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi,
                                               v_dalga_oran, v_bakiye,program_tip) for p
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
