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
orderbook = {}
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)

# global orderbook, updates, v_last_update
v_last_update = '2022'
orderbook = []
updates = 0


# *****************************ALIM SATIM İŞLEMLERİ*****************************************************

def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_genel_orderbook, v_open_pri):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati, v_last_price_g
    global v_client, v_alim_timestamp, v_alim_zamani
    # v_client = Client(API_Config.API_KEY, API_Config.API_SECRET)

    # global ask_tbl, bid_tbl
    v_volume_fark_oran = 0.06  # İlgili bid veya ask satırının tüm tablodaki volume oranı
    v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    v_kar_oran = 1.004
    v_zarar_oran = 0.995
    minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz
    # print(datetime.now(), '-', 'WHALE BAŞI ', '-', str(v_son_fiyat), '-', v_symbol, '-',  str(v_limit), '-', str(v_son_fiyat), '-', str(len(v_genel_orderbook)))
    # depth_dict = v_spot_client.depth(v_symbol, limit=v_limit)
    # v_son_fiyat = float(v_son_fiyat)

    if v_alim_var == 0:
        depth_dict = v_genel_orderbook
        try:
            #v_frame = {side: pd.DataFrame(data=depth_dict[side], columns=["price", "quantity"], dtype=float)
            #           for side in ["bids", "asks"]}

            bids_price = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 0]
            bids_quantity = np.asarray(v_genel_orderbook["bids"], dtype=float)[:, 1]
            df_bids = pd.DataFrame(dtype=float)
            df_bids["price"] = pd.Series(bids_price)
            df_bids["quantity"] = pd.Series(bids_quantity)
            # print(df_bids)
            # print('1.kolon')

            asks_price = np.asarray(v_genel_orderbook["asks"], dtype=float)[:, 0]
            asks_quantity = np.asarray(v_genel_orderbook["asks"], dtype=float)[:, 1]
            df_asks = pd.DataFrame(dtype=float)
            df_asks["price"] = pd.Series(asks_price)
            df_asks["quantity"] = pd.Series(asks_quantity)
            # print(df_asks)
            # print('2.kolon')

            bid_tbl = df_bids
            ask_tbl =df_asks

            #ask_tbl = pd.DataFrame(data=depth_dict['asks'], columns=['price', 'quantity'],dtype=float)
            #bid_tbl = pd.DataFrame(data=depth_dict['bids'], columns=['price', 'quantity'],dtype=float)
            ask_tbl = ask_tbl.fillna(0)
            bid_tbl = bid_tbl.fillna(0)
            #
            # print(bid_tbl)
            # print(ask_tbl)

            ask_tbl['price'] = pd.to_numeric(ask_tbl['price'])
            ask_tbl['quantity'] = pd.to_numeric(ask_tbl['quantity'])
            bid_tbl['price'] = pd.to_numeric(bid_tbl['price'])
            bid_tbl['quantity'] = pd.to_numeric(bid_tbl['quantity'])

            # data from websocket are not sorted yet
            ask_tbl = ask_tbl.sort_values(by='price', ascending=True)
            bid_tbl = bid_tbl.sort_values(by='price', ascending=False)

            # print('bidler', bid_tbl)
            # print('ask tablosu', ask_tbl)

            first_ask = float(ask_tbl.iloc[0, 0])
            first_bid = float(bid_tbl.iloc[0, 0])
            mid_price = float((first_ask + first_bid) / 2)

            perc_above_first_ask = ((1.0 + v_oran) * mid_price)
            perc_above_first_bid = ((1.0 - v_oran) * mid_price)

            # limits the size of the table so that we only look at orders 5% above and under market price
            ask_tbl = ask_tbl[(ask_tbl['price'] <= perc_above_first_ask)]
            bid_tbl = bid_tbl[(bid_tbl['price'] >= perc_above_first_bid)]
            #
            # print(bid_tbl)
            # print(ask_tbl)

            # changing this position after first filter makes calc faster
            fulltbl = bid_tbl.append(ask_tbl)  # append the buy and sell side tables to create one cohesive table
            volumewhale = fulltbl['quantity'].sum()

            # print(fulltbl)
            # print('Max Ask =', float(bid_tbl['quantity'].sum()), '-', float(ask_tbl['quantity'].sum()))

            v_bidask_fark_tutar_old = float(bid_tbl['quantity'].sum()) - float(ask_tbl['quantity'].sum())
            v_vol_oran_bid_old = (float(bid_tbl['quantity'].sum()) / float(volumewhale)) * 100
            v_vol_oran_ask_old = (float(ask_tbl['quantity'].sum()) / float(volumewhale)) * 100

            # print('Max Ask =', ask_tbl['price'].max(), '-', mid_price)
            # print('Min Bid =', bid_tbl['price'].min(), '-', mid_price)
            # print('Len', len(bid_tbl), '-', len(ask_tbl))

            v_son_fiyat = float(v_last_price_g)
            v_hedef_bid = float(v_son_fiyat * v_kar_oran)
            v_hedef_ask = float(v_son_fiyat * v_zarar_oran)
            #
            # if v_bidask_fark_tutar_old >= 0 and v_vol_oran_bid_old >= 70 : #v_volume_fark_oran:
            #    v_mesy = str(v_symbol) + '--' + '*Tuttum Seni Genel * HEDEF == ' + '--' + "{:.6f}".format(float(v_hedef_bid)) + \
            #                  '--' + ' Zaman = ' + '--' + str(datetime.now())[0:19] + '--' + \
            #                  'Fiyat = ' + '--' + "{:.6f}".format(float(v_son_fiyat)) + '--' + \
            #                  'Fark Tutar = ' + '--' + "{:.1f}".format(float(v_bidask_fark_tutar_old)) + '--' + \
            #                  'Bid Topl= ' + '--' + "{:.1f}".format(float(bid_tbl['volume'].sum())) + '--' + \
            #                  'Ask Topl= ' + '--' + "{:.1f}".format(float(ask_tbl['volume'].sum())) + '--' + \
            #                  'Bid_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_bid_old))
            #    Telebot_v1.mainma(v_mesy)

            # Son fiyatın üzerindeki büyük teklifleri ve aşağısındaki küçük teklifleri bırakır
            ask_tbl = ask_tbl[(ask_tbl['price'] <= float(v_son_fiyat))]  # Son fiyatın altındaki talepler fiyatı düşürür
            bid_tbl = bid_tbl[(bid_tbl['price'] >= float(v_son_fiyat))]  # Son fiyatın üzerindeki teklifler  fiyatı yükseltir

            # Tüm bu filtrelemerden sonra tabloda kayıt kaldıysa işleme devam et
            v_bid_len = len(bid_tbl)
            v_ask_len = len(ask_tbl)

            # Teklifi karşılayan satışları çıkarıyoruz
            v_bidask_fark_tutar = float(bid_tbl['quantity'].sum()) - float(ask_tbl['quantity'].sum())
            v_vol_oran_bid = (float(bid_tbl['quantity'].sum()) / float(volumewhale)) * 100
            v_vol_oran_ask = (float(ask_tbl['quantity'].sum()) / float(volumewhale)) * 100

            if v_bid_len > 0 and v_bidask_fark_tutar >= 0 and \
               float(v_vol_oran_bid) >= float(v_volume_fark_oran*100) :#and v_vol_oran_ask <1:

            #if float(v_vol_oran_bid_old) >= 70:  # or float(v_bidask_fark_tutar_old*v_son_fiyat) >=10000:
                # v_1m_c = check_change_dk(v_symbol, '1m', 500)
                if 1 == 1:  # float(v_1m_c) > 0:
                    print('SEMBOL', v_symbol, '*Tuttum Seni* HEDEF == ', "{:.6f}".format(float(v_hedef_bid)),
                          'Fark Tutar = ', "{:.1f}".format(float(v_bidask_fark_tutar)), 'Zaman = ',
                          str(datetime.now())[0:19])

                    v_mess = str(v_symbol) + '--' + '*Tuttum Seni* HEDEF == ' + '--' + "{:.6f}".format(
                        float(v_hedef_bid)) + \
                             '--' + ' Zaman = ' + '--' + str(datetime.now())[0:19] + '--' + \
                             'Fiyat = ' + '--' + "{:.6f}".format(float(v_son_fiyat)) + '--' + \
                             'Fark Tutar = ' + '--' + "{:.1f}".format(float(v_bidask_fark_tutar)) + '--' + \
                             'Bid Topl= ' + '--' + "{:.1f}".format(float(bid_tbl['quantity'].sum())) + '--' + \
                             'Ask Topl= ' + '--' + "{:.1f}".format(float(ask_tbl['quantity'].sum())) + '--' + \
                             'Bid_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_bid)) #+ '--' + \
                             #'Ask_VO= ' + '--' + "{:.2f}".format(float(v_vol_oran_ask))
                    # Telegram mesajo
                    Telebot_v1.mainma(v_mess)
                    v_mee = v_symbol + '*' + 'Hedef' + '*' + "{:.6f}".format(float(v_hedef_bid)) + '*' + \
                            'Fark Tutarlar = ' + '*' + "{:.1f}".format(float(v_bidask_fark_tutar)) + '*' + \
                            "{:.1f}".format(float(v_bidask_fark_tutar_old)) + '*' + \
                            'Fiyat:' + '*' + "{:.6f}".format(float(v_son_fiyat)) + '*' + \
                            'B_V_OS:' + '*' + "{:.1f}".format(float(v_vol_oran_bid)) + '*' + \
                            "{:.1f}".format(float(v_vol_oran_bid_old)) + '*' + \
                            'A_V_OS:' + '*' + "{:.1f}".format(float(v_vol_oran_ask)) + '*' + \
                            "{:.1f}".format(float(v_vol_oran_ask_old)) + '*' + \
                            'Zaman = ' + '*' + str(datetime.now())
                    #Telebot_v1.analiz(v_mee, v_symbol)

                    v_alim_fiyati = v_son_fiyat
                    current_timestamp = round(time.time() * 1000)
                    v_alim_timestamp = (current_timestamp + (60000)) / 1000
                    v_alim_zamani = str(datetime.now())[0:19]

                    v_hedef_bid_global = v_hedef_bid
                    v_hedef_ask_global = v_hedef_ask
                    v_alim_var = 1


                    print('****************Teklifler = ********************')
                    print(bid_tbl)
                    Telebot_v1.genel_alimlar(v_symbol, 'A')
            else:
                print('Alım için Uygun Emir Bulunamadı.!', v_symbol, datetime.now())

        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..Alım tarafı  = ' + str(exp)+str(v_symbol)
            Telebot_v1.mainma(v_hata_mesaj)
            print('hata oldu')

    elif v_alim_var == 1:
        current_timestamp = round(time.time() * 1000)
        v_satim_timestamp = current_timestamp / 1000

        try:
            v_son_fiyat = float(v_last_price_g)
            print(str(v_symbol), 'İçerde alım var.......!!', str(datetime.now())[0:19], 'Hedefi = ',
                  str(v_hedef_bid_global), 'Son Fiyat = ', str(v_son_fiyat))

            if float(v_son_fiyat) >= float(v_hedef_bid_global):
                v_profit_oran = float(((v_son_fiyat - v_alim_fiyati) * 100) / v_alim_fiyati)
                v_mess1 = 'Karla Sattı..Hedefi : ' + "{:.6f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                          '- Alım Fiyatı :' + "{:.6f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                          '- Kar Oranı :' + "{:.6f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(datetime.now())+ \
                          'Alım Zamanı : ' + str(v_alim_zamani)
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.6f}".format(float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                                   '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(datetime.now())  # + str(datetime.now())[0:19]
                print(v_mess1)
                # ******************
                Telebot_v1.mainma(v_mess1)
                Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)

                v_alim_var = 0
                Telebot_v1.genel_alimlar(v_symbol, 'S')
                #Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)

            elif float(v_son_fiyat) < float(v_hedef_ask_global):
                v_zarprofit_oran = float(((v_alim_fiyati - v_son_fiyat) * 100) / v_alim_fiyati)
                v_zarprofit_oran = float(v_zarprofit_oran)

                v_mess1 = 'Zararla Sattı..Hedefi : ' + "{:.6f}".format(float(v_hedef_ask_global)) + '- Sembol :' + str(v_symbol) + \
                          '- Alım Fiyatı :' + "{:.6f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                          '- Zarar Oranı :' + "{:.6f}".format(float(v_zarprofit_oran)) + ' - Zaman : ' + str(datetime.now()) + 'Alım Zamanı : ' + str(v_alim_zamani)
                print(v_mess1)
                v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.6f}".format(float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                                   '*' + "{:.3f}".format(float(v_zarprofit_oran)) + '*' + str(datetime.now())
                Telebot_v1.mainma(v_mess1)
                Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
                v_alim_var = 0
                Telebot_v1.genel_alimlar(v_symbol, 'S')
                #Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
            elif v_satim_timestamp >= v_alim_timestamp:
                # 1 dk yı geçtiği için satacak
                if float(v_son_fiyat) > float(v_alim_fiyati):
                    vm_karzar = 'KARLA KAPADI - '
                    v_profit_oran = float(((v_son_fiyat - v_alim_fiyati) * 100) / v_alim_fiyati)

                    v_mess1 = vm_karzar + '...Hedefi : ' + "{:.6f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                              '- Alım Fiyatı :' + "{:.6f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                              '- Kar Oranı :' + "{:.6f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(datetime.now()) + 'Alım Zamanı : ' + str(v_alim_zamani)
                    v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.6f}".format(float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                                       '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(datetime.now())
                    print(v_mess1)
                    # ******************
                    Telebot_v1.mainma(v_mess1)
                    Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
                    v_alim_var = 0
                    Telebot_v1.genel_alimlar(v_symbol, 'S')
                    #Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
                elif float(v_alim_fiyati) >= float(v_son_fiyat):
                    vm_karzar = 'ZARARLA KAPADI - '
                    v_zarprofit_oran = float(((v_alim_fiyati - v_son_fiyat) * 100) / v_alim_fiyati)
                    v_zarprofit_oran = float(v_zarprofit_oran)

                    v_mess1 = vm_karzar + '..Hedefi : ' + "{:.6f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                              '- Alım Fiyatı :' + "{:.6f}".format(float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                              '- Zarar Oranı :' + "{:.6f}".format(float(v_zarprofit_oran)) + ' - Zaman : ' + str(datetime.now()) + 'Alım Zamanı : ' + str(v_alim_zamani)
                    print(v_mess1)
                    v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.6f}".format(float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                                       '*' + "{:.3f}".format(float(v_zarprofit_oran)) + '*' + str(datetime.now())

                    Telebot_v1.mainma(v_mess1)
                    Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
                    v_alim_var = 0
                    Telebot_v1.genel_alimlar(v_symbol, 'S')
                    #Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
                # ---------------------------
            else:
                print('İçerde alım var ama henüz satılamadı...!- ', str(datetime.now())[0:19], v_symbol, ' - Hedefi = ',
                      str(v_hedef_bid_global), 'Son Fiyat = ', str(v_son_fiyat))

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
        orderbook = {}
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
    #v_last_price_g = json_message['c']
    #v_last_price_g = json_message['p']
    #print('son fiyat',v_last_price_g, datetime.now() )
    #v_open_price = candle['o']


