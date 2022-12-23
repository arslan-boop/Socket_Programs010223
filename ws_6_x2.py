import multiprocessing
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
import requests
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

# global v_hedef_bid_global, v_alim_var, v_alim_fiyati

v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati, v_alim_miktar = 0, 0, 0, 0, 0
v_last_price_g, v_alim_zamani, v_alim_timestamp, v_open_price, genel_alimlar, genel_satimlar, orderbook = 0, '', 0, 0, [], [], {}
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
v_last_update, updates, v_time_before, v_time, v_zipla = '2022', 0, '', '', 0
# orderbook = []
v_dizi_bov, v_dizi_bov_top, v_dizi_avo, v_dizi_avo_top, v_dizi_fiyat, v_fark_tutar_bov = [], [], [], [], [], []
v_dizi_bov_g, v_dizi_bov_top_g, v_dizi_avo_g, v_dizi_avo_top_g, v_dizi_fiyat_g, v_fark_tutar_bov_g = [], [], [], [], [], []


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


# *****************************ALIM SATIM İŞLEMLERİ*****************************************************

def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_genel_orderbook, v_open_pri, v_islem_tutar, v_volume_fark_oran,
                     v_oran, v_kar_oran, v_zarar_oran, minVolumePerc, v_test_prod):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati, v_last_price_g, v_alim_miktar
    global v_client, v_alim_timestamp, v_alim_zamani

    if v_alim_var == 0:
        depth_dict = v_genel_orderbook
        try:
            # v_frame = {side: pd.DataFrame(data=depth_dict[side], columns=["price", "quantity"], dtype=float)
            #           for side in ["bids", "asks"]}
            bids_price = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 0]
            bids_quantity = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 1]
            df_bids = pd.DataFrame(dtype=float)
            df_bids["price"] = pd.Series(bids_price)
            df_bids["quantity"] = pd.Series(bids_quantity)

            asks_price = np.asarray(v_genel_orderbook["asks"], dtype=float)[:, 0]
            asks_quantity = np.asarray(v_genel_orderbook["asks"], dtype=float)[:, 1]
            df_asks = pd.DataFrame(dtype=float)
            df_asks["price"] = pd.Series(asks_price)
            df_asks["quantity"] = pd.Series(asks_quantity)
            bid_tbl = df_bids
            ask_tbl = df_asks
            # ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'],dtype=float)
            # bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'],dtype=float)
            ask_tbl = ask_tbl.fillna(0)
            bid_tbl = bid_tbl.fillna(0)
            #
            ask_tbl['price'] = pd.to_numeric(ask_tbl['price'])
            ask_tbl['quantity'] = pd.to_numeric(ask_tbl['quantity'])
            bid_tbl['price'] = pd.to_numeric(bid_tbl['price'])
            bid_tbl['quantity'] = pd.to_numeric(bid_tbl['quantity'])

            # data from websocket are not sorted yet
            ask_tbl = ask_tbl.sort_values(by='price', ascending=True)
            bid_tbl = bid_tbl.sort_values(by='price', ascending=False)

            first_ask = float(ask_tbl.iloc[0, 0])
            first_bid = float(bid_tbl.iloc[0, 0])
            mid_price = float((first_ask + first_bid) / 2)

            perc_above_first_ask = ((1.0 + v_oran) * mid_price)
            perc_above_first_bid = ((1.0 - v_oran) * mid_price)

            # limits the size of the table so that we only look at orders 5% above and under market price
            ask_tbl = ask_tbl[(ask_tbl['price'] <= perc_above_first_ask)]
            bid_tbl = bid_tbl[(bid_tbl['price'] >= perc_above_first_bid)]
            #
            # changing this position after first filter makes calc faster
            fulltbl = bid_tbl.append(ask_tbl)  # append the buy and sell side tables to create one cohesive table
            volumewhale = fulltbl['quantity'].sum()

            v_bidask_fark_tutar_old = float(bid_tbl['quantity'].sum()) - float(ask_tbl['quantity'].sum())
            v_vol_oran_bid_old = (float(bid_tbl['quantity'].sum()) / float(volumewhale)) * 100
            v_vol_oran_ask_old = (float(ask_tbl['quantity'].sum()) / float(volumewhale)) * 100

            v_son_fiyat = float(v_last_price_g)
            # v_hedef_bid = float(v_son_fiyat * v_kar_oran)
            # v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
            # Son fiyatın üzerindeki büyük teklifleri ve aşağısındaki küçük teklifleri bırakır
            ask_tbl = ask_tbl[(ask_tbl['price'] <= float(v_son_fiyat))]
            bid_tbl = bid_tbl[(bid_tbl['price'] >= float(v_son_fiyat))]
            v_bid_len = len(bid_tbl)
            # v_ask_len = len(ask_tbl)

            v_bidask_fark_tutar = float(bid_tbl['quantity'].sum()) - float(ask_tbl['quantity'].sum())
            v_vol_oran_bid = (float(bid_tbl['quantity'].sum()) / float(volumewhale)) * 100
            v_vol_oran_ask = (float(ask_tbl['quantity'].sum()) / float(volumewhale)) * 100

            v_karar,v_zip = main_log_karar(v_symbol, v_bidask_fark_tutar, v_bidask_fark_tutar_old, v_son_fiyat,
                                     v_vol_oran_bid, v_vol_oran_bid_old, v_vol_oran_ask, v_vol_oran_ask_old,
                                     v_volume_fark_oran)
            if v_karar == 1:
                if v_test_prod == 'P':
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati ,v_alim_zamani = buy_coin(v_symbol, v_islem_tutar, v_bidask_fark_tutar, bid_tbl,
                                                            ask_tbl, v_vol_oran_bid, v_vol_oran_ask,
                                                            v_kar_oran, v_zarar_oran)
                else:
                    v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, \
                    v_alim_miktar, v_alim_fiyati,v_alim_zamani = buy_coin_test(v_symbol, v_islem_tutar, v_bidask_fark_tutar, bid_tbl,
                                                                 ask_tbl, v_vol_oran_bid, v_vol_oran_ask,
                                                                 v_kar_oran, v_zarar_oran,v_zip)

                v_alim_var = 1
            else:
                print('Alım için Uygun Emir Bulunamadı.!', v_symbol, datetime.now())
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Alım tarafı  = ' + str(exp) + str(v_symbol)
            Telebot_v1.mainma(v_hata_mesaj)
    elif v_alim_var == 1:

        # Test için analiz logu
        # if v_test_prod == 'T':
        #     test_log(v_genel_orderbook, v_symbol)

        current_timestamp = round(time.time() * 1000)
        v_satim_timestamp = current_timestamp / 1000
        try:
            v_son_fiyat = float(v_last_price_g)
            print(str(v_symbol), 'İçerde alım var.......!!', str(datetime.now())[0:19], 'Hedefi = ',
                  str(v_hedef_bid_global), 'Son Fiyat = ', str(v_last_price_g))

            if float(v_last_price_g) > float(v_hedef_bid_global):
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 1,v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 1,v_alim_zamani)
                v_alim_var == 0
            elif float(v_last_price_g) < float(v_hedef_ask_global):
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 2,v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 2,v_alim_zamani)
            elif v_satim_timestamp >= v_alim_timestamp:
                if v_test_prod == 'P':
                    sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, 3,v_alim_zamani)
                else:
                    sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, 3,v_alim_zamani)
                v_alim_var == 0
            else:
                print('İçerde alım var ama henüz satılamadı...!- ', str(datetime.now())[0:19], v_symbol, ' - Hedefi = ',
                      str(v_hedef_bid_global), 'Son Fiyat = ', str(v_last_price_g))
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Satım tarafı  = ' + str(exp)
            Telebot_v1.mainma(v_hata_mesaj)


