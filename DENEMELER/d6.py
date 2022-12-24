import os
from time import sleep
import threading

from binance.client import Client
from binance import ThreadedWebsocketManager

import API_Config

# init
api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'
client = Client(api_key, api_secret)

price = {'BTCUSDT': None, 'error': False}


def handle_socket_message(msg):
    candle = msg['k']
    close = float(candle['c'])
    is_candle_closed = candle['x']
    print('Geldi')

def btc_pairs_trade(msg):
    if msg['e'] != 'error':
        price['BTCUSDT'] = float(msg['c'])
    else:
        price['error'] = True
    print('Fiyat',float(price['BTCUSDT']))

    if float(price['BTCUSDT']) ==0:
        sleep(0.1)
    # while not price['BTCUSDT']:
    #     # wait for WebSocket to start streaming data
    #     sleep(0.1)


def main():
    bsm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    bsm.start()
    bsm.start_symbol_ticker_socket(symbol='BTCUSDT', callback=btc_pairs_trade)
    bsm.start_kline_socket(callback=handle_socket_message, symbol='BTCUSDT',interval=Client.KLINE_INTERVAL_1MINUTE)

    bsm.join()

    # t1 = threading.Thread(target=bsm.start())
    # t1.start()
    # t1.join(2)
    #
    # t2 = threading.Thread(target=bsm.start_symbol_ticker_socket(symbol='BTCUSDT', callback=btc_pairs_trade))
    # t2.start()
    # t2.join(2)

    while True:
        # error check to make sure WebSocket is working
        if price['error']:
            # stop and restart socket
            bsm.stop()
            sleep(2)
            bsm.start()
            price['error'] = False

        else:
            if price['BTCUSDT'] > 10000:
                try:
                    #order = client.order_market_buy(symbol='ETHUSDT', quantity=100)
                    print('Geldi', price['BTCUSDT'])
                    break
                except Exception as e:
                    print(e)

        sleep(0.1)
        bsm.stop()

if __name__ == "__main__":
    main()
