import time

import websocket, json, pprint
import requests
from json import loads
from datetime import datetime
from time import sleep
# from threading import Thread
import threading

global orderbook, updates, emir_defteri, v_last_update
v_last_update = '2022'
orderbook = {}
emir_defteri = {}
updates = 0

global v_sembol, v_limit
v_sembol = 'btcusdt'
v_limit = 1000


class Socketine():
    # def basla(self, v_lim, v_sem):
    def __init__(self, v_lim, v_sem):
        print('Soketi başlattı')
        # global v_limit, v_sembol
        self.v_limit = v_lim
        self.v_sembol = v_sem.lower()
        self.v_soc = "wss://stream.binance.com:9443/ws/" + v_sembol + "@depth"
        self.ws = websocket.WebSocketApp(self.v_soc, on_open=self.on_open, on_close=self.on_close,
                                         on_message=self.on_message)
        self.orderbook = {}
        self.emir_defteri = {}
        self.updates = 0
        print('Soketi başlattı ---son')
        # keep connection alive
        #self.ws.run_forever()

    def run_forever(self):
        self.ws.run_forever()

    def on_message(self, ws, message):
        # print('received message')
        # json_message = json.loads(message)
        # pprint.pprint(json_message)
        data = loads(message)
        # pprint.pprint(data)

        # Orderbookda snapshottan alınan asıl , ana defter var. Yukarıdaki
        # data da ise anlı akan veriler var. Bu verileri defterde güncelliyoruz.
        if len(self.orderbook) == 0:
            self.orderbook = self.get_snapshot()

        # get lastUpdateId
        lastUpdateId = self.orderbook['lastUpdateId']
        # print('Order Book =', orderbook)
        self.emir_defteri = self.orderbook
        #print('Anlık Data', len(data["b"]))
        #print('İçerde Emir Defterindeki Bids ve Ask =', len(self.orderbook["bids"]), '-', len(self.orderbook["asks"]))

        # drop any updates older than the snapshot
        if self.updates == 0:
            if data['U'] <= lastUpdateId + 1 and data['u'] >= lastUpdateId + 1:
                print(f'lastUpdateId {data["u"]}')
                self.orderbook['lastUpdateId'] = data['u']
                self.process_updates(data)
            else:
                print('discard update')

        # check if update still in sync with orderbook
        elif data['U'] == lastUpdateId + 1:
            # print(f'lastUpdateId {data["u"]}')
            self.orderbook['lastUpdateId'] = data['u']
            self.process_updates(data)
        else:
            print('Out of sync, abort')

    def process_updates(self, data):
        #with self.lock:
            for update in data['b']:
                self.manage_orderbook('bids', update)
            for update in data['a']:
                self.manage_orderbook('asks', update)
                # last_update['last_update'] = datetime.now()
            self.v_last_update = datetime.now()
            self.v_book = self.get_ordergenelorder_book()
            print('Son güncelleme', self.v_last_update, len(self.v_book["bids"]))

    # Update orderbook, differentiate between remove, update and new
    def manage_orderbook(self, side, update):
        # extract values
        price, qty = update

        # loop through orderbook side
        for x in range(0, len(self.orderbook[side])):
            if price == self.orderbook[side][x][0]:
                # when qty is 0 remove from orderbook, else
                # update values
                if qty == 0:
                    del self.orderbook[side]
                    print(f'Removed {price} {qty}')
                    break
                else:
                    self.orderbook[side][x] = update
                    # print(f'Updated: {price} {qty}')
                    break
            # if the price level is not in the orderbook,
            # insert price level, filter for qty 0
            elif price > self.orderbook[side][x][0]:
                if qty != 0:
                    self.orderbook[side].insert(x, update)
                    # print(f'New price: {price} {qty}')
                    break
                else:
                    break

    def on_open(self, ws):
        print('opened connection')

    def on_close(self, ws):
        print('closed connection')

    # retrieve orderbook snapshot
    def get_ordergenelorder_book(self):
        # print('asfa', orderbook)
        # print('Emir Defterindeki Bids ve Ask =', len(orderbook["bids"]),'-', len(orderbook["asks"]))
        return self.orderbook

    def get_snapshot(self):
        # v_mes ='https://www.binance.com/api/v1/depth?symbol='+v_sembol+'&limit='+str(v_limit)
        print('Snapshot alındı', 'Sembol=', self.v_sembol, 'Limit=', self.v_limit, 'Zaman=', datetime.now())
        # r = requests.get('https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000')
        r = requests.get(
            'https://www.binance.com/api/v1/depth?symbol=' + self.v_sembol.upper() + '&limit=' + str(self.v_limit))
        return loads(r.content.decode())


def run_frontdata(v_limit, v_sembol):
    while (True):
        try:
            # v_basclass = Socketine(v_limit, v_sembol)
            # time.sleep(1.666)
            # print('Anlık order bokk ', v_basclass.get_ordergenelorder_book, datetime.now())

            v_basclass = Socketine(v_limit, v_sembol)
            print('Anlık order bokk ', v_basclass.get_ordergenelorder_book, datetime.now())

            # t4 = threading.Thread(target=v_basclass, args=(v_limit, v_sembol))
            # t4.start()
            time.sleep(2)
            t5 = threading.Thread(target=v_basclass.run_forever())
            t5.start()
            print('Anlık order bokdwefwegfqk ', v_basclass.get_ordergenelorder_book, datetime.now())

        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..T1  = ' + str(exp)
            time.sleep(2)


if __name__ == "__main__":
    v_sembol = 'btcusdt'
    v_limit = 1000
    v_sembol = v_sembol.lower()
    run_frontdata(v_limit, v_sembol)
    # t4 = threading.Thread(target=run_frontdata, args=(v_limit, v_sembol))
    # time.sleep(2)
    # t4.start()
    # time.sleep(2)
    # print('dfvbdfsbghb')
    # vo = Socketine.orderbook
    # print('Anlık order bokk ', vo, datetime.now())