# *********************************** KARAR MEKANİZMASI *********************************************

def main_log_karar(v_symbol, v_bidask_fark_tutar, v_bidask_fark_tutar_old, v_son_fiyat, v_vol_oran_bid,
                   v_vol_oran_bid_old, v_vol_oran_ask, v_vol_oran_ask_old, v_volume_fark_oran):
    global v_time, v_time_before, v_zipla
    global v_dizi_bov, v_dizi_bov_top, v_dizi_avo, v_dizi_avo_top, v_dizi_fiyat, v_fark_tutar_bov
    global  v_dizi_bov_g, v_dizi_bov_top_g, v_dizi_avo_g, v_dizi_avo_top_g, v_dizi_fiyat_g, v_fark_tutar_bov_g

    v_zipla = 0
    v_al_sat = 0

    v_time = str(datetime.now())[0:19]

    v_dizi_bov.append(float(v_vol_oran_bid))
    v_dizi_bov_top.append(float(v_vol_oran_bid_old))
    v_dizi_avo.append(float(v_vol_oran_ask))
    v_dizi_avo_top.append(float(v_vol_oran_ask_old))
    v_dizi_fiyat.append(v_son_fiyat)
    v_fark_tutar_bov.append(float(v_bidask_fark_tutar))

    print('Top ', sum(v_dizi_bov), len(v_dizi_bov))

    if v_time_before != v_time:
        v_dizi_bov_g.append(float(sum(v_dizi_bov) / len(v_dizi_bov)))
        v_dizi_bov_top_g.append(float(sum(v_dizi_bov_top) / len(v_dizi_bov_top)))
        v_dizi_avo_g.append(float(sum(v_dizi_avo) / len(v_dizi_avo)))
        v_dizi_avo_top_g.append(float(sum(v_dizi_avo_top) / len(v_dizi_avo_top)))
        v_dizi_fiyat_g.append(float(sum(v_dizi_fiyat) / len(v_dizi_fiyat)))
        v_fark_tutar_bov_g.append(float(sum(v_fark_tutar_bov) / len(v_fark_tutar_bov)))

        if len(v_dizi_bov_g) > 1:
            # Girerken fiyatı da kontrol et..Fiyatın düştüğü yerde girme
            v_last_fiyat = float(v_dizi_fiyat_g[-1])
            v_prev_fiyat = float(v_dizi_fiyat_g[-2])
            if v_last_fiyat >= v_prev_fiyat :
                v_fiyat_ok = 1
            else:
                v_fiyat_ok = 0
            #------------------------------------------------------------
            # Bid oranlarında bir anormallik  ziplama var mı ?
            v_last_b = float(v_dizi_bov_g[-1])
            v_prev_b = float(v_dizi_bov_g[-2])
            v_bov_oran = float(v_last_b - v_prev_b)
            v_last_t = float(v_dizi_bov_top_g[-1])
            v_prev_t = float(v_dizi_bov_top_g[-2])
            v_bov_oran_t = float(v_last_t - v_prev_t)

            if v_prev_b <= 0.1 and v_last_b >= 1:
                v_zipla = 1
            elif v_prev_b > 0.15 and v_prev_b < 0.30 and v_last_b >= 2 and v_last_b <=3:
                v_zipla = 1
            elif v_prev_b > 0.5 and float(v_last_b / v_prev_b) > 3:
                v_zipla = 1
            else:
                v_zipla = 0
            #--------------------------------------------------------------

        else:
            v_bov_oran = 0
            v_bov_oran_t = 0

        # BOV oranlarında ki ilerlemenin durumu. Kullanmak istersek
        if v_bov_oran > 0:
            print('BOV artıyor...')
            v_bov_arti = 1
        elif v_bov_oran < 0:
            print('BOV azalıyor...')
            v_bov_arti = 2
        else:
            print('BOV sabit...')
            v_bov_arti = 3

        if v_bov_oran_t > 0:
            print('BOV_T artıyor...')
            v_bov_arti_t = 1
        elif v_bov_oran_t < 0:
            print('BOV_T azalıyor...')
            v_bov_arti_t = 2
        else:
            print('BOV_T sabit...')
            v_bov_arti_t = 3
        #----------------------------------------------------------------

        if float(v_vol_oran_bid) >= float(v_volume_fark_oran * 100) and \
                float(v_vol_oran_bid) > float(v_vol_oran_ask) and \
                v_bov_arti == 1 and v_bov_arti_t == 1 and v_zipla == 1 and v_fiyat_ok==1:
            v_al_sat = 1
        else:
            v_al_sat = 0

        print('Dizi bov',v_dizi_bov)
        #Sn lik hesaplamalar yapıldığı için her sn değiştiğinde bu dizileri sıfırla
        v_dizi_bov = []
        v_dizi_bov_top = []
        v_dizi_avo = []
        v_dizi_avo_top = []
        v_dizi_fiyat = []
        v_fark_tutar_bov  = []

    #-----------------------------------------------------------------------------------

    v_mee = v_symbol + '*' + 'Fark Tutarlar = ' + '*' + "{:.1f}".format(float(v_bidask_fark_tutar)) + '*' + \
            'Fark Top = ' + '*' + "{:.1f}".format(float(v_bidask_fark_tutar_old)) + '*' + \
            'Fiyat:' + '*' + "{:.6f}".format(float(v_son_fiyat)) + '*' + \
            'B_V_OS:' + '*' + "{:.1f}".format(float(v_vol_oran_bid)) + '*' + \
            "{:.1f}".format(float(v_vol_oran_bid_old)) + '*' + \
            'A_V_OS:' + '*' + "{:.1f}".format(float(v_vol_oran_ask)) + '*' + \
            "{:.1f}".format(float(v_vol_oran_ask_old)) + '*' + \
            'Zaman = ' + '*' + str(datetime.now())
    Telebot_v1.analiz(v_mee, v_symbol)

    v_time_before = v_time

    if len(v_dizi_bov_g) > 3:
        print('dizi genel', v_dizi_bov_g)
        v1 = float(v_dizi_bov_g[-1])
        v2 = float(v_dizi_bov_g[-2])
        v3 = float(v_dizi_bov_g[-3])
        v_dizi_bov_g =[]
        v_dizi_bov_g.append(v3)
        v_dizi_bov_g.append(v2)
        v_dizi_bov_g.append(v1)
        print('dizi genel', v_dizi_bov_g)

    return v_al_sat, v_zipla
    # ***************************************************************************************
    # ALma kriterleri değişti.
    # 1- BOV Top oran %45 ve üzeri olacak (v_vol_oran_bid_old )
    # 2- v_vol_oran_bid %10 ve üzeri daha iyi . Fakat %1 ile de arta arta gelebiliyor.
    # 3- BOV / AVO oranı min 3 katı olacak
    # 4- BOV Toplam negatif olmayacak, hatta daha önceki saniyede - iken + ya dönecek

    # if v_bid_len > 0 and v_bidask_fark_tutar >= 0 and float(v_vol_oran_bid) >= float(v_volume_fark_oran * 100):
    # if 1 == 1:  # and float(ask_tbl['quantity'].sum()) <2 and v_vol_oran_ask <1 and \  # float(v_vol_oran_bid) <20:


