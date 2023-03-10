import warnings
import requests
from json import loads
from datetime import datetime
warnings.simplefilter(action='ignore', category=FutureWarning)
import threading
from binance.spot import Spot as Client
import json
import pandas as pd
import websocket
from binance.client import Client as Client1
import sqlite3
import time
from multiprocessing import Process

from datetime import datetime
import API_Config
import talib as ta
import numpy as np
import DB_transactions3
import Telebot_v1
from threading import Thread

con = sqlite3.connect("TRADE.db")
cursor = con.cursor()

global v_last_price_g, bid_tbl_g, ask_tbl_g, v_limit_g, v_sembol_g, \
    v_inter_g, v_in_g, v_hedef_bid_global, v_alim_var,v_alim_fiyati
v_last_price_g, bid_tbl_g, ask_tbl_g, v_limit_g, v_sembol_g, \
v_inter_g, v_in_g = 0, [], [], 1000, 'btcusdt', '1s', '1000ms'

v_hedef_bid_global = 0
v_hedef_ask_global = 0
v_alim_var = 0
v_alim_fiyati = 0

global genel_orderbook
genel_orderbook = []
global v_dosya_coin
v_dosya_coin = []
global son_fiyatlar
son_fiyatlar = []

# **************************************************************************************
def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_genel_orderbook):
    global  v_alim_var, v_hedef_bid_global,v_hedef_ask_global,v_alim_fiyati
    # global ask_tbl, bid_tbl
    v_volume_fark_oran = 5  # İlgili bid veya ask satırının tüm tablodaki volume oranı
    v_oran = 0.05  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    v_kar_oran = 1.003
    v_zarar_oran = 0.997
    minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz

    # Socket classının  sağladığı güncel orderbook la işlem yapacağız.
    # depth_dict = v_spot_client.depth(v_symbol, limit=v_limit)
    depth_dict = v_genel_orderbook

    v_son_fiyat = float(v_son_fiyat)
    v_frame = {side: pd.DataFrame(data=depth_dict[side], columns=["price", "quantity"], dtype=float)
               for side in ["bids", "asks"]}
    ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'])
    bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'])

    # print(ask_tbl.head(5))
    print(datetime.now(), '-', 'WHALE BAŞI ', '-', str(v_son_fiyat), '-', v_symbol, '-', str(v_limit), '-',
          str(v_son_fiyat), '-', str(len(v_genel_orderbook)))

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
    # first_bid = float(bid_tbl.iloc[1, 0])

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

    # fulltbl = fulltbl[(fulltbl['volume'] >= minVolume)]  # limit our view to only orders greater than or equal to the minVolume size
    ask_tbl = ask_tbl[(ask_tbl['volume'] >= minVolume)]  #
    bid_tbl = bid_tbl[(bid_tbl['volume'] >= minVolume)]  #
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    # print('Len önce ', len(bid_tbl), 'minvol=', minVolume)
    # print(bid_tbl)

    # Son fiyatın üzerindeki büyük teklifleri ve aşağısındaki küçük teklifleri bırakır
    ask_tbl = ask_tbl[(ask_tbl['price'] <= float(v_son_fiyat))]  # Son fiyatın altındaki talepler fiyatı düşürür
    bid_tbl = bid_tbl[(bid_tbl['price'] >= float(v_son_fiyat))]  # Son fiyatın üzerindeki teklifler  fiyatı yükseltir

    # Tüm bu filtrelemerden sonra tabloda kayıt kaldıysa işleme devam et
    v_bid_len = len(bid_tbl)
    v_ask_len = len(ask_tbl)

    #Teklifi karşılayan satışları çıkarıyoruz
    v_bidask_fark_tutar= float(bid_tbl['volume'].sum())-float(ask_tbl['volume'].sum())

    v_vol_oran_bid = (float(bid_tbl['volume'].sum()) / float(volumewhale)) * 100
    v_hedef_bid = float(v_son_fiyat * v_kar_oran)
    v_vol_oran_ask = (float(ask_tbl['volume'].sum()) / float(volumewhale)) * 100
    v_hedef_ask = "{:.8f}".format(float(v_son_fiyat * v_zarar_oran))

    print('************************************ORANLAR************************************')
    print('Volumemler-Full= ', "{:.1f}".format(volumewhale), 'Bid = ', str("{:.1f}".format(bid_tbl['volume'].sum())),'Ask = ', str("{:.1f}".format(ask_tbl['volume'].sum())))
    print('Bid Len ve Son Fiyat', v_bid_len, v_ask_len)
    print('Teklif/Total Vol: ', v_vol_oran_bid, '-','Talep/Total Vol:' ,v_vol_oran_ask, 'Parametrik > oran:', v_volume_fark_oran)
    print('Son Fiyat = ',v_son_fiyat, ' Alım Satım Farkı :', "{:.1f}".format(float(v_bidask_fark_tutar)))

    # Alım olmuşsa hedefe gelmişmi kontrolü
    #**********************************************************
    if v_alim_var == 1 :
       print('İçerde alım var.......!!' , 'Hedefi = ',str( v_hedef_bid_global) ,'Son Fiyat = ', str(v_son_fiyat))

       if v_son_fiyat>= v_hedef_bid_global:
           v_profit_oran = float(((v_son_fiyat - v_alim_fiyati) * 100) / v_alim_fiyati)
           v_profit_oran = "{:.3f}".format(v_profit_oran)

           v_mess1 = 'Karla Sattı..Hedefi : '+str(v_hedef_bid_global) +'- Sembol :'+str(v_sembol_g)+ \
                      '- Alım Fiyatı :' + str(v_alim_fiyati) + \
                      ' - Satım Fiyatı : '+ str(v_son_fiyat)  +'- Kar Oranı :'+str(v_profit_oran)+ ' - Zaman : ' + str(v_time)

           Telebot_v1.mainma(v_mess1)
           v_alim_var = 0
       elif v_son_fiyat <= v_hedef_ask_global:
           v_zarprofit_oran = float(((v_alim_fiyati-v_son_fiyat) * 100) / v_alim_fiyati)
           v_zarprofit_oran = "{:.3f}".format(v_zarprofit_oran)

           v_mess1 = 'Zararla Sattı..Hedefi : '+str(v_hedef_ask_global) +'- Sembol :'+str(v_sembol_g)+ \
                      '- Alım Fiyatı :' + str(v_alim_fiyati) + \
                      ' - Satım Fiyatı : '+ str(v_son_fiyat)  +'- Kar Oranı :'+str(v_zarprofit_oran)+ ' - Zaman : ' + str(v_time)

           Telebot_v1.mainma(v_mess1)
           v_alim_var = 0
    else:
        if v_bid_len > 0 and v_bidask_fark_tutar> 0:
            # Toplam hacme göre oran (Bid ve Askların toplamı). Oran ne kadar büyükse teklif o kadar yüksektir.
            # Son fiyatı geçen tekliflerin toplamı ile son fiyat arasındaki fark önemli olacak
            #print('Oranlar = ', v_vol_oran_bid, '-', v_volume_fark_oran, '-', str(float(bid_tbl.iloc[0, 0])), '-', v_son_fiyat)
            if v_vol_oran_bid >= v_volume_fark_oran : #and float(bid_tbl.iloc[0, 0]) > v_son_fiyat:  # (v_hedef_bid >= v_son_fiyat * v_kar_oran):
                print('SEMBOL', v_symbol, '***ARTMALI *** HEDEF == ', "{:.5f}".format(v_hedef_bid), ' Zaman = ', v_time)
                print('Güncel Fiyat= ', "{:.5f}".format(float(v_son_fiyat)), ' Teklif Fiyatı = ', float(bid_tbl.iloc[0, 0]),
                      ' Teklif Total = ', "{:.1f}".format(float(bid_tbl['volume'].sum())), 'Teklif/Total Volume Oran=(%)', "{:.2f}".format(v_vol_oran_bid))
                      #' Telif Total = ', "{:.1f}".format(float(bid_tbl.iloc[0, 2])), 'Volume Oran=(%)', "{:.2f}".format(v_vol_oran_bid))
                # print('Güncel = ', v_son_fiyat ) #, ' Teklif = ',bid_tbl_son.head(1) )
                v_mess = str(v_sembol_g) + '--' + '***ARTMALI *** HEDEF == ' + '--' + str(v_hedef_bid) + '--' + ' Zaman = ' + \
                         '--' + str(v_time)+ '--' +'Son Fiyat = ',v_son_fiyat
                Telebot_v1.mainma(v_mess)
                v_alim_fiyati= v_son_fiyat
                v_hedef_bid_global = v_hedef_bid
                v_hedef_ask_global = v_son_fiyat * 0.98
                v_alim_var = 1
                print('****************Teklifler = ********************')
                print(bid_tbl)
                return 1
        else:
            # print('SEMBOL', v_symbol, 'Uygun Emir Bulunamadı - Bid', datetime.now(), )
            return 0
        if v_ask_len > 0  and v_bidask_fark_tutar <0 :
            # Toplam hacme göre oran (Bid ve Askların toplamı)
            if v_vol_oran_ask >= v_volume_fark_oran : #and (float(ask_tbl.iloc[0, 0]) < v_son_fiyat):
                print('SEMBOL', v_symbol, '*****DÜŞMELİ *** HEDEF == ', "{:.5f}".format(float(v_hedef_ask)), ' Zaman = ',v_time)
                print('Güncel Fiyat= ', "{:.5f}".format(float(v_son_fiyat)), ' Talep Fiyatı = ', float(ask_tbl.iloc[0, 0]),
                      'Talep Total = ', "{:.1f}".format(float(ask_tbl['volume'].sum())), 'Talep/Total Volume Oran=(%)', "{:.2f}".format(v_vol_oran_ask))
                # print('Güncel = ', v_son_fiyat ) #, ' Teklif = ',bid_tbl_son.head(1) )
                v_mess = str(v_sembol_g) + '--' + 'Son Fiyat=',"{:.8f}".format(float(v_son_fiyat)), '***DÜŞMELİ *** HEDEF == ' + '--' + str(v_hedef_ask) + '--' + ' Zaman = ' + '--' + str(v_time)
                Telebot_v1.mainma(v_mess)

                print('**********************Talepler = ************************')
                print(ask_tbl)
                return 1
        else:
            # print('Uygun Emir Bulunamadı - Ask')
            return 0
        # else:
        # print('*******************ANIK İZLEME TABLOSU************************', v_time)
        # print('Güncel Altında= ', v_son_fiyat, ' Teklif = ', float(bid_tbl.iloc[0, 0]), ' Total = ', float(bid_tbl.iloc[0, 2]))
        # return 0


