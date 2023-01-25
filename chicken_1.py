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
v_last_price_g, v_alim_zamani, v_alim_timestamp, v_alim_orjtimestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, 0, [], [], {}
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET, {"verify": False, "timeout": 20} )

#client = Client("api-key", "api-secret", {"verify": False, "timeout": 20})


v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla = '2022', 0, '', '', '', '', 0
closes, highes, lowes, kesmeler, openes = [], [], [], [], []

closes_on, highes_on, lowes_on, kesmeler_on, openes_on = [], [], [], [], []
closes_1m, highes_1m, lowes_1m, kesmeler_1m, openes_1m = [], [], [], [], []
closes_3m, highes_3m, lowes_3m, kesmeler_3m, openes_3m = [], [], [], [], []
closes_5m, highes_5m, lowes_5m, kesmeler_5m, openes_5m = [], [], [], [], []
closes_15m, highes_15m, lowes_15m, kesmeler_15m, openes_15m = [], [], [], [], []
closes_1h, highes_1h, lowes_1h, kesmeler_1h, openes_1h = [], [], [], [], []
closes_4h, highes_4h, lowes_4h, kesmeler_4h, openes_4h = [], [], [], [], []

v_mum_boyu_1m, v_mum_boyu_3m, v_mum_boyu_5m, v_mum_boyu_15m, v_mum_boyu_1h, v_mum_boyu_4h = 0, 0, 0, 0, 0, 0
v_mum_boyu_1m_c, v_mum_boyu_3m_c, v_mum_boyu_5m_c, v_mum_boyu_15m_c, v_mum_boyu_1h_c, v_mum_boyu_4h_c = 0, 0, 0, 0, 0, 0
v_mum_boyu_1m_o, v_mum_boyu_3m_o, v_mum_boyu_5m_o, v_mum_boyu_15m_o, v_mum_boyu_1h_o, v_mum_boyu_4h_o = 0, 0, 0, 0, 0, 0

v_dosya_alinan, v_dosya_satilan, v_dosya_sembol, v_dosya_sabika, v_dosya_sabika1, v_dosya_parametre, v_dosya_acilsat, v_dosya_acilal, \
v_dosya_genelbuy, v_dosya_sonuc, v_dosya_islenen = '', '', '', '', '', '', '', '', '', '', ''


# genel_program_tipi, genel_piyasa_modu = '', ''

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
def iz_suren_kar_stop(v_symbol, v_inter, v_kar_oran):
    global v_hedef_bid_global, v_hedef_ask_global, v_last_price_g, v_alim_fiyati,v_ters_kesim
    global v_mum_boyu_1m, v_mum_boyu_3m, v_mum_boyu_5m, v_mum_boyu_15m, v_mum_boyu_1h, v_mum_boyu_4h
    global closes_1m, highes_1m, lowes_1m, kesmeler_1m, openes_1m
    global closes_3m, highes_3m, lowes_3m, kesmeler_3m, openes_3m
    global closes_5m, highes_5m, lowes_5m, kesmeler_5m, openes_5m
    global closes_15m, highes_15m, lowes_15m, kesmeler_15m, openes_15m
    global closes_1h, highes_1h, lowes_1h, kesmeler_1h, openes_1h
    global closes_4h, highes_4h, lowes_4h, kesmeler_4h, openes_4h

    v_mumboy, v_mumboy_prev, v_izsur_stop, v_acilst = 0, 0, 0, 0

    # Belirlenen kar hedefine ulaştı. Artık iz süren kar stopla dk ta 2 mum kırmızı olana kadar devam..
    # Veya yeni stop oranına tekrar inerse satar
    # v_hedef_ask_global = v_hedef_ask_global - float((float(v_last_price_g) / (100 + float(v_kar_oran))) / 2)
    #v_hedef_ask_global = float(v_alim_fiyati) + (float(v_alim_fiyati) * (float(v_kar_oran) / 2)) / 100

    while True:
        # time.sleep(0.5)
        # v_mumboy, v_mumboy_prev = get_mum_boyu(v_symbol, v_inter)

        if v_inter == '1m':
            v_mumboy = float(v_mum_boyu_1m)
            v_mumboy_prev = closes_1m[-1]
        if v_inter == '3m':
            v_mumboy = float(v_mum_boyu_3m)
            v_mumboy_prev = closes_3m[-1]
        if v_inter == '5m':
            v_mumboy = float(v_mum_boyu_5m)
            v_mumboy_prev = closes_5m[-1]
        if v_inter == '15m':
            v_mumboy = float(v_mum_boyu_15m)
            v_mumboy_prev = closes_15m[-1]
        if v_inter == '1h':
            v_mumboy = float(v_mum_boyu_1h)
            v_mumboy_prev = closes_1h[-1]
        if v_inter == '4h':
            v_mumboy = float(v_mum_boyu_4h)
            v_mumboy_prev = closes_4h[-1]

        if float(v_mumboy) < 0 and float(v_mumboy_prev) < 0:
            v_izsur_stop = 1
            v_satim_sebeb = 'İzsürdü..2 mum red'
            break

        if float(v_last_price_g) < float(v_hedef_ask_global):
            v_izsur_stop = 1
            v_satim_sebeb = 'İzsürdü..Zarar Seviyesine Ulaştı'
            break

        v_acilst = acil_satim(v_symbol)
        if v_acilst == 1:
            v_izsur_stop = 1
            v_satim_sebeb = 'İzsürdü..Acil Satim İstendi'
            break

        if v_ters_kesim==1:
            v_izsur_stop = 1
            v_satim_sebeb = 'İzsürdü..2.mum Kırmuzı'
            break

    return v_izsur_stop,v_satim_sebeb


# ***********************************************************************************************************************
def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_bakiye,
                     v_program_tip, v_sabika_sure):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati, v_last_price_g, v_alim_miktar
    global v_client, v_alim_timestamp, v_alim_zamani, v_hizli_gonzales, v_ters_kesim, v_alim_orjtimestamp
    v_acilal = 0

    if v_alim_var == 0:
        try:
            v_zip = 0
            # Acil alınacak durumlar için
            v_acilal = acil_alim_dosya(v_symbol)

            if v_hizli_gonzales == 1:  # Alım yap denmiş demektir.
                if v_test_prod == 'P':
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani, v_alim_orjtimestamp = buy_coin(v_symbol, v_islem_tutar,
                                                                                                v_kar_oran,
                                                                                                v_zarar_oran, v_zip,
                                                                                                v_bakiye, v_program_tip,
                                                                                                v_sabika_sure)
                else:
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani, v_alim_orjtimestamp = buy_coin_test(v_symbol,
                                                                                                     v_islem_tutar,
                                                                                                     v_kar_oran,
                                                                                                     v_zarar_oran,
                                                                                                     v_zip, v_bakiye,
                                                                                                     v_program_tip,
                                                                                                     v_sabika_sure)

                v_alim_var = 1
                v_hizli_gonzales = 0
            elif v_acilal == 1:  # Alım yap denmiş demektir.
                if v_test_prod == 'P':
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani, v_alim_orjtimestamp = buy_coin(v_symbol, v_islem_tutar,
                                                                                                v_kar_oran,
                                                                                                v_zarar_oran, v_zip,
                                                                                                v_bakiye, v_program_tip,
                                                                                                v_sabika_sure)
                else:
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati, v_alim_zamani, v_alim_orjtimestamp = buy_coin_test(v_symbol,
                                                                                                     v_islem_tutar,
                                                                                                     v_kar_oran,
                                                                                                     v_zarar_oran,
                                                                                                     v_zip, v_bakiye,
                                                                                                     v_program_tip,
                                                                                                     v_sabika_sure)
                v_alim_var = 1
                v_hizli_gonzales = 0
            else:
                # print('')
                print('Alım için Uygun Emir Bulunamadı.!', v_symbol, datetime.now())
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Alım tarafı  = ' + str(exp) + '-' + str(v_symbol) + '-' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj, v_program_tip)

    elif v_alim_var == 1:
        current_timestamp = round(time.time() * 1000)
        v_satim_timestamp = current_timestamp / 1000
        try:
            v_son_fiyat = float(v_last_price_g)
            print(str(v_symbol), 'İçerde alım var.......!!', str(datetime.now())[0:19], 'Hedefi = ',
                  str(v_hedef_bid_global), 'Son Fiyat = ', str(v_last_price_g))

            # Acil Satım emri varsa
            v_acilsat = acil_satim(v_symbol)

            # ******************************************************Belirlenen kar sağlandıysa
            if float(v_last_price_g) > float(v_hedef_bid_global):
                v_satim_sebeb = 'Kar Hedefine Ulasti'
                if v_test_prod == 'P':
                    # Karı devam ettir
                    v_izsur_stop,v_satim_sebeb = iz_suren_kar_stop(v_symbol, '1m', v_kar_oran)
                    #v_izsur_stop =1
                    if v_izsur_stop == 1:
                        #v_satim_sebeb = 'İzsürdü..Kar Hedefine Ulasti'
                        sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani, v_satim_sebeb,
                                  v_program_tip,
                                  v_sabika_sure)
                        v_alim_var = 0
                        v_ters_kesim = 0
                        v_hizli_gonzales = 0
                else:
                    v_izsur_stop,v_satim_sebeb = iz_suren_kar_stop(v_symbol, '1m', v_kar_oran)
                    #v_izsur_stop = 1
                    if v_izsur_stop == 1:
                        #v_satim_sebeb = 'İzsürdü..Kar Hedefine Ulasti'
                        sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani, v_satim_sebeb,
                                       v_program_tip, v_sabika_sure)
                        v_alim_var = 0
                        v_ters_kesim = 0
                        v_hizli_gonzales = 0

                # time.sleep(60)
            # ********************************************************Belirlenen zararın altına indiyse
            elif float(v_last_price_g) < float(v_hedef_ask_global):
                v_satim_sebeb = 'Zarar Seviyesinin Altina Dustu'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 2, v_alim_zamani, v_satim_sebeb, v_program_tip,
                              v_sabika_sure)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 2, v_alim_zamani, v_satim_sebeb,
                                   v_program_tip, v_sabika_sure)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
                # *********************************************** 5 dk geçtikten sonra zarar etme şansın kalmasın
            # elif (v_satim_timestamp >= v_alim_timestamp)  :
            #    v_hedef_ask_global = float(v_alim_fiyati)
            # v_satim_sebeb = 'Uyusuk Cıktı'
            # **********************************************************İlgili süre dolduysa
            # elif (v_satim_timestamp >= v_alim_timestamp) and float(v_alim_fiyati) >= float(v_last_price_g):
            #     v_satim_sebeb = 'Uyusuk Cıktı'
            #     if v_test_prod == 'P':
            #         sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 3, v_alim_zamani, v_satim_sebeb, v_program_tip,
            #                   v_sabika_sure)
            #     else:
            #         sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 3, v_alim_zamani, v_satim_sebeb,
            #                        v_program_tip, v_sabika_sure)
            #     v_alim_var = 0
            #     v_ters_kesim = 0
            #     v_hizli_gonzales = 0
            #     # time.sleep(60)
            # ***********************************************************2.mum da eksiye döndüyse
            elif v_ters_kesim == 1:  # Satım koşulları gerçekleşmiş.
                v_satim_sebeb = '2.mum Kırmızıya Dondu'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani, v_satim_sebeb, v_program_tip,
                              v_sabika_sure)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani, v_satim_sebeb,
                                   v_program_tip, v_sabika_sure)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            # ************************************************************** Acil satım yapılacaksa (manuel müdahale)
            elif v_acilsat == 1:  # Satım koşulları gerçekleşmiş.
                v_satim_sebeb = 'Acil Satimi Istendi.'
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani, v_satim_sebeb, v_program_tip,
                              v_sabika_sure)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1, v_alim_zamani, v_satim_sebeb,
                                   v_program_tip, v_sabika_sure)
                v_alim_var = 0
                v_ters_kesim = 0
                v_hizli_gonzales = 0
                # time.sleep(60)
            else:
                print('İçerde alım var ama henüz satılamadı...!- ', str(datetime.now())[0:19], v_symbol, ' - Hedefi = ',
                      str(v_hedef_bid_global), 'Son Fiyat = ', str(v_last_price_g))
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Satım tarafı  = ' + str(exp) + '-' + str(v_symbol) + '-' + str(
                datetime.now())
            Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ****************************SATIM********************************
def sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip, v_alim_zamani, v_satim_sebeb, v_program_tip,
              v_sabika_sure):
    global v_alim_var, v_dosya_sabika, v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika1, v_dosya_sonuc
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
                    v_kisa_mes = 'KARLA KAPADI - ' + str(v_satim_sebeb)
                else:
                    v_kisa_mes = 'Karla Sattı..' + str(v_satim_sebeb)

                v_oran_mesaj = '- Kar Oranı :'
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.8f}".format(float(v_alim_fiyati)) + '*' + \
                                   "{:.8f}".format(float(v_satim_fiyati)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani) + '*' + str(
                    v_alim_zamani) + '*' + \
                                   str(v_satim_sebeb)
                Telebot_v1.sabikali_yap(v_symbol, v_dosya_sabika, int(v_sabika_sure))
            else:
                # ******Zarar edenler cezasını çeksin******
                Telebot_v1.sabikali_yap(v_symbol, v_dosya_sabika, int(v_sabika_sure))

                v_profit_oran = float(((float(v_alim_fiyati) - float(v_satim_fiyati)) * 100) / float(v_alim_fiyati))
                if v_tip == 3:
                    v_kisa_mes = 'ZARARLA KAPADI.' + str(v_satim_sebeb)
                else:
                    v_kisa_mes = 'Zararla Sattı..' + str(v_satim_sebeb)

                v_oran_mesaj = '- Zarar Oranı :'
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.8f}".format(
                    float(v_alim_fiyati)) + '*' + "{:.8f}".format(float(v_satim_fiyati)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + \
                                   str(v_satim_zamani) + '*' + str(v_alim_zamani) + '*' + \
                                   str(v_satim_sebeb)
            # ----------------------------------------------------------------
            v_mess1 = 'Program Tipi = ' + str(v_program_tip) + v_kisa_mes + ' Hedefi : ' + "{:.8f}".format(
                float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                      '- Alım Fiyatı :' + "{:.8f}".format(
                float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.8f}".format(float(v_satim_fiyati)) + \
                      str(v_oran_mesaj) + "{:.8f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(v_satim_zamani) + \
                      'Alım Zamanı : ' + str(v_alim_zamani)

            Telebot_v1.mainma(v_mess1, v_program_tip)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj, v_dosya_sonuc)
            v_alim_var = 0
            Telebot_v1.genel_alimlar(v_symbol, 'S', v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika)
            # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)

        else:
            v_hata = 'SATIM işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata, v_program_tip)
    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.sell_coin  = ' + str(exp) + '-' + str(v_symbol) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ***********************************************************************************************************************
def sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip, v_alim_zamani, v_satim_sebeb, v_program_tip,
                   v_sabika_sure):
    global v_alim_var2

    try:
        v_son_fiyat = float(v_last_price_g)
        v_satim_fiyati = v_son_fiyat
        v_satim_zamani = str(datetime.now())

        if float(v_satim_fiyati) > float(v_alim_fiyati):
            v_profit_oran = float(((float(v_satim_fiyati) - float(v_alim_fiyati)) * 100) / float(v_alim_fiyati))
            if v_tip == 3:
                v_kisa_mes = 'KARLA KAPADI - ' + str(v_satim_sebeb)
            else:
                v_kisa_mes = 'Karla Sattı..' + str(v_satim_sebeb)

            v_oran_mesaj = '- Kar Oranı :'
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.8f}".format(float(v_alim_fiyati)) + '*' + \
                               "{:.8f}".format(float(v_satim_fiyati)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_satim_zamani) + '*' + str(
                v_alim_zamani) + '*' + \
                               str(v_satim_sebeb)

            Telebot_v1.sabikali_yap(v_symbol, v_dosya_sabika, int(v_sabika_sure))
        else:
            # ******Zarar edenler cezasını çeksin******
            Telebot_v1.sabikali_yap(v_symbol, v_dosya_sabika, int(v_sabika_sure))

            v_profit_oran = float(((float(v_alim_fiyati) - float(v_satim_fiyati)) * 100) / float(v_alim_fiyati))
            if v_tip == 3:
                v_kisa_mes = 'ZARARLA KAPADI.' + str(v_satim_sebeb)
            else:
                v_kisa_mes = 'Zararla Sattı..' + str(v_satim_sebeb)

            v_oran_mesaj = '- Zarar Oranı :'
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.8f}".format(
                float(v_alim_fiyati)) + '*' + "{:.8f}".format(float(v_satim_fiyati)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + \
                               str(v_satim_zamani) + '*' + str(v_alim_zamani) + '*' + \
                               str(v_satim_sebeb)

        v_mess1 = 'Program Tipi = ' + str(v_program_tip) + v_kisa_mes + ' Hedefi : ' + "{:.8f}".format(
            float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                  '- Alım Fiyatı :' + "{:.8f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.8f}".format(
            float(v_satim_fiyati)) + \
                  str(v_oran_mesaj) + "{:.8f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(v_satim_zamani) + \
                  'Alım Zamanı : ' + str(v_alim_zamani)

        Telebot_v1.mainma(v_mess1, v_program_tip)
        Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj, v_dosya_sonuc)
        v_alim_var = 0
        Telebot_v1.genel_alimlar(v_symbol, 'S', v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika)
        # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.11   = ' + str(exp) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ***********************************************************************************************************************
def buy_coin(v_symbol, v_islem_tutar, v_kar_oran, v_zarar_oran, v_zip, v_bakiye, v_program_tip, v_sabika_sure):
    global v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika
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
            v_alim_timestamp = (current_timestamp + (300000)) / 1000
            v_alim_orjtimestamp = (current_timestamp) / 1000

            # v_alim_zamani = str(datetime.now())[0:19]
        else:
            v_hata = 'Alım işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata, v_program_tip)

        v_mess = 'Program Tipi = ' + str(v_program_tip) + str(
            v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'Miktar = ' + '--' + "{:.1f}".format(float(v_alim_miktar)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.1f}".format(float(v_islem_tutar)) + '--' + \
                 'Zip=' + '--' + str(v_zip)
        # Telegram mesajo
        Telebot_v1.mainma(v_mess, v_program_tip)
        Telebot_v1.genel_alimlar(v_symbol, 'A', v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika)
        v_sembolmik = v_symbol.replace("BUSD", "")
        v_alim_miktar = v_client.get_asset_balance(asset=v_sembolmik).get('free')
        v_alim_miktar = get_round_step_quantity(v_symbol, float(v_alim_miktar))

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, \
               v_alim_timestamp, v_alim_miktar, v_alim_fiyati, v_alim_zamani, v_alim_orjtimestamp

    except Exception as exp:
        v_hata_mesaj = 'Alırken  Hata Oluştu!!.. buy_coin   = ' + str(exp) + '-' + str(v_symbol) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ************************************************************ ************************TEST ALIM**********************/
def buy_coin_test(v_symbol, v_islem_tutar, v_kar_oran, v_zarar_oran, v_zip, v_bakiye, v_program_tip, v_sabika_sure):
    global v_last_price_g, v_alim_zamani, v_alim_var, v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika
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
        v_alim_timestamp = (current_timestamp + (300000)) / 1000
        v_alim_orjtimestamp = (current_timestamp) / 1000
        # v_alim_var = 1

        v_mess = 'Program Tipi = ' + str(v_program_tip) + str(
            v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.1f}".format(float(v_islem_tutar)) + '--' + \
                 'Zip=' + '--' + str(v_zip)
        # Telegram mesajo
        Telebot_v1.mainma(v_mess, v_program_tip)
        Telebot_v1.genel_alimlar(v_symbol, 'A', v_dosya_genelbuy, v_dosya_alinan, v_dosya_satilan, v_dosya_sabika)

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, \
               v_alim_timestamp, v_alim_miktar, v_alim_fiyati, v_alim_zamani, v_alim_orjtimestamp
    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!.. buy_coin_test    = ' + str(exp) + '-' + str(v_symbol) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ***********************************************************************************************************************
def on_message_f_1m(ws_front_1m, message):
    global v_last_price_g, closes_1m, highes_1m, lowes_1m, openes_1m, v_mum_boyu_1m, v_mum_boyu_1m_o, v_mum_boyu_1m_c

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']

    v_mum_boyu_1m_o = float(open)
    v_mum_boyu_1m_c = float(close)
    v_mum_boyu_1m = float(close) - float(open)

    # print('v_mum_boyu_1m', close, open, v_mum_boyu_1m,datetime.now())

    is_candle_closed = candle['x']
    if is_candle_closed:
        closes_1m.append(close)
        if len(closes_1m) > 10:
            closes_1m.pop(0)


def on_open_f_1m(ws_front_1m):
    global vn_front_1m
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front_1m, "id": 1}
    ws_front_1m.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f_1m(ws_front_1m):
    print('Error olustu')


def on_close_f_1m(ws_front_1m):
    print('closed connection')


# ***********************************************************************************************************************
def on_message_f_3m(ws_front_3m, message):
    global v_last_price_g, closes_3m, highes_3m, lowes_3m, openes_3m, v_mum_boyu_3m, v_mum_boyu_3m_o, v_mum_boyu_3m_c

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']

    v_mum_boyu_3m_o = float(open)
    v_mum_boyu_3m_c = float(close)
    v_mum_boyu_3m = float(close) - float(open)
    # print('v_mum_boyu_3m', close, open, v_mum_boyu_3m, datetime.now())

    is_candle_closed = candle['x']
    if is_candle_closed:
        closes_3m.append(close)
        if len(closes_3m) > 10:
            closes_3m.pop(0)


def on_open_f_3m(ws_front_3m):
    global vn_front_3m
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front_3m, "id": 1}
    ws_front_3m.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f_3m(ws_front_3m):
    print('Error olustu')


