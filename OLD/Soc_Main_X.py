import time
import Soc_X_1
import threading

from datetime import datetime

if __name__ == "__main__":
    try:
        print('Başladı')
        i=1
        with open('Sembol3.txt', 'r') as dosya:
            for line in dosya.read().splitlines():
                print(line)
                v_symbol = line
                #v_symbol = 'BTCUSDT'
                #Soc_X_1.main(v_symbol)
                print('İşlenen', v_symbol, datetime.now())
                if i==1 :
                    # t1 = threading.Thread(target=Soc_X_1.main, args=(v_symbol))
                    # t1.start()
                    Soc_X_1.main(v_symbol)
                    time.sleep(7)
                    print('İşlenen', v_symbol, datetime.now())
                if i==2 :
                    # t2 = threading.Thread(target=Soc_X_1.main, args=(v_symbol))
                    # t2.start()
                    Soc_X_1.main(v_symbol)
                    time.sleep(5)

                i=i+1
            print('Dosya tamam')
    except Exception as exp:
        v_hata_mesaj = 'Hata Oluştu!!..T1  = ' + str(exp)

