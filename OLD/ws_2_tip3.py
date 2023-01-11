"""
Farklar ; Seçerken coin_bul if ifadesi
         satarken coin_sat ifadesi
         Tip ifadeleri
"""
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
    v_return_coin, v_son_fiyatm, v_interval, v_degis_oran, v_degis_oran1 = 'XXX', 0, '1m', 1, 0.4

    with open('../DOSYALAR/Sembol3.txt', 'r') as dosya:
        for line in dosya.read().splitlines():
            # print(line)
            if v_last_buyed_coin == 'YYY':
                v_symbol = line
            else:
                v_symbol = v_last_buyed_coin
            if len(v_symbol) < 4:
                break

            v_1m_c, v_3m_c, v_5m_c, v_15m_c, v_60m_c, v_son_fiyat = check_change(v_symbol, '1m', 500, v_client)

            v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
            v_ema_arti_3m, v_3m_sonfiyat, adx_cross_up, adx_cross_down, adx_arti, \
            pp_adx_arti1, pp_adx_arti2, pp_adx_arti3, \
            adx_cross_up_1, adx_cross_up_2, adx_cross_up_3, \
            adx_cross_down_1, adx_cross_down_2, adx_cross_down_3 = check_exist(v_symbol, '1m', 500, v_client)

            v_ema_cross_up3mx, v_ema_cross_down3mx, v_ema_cross_up3m_onx, v_ema_cross_down3m_onx, v_ema_arti_3m_onx, \
            v_ema_arti_3mx, v_3m_sonfiyatx, adx_cross_upx, adx_cross_downx, adx_artix, \
            pp_adx_arti1x, pp_adx_arti2x, pp_adx_arti3x, \
            adx_cross_up_1x, adx_cross_up_2x, adx_cross_up_3x, \
            adx_cross_down_1x, adx_cross_down_2x, adx_cross_down_3x = check_exist(v_symbol, '3m', 500, v_client)

            # if (v_3m_c >= v_degis_oran) and (v_5m_c >= v_degis_oran)  and (v_15m_c >= v_degis_oran) and\
            #         (v_60m_c >= v_degis_oran) and (v_ema_cross_up3m == True) and (v_ema_arti_3m ==1):

            # if (v_ema_cross_up3m == True) and (adx_arti == 1) and (pp_adx_arti1 == 1) and (pp_adx_arti2 == 1) and \
            #         (adx_artix == 1) and (pp_adx_arti1x == 1) and (pp_adx_arti2x == 1) and (v_ema_arti_3mx ==1):
            #
            if (v_ema_cross_up3m == True) and (adx_arti == 1) and (v_5m_c > v_degis_oran1):
                print(v_symbol, ' Alınacak ..!! ', ' Zaman=',
                      datetime.now())  # , str(v_1m_c), str(v_3m_c), str(v_5m_c), str(v_15m_c),v_ema_cross_up3m )
                v_return_coin = v_symbol
                v_interval = '1m'
                break
            else:
                print('Bu coin uygun değil = ', v_symbol, 'Zaman', datetime.now())
                v_last_buyed_coin = 'YYY'
                v_return_coin = 'XXX'
                v_interval = '1m'
    dosya.close()
    return v_return_coin, v_3m_sonfiyat, v_interval, v_last_buyed_coin


#  -----------------------------
def check_change(v_symbol, v_interval, v_limit, v_cli):
    v_interval = '1m'
    klines = v_cli.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
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


# *******************************************************************************
def coin_al(v_symb, v_last_p, v_inte):
    v_test_t = 2
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    # ******TELEGRAM MESAJI ********************
    v_mess = ' Tuttum Seni (T3) =' + 'Coin = ' + v_symb + ' Buy Price =' + str(v_last_p) + ' Saat = ' + v_time
    # if v_time_bef != v_time:  # Aynı period (dk ) içinde 2 defa mesaj atmasını engellemek için
    Telebot_v1.mainma(v_mess)
    # v_time_bef = v_time
    v_bakiye = DB_transactions3.Select_Balance(v_test_t)
    DB_transactions3.con.commit()
    DB_transactions3.Delete_Table(v_symb, 'T3')
    DB_transactions3.con.commit()
    DB_transactions3.Add_value(v_symb, v_inte, v_last_p, v_time, v_time, None, None, None, 'T3', None, v_bakiye)
    DB_transactions3.con.commit()
    v_alim_v = 1
    return v_alim_v


# *******************************************************************************************************
def on_open(ws):
    print('opened connection')


def on_close(ws):
    print('closed connection')