def on_close_f_3m(ws_front_3m):
    print('closed connection')


# ***********************************************************************************************************************
def on_message_f_5m(ws_front_5m, message):
    global v_last_price_g, closes_5m, highes_5m, lowes_5m, openes_5m, v_mum_boyu_5m, v_mum_boyu_5m_o, v_mum_boyu_5m_c

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']

    v_mum_boyu_5m_o = float(open)
    v_mum_boyu_5m_c = float(close)
    v_mum_boyu_5m = float(close) - float(open)
    # print('v_mum_boyu_5m', close, open, v_mum_boyu_5m, datetime.now())

    is_candle_closed = candle['x']
    if is_candle_closed:
        closes_5m.append(close)
        if len(closes_5m) > 10:
            closes_5m.pop(0)


def on_open_f_5m(ws_front_5m):
    global vn_front_5m
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front_5m, "id": 1}
    ws_front_5m.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f_5m(ws_front_5m):
    print('Error olustu')


def on_close_f_5m(ws_front_5m):
    print('closed connection')


# ***********************************************************************************************************************
def on_message_f_15m(ws_front_15m, message):
    global v_last_price_g, closes_15m, highes_15m, lowes_15m, openes_15m, v_mum_boyu_15m, v_mum_boyu_15m_o, v_mum_boyu_15m_c

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']

    v_mum_boyu_15m_o = float(open)
    v_mum_boyu_15m_c = float(close)
    v_mum_boyu_15m = float(close) - float(open)

    is_candle_closed = candle['x']
    if is_candle_closed:
        closes_15m.append(close)
        if len(closes_15m) > 10:
            closes_15m.pop(0)


def on_open_f_15m(ws_front_15m):
    global vn_front_15m
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front_15m, "id": 1}
    ws_front_15m.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f_15m(ws_front_15m):
    print('Error olustu')


def on_close_f_15m(ws_front_15m):
    print('closed connection')


# ***********************************************************************************************************************
def on_message_f_1h(ws_front_1h, message):
    global v_last_price_g, closes_1h, highes_1h, lowes_1h, openes_1h, v_mum_boyu_1h, v_mum_boyu_1h_o, v_mum_boyu_1h_c

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']

    v_mum_boyu_1h_o = float(open)
    v_mum_boyu_1h_c = float(close)
    v_mum_boyu_1h = float(close) - float(open)

    is_candle_closed = candle['x']
    if is_candle_closed:
        closes_1h.append(close)
        if len(closes_1h) > 10:
            closes_1h.pop(0)


def on_open_f_1h(ws_front_1h):
    global vn_front_1h
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front_1h, "id": 1}
    ws_front_1h.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f_1h(ws_front_1h):
    print('Error olustu')


def on_close_f_1h(ws_front_1h):
    print('closed connection')


# ***********************************************************************************************************************
def on_message_f_4h(ws_front_4h, message):
    global v_last_price_g, closes_4h, highes_4h, lowes_4h, openes_4h, v_mum_boyu_4h, v_mum_boyu_4h_o, v_mum_boyu_4h_c

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']

    v_mum_boyu_4h_o = float(open)
    v_mum_boyu_4h_c = float(close)
    v_mum_boyu_4h = float(close) - float(open)

    is_candle_closed = candle['x']
    if is_candle_closed:
        closes_4h.append(close)
        if len(closes_4h) > 10:
            closes_4h.pop(0)


def on_open_f_4h(ws_front_4h):
    global vn_front_4h
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front_4h, "id": 1}
    ws_front_4h.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f_4h(ws_front_4h):
    print('Error olustu')


def on_close_f_4h(ws_front_4h):
    print('closed connection')


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
        v_ters_kesim, v_alim_var, v_hizli_gonzales, v_ziplama_oran, kesmeler, \
        v_alim_zamani, v_mum_sayisi, v_dalga_oran, genel_program_tipi, genel_piyasa_modu, v_alim_orjtimestamp
    # v_l_c_p, v_p_c_p2, v_1m_c, v_p_c_p3, v_3m_c, v_p_c_p5, v_5m_c = 0, 0, 0, 0, 0, 0, 0
    v_ayni_mum_icinde = 0

    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    # v_last_price_g = candle['c']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])
    v_symbol = candle['s']
    is_candle_closed = candle['x']

    # ****************Mum kapanış zamanı bilgileri
    candle_start_time = candle['t']
    candle_close_time = candle['T']
    candle_start_time = candle_start_time / 1000
    candle_close_time = candle_close_time / 1000
    dt_c_start = datetime.fromtimestamp(float(candle_start_time))
    dt_c_close = datetime.fromtimestamp(float(candle_close_time))

    # print('Closes', closes[-1],closes[-2],closes[-3],datetime.now())
    # print('closes dizisi ik', v_symbol, dt_c_start,dt_c_close, datetime.now())
    # print('Geldi', v_symbol, close, '-', open, '-', high, '-', low, '-', datetime.now())

    x = ((float(close) - float(open)) / float(open)) * 100
    if float(x) >= float(v_ziplama_oran):
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

    # *************************Aynı mum içinde satmaya çalışma alındıysa
    # if v_altime != v_sattime:
    if int(v_alim_orjtimestamp) > int(candle_start_time) and int(v_alim_orjtimestamp) < int(candle_close_time):
        v_ayni_mum_icinde = 1
    else:
        v_ayni_mum_icinde = 0

    if v_ayni_mum_icinde == 0 and v_alim_var == 1:
        if is_candle_closed == False and v_ters_kesim == 0:
            candle_acil_satim(v_symbol, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                              v_dalga_oran)
            # v_m = str(v_symbol) + '*' + 'Acil SAT' + '*' + str(open) + '*' + str(close) + '*' + \
            #       "{:.2f}".format(float(x)) + '*' + str(datetime.now())
            # Telebot_v1.analiz_islem_log(v_m, v_symbol)


# *********************************************************************************************
def candle_acil_satim(v_symbol, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran, v_dalga_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales, genel_program_tipi, genel_piyasa_modu
    try:
        time.sleep(1.22)
        closes.append(close)
        highes.append(high)
        lowes.append(low)
        openes.append(open)

        # 2.mum kırmızıya döndü
        if float(openes[-1]) > float(closes[-1]) and float(openes[-2]) > float(closes[-2]):
            v_ters_kesim = 1
            vm1 = 'Acil Satım Yapılacak...!..  = ' + str(v_symbol) + str(datetime.now()) + '*' + str(float(closes[-1])) \
                  + '*' + str(openes[-1]) + '*' + str(openes[-2]) + '*' + str(closes[-2]) + '*' + str(v_last_price_g)
            Telebot_v1.mainma(vm1, genel_program_tipi)
        else:
            print('İçerde alım var fakat satılamadı  ', v_symbol, datetime.now())
            v_ters_kesim = 0

        closes.pop()
        highes.pop()
        lowes.pop()
        openes.pop()

    except Exception as exp:
        v_hata_mesaj = 'Hata candle_acil_satim!..  = ' + str(exp) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# **********************************************************************************************************************
def candle_islem(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                 v_mum_sayisi, v_dalga_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales, genel_program_tipi, genel_piyasa_modu
    v_toplam = 0
    try:
        closes.append(close)
        highes.append(high)
        lowes.append(low)
        openes.append(open)
        # time.sleep(0.66)

        if v_alim_var == 0:
            v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes,
                                                                                 lowes, 10, 30)
            v_girme, v_1m_c = check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, 2,
                                                 v_ziplama_oran, genel_piyasa_modu)

            if v_ema_cross_up == 1:
                kesmeler.append(1)
            else:
                kesmeler.append(0)

            # Son 5 dk içinde kesme varsa
            if len(kesmeler) > 15:
                kesmeler.pop(0)

            v_toplam = int(sum(kesmeler))

            if float(v_1m_c) > float(v_ziplama_oran) and v_girme == 0 : #and (v_toplam >= 1 or ema_artik == 1):
                v_hizli_gonzales = 1
                v_hata_mesaj = 'Hızlı Artan Var..  = ' + str(v_symbol) + ' Fiyat=' + \
                               str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                               'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
                Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)
                # time.sleep(1)
            else:
                print('Değişim Anormal Yok= ', v_symbol, datetime.now())
                v_hizli_gonzales = 0
        else:
            time.sleep(1.333)
            if float(openes[-1]) > float(closes[-1]) and float(closes[-1]) > float(v_last_price_g):
                v_ters_kesim = 1
                vm1 = 'Çık!..  = ' + str(v_symbol) + str(datetime.now())
                # Telebot_v1.mainma(vm1,genel_program_tipi)
            else:
                print('İçerde alım var fakat satılamadı  ', v_symbol, datetime.now())
                v_ters_kesim = 0

        if len(closes) > 500:
            closes.pop(0)
            highes.pop(0)
            lowes.pop(0)
            openes.pop(0)
    except Exception as exp:
        v_hata_mesaj = 'Hata candle_islem_acil_alim!..  = ' + str(exp) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# *********************************************
