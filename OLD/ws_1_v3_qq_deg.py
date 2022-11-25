import websocket
import json
import API_Config
import talib as ta
import numpy as np
import time
import DB_transactions3
import Telebot_v1
from datetime import datetime
from binance.client import Client

macds = []
closes = []
highs = []
lows = []
in_position = False


def coin_bul():
    global v_client, v_last_buyed_coin
    v_client = Client(API_Config.API_KEY, API_Config.API_SECRET)
    # global v_return_coin, v_client,v_last_buyed_coin
    v_last_buyed_coin = 'YYY'
    v_return_coin, v_son_fiyatm, v_interval, v_degis_oran, v_degis_oran1 = 'XXX', 0, '1m', 0.4, 0.2

    with open('../Sembol.txt', 'r') as dosya:
        for line in dosya.read().splitlines():
            # print(line)
            if v_last_buyed_coin == 'YYY':
                v_symbol = line
            else:
                v_symbol = v_last_buyed_coin
            if len(v_symbol) < 4:
                break

            v_4h_olusmadi, v_change_4h, v_ema_cross_up4h, v_ema_cross_down4h, \
                v_son_fiyat4h = check_exist(v_symbol, '4h', 500, v_client)
            v_2h_olusmadi, v_change_2h, v_ema_cross_up2h, v_ema_cross_down2h, \
                v_son_fiyat2h = check_exist(v_symbol, '2h', 500, v_client)
            v_1h_olusmadi, v_change_1h, v_ema_cross_up1h, v_ema_cross_down1h, \
                v_son_fiyat1h = check_exist(v_symbol, '1h', 500, v_client)
            v_15m_olusmadi, v_change_15m, v_ema_cross_up15m, v_ema_cross_down15m, \
                v_son_fiyat15m = check_exist(v_symbol, '15m', 500, v_client)
            v_5m_olusmadi, v_change_5m, v_ema_cross_up5m, v_ema_cross_down5m, \
                v_son_fiyat5m = check_exist(v_symbol, '5m', 500, v_client)
            v_3m_olusmadi, v_change_3m, v_ema_cross_up3m, v_ema_cross_down3m, \
                v_son_fiyat3m = check_exist(v_symbol, '3m', 500, v_client)
            v_1m_olusmadi, v_change_1m, v_ema_cross_up1m, v_ema_cross_down1m, \
                v_son_fiyat1m = check_exist(v_symbol, '1m', 500, v_client)

            if ((v_change_1m >= v_degis_oran1) or (v_1m_olusmadi == 1)) and (
                    (v_change_3m >= v_degis_oran) or (v_3m_olusmadi == 1)) and \
                    ((v_change_5m >= v_degis_oran) or (v_5m_olusmadi == 1)) and (
                    (v_change_15m >= v_degis_oran) or (v_15m_olusmadi == 1)) \
                    and ((v_change_1h >= v_degis_oran) or (v_1h_olusmadi == 1)) and (
                    (v_change_2h >= v_degis_oran) or (v_2h_olusmadi == 1)) \
                    and ((v_change_4h >= v_degis_oran) or (v_4h_olusmadi == 1)) and v_ema_cross_up1m == True:
                print(v_symbol, ' Alınacak ..!! ', 'Son Fiyat = ', v_son_fiyat1m, ' 1 dk lık Değişim Orani = ',
                      str(v_change_1m), ' Zaman=', datetime.now())
                v_return_coin = v_symbol
                v_interval = '1m'
                break
            else:
                print('Bu coin uygun değil = ', v_symbol, 'Zaman', datetime.now())
                v_last_buyed_coin = 'YYY'
                v_return_coin = 'XXX'
                v_interval = '1m'
        dosya.close()
        return v_return_coin, v_son_fiyat1m, v_interval, v_last_buyed_coin


#  -----------------------------
def coin_al(v_symb, v_last_p, v_inte):
    v_test_t = 2
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    # ******TELEGRAM MESAJI ********************
    v_mess = ' Tuttum Seni (TIP-V) =' + 'Coin = ' + v_symb + ' Buy Price =' + str(v_last_p) + ' Saat = ' + v_time
    # if v_time_bef != v_time:  # Aynı period (dk ) içinde 2 defa mesaj atmasını engellemek için
    Telebot_v1.mainma(v_mess)
    # v_time_bef = v_time
    v_bakiye = DB_transactions3.Select_Balance1(v_test_t)
    DB_transactions3.con.commit()
    DB_transactions3.Delete_Table1(v_symb, 'TIP-V')
    DB_transactions3.con.commit()
    DB_transactions3.Add_value1(v_symb, v_inte, v_last_p, v_time, v_time, None, None, None, 'TIP-V', None, v_bakiye)
    DB_transactions3.con.commit()
    v_alim_v = 1
    return v_alim_v


