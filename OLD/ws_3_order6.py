import warnings

import ws_3_order6_socket

warnings.simplefilter(action='ignore', category=FutureWarning)
import threading
import traceback
import logging
import websocket, json, pprint
from binance.spot import Spot as Client
import json
import pandas as pd
from binance.client import Client as Client1
import sqlite3
import time
from datetime import datetime
import API_Config
import talib as ta
import numpy as np
import DB_transactions3
import Telebot_v1
from threading import Thread
from ws_3_order6_socket import Client_Socket

con = sqlite3.connect("TRADE.db")
cursor = con.cursor()

global v_last_price_g, bid_tbl_g, ask_tbl_g, v_limit_g, v_sembol_g, v_inter_g, v_in_g
v_last_price_g, bid_tbl_g, ask_tbl_g, v_limit_g, v_sembol_g, v_inter_g, v_in_g = 0, [], [], 1000, 'btcusdt', '1s', '1000ms'
global genel_orderbook
genel_orderbook = {}


# **************************************************************************************
def whale_order_full(v_symbol, v_limit, v_spot_client, v_son_fiyat, v_genel_orderbook):
    # global ask_tbl, bid_tbl
    v_volume_fark_oran = 2  # İlgili bid veya ask satırının tüm tablodaki volume oranı
    v_oran = 0.05  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    v_kar_oran = 1.003
    v_zarar_oran = 0.997
    minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz

    # print('son fii',v_son_fiyat )
    # Socket classının  sağladığı güncel orderbook la işlem yapacağız.
    # depth_dict = v_spot_client.depth(v_symbol, limit=v_limit)
    depth_dict = v_genel_orderbook

    v_son_fiyat = float(v_son_fiyat)
    v_frame = {side: pd.DataFrame(data=depth_dict[side], columns=["price", "quantity"], dtype=float)
               for side in ["bids", "asks"]}
    ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'])
    bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'])

    #print('Len Bid  İlkler=', len(bid_tbl), 'Len Ask = ',len(ask_tbl) )
    # Fiyatları nümeric yap
    ask_tbl['price'] = pd.to_numeric(ask_tbl['price'])
    ask_tbl['quantity'] = pd.to_numeric(ask_tbl['quantity'])
    bid_tbl['price'] = pd.to_numeric(bid_tbl['price'])
    bid_tbl['quantity'] = pd.to_numeric(bid_tbl['quantity'])
    # print('öncesi',ask_tbl)

    # Tabloya Hacim kolonu ekle. Hacim toplam alım tutarı aslında
    # Bunun için öncelikle ara tablo(frame)oluşturuyoruz 3 kolonlu
    ob_ask = pd.DataFrame(columns=['price', 'quantity', 'volume'])
    ob_bid = pd.DataFrame(columns=['price', 'quantity', 'volume'])
    if len(ask_tbl) < 1 or len(bid_tbl) < 1:
        return
    for i in range(len(bid_tbl)):
        v_total_b = float(bid_tbl['price'][i] * bid_tbl['quantity'][i])
        v_fiyat_b = bid_tbl['price'][i]
        v_miktar_b = bid_tbl['quantity'][i]
        ob_bid.loc[(i + 1) - 1] = [v_fiyat_b, v_miktar_b, v_total_b]

    for i in range(len(ask_tbl)):
        v_total_a = float(ask_tbl['price'][i] * ask_tbl['quantity'][i])
        v_fiyat_a = ask_tbl['price'][i]
        v_miktar_a = ask_tbl['quantity'][i]
        ob_ask.loc[(i + 1) - 1] = [v_fiyat_a, v_miktar_a, v_total_a]

    # Hacmide işin içine katıp tekrar baştaki tabloya atadık
    ask_tbl = ob_ask
    bid_tbl = ob_bid
    # print(ask_tbl)
    # data from websocket are not sorted yet
    ask_tbl = ask_tbl.sort_values(by='price', ascending=True)
    bid_tbl = bid_tbl.sort_values(by='price', ascending=False)

    # get first on each side
    first_ask = float(ask_tbl.iloc[1, 0])
    #first_bid = float(bid_tbl.iloc[1, 0])

    # Teklif ve talep emir satırlarını belirlenen % oranı kadar yukarıda veya aşağıdaki fiyata
    # çekiyoruz. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    perc_above_first_ask = ((1.0 + v_oran) * first_ask)
    perc_above_first_bid = ((1.0 - v_oran) * first_ask)

    # limits the size of the table so that we only look at orders 5% above and under market price
    ask_tbl = ask_tbl[(ask_tbl['price'] <= perc_above_first_ask)]
    bid_tbl = bid_tbl[(bid_tbl['price'] >= perc_above_first_bid)]

    # changing this position after first filter makes calc faster
    bid_tbl['volume'] = pd.to_numeric(bid_tbl['volume'])
    ask_tbl['volume'] = pd.to_numeric(ask_tbl['volume'])
    fulltbl = bid_tbl.append(ask_tbl)  # append the buy and sell side tables to create one cohesive table

    volumewhale = fulltbl['volume'].sum()
    minVolume = fulltbl['volume'].sum() * minVolumePerc  # Calc minimum Volume for filteringg
    #print('Volumeler-Full= ',volumewhale, 'Bid = ',str(bid_tbl['volume'].sum()),'Ask = ', str(ask_tbl['volume'].sum()) )

    # fulltbl = fulltbl[(fulltbl['volume'] >= minVolume)]  # limit our view to only orders greater than or equal to the minVolume size
    ask_tbl = ask_tbl[(ask_tbl['volume'] >= minVolume)]  #
    bid_tbl = bid_tbl[(bid_tbl['volume'] >= minVolume)]  #
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    # print('Len önce ', len(bid_tbl), 'minvol=', minVolume)
    # print(bid_tbl)

    # Son fiyatın üzerindeki büyük teklifleri ve aşağısındaki küçük teklifleri bırakır
    ask_tbl = ask_tbl[(ask_tbl['price'] < float(v_son_fiyat))]  # Son fiyatın altındaki talepler fiyatı düşürür
    bid_tbl = bid_tbl[(bid_tbl['price'] > float(v_son_fiyat))]  # Son fiyatın üzerindeki teklifler  fiyatı yükseltir

    # Tüm bu filtrelemerden sonra tabloda kayıt kaldıysa işleme devam et
    v_bid_len = len(bid_tbl)
    v_ask_len = len(ask_tbl)
    print('Bid Len ve Son Fiyat', v_bid_len, v_ask_len, v_son_fiyat)
    if v_bid_len > 0:
        # Toplam hacme göre oran (Bid ve Askların toplamı). Oran ne kadar büyükse teklif o kadar yüksektir.
        v_vol_oran_bid = (float(bid_tbl['volume'].sum()) / float(volumewhale)) * 100
        v_hedef_bid = float(v_son_fiyat * v_kar_oran)
        # Son fiyatı geçen tekliflerin toplamı ile son fiyat arasındaki fark önemli olacak
        print('Oranlar = ', v_vol_oran_bid, '-', v_volume_fark_oran, '-', str(float(bid_tbl.iloc[0, 0])), '-',
              v_son_fiyat)
        if v_vol_oran_bid >= v_volume_fark_oran and float(
                bid_tbl.iloc[0, 0]) > v_son_fiyat:  # (v_hedef_bid >= v_son_fiyat * v_kar_oran):
            print('***ARTMALI *** HEDEF == ', "{:.4f}".format(v_hedef_bid), ' Zaman = ', v_time)
            print('Güncel Fiyat= ', "{:.4f}".format(float(v_son_fiyat)), ' Teklif Fiyatı = ', float(bid_tbl.iloc[0, 0]),
                  ' Total = ', "{:.1f}".format(float(bid_tbl.iloc[0, 2])), 'Volume Oran=(%)',
                  "{:.2f}".format(v_vol_oran_bid))
            # print('Güncel = ', v_son_fiyat ) #, ' Teklif = ',bid_tbl_son.head(1) )
            v_mess = str(v_sembol_g) + '--' + '***ARTMALI *** HEDEF == ' + '--' + str(
                v_hedef_bid) + '--' + ' Zaman = ' + '--' + str(v_time)
            Telebot_v1.mainma(v_mess)
            print('Teklifler = ')
            print(bid_tbl)
            return 1
    else:
        print('Uygun Emir Bulunamadı - Bid')
        return 0
    if v_ask_len > 0:
        # Toplam hacme göre oran (Bid ve Askların toplamı)
        v_vol_oran_ask = (float(ask_tbl['volume'].sum()) / float(volumewhale)) * 100
        v_hedef_ask = float(v_son_fiyat * v_zarar_oran)

        if v_vol_oran_ask >= v_volume_fark_oran and (float(ask_tbl.iloc[0, 0]) < v_son_fiyat):
            print('*****DÜŞMELİ *** HEDEF == ', "{:.4f}".format(float(v_hedef_ask)), ' Zaman = ', v_time)
            print('Güncel Fiyat= ', "{:.4f}".format(float(v_son_fiyat)), ' Talep Fiyatı = ', float(ask_tbl.iloc[0, 0]),
                  ' Total = ', "{:.1f}".format(float(ask_tbl.iloc[0, 2])), 'Volume Oran=(%)',
                  "{:.2f}".format(v_vol_oran_ask))
            # print('Güncel = ', v_son_fiyat ) #, ' Teklif = ',bid_tbl_son.head(1) )
            v_mess = str(v_sembol_g) + '--' + '***DÜŞMELİ *** HEDEF == ' + '--' + str(
                v_hedef_ask) + '--' + ' Zaman = ' + '--' + str(v_time)
            Telebot_v1.mainma(v_mess)

            print('Talepler = ')
            print(ask_tbl)
            return 1
    else:
        print('Uygun Emir Bulunamadı - Ask')
        return 0
    # else:
    # print('*******************ANIK İZLEME TABLOSU************************', v_time)
    # print('Güncel Altında= ', v_son_fiyat, ' Teklif = ', float(bid_tbl.iloc[0, 0]), ' Total = ', float(bid_tbl.iloc[0, 2]))
    # return 0