def candle_islem_acil_alim(v_symbol, kesmeler, open, close, high, low, closes, highes, lowes, openes, v_ziplama_oran,
                           v_mum_sayisi, v_dalga_oran):
    global v_last_price_g, v_open_price, v_kesim, v_ters_kesim, v_alim_var, v_hizli_gonzales, genel_program_tipi, genel_piyasa_modu
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
                                             v_ziplama_oran, genel_piyasa_modu)

        if v_ema_cross_up == 1:
            kesmeler.append(1)
        else:
            kesmeler.append(0)
            # Son 5 dk içinde kesme varsa
        if len(kesmeler) > 15:
            kesmeler.pop(0)

        v_toplam = int(sum(kesmeler))

        if float(v_1m_c) > float(v_ziplama_oran) and v_girme == 0 and (v_toplam >= 1 or ema_artik == 1):
            v_hizli_gonzales = 1
            v_hata_mesaj = 'Acil...Hızlı Artan Var..  = ' + str(v_symbol) + ' Fiyat=' + \
                           str(close) + 'Oran=' + "{:.2f}".format(float(v_1m_c)) + \
                           'Son =' + str(closes[-1]) + 'Prev=' + str(closes[-2]) + 'Zaman=' + str(datetime.now())
            Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)
            # time.sleep(1)
        else:
            print('Acil Alımı Durumu Olışmadı.... ', v_symbol, datetime.now())
            v_hizli_gonzales = 0

        # Aciliyet nedeniyle geçici eklenen değerleri geri kaldır. Çünkü zaten mum kapanışında eklenecek.
        closes.pop()
        highes.pop()
        lowes.pop()
        openes.pop()
        kesmeler.pop()

    except Exception as exp:
        v_hata_mesaj = 'Hata candle_islem_acil_alim!..  = ' + str(exp) + '-' + str(v_symbol) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# ************************
def check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, v_ilk_kontrol,
                       v_ziplama_oran, v_genel_piyasa_modu):
    # İşleme girme şartları
    # 1-En yüksek mum olacak , 2-Kendinden önceki x kadar mumum dalgalanması belirtilen oranda olacak
    # 3-Ziplama oranı kadar en yüksek mumdan yüksek olacak , 4-Sabıkasız olacak
    global v_dosya_sabika, v_dosya_sabika1
    global v_mum_boyu_1m, v_mum_boyu_3m, v_mum_boyu_5m, v_mum_boyu_15m, v_mum_boyu_1h, v_mum_boyu_4h
    global closes_1m, highes_1m, lowes_1m, kesmeler_1m, openes_1m
    global closes_3m, highes_3m, lowes_3m, kesmeler_3m, openes_3m
    global closes_5m, highes_5m, lowes_5m, kesmeler_5m, openes_5m
    global closes_15m, highes_15m, lowes_15m, kesmeler_15m, openes_15m
    global closes_1h, highes_1h, lowes_1h, kesmeler_1h, openes_1h
    global closes_4h, highes_4h, lowes_4h, kesmeler_4h, openes_4h
    global v_mum_boyu_1m_c, v_mum_boyu_3m_c, v_mum_boyu_5m_c, v_mum_boyu_15m_c, v_mum_boyu_1h_c, v_mum_boyu_4h_c
    global v_mum_boyu_1m_o, v_mum_boyu_3m_o, v_mum_boyu_5m_o, v_mum_boyu_15m_o, v_mum_boyu_1h_o, v_mum_boyu_4h_o

    mum_boyu_orani = 0
    v_mum_poz_3m, v_mum_poz_5m, v_mum_poz_15m, v_mum_poz_4h = 0, 0, 0, 0

    # global mum_ortalama
    mum_ortalama = []

    v_girme, v_girms, v_girmex1 = 0, 0, 0

    v_close = closes[-1]
    v_open = openes[-1]

    if float(v_close) == float(v_open):
        v_artim_oran = 0
    else:
        v_artim_oran = ((float(v_close) - float(v_open)) / float(v_open)) * 100
        # -----------
    if len(closes) < int(v_mum_sayisi):
        v_say = len(closes)
    else:
        v_say = int(v_mum_sayisi)

    # Dosya oluşturulurken yapılan fitreleme
    if v_ilk_kontrol == 1:
        v_min = float(closes[-1])
        v_max = float(closes[-1])
        # *******************************************************
        for i in range(1, v_say):
            # print('cl',float(closes[-i - 1]))
            if float(closes[-i - 1]) > v_max:
                v_max = float(closes[-i - 1])
            if float(closes[-i - 1]) < v_min:
                v_min = float(closes[-i - 1])

        if float(v_max) == float(v_min):
            v_dalgalanma_oran = 0
        else:
            v_dalgalanma_oran = ((float(v_max) - float(v_min)) / float(v_min)) * 100
            # Son mumdan öncekilerde mumlar arası dalgalanma belirlenen orandan büyükse bu yakın zamanda çıkmıştır veya testre piyasası yine alma
            if float(v_dalgalanma_oran) > float(v_dalga_oran):
                v_girme = v_girme + 1

    else:  # Alım satımlarda yapılan anlık fitreleme
        v_min = float(closes[-2])
        v_max = float(closes[-2])

        # print('mum1', mum_ortalama, len(mum_ortalama)) # closes[-2],closes[-1])
        # print('ilk-',v_girme, 'Min - Max', v_min, v_max, 'Close/open', v_close, v_open, datetime.now())
        # *******************************************************
        for i in range(1, v_say):
            if float(closes[-i - 1]) > v_max:
                v_max = float(closes[-i - 1])
            if float(closes[-i - 1]) < v_min:
                v_min = float(closes[-i - 1])

            # Mum boylarının ortalama bir değerini bulup zıplamada kullanacağıx
            if float(closes[-i - 1]) == float(openes[-i - 1]):
                mum_ortalama.append(0)
            else:
                mum_boyu_orani = ((float(closes[-i - 1]) - float(openes[-i - 1])) / float(openes[-i - 1])) * 100
                if mum_boyu_orani < 0:
                    mum_boyu_orani = float(-1 * float(mum_boyu_orani))
                    mum_ortalama.append(mum_boyu_orani)
                else:
                    mum_ortalama.append(mum_boyu_orani)

            # Son mum belirlenen aralıktaki en yüksek mum değilse girme
            if float(closes[-i - 1]) > float(v_close):
                v_girme = v_girme + 1
                break
        # *******************************************************
        # print('mum1', mum_ortalama, len(mum_ortalama))  # closes[-2],closes[-1])
        if float(v_max) == float(v_min):
            v_dalgalanma_oran = 0
        else:
            v_dalgalanma_oran = ((float(v_max) - float(v_min)) / float(v_min)) * 100

        if v_girme == 0:
            # Son mumdan öncekilerde mumlar arası dalgalanma belirlenen orandan büyükse bu yakın zamanda çıkmıştır veya testre piyasası yine alma
            # if float(v_dalgalanma_oran) > float(v_dalga_oran):
            #     v_girme = v_girme + 1

            # En yüksek mum kapanışının üstünde zıplama oran kadar yükselti olsun
            # if float(v_close) == float(v_max):
            #     v_zip_hesap = 0
            # else:
            v_zip_hesap = ((float(v_close) - float(v_max)) / float(v_max)) * 100

            #if float(v_zip_hesap) < float(v_ziplama_oran) * 1.6 and float(v_zip_hesap) > float(v_ziplama_oran) * 0.4:
            if float(v_zip_hesap) > float(v_ziplama_oran)*0.5 :
                print('ok')
            else:
                v_girme = v_girme + 1

            # Son mum artım oranı ortalama mumun en az 2 katı olsun
            if len(mum_ortalama) > 0:
                v_ort_mumboyoran = float(float(sum(mum_ortalama)) / len(mum_ortalama))
            else:
                v_ort_mumboyoran = 0

            if float(v_artim_oran) < float(v_ort_mumboyoran) * 8:
                v_girme = v_girme + 1

            # Boğada artım oranı ortalam mum artım oranının en az 3 katı değilse girme
            # if v_genel_piyasa_modu == 'B':
            #     if float(v_artim_oran) < float(v_ort_mumboyoran) * 1.5:
            #         v_girme = v_girme + 1

            # Dalga 5 katlı mumdan büyükse girmesin
            # Bogada birden zıplamalar olabilir. O nedenle ortalama mumlar küçük olduğundan dalyaga göre oran yüksek olmalı
            # if v_genel_piyasa_modu == 'B':
            #     print('fddsf')
            #     if float(v_ort_mumboyoran) > 0:
            #         if float(v_dalgalanma_oran) > float(v_ort_mumboyoran) * 8:
            #             v_girme = v_girme + 1
            # else:
            #     if float(v_ort_mumboyoran) > 0:
            #         if float(v_dalgalanma_oran) > float(v_ort_mumboyoran) * 3:
            #             v_girme = v_girme + 1

            # Anlık mumların pozitif olması
            # if float(v_mum_boyu_1m) < 0:
            #     v_girme = v_girme + 1
            # if float(v_mum_boyu_3m) < 0:
            #     v_girme = v_girme + 1
            # if float(v_mum_boyu_5m) < 0:
            #     v_girme = v_girme + 1
            # if float(v_mum_boyu_15m) < 0:
            #     v_girme = v_girme + 1
            # if float(v_mum_boyu_1h) < 0:
            #     v_girme = v_girme + 1
            # if float(v_mum_boyu_4h) < 0:
            #     v_girme = v_girme + 1

            # ------------------------------------
            # 3m peryotta son 5 mumum en yükseği değilse girme
            # v_girmex1 = get_first_set_of_closes_online(v_symbol, '3m', 5)
            v_closex1 = v_mum_boyu_3m_c
            # print(v_closex1, datetime.now())
            # print('Closes', closes_3m)
            # v_mum_boyu = float(closes[-1]) - float(openes_on[-1])

            # for i in range(1, 5):
            #     if float(closes_3m[-i]) > float(v_closex1):
            #         v_girmex1 = v_girmex1 + 1
            #         break
            #
            # v_girme = v_girmex1 + 1

    # Tüm ilk ve son kontrollerde sabikalı olmaması lazım
    v_girms = sabikalilari_temizle(v_symbol)
    v_girme = v_girme + int(v_girms)

    return v_girme, v_artim_oran