# ***********************************TEST İÇİN LOG******************************
def test_log(v_genel_orderbook, v_symbol):
    bids_price = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 0]
    bids_quantity = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 1]
    df_bids = pd.DataFrame(dtype=float)
    df_bids["price"] = pd.Series(bids_price)
    df_bids["quantity"] = pd.Series(bids_quantity)

    asks_price = np.asarray(v_genel_orderbook["asks"], dtype=float)[:, 0]
    asks_quantity = np.asarray(v_genel_orderbook["asks"], dtype=float)[:, 1]
    df_asks = pd.DataFrame(dtype=float)
    df_asks["price"] = pd.Series(asks_price)
    df_asks["quantity"] = pd.Series(asks_quantity)
    bid_tbl = df_bids
    ask_tbl = df_asks
    # ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'],dtype=float)
    # bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'],dtype=float)
    ask_tbl = ask_tbl.fillna(0)
    bid_tbl = bid_tbl.fillna(0)
    #
    ask_tbl['price'] = pd.to_numeric(ask_tbl['price'])
    ask_tbl['quantity'] = pd.to_numeric(ask_tbl['quantity'])
    bid_tbl['price'] = pd.to_numeric(bid_tbl['price'])
    bid_tbl['quantity'] = pd.to_numeric(bid_tbl['quantity'])

    # data from websocket are not sorted yet
    ask_tbl = ask_tbl.sort_values(by='price', ascending=True)
    bid_tbl = bid_tbl.sort_values(by='price', ascending=False)

    first_ask = float(ask_tbl.iloc[0, 0])
    first_bid = float(bid_tbl.iloc[0, 0])
    mid_price = float((first_ask + first_bid) / 2)

    perc_above_first_ask = ((1.0 + v_oran) * mid_price)
    perc_above_first_bid = ((1.0 - v_oran) * mid_price)

    # limits the size of the table so that we only look at orders 5% above and under market price
    ask_tbl = ask_tbl[(ask_tbl['price'] <= perc_above_first_ask)]
    bid_tbl = bid_tbl[(bid_tbl['price'] >= perc_above_first_bid)]
    #
    # changing this position after first filter makes calc faster
    fulltbl = bid_tbl.append(ask_tbl)  # append the buy and sell side tables to create one cohesive table
    volumewhale = fulltbl['quantity'].sum()

    v_bidask_fark_tutar_old = float(bid_tbl['quantity'].sum()) - float(ask_tbl['quantity'].sum())
    v_vol_oran_bid_old = (float(bid_tbl['quantity'].sum()) / float(volumewhale)) * 100
    v_vol_oran_ask_old = (float(ask_tbl['quantity'].sum()) / float(volumewhale)) * 100

    v_son_fiyat = float(v_last_price_g)

    # v_hedef_bid = float(v_son_fiyat * v_kar_oran)
    # v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
    # Son fiyatın üzerindeki büyük teklifleri ve aşağısındaki küçük teklifleri bırakır
    ask_tbl = ask_tbl[(ask_tbl['price'] <= float(v_son_fiyat))]  #
    bid_tbl = bid_tbl[(bid_tbl['price'] >= float(v_son_fiyat))]  #
    # Tüm bu filtrelemerden sonra tabloda kayıt kaldıysa işleme devam et
    v_bid_len = len(bid_tbl)
    # v_ask_len = len(ask_tbl)
    # Teklifi karşılayan satışları çıkarıyoruz
    v_bidask_fark_tutar = float(bid_tbl['quantity'].sum()) - float(ask_tbl['quantity'].sum())
    v_vol_oran_bid = (float(bid_tbl['quantity'].sum()) / float(volumewhale)) * 100
    v_vol_oran_ask = (float(ask_tbl['quantity'].sum()) / float(volumewhale)) * 100

    v_mee = v_symbol + '*' + 'Fark Tutarlar = ' + '*' + "{:.1f}".format(float(v_bidask_fark_tutar)) + '*' + \
            'Fark Top = ' + '*' + "{:.1f}".format(float(v_bidask_fark_tutar_old)) + '*' + \
            'Fiyat:' + '*' + "{:.6f}".format(float(v_son_fiyat)) + '*' + \
            'B_V_OS:' + '*' + "{:.1f}".format(float(v_vol_oran_bid)) + '*' + \
            "{:.1f}".format(float(v_vol_oran_bid_old)) + '*' + \
            'A_V_OS:' + '*' + "{:.1f}".format(float(v_vol_oran_ask)) + '*' + \
            "{:.1f}".format(float(v_vol_oran_ask_old)) + '*' + \
            'Zaman = ' + '*' + str(datetime.now())
    Telebot_v1.analiz(v_mee, v_symbol)


