import websocket, json, pprint
import requests
from json import loads
from datetime import datetime

global orderbook, updates
orderbook = {}
updates = 0

global v_sembol, v_limit,  genelbok
v_sembol = 'btcusdt'
v_limit = 1000


def basla( v_lim,  v_sem):
    global v_limit,v_sembol
    v_limit = v_lim
    v_sembol = v_sem.lower()
    v_soc = "wss://stream.binance.com:9443/ws/" + v_sembol + "@depth"
    ws = websocket.WebSocketApp(v_soc, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()


def on_open(ws):
    print('opened connection')


def on_close(ws):
    print('closed connection')


def on_message(ws, message):
    global genelbok
    global orderbook
    print('received message')
    # json_message = json.loads(message)
    # pprint.pprint(json_message)
    data = loads(message)
    if len(orderbook) == 0:
        orderbook = get_snapshot()

    # get lastUpdateId
    lastUpdateId = orderbook['lastUpdateId']
    # print('Order Book =', orderbook)
    genelbok = orderbook
    # print('genel bokmmmmmm', genelbok)
    # print('Order Dizi Bids =', len(orderbook["bids"]))
    # print('Order Dizi Asks=', len(orderbook["asks"]))

    # drop any updates older than the snapshot
    if updates == 0:
        if data['U'] <= lastUpdateId + 1 and data['u'] >= lastUpdateId + 1:
            print(f'lastUpdateId {data["u"]}')
            orderbook['lastUpdateId'] = data['u']
            process_updates(data)
        else:
            print('discard update')

    # check if update still in sync with orderbook
    elif data['U'] == lastUpdateId + 1:
        print(f'lastUpdateId {data["u"]}')
        orderbook['lastUpdateId'] = data['u']
        process_updates(data)
    else:
        print('Out of sync, abort')

    # retrieve orderbook snapshot


def process_updates(data):
    # with lock:
    for update in data['b']:
        manage_orderbook('bids', update)
    for update in data['a']:
        manage_orderbook('asks', update)
        # last_update['last_update'] = datetime.now()
    orderbook['last_update'] = datetime.now()


# Update orderbook, differentiate between remove, update and new


def manage_orderbook(self, side, update):
    # extract values
    price, qty = update

    # loop through orderbook side
    for x in range(0, len(orderbook[side])):
        if price == orderbook[side][x][0]:
            # when qty is 0 remove from orderbook, else
            # update values
            if qty == 0:
                del orderbook[side]
                # print(f'Removed {price} {qty}')
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


# retrieve orderbook snapshot


def get_snapshot():
    # v_mes ='https://www.binance.com/api/v1/depth?symbol='+v_sembol+'&limit='+str(v_limit)
    print('Snapshot alındı', 'Sembol=', v_sembol, 'Limit=', v_limit, 'Zaman=', datetime.now())
    # r = requests.get('https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000')
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=' + v_sembol.upper() + '&limit=' + str(v_limit))
    return loads(r.content.decode())


if __name__ == "__main__":
    v_sembol = 'btcusdt'
    v_limit = 1000
    v_sembol = v_sembol.lower()
    url = "wss://stream.binance.com:9443/ws/btcusdt@depth"
    # vurl = "wss://stream.binance.com:9443/ws/" + v_sembol_g + "@depth"
    # socket = f'wss://stream.binance.com:9443/ws/{v_sembol_g}@depth',
    basla( v_limit,v_sembol)