# *************************************************************************************************EMA CHECK
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
    global v_sembol_islenen, v_last_price_g, genel_program_tipi
    # print('Fiyat', float(price[v_symbol]))
    if msg['e'] != 'error':
        v_last_price_g = float(msg['c'])
        # print('Fiyat', float(v_last_price_g),datetime.now())
    else:
        v_last_price_g = 0
        vmesaj = 'Hata - Son fiyat sıfır!..btc_pairs_trade  = ' + str(v_sembol_islenen)
        Telebot_v1.mainma(vmesaj, genel_program_tipi)
    # print('Fiyat', v_last_price_g,datetime.now())
    if v_last_price_g == 0:
        time.sleep(0.1)


# ***********************************************************************************************************************
def socket_thread_front(v_symbol, v_inter):
    global vn_front, v_sembol_islenen
    # v_symbol = v_symbol.lower()
    v_sembol_islenen = v_symbol
    bsm = ThreadedWebsocketManager(api_key=API_Config.API_KEY, api_secret=API_Config.API_SECRET)
    bsm.start()
    bsm.start_symbol_ticker_socket(symbol=v_symbol, callback=son_fiyat_getir)
    bsm.join(1.66)
    # print('fff')


# ***********************************************************************************************************************
# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter, v_zam, v_dalga_or):
    global vn_front, v_mum_sayisi, v_dalga_oran
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
def socket_front_closeslar(v_symbol, v_inter):
    global vn_front, vn_front_1m, vn_front_3m, vn_front_5m, vn_front_15m, vn_front_1h, vn_front_4h, v_mum_sayisi, v_dalga_oran
    v_symbol = v_symbol.lower()
    v_sembol_deg1 = f'[{v_symbol}@kline_{v_inter}]'  # <symbol>@kline_<interval>
    v_sembol_deg5 = v_sembol_deg1.replace("[", "")
    v_sembol_deg5 = v_sembol_deg5.replace("]", "")

    if v_inter == '1m':
        vn_front_1m = [v_sembol_deg5]
        socket_f_1m = 'wss://stream.binance.com:9443/ws'
        ws_front_1m = websocket.WebSocketApp(socket_f_1m, on_message=on_message_f_1m, on_open=on_open_f_1m,
                                             on_close=on_close_f_1m)
        wst_1m = threading.Thread(target=ws_front_1m.run_forever)
        wst_1m.start()
        wst_1m.join(2)

    if v_inter == '3m':
        vn_front_3m = [v_sembol_deg5]
        socket_f_3m = 'wss://stream.binance.com:9443/ws'
        ws_front_3m = websocket.WebSocketApp(socket_f_3m, on_message=on_message_f_3m, on_open=on_open_f_3m,
                                             on_close=on_close_f_3m)
        wst_3m = threading.Thread(target=ws_front_3m.run_forever)
        wst_3m.start()
        wst_3m.join(2)

    if v_inter == '5m':
        vn_front_5m = [v_sembol_deg5]
        socket_f_5m = 'wss://stream.binance.com:9443/ws'
        ws_front_5m = websocket.WebSocketApp(socket_f_5m, on_message=on_message_f_5m, on_open=on_open_f_5m,
                                             on_close=on_close_f_5m)
        wst_5m = threading.Thread(target=ws_front_5m.run_forever)
        wst_5m.start()
        wst_5m.join(2)

    if v_inter == '15m':
        vn_front_15m = [v_sembol_deg5]
        socket_f_15m = 'wss://stream.binance.com:9443/ws'
        ws_front_15m = websocket.WebSocketApp(socket_f_15m, on_message=on_message_f_15m, on_open=on_open_f_15m,
                                              on_close=on_close_f_15m)
        wst_15m = threading.Thread(target=ws_front_15m.run_forever)
        wst_15m.start()
        wst_15m.join(2)

    if v_inter == '1h':
        vn_front_1h = [v_sembol_deg5]
        socket_f_1h = 'wss://stream.binance.com:9443/ws'
        ws_front_1h = websocket.WebSocketApp(socket_f_1h, on_message=on_message_f_1h, on_open=on_open_f_1h,
                                             on_close=on_close_f_1h)
        wst_1h = threading.Thread(target=ws_front_1h.run_forever)
        wst_1h.start()
        wst_1h.join(2)

    if v_inter == '4h':
        vn_front_4h = [v_sembol_deg5]
        socket_f_4h = 'wss://stream.binance.com:9443/ws'
        ws_front_4h = websocket.WebSocketApp(socket_f_4h, on_message=on_message_f_4h, on_open=on_open_f_4h,
                                             on_close=on_close_f_4h)
        wst_4h = threading.Thread(target=ws_front_4h.run_forever)
        wst_4h.start()
        wst_4h.join(2)


# ***********************************************************************************************************************
def dosyalari_temizle():
    global v_dosya_alinan, v_dosya_satilan, v_dosya_islenen
    open(v_dosya_alinan, 'w').close()
    open(v_dosya_satilan, 'w').close()
    open(v_dosya_islenen, 'w').close()
    # open("sabikalilar.txt", 'w').close()


# ***********************************************************************************************************************
def uygun_olmayani_temizle(v_symbol, v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran, v_piyasa_modu):
    global openes, closes, highes, lowes, v_dosya_sabika, v_dosya_sabika1
    v_girme = 0
    get_first_set_of_closes(v_symbol, v_inter_g)
    # v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes, lowes, 10,30)
    v_girme, v_artim_oran = check_full_kontrol(v_symbol, openes, closes, highes, lowes, v_mum_sayisi, v_dalga_oran, 1,
                                               v_ziplama_oran, v_piyasa_modu)

    # 5 dk son 12 mum arasında en büyük değilse girme
    # v_girme1 = get_first_set_of_closes_online(v_symbol, '5m', 12)
    # v_girme = int(v_girme1) + v_girme

    return v_girme


# ***********************************************************************************************************************
def sabikalilari_temizle(v_symbol):
    global v_dosya_sabika, v_dosya_sabika1
    v_girme = 0
    with open(v_dosya_sabika, 'r') as dosya_sabika:
        for line in dosya_sabika.read().splitlines():
            aciklama = line
            s = aciklama.split("*")
            current_timestamp = round(time.time() * 1000)
            v_current_timestamp = (current_timestamp) / 1000
            v_current_timestamp = int(v_current_timestamp)
            if str(s[0]) == v_symbol and float(v_current_timestamp) < float(s[1]):
                v_girme = v_girme + 1

    with open(v_dosya_sabika1, 'r') as dosya_sabika:
        for line in dosya_sabika.read().splitlines():
            aciklama = line
            s = aciklama.split("*")
            current_timestamp = round(time.time() * 1000)
            v_current_timestamp = (current_timestamp) / 1000
            v_current_timestamp = int(v_current_timestamp)
            if str(s[0]) == v_symbol and float(v_current_timestamp) < float(s[1]):
                v_girme = v_girme + 1

    return v_girme
    # # v = str(v_symbol) +'Girme sabıka=' +  'Prev=' + str(v_close) + 'Girme = '+str(v_girme) + 'Oran='+ str(v_artim_oran)+ 'Zaman=' + str(datetime.now())
    # # Telebot_v1.mainma(v,genel_program_tipi)
    # dosya_sabika.close()


