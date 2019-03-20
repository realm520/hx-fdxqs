# encoding=utf-8

import requests
import time

class Market():
    def __init__(self, config):
        self.source = config['MARKET_SOURCE']

    def get(self, url):
        while True:
            try:
                r = requests.get(url)
            except Exception:
                time.sleep(0.5)
                continue
            if r.status_code != 200:
                time.sleep(0.5)
                continue
            r_info = r.json()
            r.close()
            return r_info
            
    def getMarkets(self):
        return self.get(self.source+'markets')

    def getTick(self, pair):
        return self.get(self.source+'ticker?market='+pair)
    
    def getLastPrice(self, coin, currency):
        if currency == 1:
            return self.getTick(coin+'_qc')['ticker']['last']
        elif currency == 2:
            return self.getTick(coin+'_usdt')['ticker']['last']


if __name__ == '__main__':
    config = {'MARKET_SOURCE': 'http://api.zb.cn/data/v1/'}
    market = Market(config)
    print(market.getLastPrice('pax', 1))