def on_message(ws, message):
    global v_satim
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
    # time.sleep(2)
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
    v_tip = 'T3'
    v_alis = DB_transactions3.Select_Table(v_symboly, v_tip)
    DB_transactions3.con.commit()
    # Bakiyeyi Alma
    v_balance = DB_transactions3.Select_Balance(v_test_tip)
    DB_transactions3.con.commit()
    v_alis_k = v_alis * 1.004
    v_alis_z = v_alis * 0.98
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    v_times = v_time

    v_ema_cross_up3m, v_ema_cross_down3m, v_ema_cross_up3m_on, v_ema_cross_down3m_on, v_ema_arti_3m_on, \
    v_ema_arti_3m, v_son_fiyat, adx_cross_upx, adx_cross_downx, adx_artix, \
    pp_adx_arti1, pp_adx_arti2, pp_adx_arti3, \
    adx_cross_up_1, adx_cross_up_2, adx_cross_up_3, \
    adx_cross_down_1, adx_cross_down_2, adx_cross_down_3 = check_exist(v_symboly, '1m', 500, v_client)

    v_mess_s = ''
    v_result = ''

    if (
            v_ema_cross_down3m == True):  # or (v_ema_arti_3m_on == 0) or (v_son_fiyat > v_alis_k) or (            v_son_fiyat < v_alis_z):  # :  #
        if v_son_fiyat > v_alis:
            v_result = 'Kar'
            v_kar_zarar_oran = float(((v_son_fiyat - v_alis) * 100) / v_alis)
            v_balance = float(v_balance + ((v_balance * v_kar_zarar_oran) / 100))
            v_mess_s = ' Karla Satti - T3 =' + 'Coin = ' + v_symboly + ' Alis Fiyat =' + str(
                v_alis) + ' Satis Fiyat =' + str(v_son_fiyat) + ' Saat = ' + v_times + ' Oran = ' + str(
                v_kar_zarar_oran)
        elif v_son_fiyat < v_alis:
            v_result = 'Zarar'
            v_kar_zarar_oran = float(((v_alis - v_son_fiyat) * 100) / v_alis)
            v_balance = float(v_balance - ((v_balance * v_kar_zarar_oran) / 100))
            v_mess_s = ' Zarar etti - T3 =' + 'Coin = ' + v_symboly + ' Alis Fiyat =' + str(
                v_alis) + ' Satis Fiyat =' + str(v_son_fiyat) + ' Saat = ' + v_times + ' Oran = ' + str(
                v_kar_zarar_oran)
        elif v_son_fiyat == v_alis:
            v_result = 'Notr'
            v_kar_zarar_oran = 0
            v_balance = v_balance * 1
            v_mess_s = ' STOP oldu - Kar/Zarar Yok -T3 =' + 'Coin = ' + v_symboly + ' Alis Fiyat =' + str(
                v_alis) + ' Satis Fiyat =' + str(v_son_fiyat) + ' Saat = ' + v_times

        v_sell_price = v_son_fiyat
        v_komisyon = float(2 * (v_balance / 1000))
        v_balance = v_balance - v_komisyon
        v_mess_s = v_mess_s + ' Bakiye = ' + str(v_balance)
        Telebot_v1.mainma(v_mess_s)

        DB_transactions3.Update_Table(v_symboly, v_sell_price,
                                      v_result, v_kar_zarar_oran, v_times, v_tip, v_balance)
        DB_transactions3.con.commit()
        DB_transactions3.Update_Balance(float(v_balance), v_test_tip, v_komisyon)
        DB_transactions3.con.commit()
        v_sat = 1
        DB_transactions3.Add_Log(v_symboly, v_tip)
        DB_transactions3.con.commit()
        DB_transactions3.Delete_Table(v_symboly, v_tip)
        DB_transactions3.con.commit()
    else:
        v_sat = 0
        print('ALIM BEKLETİLİYOR !!! T3', v_son_fiyat)

    return v_sat


# *********************************************************************
def check_exist(v_symbol, v_interval, v_limit, v_cli):
    klines = v_cli.get_klines(symbol=v_symbol, interval=v_interval, limit=v_limit)
    close = [float(entry[4]) for entry in klines]
    high = [float(entry[2]) for entry in klines]
    low = [float(entry[3]) for entry in klines]

    v_uz = len(close)
    if v_uz < 2:
        print('Oluşmamış Değer var. T3', str(v_symbol), str(v_interval))
        return 1, 0, False, False, 0
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
        ema20k = ta.EMA(close_finished, 10)
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
        ema20 = ta.EMA(close_array, 10)
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
        adx_cross_down = previous_plus_di > previous_minus_di and last_minus_di > last_plus_di
        if last_plus_di >= last_minus_di:
            adx_arti = 1
        else:
            adx_arti = 0
        # -------------------------------------
        pp_plusdi1 = plus_di[-3]
        pp_mindi1 = minus_di[-3]
        pp_plusdi2 = plus_di[-4]
        pp_mindi2 = minus_di[-4]
        pp_plusdi3 = plus_di[-5]
        pp_mindi3 = minus_di[-5]

        # Bir önceki adx**************************************
        if previous_plus_di >= previous_minus_di:
            pp_adx_arti1 = 1
        else:
            pp_adx_arti1 = 0
        adx_cross_up_1 = pp_plusdi1 < pp_mindi1 and previous_minus_di < previous_plus_di
        adx_cross_down_1 = pp_plusdi1 > pp_mindi1 and previous_minus_di > previous_plus_di

        # Bir önceki adx**************************************
        if pp_plusdi1 >= pp_mindi1:
            pp_adx_arti2 = 1
        else:
            pp_adx_arti2 = 0
        adx_cross_up_2 = pp_plusdi2 < pp_mindi2 and pp_mindi1 < pp_plusdi1
        adx_cross_down_2 = pp_plusdi2 > pp_mindi2 and pp_mindi1 > pp_plusdi1

        # Bir önceki adx**************************************
        if pp_plusdi2 >= pp_mindi2:
            pp_adx_arti3 = 1
        else:
            pp_adx_arti3 = 0
        adx_cross_up_3 = pp_plusdi3 < pp_mindi3 and pp_mindi2 < pp_plusdi2
        adx_cross_down_3 = pp_plusdi3 > pp_mindi3 and pp_mindi2 > pp_plusdi2

        return ema_cross_upk, ema_cross_downk, ema_cross_up, ema_cross_down, ema_arti, ema_artik, \
               v_last_closing_price, adx_cross_up, adx_cross_down, adx_arti, \
               pp_adx_arti1, pp_adx_arti2, pp_adx_arti3, \
               adx_cross_up_1, adx_cross_up_2, adx_cross_up_3, \
               adx_cross_down_1, adx_cross_down_2, adx_cross_down_3

        # print('last_plus_di = ', last_plus_di, "last_minus_di = ", last_minus_di, "previous_plus_di = ", previous_plus_di, "previous_minus_di = ", previous_minus_di, "adx_cross_up =", adx_cross_up)


