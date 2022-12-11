import multiprocessing
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
import requests

from json import loads
from itertools import zip_longest
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

v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati = 0, 0, 0, 0
v_last_price_g = 0
v_alim_zamani = ''
v_alim_timestamp = 0
v_open_price = 0
genel_alimlar = []
genel_satimlar = []
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)

# global orderbook, updates, v_last_update
v_last_update = '2022'
orderbook = {}
updates = 0


# *****************************ALIM SATIM İŞLEMLERİ*****************************************************
def UniqueResults(dataframe):
    tmp = [dataframe[col].unique() for col in dataframe]
    return pd.DataFrame(zip_longest(*tmp), columns=dataframe.columns)

#With New DataFrame
def UniqueResults1(dataframe):
    df = pd.DataFrame()
    for col in dataframe:
        S=pd.Series(dataframe[col].unique())
        df[col]=S.values
    return df

def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_genel_orderbook, v_open_pri):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati, v_last_price_g
    global v_client, v_alim_timestamp, v_alim_zamani
    # v_client = Client(API_Config.API_KEY, API_Config.API_SECRET)
    #depth_dict = []
    # global ask_tbl, bid_tbl
    v_volume_fark_oran = 0.01  # İlgili bid veya ask satırının tüm tablodaki volume oranı
    v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    v_kar_oran = 1.004
    v_zarar_oran = 0.995
    minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz
    if v_alim_var == 0:
        #depth_dict = np.asarray(v_genel_orderbook['asks'], dtype=float)[:,0]
        depth_dict = v_genel_orderbook
        print('değer',v_genel_orderbook['asks'][0])
        try:
            # ob_ask = pd.DataFrame(columns=['price', 'quantity'])
            # ob_bid = pd.DataFrame(columns=['price', 'quantity'])
            #
            # for i in range(len(depth_dict['bids'])):
            #      price = depth_dict['bids'][i][0]
            #      quantity= depth_dict['bids'][i][1]
            #      ob_bid.loc[(i + 1) - 1] = [price, quantity]
            #
            # for i in range(len(depth_dict['asks'])):
            #     price = depth_dict['asks'][i][0]
            #     quantity = depth_dict['asks'][i][1]
            #     ob_ask.loc[(i + 1) - 1] = [price, quantity]
            # diziask = []
            # print(len(depth_dict['asks']))
            # # print(depth_dict['asks'][0])
            # print(depth_dict['asks'])
            # #
            # numpy_array2 = np.array(depth_dict['asks'])
            # print(numpy_array2.ndim) # dizinin boyutunu söyler
            # print(numpy_array2.shape) # dizinin satır ve sütün sayısını söyler
            # #
            # # # 1. sütun
            # # first_column = numpy_array[:, 0]
            # diziask = depth_dict['asks']
            #
            # arr = np.array(depth_dict['asks'])
            #dtype = int32

            #depth_dict = np.array(depth_dict)
            # mean_data = np.asarray(mean_data)
            #R = np.array(mean_data)[:,0]
            # R = np.array(mean_data[:, 0]) bunu kullan
            # c_price=[]
            #
            # c_price = depth_dict['asks'][:, 0]
            # print(c_price)
            print('s')

            # c_price = np.asarray(depth_dict['asks'], dtype=float)[:,0]
            # c_quantity = np.asarray(depth_dict['asks'], dtype=float)[:,1]

            #c_price = np.array(depth_dict['asks'][:,0], dtype=float)
            #c_quantity = np.array(depth_dict['asks'][:,1], dtype=float)

            # c_price = np.array(depth_dict['asks'])[:,0]
            # c_quantity = np.array(depth_dict['asks'])[:,1]


            #df = pd.DataFrame(data=c_price, columns=["price"], dtype=float)
            #df = pd.DataFrame(data=type(c_price), columns=["price"], dtype=float)
            # df = pd.DataFrame(dtype=float)
            # #df["price"] = pd.Series(c_price)
            # df["quantity"] = pd.Series(c_quantity)
            # print(df)
            # print('1.kolon')

            # print('1.kolon')
            # print(c_price[0])
            # print('2.kolon')
            # print(c_quantity[0])
            # if  len(c_price) != len(c_quantity ):
            #     print('Eşit değil',len(c_price), len(c_quantity ) )
            # else:
            #print('Eşit looooo', len(c_price), len(c_quantity))
            # # 1. ve 2. sütun
            # first_and_second_column = numpy_array[:, 0:2]
            #
            # d= depth_dict['asks'][:0]
            # print('dee',d)
            # ask_tbl = pd.DataFrame(data=d)
            # #bid_tbl = pd.DataFrame(data=depth_dict['bids'])
            # print(ask_tbl)
            # #print(bid_tbl)
            #
            # # ask_tbl = pd.DataFrame(data=depth_dict['asks'][0])
            # # print('başson')
            # print(ask_tbl[0],ask_tbl[1] )
            # print('son')
            # price = bid_tbl[0]
            # q = bid_tbl[1]
            # df_list.append(price)
            # print(df_list)
            # df_list.append(q)
            # print(df_list)


            #df = pd.concat(df_list).reset_index(drop=True)
            #print(bid_tbl[0])
            #out = UniqueResults1(bid_tbl)
            #print(out)
            # print(df)
            print('son')


            #ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'])
            #bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'])

            #ask_tbl = pd.Series(data=depth_dict['asks'], index=pd.Index)

            #print(bid_tbl)

            # for i in range(len(bid_tbl)):
            #     v_total_b = float(bid_tbl['price'][i] * bid_tbl['quantity'][i])
            #     v_fiyat_b = bid_tbl['price'][i]
            #     v_miktar_b = bid_tbl['quantity'][i]
            #     ob_bid.loc[(i + 1) - 1] = [v_fiyat_b, v_miktar_b, v_total_b]
            #
            #price_array =
            #dict_keys(['lastUpdateId', 'bids', 'asks'])
            #df = pd.DataFrame(data=depth_dict['bids'], columns=["price", "quantity"], dtype=float)

            # ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'])
            # bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'])
            # print(ask_tbl)
            # print(bid_tbl)


            # for side in ["bids", "asks"]:
            #     df = pd.DataFrame(depth_dict[side], columns=["price", "quantity"], dtype=float)
            #     #df1 = df.apply(lambda col: pd.Series(col.unique()))

                #out = UniqueResults(df)
                #df = df.fillna(0)
                #df["side"] = side
                #print('Side yazacak', df["side"])
                #df_list.append(df)
                #print('df _list yaz ', df_list)

            # print('df _list yaz son ')
            # print(df_list)
            # print('df  son ')
            # print(df)
            #df = pd.concat(df_list).reset_index(drop=True)
            # print('df birleş son= ')
            # print(df)
            #
            # print('son')

            #
            # v_frame = {side: pd.DataFrame(data=depth_dict[side], columns=["price", "quantity"], dtype=float)
            #            for side in ["bids", "asks"]}
            # print(len(v_frame))
            # print(v_frame)

            # ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'])
            # bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'])
            # # ask_tbl = pd.Series(data=depth_dict['asks'], columns=['price', 'quantity'])
            # bid_tbl = pd.Series(data=depth_dict['bids'], columns=['price', 'quantity'])
            #
            # print(len(bid_tbl))
            # print(len(ask_tbl))
            # Adding list to pandas DataFrame
            #Boş olan satırlarda hata verdiği için eklendi. Değerlerin değişmediği görüldü.09.12
            # ask_tbl['price'] = pd.Series(ask_tbl['price'])
            # ask_tbl['quantity'] = pd.Series(ask_tbl['quantity'])
            # bid_tbl['price'] = pd.Series(bid_tbl['price'])
            # bid_tbl['quantity'] = pd.Series(bid_tbl['quantity'])
            #
            # ask_tbl = ask_tbl.fillna(0)
            # bid_tbl = bid_tbl.fillna(0)

        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Alım tarafı  = ' + str(exp)
            # print(bid_tbl)
            # print(ask_tbl)
            Telebot_v1.mainma(v_hata_mesaj)
            pass
    elif v_alim_var == 1:
        try:
            print('alım vqr')

        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Satım tarafı  = ' + str(exp)
            Telebot_v1.mainma(v_hata_mesaj)