# *******************************************************Frontun soketi
def on_open_f(ws_front):
    subscribe_message = {"method": "SUBSCRIBE", "params": vn_front, "id": 1}
    ws_front.send(json.dumps(subscribe_message))
    print('opened connection', subscribe_message)


def on_error_f(ws_front):
    print('Error olustu')


def on_close_f(ws_front):
    print('closed connection')


def on_message_f(ws_front, message):
    global v_last_price_g
    json_message = json.loads(message)
    # print('Gelen mesaj: ', json_message)
    candle = json_message['k']
    v_last_price_g = candle['c']
    print('ON-FRONT SEMBOL=', str(json_message['s']), 'Son fiyat  = ', v_last_price_g)


# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter):
    global vn_front, ws_front_g
    v_symbol = v_symbol.lower()
    v_sembol_deg1 = f'[{v_symbol}@kline_{v_inter}]'
    v_sembol_deg5 = v_sembol_deg1.replace("[", "")
    v_sembol_deg5 = v_sembol_deg5.replace("]", "")
    vn_front = [v_sembol_deg5]
    socket_f = 'wss://stream.binance.com:9443/ws'
    # ws_front = websocket.WebSocketApp(socket_f, on_message=on_message_f, on_open=on_open_f, on_close=on_close_f, on_error=on_error_f)
    ws_front = websocket.WebSocketApp(socket_f, on_message=on_message_f, on_open=on_open_f, on_close=on_close_f)
    ws_front.run_forever()