# ***********************************************************************************************************************
def dosya_aktar(v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran, v_program_tip, v_piyasa_modu):
    global v_dosya_coin, v_dosya_sembol, v_dosya_sabika, v_dosya_sabika1, v_dosya_islenen, v_dosya_islenen_1, v_dosya_islenen_2
    v_girme = 0
    # #
    DB_transactions3.database_baglan(v_program_tip)
    #
    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write(v_dosya_sembol)
    DB_transactions3.high_oran_coin(v_program_tip)
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open(v_dosya_sembol, 'r') as dosya:
        i = 0
        p = 0
        x = 0
        for line in dosya.read().splitlines():
            v_mumboy1, v_mumboy2, v_mumboy3, v_mumboy4 = 0, 0, 0, 0
            v_girme = 0
            v_symbol = line
            time.sleep(0.2)

            # Sabıkalıysa diğer uygunluklara bakmaya gerek yok
            v_girmes = sabikalilari_temizle(v_symbol)
            v_girme = v_girme + int(v_girmes)

            if v_girme == 0:
                # Uygun olmayanları listeden çıkar. Dalgalanma bandı dışındaki ve sabıkalıları temizler
                v_girmeu = uygun_olmayani_temizle(v_symbol, v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran, v_piyasa_modu)
                v_girme = v_girme + int(v_girmeu)

                # Mumları pozitif değilse de girme
                if v_girme == 0:
                    # Belirtilen mumlar hep pozitif olmalı
                    # v_mumboy1, v_mumboy_prev1 = get_mum_boyu(v_symbol, '5m')
                    # v_mumboy2, v_mumboy_prev2 = get_mum_boyu(v_symbol, '15m')
                    # v_mumboy3, v_mumboy_prev3 = get_mum_boyu(v_symbol, '1h')
                    # v_mumboy4, v_mumboy_prev4 = get_mum_boyu(v_symbol, '4h')

                    # #4s de bir trend olsun
                    # v_girme1 = get_first_set_of_closes_online(v_symbol, '4h', 1)
                    # v_girme = int(v_girme1) + v_girme
                    #
                    # v_girme2 = get_first_set_of_closes_online(v_symbol, '1h', 1)
                    # v_girme = int(v_girme2) + v_girme
                    #
                    # if float(v_mumboy1) < 0:
                    #     v_girme = v_girme + 1
                    # if float(v_mumboy2) < 0:
                    #     v_girme = v_girme + 1
                    # if float(v_mumboy3) < 0:
                    #     v_girme = v_girme + 1
                    # if float(v_mumboy4) < 0:
                    #     v_girme = v_girme + 1

                    # Diğer robotlarca işleniyorsa da bakma
                    if v_girme == 0:
                        # Coin diğer robotlarca isleniyorsa alma
                        with open(v_dosya_islenen_1, 'r') as dosya_islenen1:
                            for l1 in dosya_islenen1.read().splitlines():
                                if v_symbol == l1:
                                    v_girme = v_girme + 1
                        dosya_islenen1.close()

                        # Coin diğer robotlarca isleniyorsa alma
                        with open(v_dosya_islenen_2, 'r') as dosya_islenen2:
                            for l2 in dosya_islenen2.read().splitlines():
                                if v_symbol == l2:
                                    v_girme = v_girme + 1
                        dosya_islenen2.close()

            # *******************************************

            if v_girme == 0:
                if i < 55:
                    v_dosya_coin.append(line)
                    print('Dosyaya eklenen Coin..: ', line, i, '**', datetime.now())
                    x = x + 1
                    if x == 55:
                        break
                else:
                    print('Devamı...Dosyaya eklenen Coin..: ', line, i, datetime.now())
                i += 1
            else:
                print('Dosyaya Uygun Değil .: ', line, p, '**', datetime.now())
                p = p + 1

    dosya.close()
    print('Dosya Tamamlandı', v_dosya_coin)

    # Bu işlenenleri aynı anda diğer programlar almasın
    for i in range(len(v_dosya_coin)):
        Telebot_v1.islenen_coinler(v_dosya_islenen, str(v_dosya_coin[i]))


# ***********************************************************************************************************************
def islenen_son_temizlik_yap():
    global v_dosya_coin, v_dosya_sembol, v_dosya_sabika, v_dosya_sabika1, v_dosya_islenen, v_dosya_islenen_1, v_dosya_islenen_2

    with open(v_dosya_islenen, 'r') as dosya:
        i = 0
        p = 0
        for line in dosya.read().splitlines():
            v_symbol = line

            # Coin diğer robotlarca isleniyorsa alma
            with open(v_dosya_islenen_1, 'r') as dosya_islenen1:
                for l1 in dosya_islenen1.read().splitlines():
                    if v_symbol == l1:
                        v_dosya_coin.remove(l1)  # v_girme = v_girme + 1
            dosya_islenen1.close()

            # Coin diğer robotlarca isleniyorsa alma
            with open(v_dosya_islenen_2, 'r') as dosya_islenen2:
                for l2 in dosya_islenen2.read().splitlines():
                    if v_symbol == l2:
                        v_dosya_coin.remove(l2)  # v_girme = v_girme + 1
            dosya_islenen2.close()

    dosya.close()
    print('Son temizlik  Tamamlandı', v_dosya_coin)


# ***********************************************************************************************************************
def run_frontdata(v_sem, v_int, v_mum_sayisi, v_dalga_oran, v_program_tip):
    global closes
    try:
        # print('Clo', len(closes),datetime.now())
        # Closes Socketleri için ilk değerleri oluşturur
        """
        get_first_closeslar_olustur(v_sem, '1m')
        time.sleep(0.5)
        get_first_closeslar_olustur(v_sem, '3m')
        time.sleep(0.5)
        get_first_closeslar_olustur(v_sem, '5m')
        time.sleep(0.5)
        get_first_closeslar_olustur(v_sem, '15m')
        time.sleep(0.1)
        get_first_closeslar_olustur(v_sem, '1h')
        time.sleep(0.1)
        get_first_closeslar_olustur(v_sem, '4h')
        time.sleep(0.1)

        socket_front_closeslar(v_sem, '1m')
        time.sleep(0.5)
        socket_front_closeslar(v_sem, '3m')
        time.sleep(0.5)
        socket_front_closeslar(v_sem, '5m')
        time.sleep(0.5)
        socket_front_closeslar(v_sem, '15m')
        time.sleep(0.1)
        socket_front_closeslar(v_sem, '1h')
        time.sleep(0.1)
        socket_front_closeslar(v_sem, '4h')
        """

        # print('Clo', closes[-1], closes[-2],closes[-3], openes[-1], openes[-2],openes[-3], datetime.now())

        # İşlem yapılan ana closes oluşturulur
        get_first_set_of_closes(v_sem, v_int)

        # EMA, ADX gibi indikatörleri sn likte oluşturmak için kline lı kullanım..Yenileme 2 sn. Ama her sn veri geliyor.
        socket_front(v_sem, v_int, v_mum_sayisi, v_dalga_oran)

        # Son fiyatı almak için. Sn lik data yenileme
        socket_thread_front(v_sem, v_int)
        # time.sleep(2)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..run_frontdata  = ' + str(exp) + '-' + \
                       str(v_sem) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ***********************************************************************************************************************
def get_snapshot(v_sembol, v_limit):
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())


# ***********************************************************************************************************************
def main_islem(v_sembol_g, v_limit_g, v_inter_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
               v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye,
               v_program_tip, v_sabika_sure, v_piyasa_modu):
    print('Main İşlemelri Başladı ', v_sembol_g, datetime.now())

    global genel_program_tipi, genel_piyasa_modu

    try:
        # time.sleep(1.333)
        genel_program_tipi = v_program_tip
        genel_piyasa_modu = v_piyasa_modu

        # Processler açıldığında parametreler silindiği için tekrar atandılar.
        dosya_parametre_ata(v_program_tip, v_piyasa_modu)

        # print('Alınn', v_dosya_satilan, v_dosya_alinan)

        run_frontdata(v_sembol_g, v_inter_g, v_mum_sayisi, v_dalga_oran, v_program_tip)
        # time.sleep(0.33)
        islem(v_sembol_g, v_limit_g, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_ziplama_oran, v_bakiye,
              v_program_tip, v_sabika_sure, v_piyasa_modu)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem   = ' + str(exp) + '-' + str(v_sembol_g) + '-' + str(
            datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# *********************************************************************************************************
def kota_mesaj(v_kota_doldu):
    v_atildi = 1
    while True:
        if v_atildi == 1:
            v_mesajx = 'İçerde alım var. Kota dolduğu için yeni alım yapılamıyor!!!...' + str(datetime.now())
            Telebot_v1.mainma(v_mesajx, v_program_tip)
            time.sleep(60)
            v_atildi = 0
            break
    return v_atildi


# ***********************************************************************************************************************
def islem(v_sembol_g, v_limit_g, v_islem_tutar, v_kar_oran, v_zarar_oran, v_test_prod, v_zip, v_bakiye, v_program_tip,
          v_sabika_sure, v_piyasa_modu):
    global v_last_price_g, v_open_price, v_alim_var, v_ziplama_oran, genel_program_tipi, genel_piyasa_modu
    v_ziplama_oran = float(v_zip)
    v_atildi = 0
    v_on_zaman = ''
    # time.sleep(1.66)
    try:
        genel_program_tipi = v_program_tip
        genel_piyasa_modu = v_piyasa_modu

        while (True):
            v_tt = str(datetime.now())[0:16]
            v_kota_doldu = icerdeki_alinan()
            if v_kota_doldu >= 5:
                print('KOTA doldu...')
                # if v_atildi ==0 :
                #     v_atildi = kota_mesaj(v_kota_doldu)

                # v_mesajx = 'İçerde alım var. Kota dolduğu için yeni alım yapılamıyor!!!...' + str(datetime.now())
                # Telebot_v1.mainma(v_mesajx, v_program_tip)
                # v_on_zaman = v_tt
                if v_alim_var == 1:
                    time.sleep(0.2)
                    # time.sleep(2)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                     v_zarar_oran, v_test_prod, v_bakiye, v_program_tip, v_sabika_sure)
            else:
                if v_alim_var == 0:
                    time.sleep(0.2)
                    # time.sleep(800)
                    if v_last_price_g != 0:
                        # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, datetime.now())

                        whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                         v_zarar_oran, v_test_prod, v_bakiye, v_program_tip, v_sabika_sure)
                else:
                    time.sleep(0.2)
                    # time.sleep(800)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_islem_tutar, v_kar_oran,
                                     v_zarar_oran, v_test_prod, v_bakiye, v_program_tip, v_sabika_sure)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + '-' + str(v_sembol_g) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)


# ***********************************************************************************************************************
def icerdeki_alinan():
    global v_dosya_satilan, v_dosya_alinan
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
    global closes, highes, lowes, openes, v_dosya_coin, kesmeler, genel_program_tipi
    closes, highes, lowes, kesmeler, openes = [], [], [], [], []
    try:
        i = 0
        if v_inter == '1m':
            v_sure = "2 hour ago UTC"
            v_son_15 = 120
        elif v_inter == '3m':
            v_sure = "5 hour ago UTC"
            v_son_15 = 100
        elif v_inter == '5m':
            v_sure = "10 hour ago UTC"
            v_son_15 = 120
        elif v_inter == '15m':
            v_sure = "30 hour ago UTC"
            v_son_15 = 120
        elif v_inter == '1h':
            v_sure = "24 hour ago UTC"
            v_son_15 = 24
        elif v_inter == '4h':
            v_sure = "96 hour ago UTC"
            v_son_15 = 16

            # klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")

        for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
            closes.append(float(kline[4]))
            highes.append(float(kline[2]))
            lowes.append(float(kline[3]))
            openes.append(float(kline[1]))
            i = i + 1
            # Kesmelerin ilk 15 sini doldur
            # print('son', len(closes))
            # print('son2s', closes)
            if i >= v_son_15 - 15:
                v_ema_cross_up, v_ema_cross_down, ema_artik = check_exist_ema_second(v_symbol, openes, closes, highes,
                                                                                     lowes, 10, 30)
                if v_ema_cross_up == 1:
                    kesmeler.append(1)
                else:
                    kesmeler.append(0)

                if len(kesmeler) > 15:
                    kesmeler.pop(0)

        closes.pop()
        highes.pop()
        lowes.pop()
        openes.pop()

    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + '-' + str(v_symbol) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# ***********************************************************************************************************************