# ******************Frontun soketi
def on_open_f(ws_front):
    print('opened connection', vn_front)
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front, "id": 1}
    ws_front.send(json.dumps(subscribe_message))


def on_error_f(self, error):
    print('HATAAAA connection')

def on_close_f(ws_front):
    print('closed connection')


def on_message_f(ws_front, message):
    global v_last_price_g
    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    v_last_price_g = candle['c']
    v_sembol_g = json_message['s']
    print('Son fiyat  = ', v_last_price_g)


# **************************************************************************************
# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter):
    global vn_front, ws_front_g
    v_symbol = v_symbol.lower()
    v_sembol_deg1 = f'[{v_symbol}@kline_{v_inter}]'
    v_sembol_deg5 = v_sembol_deg1.replace("[", "")
    v_sembol_deg5 = v_sembol_deg5.replace("]", "")
    vn_front = [v_sembol_deg5]
    socket_f = 'wss://stream.binance.com:9443/ws'
    ws_front = websocket.WebSocketApp(socket_f, on_message=on_message_f, on_open=on_open_f, on_close=on_close_f,
                                      on_error=on_error_f)
    ws_front.run_forever()
    # ws_front_g = ws_front
    # print('ws front', ws_front)


# # keep connection alive
# def run_wsler(ws):
#     ws.run_forever()
#

