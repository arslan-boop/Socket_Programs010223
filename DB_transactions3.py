import  sqlite3
import requests
import time
import json
import re
from pprint import pprint
from datetime import datetime

con = sqlite3.connect("TRADE3.db")
cursor = con.cursor()
# def Table_create():
#     cursor.execute("CREATE TABLE IF NOT EXISTS Trade_Logs (Coin_name TEXT, Period TEXT , "
#                    "Buy_Price REAL, Buy_Time TEXT, Date_System TEXT, Sell_Price REAL, Result TEXT , Percent REAL, Desc_coin TEXT, Sell_Time TEXT) ")
#     con.commit()
#
# def Table_create1():
#     cursor.execute("CREATE TABLE IF NOT EXISTS Trade_Logs_Main (Coin_name TEXT, Period TEXT , "
#                    "Buy_Price REAL, Buy_Time TEXT, Date_System TEXT, Sell_Price REAL, Result TEXT , Percent REAL, Desc_coin TEXT, Sell_Time TEXT) ")
#     con.commit()

def Add_value(v_name, v_period, v_buy_price, v_buy_time, v_date, v_sell_price, v_result, v_percent, v_desc, v_sell_time,v_balance,v_cursor,v_con):
    my_data=(v_name, v_period, v_buy_price, v_buy_time, v_date, v_sell_price, v_result, v_percent, v_desc,v_sell_time,v_balance)
    my_query="INSERT INTO Trade_Logs values(?,?,?,?,?,?,?,?,?,?,?)"
    v_cursor.execute(my_query,my_data)
    v_con.commit()
    #con.close()
def Add_Log(v_name,v_tip,v_cursor,v_con):
    my_query="INSERT INTO Trade_Logs_Main(Coin_name, Period, Buy_Price, Buy_Time, Date_System, Sell_Price," \
             " Result, Percent, Desc_coin,Sell_Time, Balance) " \
             "SELECT Coin_name, Period, Buy_Price, Buy_Time, Date_System," \
             " Sell_Price, Result, Percent, Desc_coin, Sell_Time, Balance  FROM Trade_Logs  WHERE  Coin_name = ? and Desc_coin=?"
    my_data = (v_name,v_tip)
    #cursor.execute(my_query,[my_data])
    v_cursor.execute(my_query, my_data)
    v_con.commit()
    #con.close()
def Update_Table(v_name,v_sell_price, v_result, v_percent, v_sell_time,v_tip,v_balance):
    my_query="UPDATE Trade_Logs SET Sell_Price=? ,Sell_Time=?, Result=?, Percent=?, Balance=?  WHERE Coin_name =? and Desc_coin=? "
    columnValues = (v_sell_price,v_sell_time,v_result, v_percent,v_balance,v_name,v_tip)
    cursor.execute(my_query,columnValues)
    con.commit()
    #con.close()
def Update_Balance(v_balance,v_tip,v_komisyon):
        my_query="UPDATE Parameters SET Balance3 = ? , KOMISYON3=KOMISYON3 + ? "
        columnValues =(v_balance,v_komisyon)
        cursor.execute(my_query,columnValues)
        con.commit()
def Delete_Table(v_name,v_tip):
    my_query="DELETE FROM Trade_Logs WHERE Coin_name =? and Desc_coin =?"
    mydata = (v_name,v_tip)
    #cursor.execute(my_query,[mydata])
    cursor.execute(my_query, mydata)
    con.commit()
    #con.close()
def Select_Table(v_name,v_tip): #, v_period, v_buy_price, v_buy_time, v_date, v_sell_price, v_result, v_percent, v_desc,v_sell_time):
    my_query="SELECT Buy_Price FROM Trade_Logs WHERE Coin_name =? and Desc_coin = ?"
    cursor.execute(my_query,(v_name,v_tip))
    #print("Reading single row \n")
    record = cursor.fetchone()
    #print("Buyolan: ", record[0])
    v_buy = record[0]
    #print('Buuuu', str(v_buy))
    #cursor.close()
    return v_buy
def Select_Balance(v_tip):
        my_query="SELECT Balance3  FROM Parameters "
        cursor.execute(my_query)
        #print("Reading single row \n")
        record = cursor.fetchone()
        #print("Buyolan: ", record[0])
        v_buy = record[0]
        #print('Buuuu', str(v_buy))
        #cursor.close()
        return v_buy