# ****************************SATIM********************************
def sell_coin(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip,v_alim_zamani):
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

            # print(v_mess1)
            # ******************
            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
            v_alim_var = 0
            Telebot_v1.genel_alimlar(v_symbol, 'S')
            # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
        else:
            v_hata = 'SATIM işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata)

    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ***************************TEST SATIM*************************
def sell_coin_test(v_symbol, v_alim_miktar, v_alim_fiyati, v_tip,v_alim_zamani):
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
        # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)

    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# *************************ALIM*********************************
def buy_coin(v_symbol, v_islem_tutar, v_bidask_fark_tutar, bid_tbl, ask_tbl, v_vol_oran_bid, v_vol_oran_ask, v_kar_oran,
             v_zarar_oran):
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
            v_alim_timestamp = (current_timestamp + (30000)) / 1000
            # v_alim_zamani = str(datetime.now())[0:19]
        else:
            v_hata = 'Alım işlemi Binance tarafında gerçekleşmemeiş!!! = ' + str(v_symbol)
            Telebot_v1.mainma(v_hata)

        v_mess = str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'Miktar = ' + '--' + "{:.8f}".format(float(v_alim_miktar)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.8f}".format(float(v_islem_tutar)) + '--' + \
                 'Fark Tutar = ' + '--' + "{:.1f}".format(float(v_bidask_fark_tutar)) + '--' + \
                 'Bid Topl= ' + '--' + "{:.1f}".format(float(bid_tbl['quantity'].sum())) + '--' + \
                 'Ask Topl= ' + '--' + "{:.1f}".format(float(ask_tbl['quantity'].sum())) + '--' + \
                 'Bid_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_bid)) + '--' + \
                 'Ask_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_ask))
        # Telegram mesajo
        Telebot_v1.mainma(v_mess)
        Telebot_v1.genel_alimlar(v_symbol, 'A')
        v_sembolmik = v_symbol.replace("USDT", "")
        v_alim_miktar = v_client.get_asset_balance(asset=v_sembolmik).get('free')
        v_alim_miktar = get_round_step_quantity(v_symbol, float(v_alim_miktar))

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, v_alim_miktar, v_alim_fiyati,v_alim_zamani
    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
    Telebot_v1.mainma(v_hata_mesaj)