# *******************************************************************************************************
def on_open(ws):
    print('opened connection')


def on_close(ws):
    print('closed connection')


def on_message(ws, message):
    global  v_satim
    json_message = json.loads(message)
    print('Gelen mesaj: ', json_message)
    # pprint.pprint(json_message)
    candle = json_message['k']
    # is_candle_closed = candle['x']  # True , false
    close = candle['c']
    v_sembol = json_message['s']
    print('C  = ', close)
    #   if is_candle_closed:
    #      closes.append(float(close))
    time.sleep(1)
    v_satim = coin_sat(v_sembol)
    if v_satim == 1:
        print('Satım oldu. Socket bağlantısı kapatılacak...!! . ')
        ws.close()
        # return
    else:
        print('Mum kapanışı kontrol edildi..Satılamadı.Kontrole devam edilecek ')


# --------------------------------------------------------------------------------------
def coin_sat(v_symboly):
    global v_client
    v_kar_zarar_oran = 1
    v_test_tip = 2
    v_tip = 'TIP-V'
    v_alis = DB_transactions3.Select_Table1(v_symboly, v_tip)
    DB_transactions3.con.commit()
    # Bakiyeyi Alma
    v_balance = DB_transactions3.Select_Balance1(v_test_tip)
    DB_transactions3.con.commit()
    v_alis_k = v_alis * 1.004
    # v_alis_z = v_alis * 0.98
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    v_times = v_time

    v_1m_olusmadi, v_change_1m, v_ema_cross_up1m, v_ema_cross_down1m, \
    v_son_fiyat = check_exist(v_symboly, '1m', 500, v_client)
    v_mess_s = ''
    v_result = ''

    if (v_ema_cross_down1m == True) or  (v_son_fiyat > v_alis_k):  # :  #
        if v_son_fiyat > v_alis:
            v_result = 'Kar'
            v_kar_zarar_oran = float(((v_son_fiyat - v_alis) * 100) / v_alis)
            v_balance = float(v_balance + ((v_balance * v_kar_zarar_oran) / 100))
            v_mess_s = ' Karla Satti - TIP-V =' + 'Coin = ' + v_symboly + ' Alis Fiyat =' + str(
                v_alis) + ' Satis Fiyat =' + str(v_son_fiyat) + ' Saat = ' + v_times + ' Oran = ' + str(
                v_kar_zarar_oran)
        elif v_son_fiyat < v_alis:
            v_result = 'Zarar'
            v_kar_zarar_oran = float(((v_alis - v_son_fiyat) * 100) / v_alis)
            v_balance = float(v_balance - ((v_balance * v_kar_zarar_oran) / 100))
            v_mess_s = ' Zarar etti - TIP-V =' + 'Coin = ' + v_symboly + ' Alis Fiyat =' + str(
                v_alis) + ' Satis Fiyat =' + str(v_son_fiyat) + ' Saat = ' + v_times + ' Oran = ' + str(
                v_kar_zarar_oran)
        elif v_son_fiyat == v_alis:
            v_result = 'Notr'
            v_kar_zarar_oran = 0
            v_balance = v_balance * 1
            v_mess_s = ' STOP oldu - Kar/Zarar Yok -TIP-V =' + 'Coin = ' + v_symboly + ' Alis Fiyat =' + str(
                v_alis) + ' Satis Fiyat =' + str(v_son_fiyat) + ' Saat = ' + v_times

        v_sell_price = v_son_fiyat
        v_komisyon = float(2 * (v_balance / 1000))
        v_balance = v_balance - v_komisyon
        v_mess_s = v_mess_s + ' Bakiye = ' + str(v_balance)
        Telebot_v1.mainma(v_mess_s)

        DB_transactions3.Update_Table1(v_symboly, v_sell_price,
                                       v_result, v_kar_zarar_oran, v_times, v_tip, v_balance)
        DB_transactions3.con.commit()
        DB_transactions3.Update_Balance1(float(v_balance), v_test_tip, v_komisyon)
        DB_transactions3.con.commit()
        v_sat = 1
        DB_transactions3.Add_Log1(v_symboly, v_tip)
        DB_transactions3.con.commit()
        DB_transactions3.Delete_Table1(v_symboly, v_tip)
        DB_transactions3.con.commit()
    else:
        v_sat = 0
        print('ALIM BEKLETİLİYOR !!! TIP-V', v_son_fiyat)

    return v_sat