# **************************************************************************************
def dosya_aktar():
    global v_dosya_coin
    v_dosya_coin = []
    with open('../DOSYALAR/Sembol3.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_dosya_coin.append(line)
            print('Dosyaya eklenen', v_dosya_coin)
            i += 1
    dosya.close()
    print('Dosya Tamam')

def run_frontdata(v_sem, v_int):
    while (True):
        try:
            socket_front(v_sem, v_int)
            time.sleep(0.33)
        # except:
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..run_frontdata  = ' + str(exp)
            Telebot_v1.mainma(v_hata_mesaj)
            time.sleep(2)


def get_snapshot(v_sembol,v_limit):
    print('Snapshot alındı', 'Sembol=', v_sembol, 'Limit=', v_limit, 'Zaman=', datetime.now())
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())

def t22(v_sembol_g, v_limit_g,v_int):
    v_genel_orderbook = []
    # Son fiyatı almak için Coini sürekli dinleyen socket stream --, daemon=True
    t1 = threading.Thread(target=run_frontdata, args=(v_sembol_g, v_inter_g))
    t1.start()
    time.sleep(1.666)

    # while (True):
    #     v_genel_orderbook = get_snapshot(v_sembol_g, v_limit_g)
    #     time.sleep(0.66)
    #     # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'Order Dizi Bids =',len(v_genel_orderbook["bids"]), 'Order Dizi Asks =', len(v_genel_orderbook["asks"]), datetime.now())
    #     if v_last_price_g != 0:
    #         whale_order_full(v_sembol_g, v_limit_g, v_last_price_g, v_genel_orderbook)

