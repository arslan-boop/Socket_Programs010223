from binance.client import Client
client = Client('api_key', 'api_secret')
import time
import win32api
gt = client.get_server_time()
tt=time.gmtime(int((gt["serverTime"])/1000))
win32api.SetSystemTime(tt[0],tt[1],0,tt[2],tt[3],tt[4],tt[5],0)