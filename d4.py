import websocket, json, pprint
import threading
import requests
from json import loads
from datetime import datetime

global orderbook, updates, emir_defteri_bid, emir_defteri_ask, v_last_update
v_last_update = '2022'
orderbook = []
updates = 0


def basla(v_lim, v_sem):
    # print('Soketi başlattı')
    global v_limit, v_sembol
    v_limit = v_lim
    v_sembol = v_sem.lower()
    v_soc = "wss://stream.binance.com:9443/ws/" + v_sembol + "@depth@100ms"
    wsb = websocket.WebSocketApp(v_soc, on_open=on_open, on_close=on_close, on_message=on_message)
    # ws.run_forever()
    t1 = threading.Thread(target=wsb.run_forever)
    t1.start()
    t1.join(2)
    orderbook = []
    updates = 0
    print('çıkyo')


def on_open(ws):
    print('2.Soketi başlattı .....!!!')


def on_close(ws):
    print('closed connection')


def on_message(ws, message):
    global orderbook
    # print('received message')
    data = loads(message)

    if len(orderbook) == 0:
        orderbook = get_snapshot()

    lastUpdateId = orderbook['lastUpdateId']
    print(datetime.now(), 'Anlık Data', len(data["b"]))
    print('İçerde Emir orderbook Bids ve Ask =', len(orderbook["bids"]), '-', len(orderbook["asks"]))
    # drop any updates older than the snapshot
    if updates == 0:
        if data['U'] <= lastUpdateId + 1 and data['u'] >= lastUpdateId + 1:
            # print(f'lastUpdateId {data["u"]}')
            orderbook['lastUpdateId'] = data['u']
            process_updates(data)
        else:
            print('discard update')

    # check if update still in sync with orderbook
    elif data['U'] == lastUpdateId + 1:
        # print(f'lastUpdateId {data["u"]}')
        orderbook['lastUpdateId'] = data['u']
        process_updates(data)
    else:
        print('Out of sync, abort')


def process_updates(data):
    # with lock:
    for update in data['b']:
        manage_orderbook('bids', update)
    for update in data['a']:
        manage_orderbook('asks', update)
        # last_update['last_update'] = datetime.now()
    v_last_update = datetime.now()


# Update orderbook, differentiate between remove, update and new
def manage_orderbook(side, update):
    # extract values
    price, qty = update

    # loop through orderbook side
    for x in range(0, len(orderbook[side])):
        if price == orderbook[side][x][0]:
            # when qty is 0 remove from orderbook, else
            # update values
            if qty == 0:
                del orderbook[side]
                print(f'Removed {price} {qty}')
                break
            else:
                orderbook[side][x] = update
                # print(f'Updated: {price} {qty}')
                break
        # if the price level is not in the orderbook,
        # insert price level, filter for qty 0
        elif price > orderbook[side][x][0]:
            if qty != 0:
                orderbook[side].insert(x, update)
                # print(f'New price: {price} {qty}')
                break
            else:
                break


def get_ordergenelorder_book():
    global orderbook
    return orderbook


def get_snapshot():
    # v_mes ='https://www.binance.com/api/v1/depth?symbol='+v_sembol+'&limit='+str(v_limit)
    print('Snapshot alındı', 'Sembol=', v_sembol, 'Limit=', v_limit, 'Zaman=', datetime.now())
    # r = requests.get('https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000')
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())


if __name__ == "__main__":
    print('Başlatıldı-00000000000000',datetime.now())
    v_sembol = 'btcusdt'
    v_limit = 1000
    v_sembol = v_sembol.lower()
    basla(v_limit, v_sembol)
    print('Başlatıldı')
