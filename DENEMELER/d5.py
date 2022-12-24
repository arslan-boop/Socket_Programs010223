import time
from binance import ThreadedWebsocketManager
from binance.client import Client as Client_1, AsyncClient
import API_Config

api_key = '4HnpGRb66wIgg12J81YWcx2arRb9MzzeAOLmmLnYOnwtMCFjDMUTE1b3hafcG5gt'
api_secret = 'Iu586P4BP1EBJYeRb9g3tjdJSpLYlNRclY8OfjCSRpoqZE25OuIUfy3WUyFWtOJ4'
v_client = Client_1(API_Config.API_KEY, API_Config.API_SECRET)
btc_price = {'error': False}


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

bsm = ThreadedWebsocketManager()
bsm.start()
bsm.start_symbol_ticker_socket(callback=btc_trade_history, symbol='BTCUSDT')
# stop websocket
bsm.stop()

# valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
# get timestamp of earliest date data is available
timestamp = v_client._get_earliest_valid_timestamp('BTCUSDT', '1d')
print(timestamp)

# request historical candle (or klines) data
bars = v_client.get_historical_klines('BTCUSDT', '1d', timestamp, limit=1000)

def topup_bnb(min_balance: float, topup: float):
	''' Top up BNB balance if it drops below minimum specified balance '''
	bnb_balance = v_client.get_asset_balance(asset='BNB')
	bnb_balance = float(bnb_balance['free'])
	if bnb_balance < min_balance:
		qty = round(topup - bnb_balance, 5)
		print(qty)
		order = v_client.order_market_buy(symbol='BNBUSDT', quantity=qty)
		return order
	return False

# min_balance = 1.0
# topup = 2.5
# order = topup_bnb(min_balance, topup)