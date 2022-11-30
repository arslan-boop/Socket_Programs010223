import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
import ws_4_main_s
import threading
from datetime import datetime


def sel(isim):
    print('merhaba ', isim)


def bas(v_sembol_g, v_limit_g, v_inter_g):
    # while True:
    v_genel_orderbook = []
    threads = []
    Procesler = []
    v = 'ihsan'
    t1 = threading.Thread(target=ws_4_main_s.run_frontdata, args=(v_sembol_g, v_inter_g))
    #t1 = threading.Thread(target=sel, args=(v,))
    t1.start()
    t1.join(0.2)
    print('kkkk')

if __name__ == '__main__':
    print('Başladı ', datetime.now())
    v_inter_g = '1s'
    v_limit_g = 1000
    v_sembol_g = 'VIDTUSDT'

    # ws_4_main_s.basla(v_sembol_g, v_limit_g, v_inter_g)
    bas(v_sembol_g, v_limit_g, v_inter_g)
    print('sonn')
