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

def kz_hesapla(): #, v
        my_query = "select SONUC, K_Z_ORAN, Tarih from KARZARAR ORDER BY Tarih "
        cursor.execute(my_query)
        i = 50000
        #v_bakiye = []
        v_bak = 1000
        record = cursor.fetchmany(i) #.fetchall()
        for x in record:
            v_bakiye = x
            v_durum = v_bakiye[0]
            v_oran =  v_bakiye[1]
            #v_kom = float((v_bak*75 / 100000)*2)
            v_kom = float((v_bak / 1000) * 2)

            if v_durum=='Kar':
                v_bak = (v_bak + (v_bak*v_oran)/100)-v_kom
                print('Bakiye', v_bak)
            else:
                v_bak = (v_bak - (v_bak * v_oran)/100)-v_kom
                print('Bakiye', v_bak)
            print('Sonuç ara = ', v_bak)
        con.commit()
        print('Sonuç = ', v_bak)
def satirs():
    print(len(open("Sonuc.txt", "r").readlines()))
    print(len(open("OLD/ws_4_con4.py", "r").readlines()))

if __name__ == '__main__':
    dosyadan_db()
    kz_hesapla()
    #satirs()