# ********************ORDER BOOK SOCKETİ ******************************

def basla(v_lim, v_sem):
    # print('Soketi başlattı')
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
        orderbook = []
        updates = 0
        # print('çıkyo')
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


# Update orderbook, differentiate between remove, update and new
def manage_orderbook(side, update):
    # extract values
    price, qty = update

    # loop through orderbook side
    for x in range(0, len(orderbook[side])):
        if price == orderbook[side][x][0]:
            # when qty is 0 remove from orderbook, else
            # update values
            if qty == 0:
                del orderbook[side]
                print(f'Removed {price} {qty}')
                break
            else:
                orderbook[side][x] = update
                # print(f'Updated: {price} {qty}')
                break
        # if the price level is not in the orderbook,
        # insert price level, filter for qty 0
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
    v_open_price = candle['o']


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


def dosyalari_temizle():
    open("Alinanlar.txt", 'w').close()
    open("Satilanlar.txt", 'w').close()


def dosya_aktar():
    global v_dosya_coin
    # #
    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write()
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open('Sembol3.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_symbol = line
            # v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
            # v_ema_arti_3m, v_3m_sonfiyat, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, v_1m_c, \
            # v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p = check_exist(v_symbol, '1m', 500, v_client)
            #
            # if adx_arti == 1 and stoc_arti==1 and v_3m_c>0 and v_15m_c>0 and v_60m_c> 0:
            v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_son_fiyat = check_change(v_symbol, '1m', 500)
            if 1 == 1:  # v_3m_c > 0 and v_5m_c > 0 :# and v_15m_c > 0 and v_60m_c > 0:
                if i <= 9:
                    v_dosya_coin.append(line)
                    print('Dosyaya eklenen Coin..: ', line, i, datetime.now())
                else:
                    print('Devamı...Dosyaya eklenen Coin..: ', line, i, datetime.now())
                i += 1
            else:
                print('Dosyaya Uygun Değil .: ', line, i, datetime.now())
    dosya.close()
    print('Dosya Tamamlandı', v_dosya_coin)


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
    # https://www.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT
    # print('Snapshot alındı', 'Sembol=', v_sembol, 'Limit=', v_limit, 'Zaman=', datetime.now())
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())