# def socket_data(v_sembol_g, v_in_g):
#     global vn
#     # v_sembol_deg1 = f'[{v_s}@depth]'
#     v_sembol_g = v_sembol_g.lower()
#     v_sembol_deg1 = f'[{v_sembol_g}@depth@{v_in_g}]'
#     v_sembol_deg5 = v_sembol_deg1.replace("[", "")
#     v_sembol_deg5 = v_sembol_deg5.replace("]", "")
#     vn = [v_sembol_deg5]
#     socket = 'wss://stream.binance.com:9443/ws'
#     ws = websocket.WebSocketApp(socket, on_message=on_message, on_open=on_open, on_close=on_close)
#     ws.run_forever()


def run_frontdata(v_sem, v_int):
    while (True):
        try:
            socket_front(v_sem, v_int)
            time.sleep(1.666)
        #except:
        #    time.sleep(2)
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..T3  =  ' + str(exp)


def run_order_book_ozet(v_sembol_g, v_inter_g, v_limit_g, v_in_g):
    ws_socket = Client_Socket(v_sembol_g, v_inter_g, v_limit_g, v_in_g)
    ws_socket.run_forever()


def run_order_book(v_sembol_g, v_inter_g, v_limit_g, v_in_g):
    while (True):
        try:
            run_order_book_ozet(v_sembol_g, v_inter_g, v_limit_g, v_in_g)
            time.sleep(1.666)
        except:
            time.sleep(2)

