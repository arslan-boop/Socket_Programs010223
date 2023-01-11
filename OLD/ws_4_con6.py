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

DB_FILE = "../TRADE3.DB"
con = sqlite3.connect(DB_FILE, timeout=10)
cursor = con.cursor()

# global v_hedef_bid_global, v_alim_var, v_alim_fiyati

v_hedef_bid_global, v_hedef_ask_global, v_alim_var, v_alim_fiyati = 0, 0, 0, 0
v_last_price_g = 0
v_open_price = 0
genel_alimlar = []
genel_satimlar = []
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)


def whale_order_full(v_symbol, v_limit, v_son_fiyat, v_genel_orderbook, v_open_pri):
    global v_alim_var, v_hedef_bid_global, v_hedef_ask_global, v_alim_fiyati
    global v_client
    # v_client = Client(API_Config.API_KEY, API_Config.API_SECRET)

    # global ask_tbl, bid_tbl
    v_volume_fark_oran = 3  # İlgili bid veya ask satırının tüm tablodaki volume oranı
    v_oran = 0.03  # ask ve bidlerin listede gideceği fiyat oranı. İlk kayıt 100 ve oran %5 ise 105 ile 95 arasında fiyatı olan emirleri alıyoruz
    v_kar_oran = 1.003
    v_zarar_oran = 0.99
    minVolumePerc = 0.01  # volumesi yani toplam tutarı  tüm tutarın % xx den büyük olan satırları alıyoruz
    # print(datetime.now(), '-', 'WHALE BAŞI ', '-', str(v_son_fiyat), '-', v_symbol, '-',  str(v_limit), '-', str(v_son_fiyat), '-', str(len(v_genel_orderbook)))
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

            Telebot_v1.genel_alimlar(v_symbol, 'S')

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

            Telebot_v1.genel_alimlar(v_symbol, 'S')
        else:
            print('İçerde alım var ama henüz satılamadı...!- ', v_symbol, ' - Hedefi = ', str(v_hedef_bid_global),
                  'Son Fiyat = ', str(v_son_fiyat))
    else:
        if v_bid_len > 0 and v_bidask_fark_tutar >= 0 and v_vol_oran_bid >= v_volume_fark_oran:
            # v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
            # v_ema_arti_3m, v_3m_sonfiyat, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, v_1m_c, \
            # v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p = check_exist(v_symbol, '1m', 500, v_client)

            if 1 == 1:  # adx_arti == 1 and stoc_arti == 1:
                print('SEMBOL', v_symbol, '***ARTMALI *** HEDEF == ', "{:.6f}".format(float(v_hedef_bid)), ' Zaman = ',
                      v_time)
                v_mess = str(v_symbol) + '--' + '***ARTMALI *** HEDEF == ' + '--' + "{:.6f}".format(
                    float(v_hedef_bid)) + \
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
            else:
                v_me = 'Alacaktı fakat stoclar engel -' + str(adx_arti) + '-' + str(stoc_arti) + str(v_time)
                Telebot_v1.mainma(v_me)
        else:
            print('Alım için Uygun Emir Bulunamadı.!', v_symbol, datetime.now())


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
    open("../DOSYALAR/Alinanlar.txt", 'w').close()
    open("../DOSYALAR/Satilanlar.txt", 'w').close()


def dosya_aktar():
    global v_dosya_coin

    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write()
    DB_transactions3.con.commit()

    v_dosya_coin = []
    with open('../DOSYALAR/Sembol3.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            v_symbol = line
            # v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
            # v_ema_arti_3m, v_3m_sonfiyat, adx_cross_up, adx_cross_down, adx_arti, stoc_arti, v_1m_c, \
            # v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_l_c_p = check_exist(v_symbol, '1m', 500, v_client)
            #
            # if adx_arti == 1 and stoc_arti==1 and v_3m_c>0 and v_15m_c>0 and v_60m_c> 0:
            v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_son_fiyat = check_change(v_symbol, '1m', 500)
            if v_3m_c > 0 and v_5m_c > 0 and v_15m_c > 0 and v_60m_c > 0:
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
    return loads(r.content.decode())


# Her bir process için
def main_islem(v_sembol_g, v_limit_g, v_inter_g):
    print('Başladı ', v_sembol_g, datetime.now())
    try:
        run_frontdata(v_sembol_g, v_inter_g)
        time.sleep(1)
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


def alinan_satilan_esitmi():
    # print(len(open("Sonuc.txt", "r").readlines()))
    genel_satimlar = len(open("../DOSYALAR/Satilanlar.txt", "r").readlines())
    genel_alimlar = len(open("../DOSYALAR/Alinanlar.txt", "r").readlines())

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
    v_limit_g = 1000
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