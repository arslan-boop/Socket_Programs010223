import os
from time import sleep
import threading
from binance.client import Client
from binance import ThreadedWebsocketManager
import API_Config
from datetime import datetime
import time
import numpy
import talib

# init
api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'
v_client = Client(api_key, api_secret)
price = {'BTCUSDT': None, 'error': False}
closes = []
v_sem = 'BTCUSDT'
def btc_pairs_trade(msg):
    global  v_sem
    v_symbol = v_sem
    print('Mesaj', str(float(msg['c'])),str(float(msg['o'])),str(float(msg['h'])),str(float(msg['l'])),datetime.now() )
    if msg['e'] != 'error':
        price[v_symbol] = float(msg['c'])
    else:
        price['error'] = True
    #print('Fiyat', float(price[v_symbol]),datetime.now())

    if float(price[v_symbol]) == 0:
        sleep(0.1)
    # while not price['BTCUSDT']:
    #     # wait for WebSocket to start streaming data
    #     sleep(0.1)

def handle_socket_message(msg):
    candle = msg['k']
    close = float(candle['c'])
    open = float(candle['o'])
    high = float(candle['h'])
    low = float(candle['l'])

    is_candle_closed = candle['x']
    print('Geldi',close,'-',open,'-',high,'-',low,'-',datetime.now())
    if is_candle_closed:
        closes.append(close)
        if len(closes) > 90:
            # We done't want the arry to get too big for the RAM
            closes.pop(0)
            np_closes = numpy.array(closes)
            #rsi = talib.RSI(np_closes, Trade.RSI_PERIOD)
            #last_rsi = rsi[-1]

    #         self.buy_or_sell()
    #         print("PRICE - {} -- RSI - {} -- TIME - {}".format(self.close, self.last_rsi,
    #               datetime.now().strftime('%H:%M:%S')))

def get_first_set_of_closes(v_symbol):
    global closes
    #for kline in v_client.get_historical_klines(v_symbol, v_client.KLINE_INTERVAL_1MINUTE, "9 hour ago UTC"):
    #for kline in v_client.get_historical_klines(v_symbol, '1s', "1 hour ago UTC"):
    # current_timestamp = round(time.time() * 1000)
    # current_timestamp = current_timestamp / 1000
    # current_timestamp = int(current_timestamp)
    # v_start = (current_timestamp - (600000)) / 1000
    # v_start=int(v_start)
    # #
    # for kline in v_client.get_historical_klines(symbol = v_symbol,
    #                                             start_str=str(v_start),
    #                                             end_str=str(current_timestamp),
    #                                             interval = '1s',
    #                                             limit = 500):
    # En fazla 1000 tane kayıt alıyor geçmişe doğru
    for kline in v_client.get_historical_klines(v_symbol, '1s', "5 minute ago UTC"):
        closes.append(float(kline[4]))
        #print(closes)

    print(len(closes))

def main():
    v_symbol = 'BTCUSDT'
    get_first_set_of_closes(v_symbol)
    bsm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    bsm.start()
    bsm.start_symbol_ticker_socket(symbol=v_symbol, callback=btc_pairs_trade)
    #bsm start_symbol_ticker_socket(symbol=v_symbol, callback=btc_pairs_trade)
    # bsm.start_kline_socket(callback=handle_socket_message, symbol=v_symbol, interval=v_client.KLINE_INTERVAL_1MINUTE)
    bsm.join()

    while True:
        # error check to make sure WebSocket is working
        if price['error']:
            # stop and restart socket
            bsm.stop()
            sleep(2)
            bsm.start()
            price['error'] = False
        else:
            print('Geldi00', price[v_symbol])
            if price[v_symbol] > 10000:
                try:
                    # order = client.order_market_buy(symbol='ETHUSDT', quantity=100)
                    print('Geldi', price[v_symbol])
                    break
                except Exception as e:
                    print(e)

        sleep(0.1)
        bsm.stop()


if __name__ == "__main__":
    main()