# Her bir process için
def main_islem(v_sembol_g, v_limit_g, v_inter_g):
    print('Başladı ', v_sembol_g, datetime.now())
    try:
        run_frontdata(v_sembol_g, v_inter_g)
        time.sleep(2)
        basla(v_limit_g, v_sembol_g)
        time.sleep(2)
        # print('basson')
        islem(v_sembol_g, v_limit_g)
        # time.sleep(5)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


def islem(v_sembol_g, v_limit_g):
    global v_last_price_g, v_open_price, orderbook
    v_genel_orderbook = {}
    cc = []
    v_genel_orderbook = orderbook  # get_snapshot(v_sembol_g, v_limit_g)
    #v_genel_orderbook = get_snapshot(v_sembol_g, v_limit_g)
    time.sleep(10)
    #
    # print('ord1',orderbook)
    # print('or2',v_genel_orderbook)
    # print('or3', v_genel_orderbook1)
    # print('ss')

    try:
        while (True):
            if v_alim_var == 0:
                time.sleep(0.3)
                v_genel_orderbook = orderbook #get_ordergenelorder_book()
                # print('1...',v_sembol_g, datetime.now())
                # v_genel_orderbook = np.array(orderbook,dtype=float)  # get_snapshot(v_sembol_g, v_limit_g)
                # print('ord1',orderbook)
                #v_genel_orderbook = orderbook
                #v_genel_orderbook["bids"]
                #y=v_genel_orderbook.get("bids")
                if len(v_genel_orderbook["bids"]) > 0:
                    c_price = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 0]
                    c_quantity = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 1]
                    print('Bids',v_genel_orderbook)
                else:
                    print('YOKLAAAA')

                #print('cprice', c_price[2][2])
                #print('Bids_y', y)
                """
                for i in x:
                    print(x[i])

                for i, j, z in v_genel_orderbook.items():
                    print(i, j,z)
                """
                #v_genel_orderbook = get_snapshot(v_sembol_g, v_limit_g)
                # print('2...', datetime.now())
                # time.sleep(0.1)
                # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'Order Dizi Bids =',
                #       len(v_genel_orderbook["bids"]), 'Order Dizi Asks =', len(v_genel_orderbook["asks"]),
                #       datetime.now())
                #print('değer', type(v_genel_orderbook)['asks'][0])
                #
                # for s in range(len(v_genel_orderbook)):
                #     if v_genel_orderbook[s]["asks"]==0:
                #         print('başardı')
                # cc= get_ordergenelorder_book()
                # print('değer', v_genel_orderbook)
                # print('ddd',cc)
                # # if len(v_genel_orderbook)>0:
                # c_price = np.asarray(v_genel_orderbook['bids'], dtype=float)[:, 0]
                # c_q = np.asarray(v_genel_orderbook['bids'], dtype=float)[:, 1]
                #
                # print('sss',c_price)
                # print('sss', c_q)
                #
                if v_last_price_g != 0:
                    print('W1...', v_sembol_g, datetime.now())
                    #whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price)
            else:
                # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'alim tarafi', v_alim_var)
                time.sleep(3)
                # if v_last_price_g != 0 and len(v_genel_orderbook["bids"]) > 0:
                #      whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price)
                # # print('W2...', v_sembol_g, datetime.now())
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


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


# ************************

if __name__ == '__main__':
    v_dosya_coin = []
    Procesler = []
    # global v_limit_g, v_sembol_g, v_inter_g
    # print('Başladı ', datetime.now())
    v_inter_g = '1s'
    v_limit_g = 100
    v_in_g = '1000ms'
    try:
        while True:
            print('İlk Başladı.........', datetime.now())
            while True:
                print('Başladı.........', datetime.now())

                # Alınan ve satılanlar dosyalarını temizliyor
                dosyalari_temizle()
                dosya_aktar()

                # Eğer uygun coin bulamadıysan yeniden başa dön
                if len(v_dosya_coin) < 1:
                    v_maxw = 1
                    break
                else:
                    v_maxw = len(v_dosya_coin)

                with concurrent.futures.ProcessPoolExecutor(max_workers=v_maxw) as executer:
                    results = [executer.submit(main_islem, v_dosya_coin[p], v_limit_g, v_inter_g) for p in
                               range(len(v_dosya_coin))]
                    # print('Başla.', results)
                    while True:
                        time.sleep(300)
                        v_esit = alinan_satilan_esitmi()
                        # v_esit =0
                        if v_esit == 1:
                            active = multiprocessing.active_children()
                            # print(f'Active Children: {active}')
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
                        else:
                            v_m = 'İçerde alım olduğundan yenileyemedi.....' + str(datetime.now())
                            Telebot_v1.mainma(v_m)

                print('Çalışmaya başladılar...SON')
    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)
