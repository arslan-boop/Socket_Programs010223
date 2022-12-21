current_timestamp = round(time.time() * 1000)
v_satim_timestamp = current_timestamp / 1000

try:
    v_son_fiyat = float(v_last_price_g)
    print(str(v_symbol), 'İçerde alım var.......!!', str(datetime.now())[0:19], 'Hedefi = ',
          str(v_hedef_bid_global), 'Son Fiyat = ', str(v_son_fiyat))

    if float(v_son_fiyat) >= float(v_hedef_bid_global):
        v_profit_oran = float(((v_son_fiyat - v_alim_fiyati) * 100) / v_alim_fiyati)
        v_mess1 = 'Karla Sattı..Hedefi : ' + "{:.6f}".format(float(v_hedef_bid_global)) + '- Sembol :' + str(
            v_symbol) + \
                  '- Alım Fiyatı :' + "{:.6f}".format(
            float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                  '- Kar Oranı :' + "{:.6f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(
            datetime.now()) + \
                  'Alım Zamanı : ' + str(v_alim_zamani)
        v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.6f}".format(
            float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                           '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(
            datetime.now())  # + str(datetime.now())[0:19]
        print(v_mess1)
        # ******************
        Telebot_v1.mainma(v_mess1)
        Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)

        v_alim_var = 0
        Telebot_v1.genel_alimlar(v_symbol, 'S')
        # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)

    elif float(v_son_fiyat) < float(v_hedef_ask_global):
        v_zarprofit_oran = float(((v_alim_fiyati - v_son_fiyat) * 100) / v_alim_fiyati)
        v_zarprofit_oran = float(v_zarprofit_oran)

        v_mess1 = 'Zararla Sattı..Hedefi : ' + "{:.6f}".format(float(v_hedef_ask_global)) + '- Sembol :' + str(
            v_symbol) + \
                  '- Alım Fiyatı :' + "{:.6f}".format(
            float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                  '- Zarar Oranı :' + "{:.6f}".format(float(v_zarprofit_oran)) + ' - Zaman : ' + str(
            datetime.now()) + 'Alım Zamanı : ' + str(v_alim_zamani)
        print(v_mess1)
        v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.6f}".format(
            float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                           '*' + "{:.3f}".format(float(v_zarprofit_oran)) + '*' + str(datetime.now())
        Telebot_v1.mainma(v_mess1)
        Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
        v_alim_var = 0
        Telebot_v1.genel_alimlar(v_symbol, 'S')
        # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
    elif v_satim_timestamp >= v_alim_timestamp:
        # 1 dk yı geçtiği için satacak
        if float(v_son_fiyat) > float(v_alim_fiyati):
            vm_karzar = 'KARLA KAPADI - '
            v_profit_oran = float(((v_son_fiyat - v_alim_fiyati) * 100) / v_alim_fiyati)

            v_mess1 = vm_karzar + '...Hedefi : ' + "{:.6f}".format(
                float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                      '- Alım Fiyatı :' + "{:.6f}".format(
                float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                      '- Kar Oranı :' + "{:.6f}".format(float(v_profit_oran)) + ' - Zaman : ' + str(
                datetime.now()) + 'Alım Zamanı : ' + str(v_alim_zamani)
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Kar' + '*' + "{:.6f}".format(
                float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                               '*' + "{:.3f}".format(float(v_profit_oran)) + '*' + str(datetime.now())
            print(v_mess1)
            # ******************
            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
            v_alim_var = 0
            Telebot_v1.genel_alimlar(v_symbol, 'S')
            # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
        elif float(v_alim_fiyati) >= float(v_son_fiyat):
            vm_karzar = 'ZARARLA KAPADI - '
            v_zarprofit_oran = float(((v_alim_fiyati - v_son_fiyat) * 100) / v_alim_fiyati)
            v_zarprofit_oran = float(v_zarprofit_oran)

            v_mess1 = vm_karzar + '..Hedefi : ' + "{:.6f}".format(
                float(v_hedef_bid_global)) + '- Sembol :' + str(v_symbol) + \
                      '- Alım Fiyatı :' + "{:.6f}".format(
                float(v_alim_fiyati)) + ' - Satım Fiyatı : ' + "{:.6f}".format(float(v_son_fiyat)) + \
                      '- Zarar Oranı :' + "{:.6f}".format(float(v_zarprofit_oran)) + ' - Zaman : ' + str(
                datetime.now()) + 'Alım Zamanı : ' + str(v_alim_zamani)
            print(v_mess1)
            v_karzarar_mesaj = str(v_symbol) + '*' + 'Zarar' + '*' + "{:.6f}".format(
                float(v_alim_fiyati)) + '*' + "{:.6f}".format(float(v_son_fiyat)) + \
                               '*' + "{:.3f}".format(float(v_zarprofit_oran)) + '*' + str(datetime.now())

            Telebot_v1.mainma(v_mess1)
            Telebot_v1.kar_zarar_durumu(v_karzarar_mesaj)
            v_alim_var = 0
            Telebot_v1.genel_alimlar(v_symbol, 'S')
            # Telebot_v1.analiz(v_karzarar_mesaj, v_symbol)
        # ---------------------------
    else:
        print('İçerde alım var ama henüz satılamadı...!- ', str(datetime.now())[0:19], v_symbol, ' - Hedefi = ',
              str(v_hedef_bid_global), 'Son Fiyat = ', str(v_son_fiyat))

except Exception as exp:
    v_hata_mesaj = 'Hata Oluştu!!..Satım tarafı  = ' + str(exp)
    Telebot_v1.mainma(v_hata_mesaj)
