import websocket
import requests
from json import loads
from datetime import datetime

global dizi, v_sembol, v_inter, v_limit, v_in, genelbok
v_sembol = 'BTCUSDT'
v_inter = '1s'
v_limit = 10
v_in = '1000ms'
genelbok = {}

class Client_Socket():

    def __init__(self, v_sembol_g, v_inter_g, v_limit_g, v_in_g):
        global v_sembol, v_limit
        # local data management
        self.orderbook = {}
        self.updates = 0
        v_sembol = v_sembol_g
        v_sembol_g = v_sembol_g.lower()
        v_limit = v_limit_g
        url1 = "wss://stream.binance.com:9443/ws/btcusdt@depth"
        url = "wss://stream.binance.com:9443/ws/" + v_sembol_g + "@depth"
        #vurl = "wss://stream.binance.com:9443/ws/" + v_sembol_g + "@depth"
        socket = f'wss://stream.binance.com:9443/ws/{v_sembol_g}@depth',
        # create websocket connection
        self.ws = websocket.WebSocketApp(
            url1,
            on_message=self.on_message,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws.run_forever()

    # on_error=self.on_error,

    # keep connection alive
    def run_forever(self):
        try:
            self.ws.run_forever()
        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..run_forever  = ' + str(exp)

    def get_ordergenelorder_book(self,v_param):
        global genelbok
        #print('asfa', genelbok)
        #print('Order Dizi Bids =', len(genelbok["bids"]))
        #print('Order Dizi Asks=', len(genelbok["asks"]))
        return genelbok

    # convert message to dict, process update
    def on_message(self, message):
        global genelbok
        data = loads(message)
        # check for orderbook, if empty retrieve
        if len(self.orderbook) == 0:
            self.orderbook = self.get_snapshot()

        # get lastUpdateId
        lastUpdateId = self.orderbook['lastUpdateId']
        #print('Order Book =', self.orderbook)
        genelbok = self.orderbook
        print('genel bokmmmmmm', genelbok)
        #print('Order Dizi Bids =', len(self.orderbook["bids"]))
        #print('Order Dizi Asks=', len(self.orderbook["asks"]))

        # drop any updates older than the snapshot
        if self.updates == 0:
            if data['U'] <= lastUpdateId + 1 and data['u'] >= lastUpdateId + 1:
                #print(f'lastUpdateId {data["u"]}')
                self.orderbook['lastUpdateId'] = data['u']
                self.process_updates(data)
            else:
                print('discard update')

        # check if update still in sync with orderbook
        elif data['U'] == lastUpdateId + 1:
            #print(f'lastUpdateId {data["u"]}')
            self.orderbook['lastUpdateId'] = data['u']
            self.process_updates(data)
        else:
            print('Out of sync, abort')

    # catch errors
    # def on_error(self):
    #     print('Hataatt')

    # run when websocket is closed
    def on_close(self):
        print("### closed ###")

    # run when websocket is initialised
    def on_open(self):
        print('Connected to Binance\n')

    # Loop through all bid and ask updates, call manage_orderbook accordingly
    def process_updates(self, data):
            for update in data['b']:
                self.manage_orderbook('bids', update)
            for update in data['a']:
                self.manage_orderbook('asks', update)
            self.last_update['last_update'] = datetime.now()

        # for update in data['b']:
        #     self.manage_orderbook('bids', update)
        # for update in data['a']:
        #     self.manage_orderbook('asks', update)

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
                    #print(f'Removed {price} {qty}')
                    break
                else:
                    self.orderbook[side][x] = update
                    #print(f'Updated: {price} {qty}')
                    break
            # if the price level is not in the orderbook,
            # insert price level, filter for qty 0
            elif price > self.orderbook[side][x][0]:
                if qty != 0:
                    self.orderbook[side].insert(x, update)
                    #print(f'New price: {price} {qty}')
                    break
                else:
                    break

    # retrieve orderbook snapshot

    def get_snapshot(self):
        # v_mes ='https://www.binance.com/api/v1/depth?symbol='+v_sembol+'&limit='+str(v_limit)
        print('Snapshot alındı','Sembol=',v_sembol, 'Limit=',v_limit,'Zaman=', datetime.now())
        #r = requests.get('https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000')
        r = requests.get('https://www.binance.com/api/v1/depth?symbol='+v_sembol+'&limit='+str(v_limit))
        return loads(r.content.decode())


if __name__ == "__main__":
    #create webscocket client
    try:
        v_sembol_g = 'BTCUSDT'
        v_inter_g = '1s'
        v_limit_g = 100
        v_in_g = '1000ms'
        coin = 'vsdfsd'

        client = Client_Socket('BTCUSDT', v_inter_g, v_limit_g, v_in_g)
        # run forever
        #client.run_forever()
    except Exception as exp:
        v_hata_mesaj = 'Hata Oluştu!!..run_forever  = ' + str(exp)