# ************************TEST ALIM**********************/

def buy_coin_test(v_symbol, v_islem_tutar, v_bidask_fark_tutar, bid_tbl, ask_tbl, v_vol_oran_bid, v_vol_oran_ask,
                  v_kar_oran, v_zarar_oran,v_zip):
    global v_last_price_g, v_alim_zamani
    try:
        v_son_fiyat = float(v_last_price_g)
        v_alim_zamani = str(datetime.now())
        v_alim_fiyati = v_son_fiyat
        v_hedef_bid = float(v_son_fiyat * v_kar_oran)
        v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
        v_hedef_bid_global = v_hedef_bid
        v_hedef_ask_global = v_hedef_ask
        current_timestamp = round(time.time() * 1000)
        v_alim_timestamp = (current_timestamp + (90000)) / 1000
        v_alim_var = 1

        v_mess = str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.8f}".format(float(v_hedef_bid)) + \
                 '--' + ' Zaman = ' + '--' + str(v_alim_zamani) + '--' + \
                 'Fiyat = ' + '--' + "{:.8f}".format(float(v_alim_fiyati)) + '--' + \
                 'İşlem Tutar = ' + '--' + "{:.8f}".format(float(v_islem_tutar)) + '--' + \
                 'Fark Tutar = ' + '--' + "{:.1f}".format(float(v_bidask_fark_tutar)) + '--' + \
                 'Bid Topl= ' + '--' + "{:.1f}".format(float(bid_tbl['quantity'].sum())) + '--' + \
                 'Ask Topl= ' + '--' + "{:.1f}".format(float(ask_tbl['quantity'].sum())) + '--' + \
                 'Bid_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_bid)) + '--' + \
                 'Ask_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_ask))+ '--' + \
                 'Zip='+ '--' + str(v_zip)
        # Telegram mesajo
        Telebot_v1.mainma(v_mess)
        Telebot_v1.genel_alimlar(v_symbol, 'A')

        return v_son_fiyat, v_hedef_bid, v_hedef_ask, v_hedef_bid_global, v_hedef_ask_global, v_alim_timestamp, v_alim_miktar, v_alim_fiyati,v_alim_zamani
    except Exception as exp:
        v_hata_mesaj = 'Satarken  Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