#************************************************TABLO / DOSYA YENİLEMELER
def Sel_USDT(v_name): #, v
    # Dosyaya açma
        v_semboldos = open("Sembol3.txt", "w")
        my_query = "SELECT name FROM USDT_COINS ORDER BY PRICE_CHANGE_PERCENT DESC "
        cursor.execute(my_query)
        i = 25
        record = cursor.fetchmany(i) #.fetchall()
        for x in record:
            #print(x, 'kayıt= ', record[0])
            # Dosyaya Yazma ----------------------------
            y = str(x)
            y = y.replace("('", "")
            y = y.replace("',)", "")
            v_semboldos.write(y)
            v_semboldos.write("\n")
        #cursor.close()
        con.commit()
        #con.close()

def File_write():
    Sel_USDT(1)
def Delete_USDT(v_name):
    my_query="DELETE FROM USDT_COINS WHERE  1=? "
    mydata = (v_name)
    cursor.execute(my_query,[mydata])
    #cursor.execute(my_query,(mydata))
    con.commit()
def Add_USDT(v_name, v_last_price, v_price_change, v_price_change_percent,v_time ):
    my_data=(v_name, v_last_price, v_price_change, v_price_change_percent,v_time)
    my_query="INSERT INTO USDT_COINS values(?,?,?,?,?)"
    cursor.execute(my_query,my_data)
    con.commit()
def USDT_Tablo_Yaz():
    v_time = str(datetime.now())
    v_time = v_time[0:19]
    # Eski bilgileri sil
    Delete_USDT(1)
    # # Dosyaya açma
    # v_semboldos = open("Sembol.txt", "w")
    # #---------------------
    payload={}
    headers = {
      'Content-Type': 'application/json'
    }

    url = "https://api.binance.com/api/v3/exchangeInfo"

    response = requests.request("GET", url, headers=headers, data=payload)
    markets = json.loads(response.text)
    active = {}
    for market in markets['symbols']:
        symbol = market['symbol']
        status = market['status']
        active[symbol] = status == 'TRADING'

    url = "https://api.binance.com/api/v3/ticker/24hr"

    response = requests.request("GET", url, headers=headers, data=payload)
    tickers = json.loads(response.text)
    i = 0
    prices = {}
    prices1 = {}
    prices2 = {}
    for ticker in tickers:
        symbol = ticker['symbol']
        if symbol == 'NBTUSDT':
           print('Eee')
        else:
            isUSDT = re.search("USDT$", symbol)
            #isUSDT = re.search("BUSD$", symbol)
            if (isUSDT and active[symbol]):
               if ("UP" in symbol) or ("DOWN" in symbol):
                  print('kelime geçiyor')
               else:
                   i = i + 1
                   prices[symbol] = ticker['lastPrice']
                   prices1[symbol] = ticker['priceChange']
                   prices2[symbol] = ticker['priceChangePercent']
                   # Tabloya Yazma ----------------------------
                   Add_USDT(symbol,prices[symbol],prices1[symbol],prices2[symbol],v_time)
                   # # Dosyaya Yazma ----------------------------
                   # v_semboldos.write(symbol)
                   # v_semboldos.write("\n")
                   # #-----------------------------
                   print('Sembol =', symbol, 'lastPrice=', prices[symbol],'priceChange', prices[symbol],'priceChangePercent',  prices2[symbol], str(i))

#*************************************************************************
if __name__ == '__main__':
    # Table_create()
    # Table_create1()
    #Update_Table('VIDTUSDT', 3, 'v_result', 1, 'v_sell_time', 'TIP-1',233)
    #Delete_Table()
    #Add_value('v_symboly', '1m', 43, 'dsfsd', 'dsfs', None, None, None, 'TIP-1', None,1000)
    #Update_Table(v_name, v_sell_price, v_result, v_percent, v_sell_time, v_tip, v_balance):
    #
    #Update_Balance(1000)
     USDT_Tablo_Yaz()
     File_write()
    #v_buyy = Select_Balance()
    #print('vsd', v_buyy)
    #Delete_Table('CFXUSDT', 'TIP-1')
    # v_deg = Select_Table('CFXUSDT','TIP-1 ')
    # print('alışş ',v_deg)
    #Add_value('sym', '3m',0.8,'zaman','cdsfcsd',0, 'Kar', 1, 'Atutuutuuttuula')
    #Add_value()
    #Select_Table('AVAXUSDT')
    #Update_Table('AVAXUSDT', 17, 'Kar', 1,'202020')

    # v_alis = Select_Table('AVAXUSDT')
    # v_alis = str(v_alis)



