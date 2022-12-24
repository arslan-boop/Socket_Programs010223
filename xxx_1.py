import time
from binance import ThreadedWebsocketManager
from binance.client import Client as Client_1, AsyncClient
import API_Config

api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
btc_price = {'error':False}

def btc_trade_history(msg):
    ''' define how to process incoming WebSocket messages '''
    if msg['e'] != 'error':
	print(msg['c'])
	btc_price['last'] = msg['c']
	btc_price['bid'] = msg['b']
	btc_price['last'] = msg['a']
	btc_price['error'] = False
    else:
        btc_price['error'] = True

# init and start the WebSocket
bsm = ThreadedWebsocketManager()
bsm.start()

def main():
    symbol = 'BNBBTC'
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()

    def handle_socket_message(msg):
        print(f"message type: {msg['e']}")
        print(msg)

    twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)
   streams = ['bnbbtc@miniTicker', 'bnbbtc@bookTicker']
    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

    twm.join()


if __name__ == "__main__":
   main()