# ********************ORDER BOOK SOCKETİ ******************************
def basla(v_lim, v_sem):
    global v_limit, v_sembol, orderbook, updates
    try:
        v_limit = v_lim
        v_sembol = v_sem.lower()
        v_soc = "wss://stream.binance.com:9443/ws/" + v_sembol + "@depth@100ms"
        wsb = websocket.WebSocketApp(v_soc, on_open=on_open, on_close=on_close, on_message=on_message)
        # ws.run_forever()
        t1 = threading.Thread(target=wsb.run_forever)
        t1.start()
        t1.join(2)
        orderbook = {}
        updates = 0
    except Exception as exp:
        v_hata_mesaj = 'Hata Oluştu!!..basla  = ' + str(exp)
        Telebot_v1.mainma(v_hata_mesaj)


def on_open(ws):
    print('2.Soketi başlattı .....!!!')


def on_close(ws):
    print('closed connection')


def on_message(ws, message):
    global orderbook, v_limit, v_sembol
    global updates, v_last_update

    # print('received message')
    data = loads(message)

    if len(orderbook) == 0:
        orderbook = get_snapshot(v_sembol, v_limit)

    lastUpdateId = orderbook['lastUpdateId']
    # print(datetime.now(), 'Anlık Data', len(data["b"]))
    # print('İçerde Emir orderbook Bids ve Ask =', len(orderbook["bids"]), '-', len(orderbook["asks"]))
    # drop any updates older than the snapshot
    if updates == 0:
        if data['U'] <= lastUpdateId + 1 and data['u'] >= lastUpdateId + 1:
            # print(f'lastUpdateId {data["u"]}')
            orderbook['lastUpdateId'] = data['u']
            process_updates(data)
        else:
            print('discard update')

    # check if update still in sync with orderbook
    elif data['U'] == lastUpdateId + 1:
        # print(f'lastUpdateId {data["u"]}')
        orderbook['lastUpdateId'] = data['u']
        process_updates(data)
    else:
        print('Out of sync, abort')


def process_updates(data):
    # with lock:
    for update in data['b']:
        manage_orderbook('bids', update)
    for update in data['a']:
        manage_orderbook('asks', update)
        # last_update['last_update'] = datetime.now()
    v_last_update = datetime.now()


def manage_orderbook(side, update):
    price, qty = update
    for x in range(0, len(orderbook[side])):
        if price == orderbook[side][x][0]:
            if qty == 0:
                del orderbook[side]
                print(f'Removed {price} {qty}')
                break
            else:
                orderbook[side][x] = update
                # print(f'Updated: {price} {qty}')
                break
        elif price > orderbook[side][x][0]:
            if qty != 0:
                orderbook[side].insert(x, update)
                # print(f'New price: {price} {qty}')
                break
            else:
                break