def get_first_closeslar_olustur(v_symbol, v_inter):
    global closes, highes, lowes, openes, v_dosya_coin, kesmeler, genel_program_tipi
    global closes_1m, highes_1m, lowes_1m, kesmeler_1m, openes_1m
    global closes_3m, highes_3m, lowes_3m, kesmeler_3m, openes_3m
    global closes_5m, highes_5m, lowes_5m, kesmeler_5m, openes_5m
    global closes_15m, highes_15m, lowes_15m, kesmeler_15m, openes_15m
    global closes_1h, highes_1h, lowes_1h, kesmeler_1h, openes_1h
    global closes_4h, highes_4h, lowes_4h, kesmeler_4h, openes_4h
    #
    # closes_1m, highes_1m, lowes_1m, kesmeler_1m, openes_1m = [], [], [], [], []
    # closes_3m, highes_3m, lowes_3m, kesmeler_3m, openes_3m = [], [], [], [], []
    # closes_5m, highes_5m, lowes_5m, kesmeler_5m, openes_5m = [], [], [], [], []
    # closes_15m, highes_15m, lowes_15m, kesmeler_15m, openes_15m = [], [], [], [], []
    # closes_1h, highes_1h, lowes_1h, kesmeler_1h, openes_1h = [], [], [], [], []
    # closes_4h, highes_4h, lowes_4h, kesmeler_4h, openes_4h = [], [], [], [], []

    try:
        i = 0
        if v_inter == '1m':
            v_sure = "10 minute ago UTC"
            for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
                closes_1m.append(float(kline[4]))
                highes_1m.append(float(kline[2]))
                lowes_1m.append(float(kline[3]))
                openes_1m.append(float(kline[1]))

            # Anlık verileri de attığı için bunları çıkarmamız lazım. Çünkü zaten mum kapanışlarında diziyi doldurmaya devam edecek
            closes_1m.pop()
            highes_1m.pop()
            lowes_1m.pop()
            openes_1m.pop()

        elif v_inter == '3m':
            v_sure = "30 minute ago UTC"
            for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
                closes_3m.append(float(kline[4]))
                highes_3m.append(float(kline[2]))
                lowes_3m.append(float(kline[3]))
                openes_3m.append(float(kline[1]))

            # Anlık verileri de attığı için bunları çıkarmamız lazım. Çünkü zaten mum kapanışlarında diziyi doldurmaya devam edecek
            closes_3m.pop()
            highes_3m.pop()
            lowes_3m.pop()
            openes_3m.pop()

        elif v_inter == '5m':
            v_sure = "50 minute ago UTC"
            for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
                closes_5m.append(float(kline[4]))
                highes_5m.append(float(kline[2]))
                lowes_5m.append(float(kline[3]))
                openes_5m.append(float(kline[1]))

            # Anlık verileri de attığı için bunları çıkarmamız lazım. Çünkü zaten mum kapanışlarında diziyi doldurmaya devam edecek
            closes_5m.pop()
            highes_5m.pop()
            lowes_5m.pop()
            openes_5m.pop()

        elif v_inter == '15m':
            v_sure = "3 hour ago UTC"
            for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
                closes_15m.append(float(kline[4]))
                highes_15m.append(float(kline[2]))
                lowes_15m.append(float(kline[3]))
                openes_15m.append(float(kline[1]))

            # Anlık verileri de attığı için bunları çıkarmamız lazım. Çünkü zaten mum kapanışlarında diziyi doldurmaya devam edecek
            closes_15m.pop()
            highes_15m.pop()
            lowes_15m.pop()
            openes_15m.pop()

        elif v_inter == '1h':
            v_sure = "10 hour ago UTC"
            for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
                closes_1h.append(float(kline[4]))
                highes_1h.append(float(kline[2]))
                lowes_1h.append(float(kline[3]))
                openes_1h.append(float(kline[1]))

            # Anlık verileri de attığı için bunları çıkarmamız lazım. Çünkü zaten mum kapanışlarında diziyi doldurmaya devam edecek
            closes_1h.pop()
            highes_1h.pop()
            lowes_1h.pop()
            openes_1h.pop()

        elif v_inter == '4h':
            v_sure = "96 hour ago UTC"
            for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
                closes_4h.append(float(kline[4]))
                highes_4h.append(float(kline[2]))
                lowes_4h.append(float(kline[3]))
                openes_4h.append(float(kline[1]))

            # Anlık verileri de attığı için bunları çıkarmamız lazım. Çünkü zaten mum kapanışlarında diziyi doldurmaya devam edecek
            closes_4h.pop()
            highes_4h.pop()
            lowes_4h.pop()
            openes_4h.pop()

        # print('Closes',closes_1m )
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + '-' + str(v_symbol) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# **********************************************************************************************************************
def get_mum_boyu(v_symbol, v_inter):
    # global
    closes_x, highes_x, lowes_x, openes_x = [], [], [], []
    v_close, v_open, v_mum_boyu, v_close_prev, v_open_prev, v_mum_boyu_prev = 0, 0, 0, 0, 0, 0

    try:
        if v_inter == '1s':
            v_sure = "1 minute ago UTC"
        elif v_inter == '1m':
            v_sure = "10 minute ago UTC"
        elif v_inter == '3m':
            v_sure = "30 minute ago UTC"
        elif v_inter == '5m':
            v_sure = "30 minute ago UTC"
        elif v_inter == '15m':
            v_sure = "1 hour ago UTC"
        elif v_inter == '1h':
            v_sure = "3 hour ago UTC"
        elif v_inter == '4h':
            v_sure = "12 hour ago UTC"

        for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
            closes_x.append(float(kline[4]))
            highes_x.append(float(kline[2]))
            lowes_x.append(float(kline[3]))
            openes_x.append(float(kline[1]))

        v_close = float(closes_x[-1])
        v_open = float(openes_x[-1])
        v_mum_boyu = v_close - v_open

        v_close_prev = float(closes_x[-2])
        v_open_prev = float(openes_x[-2])
        v_mum_boyu_prev = v_close_prev - v_open_prev

        return float(v_mum_boyu), float(v_mum_boyu_prev)

    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..get_mum_boyu  = ' + str(exp) + '-' + str(v_symbol) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# *********************************************************************************************************************
def get_first_set_of_closes_online(v_symbol, v_inter, v_mum_gerisay):
    global closes_on, highes_on, lowes_on, openes_on, kesmeler_on, genel_program_tipi
    closes_on, highes_on, lowes_on, kesmeler_on, openes_on = [], [], [], [], []

    try:
        i = 0
        if v_inter == '1s':
            v_sure = "15 minute ago UTC"
        if v_inter == '1m':
            v_sure = "1 hour ago UTC"
        elif v_inter == '3m':
            v_sure = "1 hour ago UTC"
        elif v_inter == '5m':
            v_sure = "2 hour ago UTC"
        elif v_inter == '1h':
            v_sure = "24 hour ago UTC"
        elif v_inter == '4h':
            v_sure = "96 hour ago UTC"

        for kline in v_client.get_historical_klines(v_symbol, v_inter, v_sure):
            closes_on.append(float(kline[4]))
            highes_on.append(float(kline[2]))
            lowes_on.append(float(kline[3]))
            openes_on.append(float(kline[1]))

        # Saatli k girerken örneğin 5 dk vs son v_mum_gerisay kadara muma bak, en yükseğiyse gir
        v_girme = 0
        v_close = closes_on[-1]
        # v_mum_boyu = float(closes[-1]) - float(openes_on[-1])

        for i in range(1, v_mum_gerisay):
            if float(closes_on[-i - 1]) > float(v_close):
                v_girme = v_girme + 1
                break
        return v_girme

    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + '-' + str(v_symbol) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, genel_program_tipi)


# ***********************************************************************************************************************
def dosyadan_parametreleri_oku():
    global v_dosya_param
    # v_dosya_parametre='DOSYALAR/parametreler.txt'
    with open(v_dosya_param, 'r') as dosya:
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
            elif i == 16:
                v_program_tip = str(s[1])
            elif i == 17:
                v_sabika_sure = int(s[1])
            i = i + 1
        dosya.close()
        print('Parametreler Yüklendi.', v_dosya_coin)
    return v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_mod, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye, \
           v_volume_fark_oran, v_oran, v_kar_oran, v_zarar_oran, minVolumePerc, v_program_tip, v_sabika_sure


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
def acil_alim_dosya(v_symbol):
    global v_dosya_acilal
    v_alinacak = 0
    with open(v_dosya_acilal, 'r') as dosya:
        for line in dosya.read().splitlines():
            if v_symbol == line:
                v_alinacak = 1
    return v_alinacak


# ***********************************************************************************************************************

