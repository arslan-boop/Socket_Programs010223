import os
from binance.client import Client
from binance import ThreadedWebsocketManager
import pprint
from time import sleep

TEST_NET = True

if __name__ == "__main__":
    if TEST_NET:
        # passkey (saved in bashrc for linux)
        api_key = os.environ.get('hXlzsJW8IkFJzOOK9kPWWY9lyZCjoQ9YCvnMZIsAq44cLjxpbYVgQFA6SZmdV4c9')

        # secret (saved in bashrc for linux)
        api_secret = os.environ.get('HC5CaqjYxNR45FP3SFRPi9Y4ATatID1BADfguo32hisZ2I3SaOqPyf0EZQTkl4F5')

        client = Client(api_key, api_secret, testnet=True)
        print("Using Binance TestNet server")
#main()
def main():
    pprint.pprint(client.get_account())
    print(client.get_asset_balance(asset='BNB'))  # BTC, USDT, ETH

    # get latest price from Binance API
    eth_price = client.get_symbol_ticker(symbol="ETHUSDT")
    print(eth_price)

if __name__ == "__main__":
    if TEST_NET:
        api_key = os.environ.get('BINANCE_TESTNET_KEY')
        api_secret = os.environ.get('BINANCE_TESTNET_PASSWORD')
        client = Client(api_key, api_secret, testnet=True)
        print("Using Binance TestNet server")

    # Add btc price and instantiate ThreadedWebsocketManager()
    btc_price = {'BTCUSDT': None, 'error': False}
    twm = ThreadedWebsocketManager()
    main()

def main():
    pprint.pprint(client.get_account())
    print(client.get_asset_balance(asset='BNB'))
    eth_price = client.get_symbol_ticker(symbol="ETHUSDT")
    print(eth_price)

    # Start the websocket manager and register
    # callback for the bitcoin price
    twm.start()
    twm.start_symbol_ticker_socket(callback=btc_values_received,
                                   symbol='BTCUSDT')

    # To keep the ThreadedWebsocketManager running using join()
    # to join it to the main thread.
    twm.join()


Get
the
BTC
value in the
last
24
hrs


def btc_values_received(msg):
    ''' Process the btc values received in the last 24 hrs '''

    pprint.pprint(msg)

    if msg['e'] != 'error':
        print(msg['e'])
        btc_price['BTCUSDT'] = float(msg['c'])
    else:
        btc_price['error'] = True

def main():
    pprint.pprint(client.get_account())
    print(client.get_asset_balance(asset='BNB'))
    eth_price = client.get_symbol_ticker(symbol="ETHUSDT")
    print(eth_price)

    twm.start()
    twm.start_symbol_ticker_socket(callback=btc_values_received, symbol='BTCUSDT')

    # wait here to receive some btc value initially through websocket callback
    while not btc_price['BTCUSDT']:
        sleep(0.1)

    # call buy ETH function with a while loop to keep a track on btc price
    buy_and_sell_ETH_at_BTC()
    # twm.join() # to stop main thread exit.
    twm.stop()

# Buy or sell ETHUSDT when BTC reaches a particular value
def buy_and_sell_ETH_at_BTC():
    while True:
        # error check to make sure WebSocket is working
        if btc_price['error']:
            # stop and restart socket (cleanup)
            twm.stop()
            sleep(2)
            twm.start()
            btc_price['error'] = False
        else:
            if 1000 < btc_price['BTCUSDT'] < 40000:   # bitcoin price
                try:
                    print("Buying when BTCUSDTprice:",btc_price['BTCUSDT'])
                    order = client.order_market_buy(symbol='ETHUSDT', quantity=1)
                    pprint.pprint(order)
                    break
                except Exception as e:
                    print(e)
                    break
            else:
                try:
                    print("Selling when BTCUSDT price:",btc_price['BTCUSDT'])
                    order = client.order_market_sell(symbol='ETHUSDT', quantity=1)
                    pprint.pprint(order)
                    break
                except Exception as e:
                    print(e)
                    break
            sleep(0.1)