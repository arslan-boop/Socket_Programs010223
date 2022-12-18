import multiprocessing
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
import requests
from json import loads
import traceback
import logging
import threading
from binance.spot import Spot as Client
import json
import pandas as pd
import websocket
from binance.client import Client as Client_1
import sqlite3
import time
from datetime import datetime
import API_Config
import talib as ta
import numpy as np
import DB_transactions3
import Telebot_v1
# from threading import Thread
from multiprocessing import Process
from multiprocessing import Pool
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

# ssl den doğacak hataları bertaraf etmek için
requests.packages.urllib3.disable_warnings()

# con = sqlite3.connect("TRADE3.DB")
# cursor = con.cursor()

DB_FILE = "../TRADE3.DB"
con = sqlite3.connect(DB_FILE, timeout=10)
cursor = con.cursor()

# global v_hedef_bid_global, v_alim_var, v_alim_fiyati

v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati = 0, 0, 0, 0
v_last_price_g = 0
v_open_price = 0
genel_alimlar = []


# **************************************************************************************
def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_genel_orderbook, v_open_pri):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati
    # global ask_tbl, bid_tbl
    v_volume_fark_oran = 3  # İlgili bid veya ask satırının tüm tablodaki volume oranı
    v_oran = 0.05  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    v_kar_oran = 1.003
    v_zarar_oran = 0.99
    minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz

    # print(datetime.now(), '-', 'WHALE BAŞI ', '-', str(v_son_fiyat), '-', v_symbol, '-',  str(v_limit), '-', str(v_son_fiyat), '-', str(len(v_genel_orderbook)))

    # Socket classının  sağladığı güncel orderbook la işlem yapacağız.
    # depth_dict = v_spot_client.depth(v_symbol, limit=v_limit)
    depth_dict = v_genel_orderbook

    v_son_fiyat = float(v_son_fiyat)
    v_frame = {side: pd.DataFrame(data=depth_dict[side], columns=["price", "quantity"], dtype=float)
               for side in ["bids", "asks"]}
    ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'])
    bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'])

    # print(ask_tbl.head(5))
    # print(v_symbol, str(v_son_fiyat), datetime.now(), '******HAM HALİ****=', len(bid_tbl), 'Len Ask = ', len(ask_tbl))
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

    # Teklifi karşılayan satışları çıkarıyoruz
    v_bidask_fark_tutar = float(bid_tbl['volume'].sum()) - float(ask_tbl['volume'].sum())
    v_vol_oran_bid = (float(bid_tbl['volume'].sum()) / float(volumewhale)) * 100
    v_hedef_bid = float(v_son_fiyat * v_kar_oran)
    v_vol_oran_ask = (float(ask_tbl['volume'].sum()) / float(volumewhale)) * 100
    v_hedef_ask = float(v_son_fiyat * v_zarar_oran)

    # print(v_symbol, '************************************ORANLAR************************************')
    # print(v_symbol, 'Volumemler-Full= ', "{:.1f}".format(volumewhale), 'Bid = ',
    #       str("{:.1f}".format(bid_tbl['volume'].sum())), 'Ask = ', str("{:.1f}".format(ask_tbl['volume'].sum())))
    # print('Bid Len ve Son Fiyat', v_bid_len, v_ask_len)
    # print('Teklif/Total Vol: ', v_vol_oran_bid, '-', 'Talep/Total Vol:', v_vol_oran_ask, 'Parametrik > oran:',
    #       v_volume_fark_oran)
    # print('Son Fiyat = ', v_son_fiyat, ' Alım Satım Farkı :', "{:.1f}".format(float(v_bidask_fark_tutar)))

    # Alım olmuşsa hedefe gelmişmi kontrolü
    # **********************************************************
    if v_alim_var == 1:
        print(str(v_symbol), 'İçerde alım var.......!!', 'Hedefi = ', str(v_hedef_bid_global), 'Son Fiyat = ',
              str(v_son_fiyat))

        if float(v_son_fiyat) >= float(v_hedef_bid_global):
            v_profit_oran = float(((v_son_fiyat - v_alim_fiyati) * 100) / v_alim_fiyati)
            v_profit_oran = float(v_profit_oran)

            v_mess1 = 'Karla Sattı..Hedefi : ' + "{:.6f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(
                v_symbol) + \
                      '- Alım Fiyatı :' + "{:.6f}".format(float(v_alim_fiyati)) + \
                      ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + '- Kar Oranı :' + "{:.6f}".format(
                float(v_profit_oran)) + ' - Zaman : ' + str(v_time)
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.6f}".format(
                float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(v_time)
            print(v_mess1)
            # ******************
            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)

            v_alim_var = 0
            v_time = str(datetime.now())
            v_time = v_time[0:19]

            # Alımlar dizisinde ilgili coini sil
            genel_alimlar.remove(v_symbol)
            # print(str(v_symbol), ' Alımlar dizisinden silindi........!!', )
            # print(genel_alimlar)

        elif float(v_son_fiyat) < float(v_hedef_ask_global):
            v_zarprofit_oran = float(((v_alim_fiyati - v_son_fiyat) * 100) / v_alim_fiyati)
            v_zarprofit_oran = float(v_zarprofit_oran)

            v_mess1 = 'Zararla Sattı..Hedefi : ' + "{:.6f}".format(float(v_hedef_ask_global)) + '- Sembol :' + str(
                v_symbol) + \
                      '- Alım Fiyatı :' + "{:.6f}".format(float(v_alim_fiyati)) + \
                      ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + '- Zarar Oranı :' + "{:.6f}".format(
                float(v_zarprofit_oran)) + ' - Zaman : ' + str(v_time)
            print(v_mess1)
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.6f}".format(
                float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                               '*' + "{:.3f}".format(float(v_zarprofit_oran)) + '*' + str(v_time)

            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)

            v_alim_var = 0
            v_time = str(datetime.now())
            v_time = v_time[0:19]

            # Alımlar dizisinde ilgili coini sil
            genel_alimlar.remove(v_symbol)
            # print(str(v_symbol), ' Alımlar dizisinden silindi........!!', )
            # print(genel_alimlar)

        else:
            print('İçerde alım var ama henüz satılamadı...!- ', v_symbol, ' - Hedefi = ', str(v_hedef_bid_global),
                  'Son Fiyat = ', str(v_son_fiyat))
    else:

        # Alırken de trende bakacak
        v_alabilirsin = 0
        # v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_son_fiyat = check_change(v_symbol, '1m', 500)
        # if v_1m_c>0  and v_3m_c > 0 and v_5m_c > 0:
        if float(v_son_fiyat) >= float(v_open_pri):
            v_alabilirsin = 1

        if v_bid_len > 0 and v_bidask_fark_tutar >= 0 and v_vol_oran_bid >= v_volume_fark_oran and v_alabilirsin == 1:
            print('SEMBOL', v_symbol, '***ARTMALI *** HEDEF == ', "{:.6f}".format(float(v_hedef_bid)), ' Zaman = ',
                  v_time)
            v_mess = str(v_symbol) + '--' + '***ARTMALI *** HEDEF == ' + '--' + "{:.6f}".format(float(v_hedef_bid)) + \
                     '--' + ' Zaman = ' + '--' + str(v_time) + '--' + 'Son Fiyat = ' + '--' + "{:.6f}".format(
                float(v_son_fiyat))

            # Telegram mesajo
            Telebot_v1.mainma(v_mess)
            v_alim_fiyati = v_son_fiyat
            v_hedef_bid_global = v_hedef_bid
            v_hedef_ask_global = v_hedef_ask
            v_alim_var = 1
            print('****************Teklifler = ********************')
            print(bid_tbl)

            Telebot_v1.genel_alimlar(v_symbol, 'A')

            # Alımlar dizisine ekle
            if genel_alimlar.count(v_symbol) == 0:
               genel_alimlar.append(v_symbol)
            #     print(str(v_symbol), ' Alımlar dizisine eklendi.....!!', )
            #     print(genel_alimlar)
        else:
            print('Alım için Uygun Emir Bulunamadı.!', v_symbol, datetime.now())
            # print('Genel Alımlar = ', genel_alimlar)


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
    v_open_price = candle['o']