# *********************************************************************
def check_exist(v_symbol, v_interval, v_limit, v_cli):
    klines = v_cli.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
    close = [float(entry[4]) for entry in klines]
    v_uz = len(close)
    if v_uz < 2:
        print('Oluşmamış Değer var. TIP-V', str(v_symbol), str(v_interval))
        return 1, 0, False, False, 0
    else:
        v_last_closing_price = close[-1]
        v_previous_closing_price = close[-2]
        v_oran1 = ((v_last_closing_price - v_previous_closing_price) * 100) / v_previous_closing_price
        v_f_oran1 = float(v_oran1)
        close_array = np.asarray(close)
        close_finished = close_array[:-1]
        # ******************    EMA
        ema5 = ta.EMA(close_finished, 5)
        ema20 = ta.EMA(close_finished, 10)
        last_ema5 = ema5[-1]
        last_ema20 = ema20[-1]
        previous_ema5 = ema5[-2]
        previous_ema20 = ema20[-2]
        ema_cross_up = previous_ema20 > previous_ema5 and last_ema5 > last_ema20
        ema_cross_down = previous_ema20 < previous_ema5 and last_ema5 < last_ema20
        # if last_ema20 >= last_ema5:
        #     ema_arti = 0
        # else:
        #     ema_arti = 1
        return 0, v_f_oran1, ema_cross_up, ema_cross_down, v_last_closing_price


# *******************************************************************
def sokete_git(v_s, v_in):
    #global v_sat
    # *************************************************************************************
    v_s = str(v_s).lower()
    socket = f'wss://stream.binance.com:9443/ws/{v_s}@kline_{v_in}'
    print('socker', socket)
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(socket, on_message=on_message, on_open=on_open, on_close=on_close)
    # ws.on_open = on_open
    ws.run_forever()
    #return v_sat


# *****************************************************************************************
if __name__ == '__main__':
    print('Başlangıç = TIP-V :', datetime.now())
    global v_client, v_last_price, v_inter, v_bulunan
    # v_client = client
    v_dosya_gun_counter = 0
    v_alim_var = 0

    while True:
        # 10 saniye bekliyoruz. Sürekli srgu göndermeye gerek yok.
        time.sleep(1)
        # print('1 saniye bekledi')
        # v_alim_var =1 # Test için bazen 1 yapıyoruz
        try:
            # İçerde alım yoksa yeni coin bul
            if v_alim_var == 0:
                v_bulunan, v_last_price, v_inter, v_last_buyed = coin_bul()
                print('İçerde alım yok - Son Alınan !!!! TIP-V ', v_last_buyed)
                #v_bulunan = 'OSMOUSDT'  # ******* TEST İÇİN
                if v_bulunan != 'XXX':
                    print('Uygun Coin Bulundu..TIP-V', datetime.now(), 'Bulunan = ', v_bulunan, 'Last Price = ',
                          v_last_price)
                    # Alım Yapılıyor
                    v_alim_var = coin_al(v_bulunan, v_last_price, v_inter)
                else:
                    # print('Dosyada uygun coin yok ..TIP-V', datetime.now())
                    v_last_buyed = 'YYY'
                    print('Dosyada uygun coin yok - Son Alınan !!!!...TIP-V  ', v_last_buyed)
                    # 5 turda bir dosyayı yenile
                    v_dosya_gun_counter = v_dosya_gun_counter + 1
                    if v_dosya_gun_counter == 5:
                        # print('Dosya Yenileniyor--TIP!!!!!!!!!!', datetime.now())
                        # Telebot_v1.mainma('Dosya Yenileniyor!!!!' + '-' + str(datetime.now()))
                        DB_transactions3.USDT_Tablo_Yaz1()
                        DB_transactions3.File_write1()
                        DB_transactions3.con.commit()
                        v_dosya_gun_counter = 0
                    v_alim_var = 0
            if v_alim_var == 1:
                print('Alım Yapılmış Satışı Bekleniyor = TIP-V ', v_bulunan, str(v_alim_var))
                # Alınan coini satarken socketi kullanacağız
                # v_satim = Coin_Sat(v_bulunan)
                sokete_git(v_bulunan, v_inter)
                # print('Socket git sonrası yor = TIP-V ', str(v_satim))
                if v_satim == 1:
                    # ws.close()
                    print(v_bulunan, ' Coin Satıldı. Yeniden coin bulunacak...TIP-V ', str(v_satim))
                    v_last_buyed_coin = v_bulunan
                    v_alim_var = 0
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..TIP-V  = ' + str(v_bulunan) + 'Hata Kodu = ' + str(exp)
            print('Hataa!!.TIP-V = ', v_hata_mesaj)
            Telebot_v1.mainma(v_hata_mesaj)

