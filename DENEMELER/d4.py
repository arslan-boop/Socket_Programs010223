import websocket, json, pprint
import threading
import requests
from json import loads
from datetime import datetime

def dene():
    return 6,7

if __name__ == "__main__":
    print('Başlatıldı-00000000000000',datetime.now())
    v1, v2 = dene()
    print('1-2', v1,v2)