def get_ordergenelorder_book():
    global orderbook
    return orderbook


# *******************************************************Frontun soketi
def on_open_f(ws_front):
    global vn_front
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front, "id": 1}
    ws_front.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f(ws_front):
    print('Error olustu')


def on_close_f(ws_front):
    print('closed connection')


def on_message_f(ws_front, message):
    global v_last_price_g, v_open_price
    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    v_last_price_g = candle['c']
    # v_last_price_g = json_message['c']
    # v_last_price_g = json_message['p']
    # print('son fiyat',v_last_price_g, datetime.now() )
    # v_open_price = candle['o']


# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter):
    global vn_front, ws_front_g
    v_symbol = v_symbol.lower()
    v_sembol_deg1 = f'[{v_symbol}@kline_{v_inter}]'
    v_sembol_deg5 = v_sembol_deg1.replace("[", "")
    v_sembol_deg5 = v_sembol_deg5.replace("]", "")
    vn_front = [v_sembol_deg5]
    socket_f = 'wss://stream.binance.com:9443/ws'
    ws_front = websocket.WebSocketApp(socket_f, on_message=on_message_f, on_open=on_open_f, on_close=on_close_f)
    wst = threading.Thread(target=ws_front.run_forever)
    wst.start()
    wst.join(2)


def dosyalari_temizle():
    open("Alinanlar.txt", 'w').close()
    open("Satilanlar.txt", 'w').close()


def dosya_aktar():
    global v_dosya_coin
    #
    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write()
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open('Sembol3.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_symbol = line
            # v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_son_fiyat = check_change(v_symbol, '1m', 500)

            v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
            v_ema_arti_3m, v_3m_sonfiyat, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, v_1m_c, \
            v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p = check_exist(v_symbol, '1m', 500, v_client)

            # if adx_arti == 1 and stoc_arti==1 and v_3m_c>0 and v_15m_c>0 and v_60m_c> 0:
            if 1 == 1:  # v_3m_c>0 and v_ema_arti_3m==1:
                if i <= 17:
                    v_dosya_coin.append(line)
                    print('Dosyaya eklenen Coin..: ', line, i, datetime.now())
                else:
                    print('Devamı...Dosyaya eklenen Coin..: ', line, i, datetime.now())
                i += 1
            else:
                print('Dosyaya Uygun Değil .: ', line, i, datetime.now())
    dosya.close()
    print('Dosya Tamamlandı', v_dosya_coin)

    with open('sabikalilar.txt', 'r') as dosya_sabika:
        i = 0
        for line in dosya_sabika.read().splitlines():
            if (line in v_dosya_coin):
                v_dosya_coin.remove(line)
    dosya_sabika.close()
    print('Sabıkalılar Temizlendi.', v_dosya_coin)


def check_change_dk(v_symbol, v_interval, v_limit):
    # v_interval = '1m'
    # global v_client, v_last_buyed_coin
    v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
    klines = v_client.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
    close = [float(entry[4]) for entry in klines]
    v_len = len(close)
    v_l_c_p = close[-1]

    if v_len < 2:
        return 0, 0, 0, 0, 0
    else:
        v_p_c_p2 = close[-2]
        v_1m_c = float(((v_l_c_p - v_p_c_p2) * 100) / v_p_c_p2)
    return v_1m_c


def check_change(v_symbol, v_interval, v_limit):
    # v_interval = '1m'
    # global v_client, v_last_buyed_coin
    v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
    klines = v_client.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
    close = [float(entry[4]) for entry in klines]
    v_len = len(close)
    v_l_c_p = close[-1]

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

    return v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p


def run_frontdata(v_sem, v_int):
    # while (True):
    try:
        socket_front(v_sem, v_int)
        # time.sleep(2)
    except Exception as exp:
        v_hata_mesaj = 'Hata Oluştu!!..run_frontdata  = ' + str(exp)
        Telebot_v1.mainma(v_hata_mesaj)
        time.sleep(2)


def get_snapshot(v_sembol, v_limit):
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())


def main_islem(v_sembol_g, v_limit_g, v_inter_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
               v_zarar_oran, minVolumePerc, v_test_prod):
    print('Başladı ', v_sembol_g, datetime.now())
    try:
        run_frontdata(v_sembol_g, v_inter_g)
        time.sleep(2.33)
        basla(v_limit_g, v_sembol_g)
        time.sleep(2.33)
        islem(v_sembol_g, v_limit_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
              v_zarar_oran, minVolumePerc, v_test_prod)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