# spot api kullanarak verdiğimiz miktardaki emirleri döner (1000 tane vs)
def hesapla_full(v_sembol_g, v_limit_g, spot_client, v_last_price_g):
    while (True):
        try:
            v_genel_orderbook = ws_3_order6_socket.Client_Socket.get_ordergenelorder_book(Client_Socket, 1)
            #print('v_cccccccccccccccccccccccccGenl book', v_genel_orderbook)
            # print('lart =', v_last_price_g)
            if v_last_price_g != 0:
                whale_order_full(v_sembol_g, v_limit_g, spot_client, v_last_price_g, v_genel_orderbook)
            time.sleep(1.666)
        except:
            time.sleep(2)


if __name__ == '__main__':
    try:
        spot_client = Client(base_url="https://api3.binance.com")
        # spot_client = Client(base_url="https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=1000")
        print('Başladı ', datetime.now())
        v_sembol_g = 'BTCUSDT'
        v_inter_g = '1s'
        v_limit_g = 100
        v_in_g = '1000ms'
        # Coini sürekli dinleyen socket stream
        t1 = threading.Thread(target=run_frontdata, args=(v_sembol_g, v_inter_g))
        t2 = threading.Thread(target=run_order_book, args=(v_sembol_g, v_inter_g, v_limit_g, v_in_g))
        t1.start()
        time.sleep(1.666)
        t2.start()
        time.sleep(5)
        i = 1
        # genel_orderbook = ws_3_order6_socket.Client_Socket.get_ordergenelorder_book(Client_Socket, 1)
        # print('Genl book', genel_orderbook)
        t3 = threading.Thread(target=hesapla_full,args=(v_sembol_g, v_limit_g, spot_client, v_last_price_g))
        t3.start()
        """
        while True:
            #print('Son fiyat iç  = ', v_last_price_g)
            genel_orderbook = ws_3_order6_socket.Client_Socket.get_ordergenelorder_book(Client_Socket, 1)
            #print('Genl book', genel_orderbook)
            #t3 = threading.Thread(target=whale_order_full,args=(v_sembol_g, v_limit_g, spot_client, v_last_price_g, genel_orderbook))
            if (v_last_price_g != 0) and len(genel_orderbook)>1:
               # t3.start()
               whale_order_full(v_sembol_g, v_limit_g, spot_client, v_last_price_g, genel_orderbook)
               time.sleep(5)
            i = i + 1
        """
        #print(v_last_price_g, '-', v_sembol_g, '---------------------------------------------------------')
        print('-----------------------')

    except Exception as exp:
        v_hata_mesaj = 'Hata Oluştu!!..T1  = ' + str(exp)