# **************************************************************************
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


# *******************************************************************
def sokete_git(v_s, v_in):
    # global v_sat
    # *************************************************************************************
    v_s = str(v_s).lower()
    socket = f'wss://stream.binance.com:9443/ws/{v_s}@kline_{v_in}'
    print('socker', socket)
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(socket, on_message=on_message, on_open=on_open, on_close=on_close)
    # ws.on_open = on_open
    ws.run_forever()
    # return v_sat


# *****************************************************************************************
if __name__ == '__main__':
    print('Başlangıç = T3 :', datetime.now())
    global v_client, v_last_price, v_inter, v_bulunan
    v_bulunan='YYY'
    # v_client = client
    v_dosya_gun_counter = 0
    v_alim_var = 0

    DB_transactions3.USDT_Tablo_Yaz()
    DB_transactions3.File_write()
    DB_transactions3.con.commit()

    while True:
        # 10 saniye bekliyoruz. Sürekli srgu göndermeye gerek yok.
        time.sleep(1)
        # print('1 saniye bekledi')
        # v_alim_var =1 # Test için bazen 1 yapıyoruz
        try:
            # İçerde alım yoksa yeni coin bul
            if v_alim_var == 0:
                v_bulunan, v_last_price, v_inter, v_last_buyed = coin_bul()
                print('İçerde alım yok - Son Alınan !!!! T3 ', v_last_buyed)
                # v_bulunan = 'OSMOUSDT'  # ******* TEST İÇİN
                if v_bulunan != 'XXX':
                    print('Uygun Coin Bulundu..T3', datetime.now(), 'Bulunan = ', v_bulunan, 'Last Price = ',
                          v_last_price)
                    # Alım Yapılıyor
                    v_alim_var = coin_al(v_bulunan, v_last_price, v_inter)
                else:
                    # print('Dosyada uygun coin yok ..T3', datetime.now())
                    v_last_buyed = 'YYY'
                    print('Dosyada uygun coin yok - Son Alınan !!!!...T3  ', v_last_buyed)
                    # 5 turda bir dosyayı yenile
                    v_dosya_gun_counter = v_dosya_gun_counter + 1
                    if v_dosya_gun_counter == 5:
                        # print('Dosya Yenileniyor--TIP!!!!!!!!!!', datetime.now())
                        # Telebot_v1.mainma('Dosya Yenileniyor!!!!' + '-' + str(datetime.now()))
                        DB_transactions3.USDT_Tablo_Yaz()
                        DB_transactions3.File_write()
                        DB_transactions3.con.commit()
                        v_dosya_gun_counter = 0
                    v_alim_var = 0
            if v_alim_var == 1:
                print('Alım Yapılmış Satışı Bekleniyor = T3 ', v_bulunan, str(v_alim_var))
                # Alınan coini satarken socketi kullanacağız
                # v_satim = Coin_Sat(v_bulunan)
                sokete_git(v_bulunan, v_inter)
                # print('Socket git sonrası yor = T3 ', str(v_satim))
                if v_satim == 1:
                    # ws.close()
                    print(v_bulunan, ' Coin Satıldı. Yeniden coin bulunacak...T3 ', str(v_satim))
                    v_last_buyed_coin = v_bulunan
                    v_alim_var = 0
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..T3  = ' + str(v_bulunan) + 'Hata Kodu = ' + str(exp)
            print('Hataa!!.T3 = ', v_hata_mesaj)
            Telebot_v1.mainma(v_hata_mesaj)