# print(datetime.now(), 'SEMBOL=', str(json_message['s']), 'Son fiyat  = ', v_last_price_g)


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
    wst = threading.Thread(target=ws_front.run_forever)
    wst.start()
    # time.sleep(5)
    wst.join(2)


# **************************************************************************************
def dosya_aktar():
    global v_dosya_coin

    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write()
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open('../Sembol3.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_symbol = line
            v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_son_fiyat = check_change(v_symbol, '1m', 500)
            if v_3m_c > 0 and v_5m_c and v_15m_c and v_60m_c > 0:
                if i <= 20:
                    v_dosya_coin.append(line)
                    print('Dosyaya eklenen Coin..: ', line, i)
                else:
                    print('Devamı...Dosyaya eklenen Coin..: ', line, i)
                i += 1
    dosya.close()
    print('Dosya Tamamlandı', v_dosya_coin)


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
    # print('Snapshot alındı', 'Sembol=', v_sembol, 'Limit=', v_limit, 'Zaman=', datetime.now())
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return hloads(r.content.decode())


# Her bir process için
def main_islem(v_sembol_g, v_limit_g, v_inter_g):
    print('Başladı ', v_sembol_g, datetime.now())
    try:
        run_frontdata(v_sembol_g, v_inter_g)
        time.sleep(5)
        islem(v_sembol_g, v_limit_g)
        # time.sleep(5)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


def islem(v_sembol_g, v_limit_g):
    global v_last_price_g, v_open_price
    v_genel_orderbook = []
    while (True):
        v_genel_orderbook = get_snapshot(v_sembol_g, v_limit_g)
        time.sleep(0.3)
        # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'Order Dizi Bids =',         len(v_genel_orderbook["bids"]), 'Order Dizi Asks =', len(v_genel_orderbook["asks"]), datetime.now())
        if v_last_price_g != 0 and len(v_genel_orderbook["bids"]) > 0:
            whale_order_full(v_sembol_g, v_limit_g, v_last_price_g, v_genel_orderbook, v_open_price)


def startup(v_tip):
    global v_limit_g, v_sembol_g, v_inter_g
    global v_dosya_coin, Procesler, v_alim_var, Threadler
    # print('Başladı ', datetime.now())
    v_inter_g = '1s'
    v_limit_g = 1000
    v_in_g = '1000ms'

    if v_tip == 1:
        dosya_aktar()
        p = 0
        for p in range(len(v_dosya_coin)):
            v_sembol_g = v_dosya_coin[p]
            # print('Dosyada ', p, v_dosya_coin[p])
            t = Process(target=main_islem, args=(v_sembol_g, v_limit_g, v_inter_g))
            Procesler.append(t)
            # print('sayısı', str(Procesler))
            p = p + 1

        # print('ttt',threads)
        for x in Procesler:
            x.start()
            print('Processler Açıldı..', Procesler)

        for x in Procesler:
            x.join(10)
        # print('SON')
        return
    else:
        # kill prosesler
        for x in Threadler:
            x.terminate()
            print('Tretler kapatıldı', Procesler)

        for x in Procesler:
            x.terminate()
            print('Processler kapatıldı', Procesler)
        time.sleep(2)
        v_dosya_coin = []
        Procesler = []
        return


if __name__ == '__main__':
    v_dosya_coin = []
    Procesler = []
    # global v_limit_g, v_sembol_g, v_inter_g
    # print('Başladı ', datetime.now())
    v_inter_g = '1s'
    v_limit_g = 1000
    v_in_g = '1000ms'
    try:
        # dosya_aktar()
        #
        # with concurrent.futures.ProcessPoolExecutor(max_workers=len(v_dosya_coin)) as executer:
        #     results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g) for p in  range(len(v_dosya_coin))]
        #
        #     for f in concurrent.futures.as_completed(results):
        #         print(f.result())
        while True:
            print('Başladı.........', datetime.now())
            dosya_aktar()
            with concurrent.futures.ProcessPoolExecutor(max_workers=len(v_dosya_coin)) as executer:
                results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g) for p in
                           range(len(v_dosya_coin))]
                # print('Başla.', results)
                while True:
                    # print('Başla.....222......', datetime.now())
                    time.sleep(60)
                    active = multiprocessing.active_children()
                    #print(f'Active Children: {active}')

                    # terminate all active children
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

            print('Çalışmaya başladılar...SON')
    except Exception as exp:
           v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
           Telebot_v1.mainma(v_hata_mesaj)