def dosya_parametre_ata(program_tip, piyasa_modu):
    global v_dosya_alinan, v_dosya_satilan, v_dosya_sembol, \
        v_dosya_sabika, v_dosya_sabika1, v_dosya_parametre, v_dosya_acilsat, v_dosya_acilal, \
        v_dosya_genelbuy, v_dosya_sonuc, v_dosya_islenen, v_dosya_islenen_1, v_dosya_islenen_2

    if piyasa_modu == 'S':
        if program_tip == 'E':
            v_dosya_parametre = 'DOSYALAR/parametreler_e.txt'
        if program_tip == 'CK1':
            v_dosya_parametre = 'DOSYALAR/parametreler_ck1.txt'
        if program_tip == 'CK2':
            v_dosya_parametre = 'DOSYALAR/parametreler_ck2.txt'

    if piyasa_modu == 'A':
        if program_tip == 'E':
            v_dosya_parametre = 'DOSYALAR/parametreler_e_A.txt'
        if program_tip == 'CK1':
            v_dosya_parametre = 'DOSYALAR/parametreler_ck1_A.txt'
        if program_tip == 'CK2':
            v_dosya_parametre = 'DOSYALAR/parametreler_ck2_A.txt'

    if piyasa_modu == 'B':
        if program_tip == 'E':
            v_dosya_parametre = 'DOSYALAR/parametreler_e_B.txt'
        if program_tip == 'CK1':
            v_dosya_parametre = 'DOSYALAR/parametreler_ck1.txt'
        if program_tip == 'CK2':
            v_dosya_parametre = 'DOSYALAR/parametreler_ck2.txt'

    if program_tip == 'CK':  # *************************************Elephant
        v_dosya_alinan = "DOSYALAR/Alinanlar_e.txt"
        v_dosya_satilan = "DOSYALAR/Satilanlar_e.txt"
        v_dosya_sembol = 'DOSYALAR/Sembol_e.txt'
        v_dosya_sabika = 'DOSYALAR/sabikalilar_e.txt'
        v_dosya_sabika1 = 'DOSYALAR/sabikalilar_ck2.txt'
        v_dosya_acilsat = 'DOSYALAR/acil_sat_e.txt'
        v_dosya_acilal = 'DOSYALAR/acil_al_e.txt'
        v_dosya_genelbuy = "DOSYALAR/genel_buy_ck.txt"
        v_dosya_sonuc = "DOSYALAR/Sonuc_e.txt"
        v_dosya_islenen = "DOSYALAR/islenen_ck.txt"
        v_dosya_islenen_1 = "DOSYALAR/islenen_ck1.txt"
        v_dosya_islenen_2 = "DOSYALAR/islenen_ck2.txt"
    elif program_tip == 'CK1':  # *************************************Elephant Bayby1
        v_dosya_alinan = "DOSYALAR/Alinanlar_ck1.txt"
        v_dosya_satilan = "DOSYALAR/Satilanlar_ck1.txt"
        v_dosya_sembol = 'DOSYALAR/Sembol_ck1.txt'
        v_dosya_sabika = 'DOSYALAR/sabikalilar_ck1.txt'
        v_dosya_sabika1 = 'DOSYALAR/sabikalilar_ck2.txt'
        v_dosya_acilsat = 'DOSYALAR/acil_sat_ck1.txt'
        v_dosya_acilal = 'DOSYALAR/acil_al_ck1.txt'
        v_dosya_genelbuy = "DOSYALAR/genel_buy_ck.txt"
        v_dosya_sonuc = "DOSYALAR/Sonuc_ck1.txt"
        v_dosya_islenen = "DOSYALAR/islenen_ck1.txt"
        v_dosya_islenen_1 = "DOSYALAR/islenen_ck.txt"
        v_dosya_islenen_2 = "DOSYALAR/islenen_ck2.txt"
    elif program_tip == 'CK2':  # *************************************Elephant Bayby2
        v_dosya_alinan = "DOSYALAR/Alinanlar_ck2.txt"
        v_dosya_satilan = "DOSYALAR/Satilanlar_ck2.txt"
        v_dosya_sembol = 'DOSYALAR/Sembol_ck2.txt'
        v_dosya_sabika = 'DOSYALAR/sabikalilar_ck2.txt'
        v_dosya_sabika1 = 'DOSYALAR/sabikalilar_ck1.txt'
        v_dosya_acilsat = 'DOSYALAR/acil_sat_ck2.txt'
        v_dosya_acilal = 'DOSYALAR/acil_al_ck2.txt'
        v_dosya_genelbuy = "DOSYALAR/genel_buy_ck.txt"
        v_dosya_sonuc = "DOSYALAR/Sonuc_ck2.txt"
        v_dosya_islenen = "DOSYALAR/islenen_ck2.txt"
        v_dosya_islenen_1 = "DOSYALAR/islenen_ck1.txt"
        v_dosya_islenen_2 = "DOSYALAR/islenen_ck.txt"


# ******************************************************************************************************
def parametre_ata():
    # ********Dosyadan parametreleri oku
    v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_mod, v_test_prod, \
    v_ziplama_oran, v_mum_sayisi, v_dalga_oran, v_bakiye, \
    v_volume_fark_oran, v_oran, v_kar_oran, v_zarar_oran, minVolumePerc, v_program_tip, \
    v_sabika_sure = dosyadan_parametreleri_oku()

    return v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
           v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, \
           v_dalga_oran, v_bakiye, v_program_tip, v_sabika_sure


# ***************************************************
def degiskenleri_basa_al():
    global v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales
    global v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook
    global v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla
    global closes, highes, lowes, openes, kesmeler
    global v_dosya_alinan, v_dosya_satilan, v_dosya_sembol, v_dosya_sabika, v_dosya_sabika1, v_dosya_parametre, \
        v_dosya_acilsat, v_dosya_acilal, v_dosya_genelbuy, v_dosya_sonuc

    v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar, v_kesim, v_ters_kesim, v_hizli_gonzales = 0, 0, 0, 0, 0, 0, 0, 0
    v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, [], [], {}
    v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
    v_last_update, updates, v_time_before, v_time, v_time_before_dk, v_time_dk, v_zipla = '2022', 0, '', '', '', '', 0
    closes, highes, lowes, openes, kesmeler = [], [], [], [], []
    v_dosya_alinan, v_dosya_satilan, v_dosya_sembol, v_dosya_sabika, v_dosya_parametre, \
    v_dosya_acilsat, v_dosya_acilal, v_dosya_genelbuy, v_dosya_sonuc = '', '', '', '', '', '', '', '', ''


# *******************************************************************
def bakiye_kontrol(v_bakiye):
    usdtBalance = v_client.get_asset_balance(asset='BUSD').get('free')

    if float(usdtBalance) < float(v_bakiye):
        vm = 'Bakiye Yetersiz............' + str(usdtBalance) + str(datetime.now())
        Telebot_v1.mainma(vm, 'CK1')
        while True:
            print('Bakiye Yetersiz...', datetime.now())


def db_baglan(program_tip):
    if program_tip == 1:
        DB_FILE = "TRADE3.DB"
    else:
        DB_FILE = "TRADE31.DB"

    con = sqlite3.connect(DB_FILE, timeout=10)
    cursor = con.cursor()
    return con, cursor


def piyasa_modunu_belirle(v_dosya_param):
    with open(v_dosya_param, 'r') as dosya:
        i = 1
        for line in dosya.read().splitlines():
            aciklama = line
            s = aciklama.split("*")
            if i == 1:
                v_piyasa_modu = str(s[1])
            i = i + 1
        dosya.close()
        print('Piyasa Modu Yüklendi.', v_dosya_coin)
    return v_piyasa_modu


# ***********************************************************************************************************************
if __name__ == '__main__':
    global con, cursor, genel_program_tipi
    global v_dosya_param
    v_dosya_coin = []

    # Genel piyasa durumu belirlendi
    v_piyasa_modu = piyasa_modunu_belirle("DOSYALAR/genel_parametreler.txt")

    if v_piyasa_modu == 'B':
        v_dosya_param = "DOSYALAR/parametreler_ck1.txt"
    elif v_piyasa_modu == 'A':
        v_dosya_param = "DOSYALAR/parametreler_ck1_A.txt"
    else:
        v_dosya_param = "DOSYALAR/parametreler_ck1.txt"

    # Tüm parametrelerin parametre dosyasından alınarak atanması
    v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
    v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, \
    v_dalga_oran, v_bakiye, v_program_tip, v_sabika_sure = parametre_ata()

    genel_program_tipi = v_program_tip

    # Farklı programlar için farklı DB ler kullanılıyor
    con, cursor = db_baglan(v_program_tip)
    #
    # dosya_parametre_ata(v_program_tip, v_piyasa_modu)
    # dosyalari_temizle()

    try:
        while True:
            # Belirlenen bakiyenin altındaysa işlem yapma
            # bakiye_kontrol(v_bakiye)

            vm = '  İlk Başladı.........' + str(datetime.now())
            Telebot_v1.mainma(vm, v_program_tip)
            print(vm)

            while True:
                # degiskenleri_basa_al()
                v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
                v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi, v_dalga_oran, \
                v_bakiye, v_program_tip, v_sabika_sure = parametre_ata()

                dosya_parametre_ata(v_program_tip, v_piyasa_modu)
                dosyalari_temizle()
                dosya_aktar(v_inter_g, v_dalga_oran, v_mum_sayisi, v_ziplama_oran, v_program_tip, v_piyasa_modu)

                vm = 'İşlem Yapacağı Coinler........' + str(len(v_dosya_coin)) + '-' + str(v_dosya_coin) + '-' + str(
                    datetime.now())
                Telebot_v1.mainma(vm, v_program_tip)

                # print('Alınn', v_dosya_satilan, v_dosya_alinan)
                # Eğer uygun coin bulamadıysan yeniden başa dön

                if len(v_dosya_coin) < 1:
                    v_maxw = 1
                    break
                else:
                    v_maxw = len(v_dosya_coin)

                # Son temizlik
                islenen_son_temizlik_yap()

                with concurrent.futures.ProcessPoolExecutor(max_workers=v_maxw) as executer:
                    results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g, v_islem_tutar,
                                               v_volume_fark_oran, v_oran, v_kar_oran,
                                               v_zarar_oran, minVolumePerc, v_test_prod, v_ziplama_oran, v_mum_sayisi,
                                               v_dalga_oran, v_bakiye, v_program_tip, v_sabika_sure, v_piyasa_modu) for
                               p
                               in
                               range(len(v_dosya_coin))]
                    # print('Başla.', results)
                    while True:
                        time.sleep(900)
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
                            Telebot_v1.mainma(v_m, v_program_tip)
                            break
                        else:
                            v_m = 'İçerde alım olduğundan yenileyemedi.....' + str(datetime.now())
                            Telebot_v1.mainma(v_m, v_program_tip)

                print('Çalışmaya başladılar...SON')
    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + '-' + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj, v_program_tip)