def islem(v_sembol_g, v_limit_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
          v_zarar_oran, minVolumePerc, v_test_prod):
    global v_last_price_g, v_open_price, orderbook, v_alim_var
    v_on_zaman = ''
    v_genel_orderbook = {}
    v_genel_orderbook = orderbook  # get_snapshot(v_sembol_g, v_limit_g)
    time.sleep(8.66)
    try:
        while (True):
            v_zaman = str(datetime.now())[0:16]
            v_kota_doldu = icerdeki_alinan()
            if v_kota_doldu >= 15:
                if v_on_zaman != v_zaman:
                    v_mesajx = 'İçerde 15 alım var. Kota dolduğu için yeni alım yapılamıyor!!!...' + str(datetime.now())
                    Telebot_v1.mainma(v_mesajx)
                    v_on_zaman = v_zaman

                if v_alim_var == 1:
                    time.sleep(0.01)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price,
                                     v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
                                     v_zarar_oran, minVolumePerc, v_test_prod)
            else:
                if v_alim_var == 0:
                    v_genel_orderbook = orderbook  # get_snapshot(v_sembol_g, v_limit_g)
                    time.sleep(0.01)
                    if v_last_price_g != 0 and len(v_genel_orderbook["bids"]) and len(v_genel_orderbook["asks"]):
                        print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'Order Dizi Bids =',
                              len(v_genel_orderbook["bids"]), 'Order Dizi Asks =', len(v_genel_orderbook["asks"]),
                              datetime.now())
                        whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price,
                                         v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
                                         v_zarar_oran, minVolumePerc, v_test_prod)
                else:
                    time.sleep(0.01)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price,
                                     v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran,
                                     v_zarar_oran, minVolumePerc, v_test_prod)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + str(v_sembol_g) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


def icerdeki_alinan():
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open("Satilanlar.txt", "r").readlines())
    genel_alimlar = len(open("Alinanlar.txt", "r").readlines())
    v_icerde = int(genel_alimlar) - int(genel_satimlar)
    return v_icerde


def alinan_satilan_esitmi():
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open("Satilanlar.txt", "r").readlines())
    genel_alimlar = len(open("Alinanlar.txt", "r").readlines())
    if genel_satimlar == genel_alimlar:
        return 1
    else:
        return 0


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
        # print('last_plus_di = ', last_plus_di, "last_minus_di = ", last_minus_di, "previous_plus_di = ", previous_plus_di, "previous_minus_di = ", previous_minus_di, "adx_cross_up =", adx_cross_up)

        # Gerçek değerler artım ve azalımlarda

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


def parametre_ata():
    v_inter_g = '1s'
    v_limit_g = 5000
    v_in_g = '1000ms'
    v_islem_tutar = 20
    v_mod = 'S'
    v_test_prod = 'T'

    if v_mod == 'S':
        v_volume_fark_oran = 0.02  # İlgili bid veya ask satırının tüm tablodaki volume oranı
        v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
        v_kar_oran = 1.004
        v_zarar_oran = 0.995
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
           v_zarar_oran, minVolumePerc, v_test_prod


if __name__ == '__main__':
    v_dosya_coin = []
    v_inter_g, v_limit_g, v_in_g, v_islem_tutar, v_volume_fark_oran, v_oran, v_kar_oran, \
    v_zarar_oran, minVolumePerc, v_test_prod = parametre_ata()

    try:
        while True:
            # usdtBalance = v_client.get_asset_balance(asset='USDT').get('free')
            vm = 'İlk Başladı.........' + str(datetime.now())
            Telebot_v1.mainma(vm)
            print(vm)
            while True:
                print('Başladı.........', datetime.now())
                dosyalari_temizle()
                dosya_aktar()

                # Eğer uygun coin bulamadıysan yeniden başa dön
                if len(v_dosya_coin) < 1:
                    v_maxw = 1
                    break
                else:
                    v_maxw = len(v_dosya_coin)

                with concurrent.futures.ProcessPoolExecutor(max_workers=v_maxw) as executer:
                    results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g, v_islem_tutar,
                                               v_volume_fark_oran, v_oran, v_kar_oran,
                                               v_zarar_oran, minVolumePerc, v_test_prod) for p
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
                            Telebot_v1.mainma(v_m)
                            break
                        else:
                            v_m = 'İçerde alım olduğundan yenileyemedi.....' + str(datetime.now())
                            Telebot_v1.mainma(v_m)

                print('Çalışmaya başladılar...SON')
    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