def main_islem(v_sembol_g, v_limit_g,v_inter_g):
    print('Başladı ', v_sembol_g, datetime.now())
    t1 = threading.Thread(target=run_frontdata, args=(v_sembol_g, v_inter_g))
    t1.start()
    t2 = threading.Thread(target=islem, args=(v_sembol_g, v_limit_g))
    t2.start()
    t1.join(0.2)
    t2.join(0.2)
    time.sleep(2)
    #print('sonuuççççççççç', v_sembol_g)

def islem(v_sembol_g, v_limit_g):
    v_genel_orderbook = []
    while (True):
        v_genel_orderbook = get_snapshot(v_sembol_g, v_limit_g)
        time.sleep(0.66)
        # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'Order Dizi Bids =',len(v_genel_orderbook["bids"]), 'Order Dizi Asks =', len(v_genel_orderbook["asks"]), datetime.now())
        if v_last_price_g != 0:
            whale_order_full(v_sembol_g, v_limit_g, v_last_price_g, v_genel_orderbook)

if __name__ == '__main__':
    v_genel_orderbook = []
    Procesler = []
    threads = []
    try:
        print('Başladı ', datetime.now())
        v_inter_g = '1s'
        v_limit_g = 1000
        v_in_g = '1000ms'
        #v_sembol_g = 'VIDTUSDT'
        # Dosyaya uygun coinleri aktardı
        dosya_aktar()
        p=1
        for p in range(len(v_dosya_coin)):
            v_sembol_g=  v_dosya_coin[p]
            print('Dosyada ',p,  v_dosya_coin[p])
            t= Process(target=main_islem , args=(v_sembol_g, v_limit_g,v_inter_g))
            Procesler.append(t)
            p = p +1

        #print('ttt',threads)
        for x in Procesler:
            x.start()

        for x in Procesler:
            x.join(0.2)
        #
        # for x in threads:
        #    x.start()
        #
        # for x in threads:
        #    x.join(0.2)
        #
        print('----------------------------------------',datetime.now())
    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp)+datetime.now()
        Telebot_v1.mainma(v_hata_mesaj)
