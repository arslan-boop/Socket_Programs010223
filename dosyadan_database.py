import requests
import sqlite3
from datetime import datetime

DB_FILE = "TRADE3.DB"
con = sqlite3.connect(DB_FILE, timeout=10)
cursor = con.cursor()
#WANUSDT*Zarar*0.149100*0.148600*0.335*2022-11-26 22:36:51

def dosyadan_db():
    with open('Sonuc.txt', 'r') as dosya:
        i = 0
        for line in dosya.read().splitlines():
            aciklama = line
            print('Dosya satırı..: ', line, i)
            i += 1
            s = aciklama.split("*")
            print(s)
            print(s[0])
            my_data = (str(s[0]), str(s[1]),float(s[2]),float(s[3]),float(s[4]),str(s[5]) )
            my_query = "INSERT INTO KARZARAR values(?,?,?,?,?,?)"
            cursor.execute(my_query, my_data)
            con.commit()
    dosya.close()
    print('Dosya Tamamlandı')

if __name__ == '__main__':
    dosyadan_db()
