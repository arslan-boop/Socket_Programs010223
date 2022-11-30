import sqlite3
from datetime import datetime

DB_FILE = "../TRADE3.DB"
conn3 = sqlite3.connect(DB_FILE, timeout=60)
cursor3 = conn3.cursor()


def deneme():
    try:
        i = 1
        while True:
            with conn3:
                my_data = ('v_symbol', '1m', 4, datetime.now(), datetime.now(), None, None, None, 'T3', None, 100)
                my_query = "INSERT INTO Trade_Logs values(?,?,?,?,?,?,?,?,?,?,?)"
                cursor3.execute(my_query, my_data)
                conn3.commit()
                #conn3.close()
            i = i + 1
            if i == 10:
                conn3.close()
                break
        print('çıkrıt')
    except Exception as exp:
        v_hata_mesaj = 'Ana Program Hata Oluştu!!..  = ' + str(exp) + str(datetime.now())


if __name__ == '__main__':
    deneme()
    print('sonrası ')