# 1 saniyelik stream verilerle kline daki son fiyatı vs alır
def socket_front(v_symbol, v_inter):
    global vn_front, ws_front_g
    v_symbol = v_symbol.lower()
    v_sembol_deg1 = f'[{v_symbol}@kline_{v_inter}]'
    #v_sembol_deg1 = f'[{v_symbol}@ticker]'
    #v_sembol_deg1 = f'[{v_symbol}@trade]'
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
            if 1==1 : #v_3m_c > 0 :# and v_15m_c > 0 and v_60m_c > 0:
                if i <= 13:
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
        time.sleep(2.33)
        basla(v_limit_g, v_sembol_g)
        time.sleep(2.33)
        # print('basson')
        islem(v_sembol_g, v_limit_g)
        # time.sleep(5)
    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..main_islem  = ' + str(exp) + str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)


def islem(v_sembol_g, v_limit_g):
    global v_last_price_g, v_open_price, orderbook
    v_genel_orderbook = {}
    v_genel_orderbook = orderbook #get_snapshot(v_sembol_g, v_limit_g)
    time.sleep(8.66)
    try:
        while (True):
            v_kota_doldu = icerdeki_alinan()
            if v_kota_doldu>=6 :
               v_mesaj = 'İçerde 3 alım var. Kota dolduğu için bekliyor...' + str(datetime.now())
               if v_alim_var == 1 :
                   time.sleep(0.01)
                   whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price)
            else:
                if v_alim_var == 0 :
                    # print('1...',v_sembol_g, datetime.now())
                    #v_genel_orderbook = orderbook  # get_snapshot(v_sembol_g, v_limit_g)
                    v_genel_orderbook = orderbook #get_snapshot(v_sembol_g, v_limit_g)
                    #print('2...', len(v_genel_orderbook["bids"]),len(v_genel_orderbook["asks"]),datetime.now())
                    time.sleep(0.01)
                    if  v_last_price_g != 0 and  len(v_genel_orderbook["bids"]) and  len(v_genel_orderbook["asks"]) :
                        print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'Order Dizi Bids =',
                              len(v_genel_orderbook["bids"]), 'Order Dizi Asks =', len(v_genel_orderbook["asks"]),
                              datetime.now())
                        # if v_last_price_g != 0 and len(v_genel_orderbook["bids"]) > 0:
                        #print('W1...', v_sembol_g, datetime.now())
                        whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price)
                else:
                    # print('İşlenen Coin ', v_sembol_g, 'Son Fiyat', v_last_price_g, 'alim tarafi', v_alim_var)
                    time.sleep(0.01)
                    whale_order_full(v_sembol_g, v_limit_g, float(v_last_price_g), v_genel_orderbook, v_open_price)
                    # print('W2...', v_sembol_g, datetime.now())
            # else:
            #     v_mesaj = 'İçerde 3 alım var. Kota dolduğu için bekliyor...'+str(datetime.now())
            #     Telebot_v1.mainma(v_mesaj)

    except Exception as exp:
        v_hata_mesaj = 'Program Hata Oluştu!!..islem  = ' + str(exp) + str(v_sembol_g)+ str(datetime.now())
        Telebot_v1.mainma(v_hata_mesaj)

def icerdeki_alinan():
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open("Satilanlar.txt", "r").readlines())
    genel_alimlar = len(open("Alinanlar.txt", "r").readlines())
    v_icerde= genel_alimlar-genel_satimlar
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


# ************************

if __name__ == '__main__':
    v_dosya_coin = []
    Procesler = []
    # global v_limit_g, v_sembol_g, v_inter_g
    # print('Başladı ', datetime.now())
    v_inter_g = '1s'
    v_limit_g = 5000
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
