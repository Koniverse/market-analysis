import datetime
import json
import logging
from time import sleep

import requests

from services.mongo import crypto_currency_coll, price_coll

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-30s %(levelname)-6s %(message)s',
                    filemode='a')
_logger = logging.getLogger(__name__)

last_run_time = False
interval = 60

# Build coinmap
compare_infos = ['lastUpdated', 'circulatingSupply', 'cmcRank', 'high24h', 'low24h', 'marketPairCount', 'maxSupply',
                 'totalSupply']
coin_map = {}
for crypto_currency in crypto_currency_coll.find({}):
    coin_map[crypto_currency.get('id')] = crypto_currency

timeout = 10
params = {
    'start': 1,
    'limit': 100,
    'sortBy': 'market_cap',
    'sortType': 'desc',
    'convert': 'USD,btc,eth',
    'cryptoType': 'all',
    'tagType': 'all',
    'aux': 'ath,atl,high24h,low24h,num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,volume_7d,volume_30d',
}

while True:
    session = requests.Session()
    session.get('https://coinmarketcap.com/')
    now = datetime.datetime.now()
    max_number = 1
    number = 0

    if not last_run_time or ((now - last_run_time) > datetime.timedelta(seconds=interval)):
        last_run_time = now
        _logger.info('Run session %s' % last_run_time)
        while number < max_number:
            retry = 0
            try:
                params['start'] = number + 1
                rs_raw = session.get('https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing', params=params,
                                     timeout=timeout)
                data = json.loads(rs_raw.text).get('data')
                update_time = datetime.datetime.now()
                crypto_currency_list = data.get('cryptoCurrencyList')
                if crypto_currency_list:
                    number += len(crypto_currency_list)
                    for crypto_currency in crypto_currency_list:
                        existed = coin_map.get(crypto_currency.get('id'))
                        # Update price if last update change
                        if not existed or existed['lastUpdated'] != crypto_currency['lastUpdated']:
                            price_data = crypto_currency.get('quotes')
                            for p in price_data:
                                p.update({
                                    'crypto_currency_id': crypto_currency.get('id'),
                                    'slug': crypto_currency.get('slug'),
                                    'symbol': crypto_currency.get('symbol')
                                })
                            price_coll.insert_many(price_data)

                        # Update info after update price
                        if not existed:
                            rs = crypto_currency_coll.insert_one(crypto_currency)
                            existed = crypto_currency.copy()
                            existed['_id'] = rs.inserted_id
                            coin_map[crypto_currency.get('id')] = existed
                        else:
                            if any(existed[i] != crypto_currency[i] for i in compare_infos):
                                crypto_currency_coll.replace_one({'_id': existed.get('_id')}, crypto_currency)
                max_number = int(data.get('totalCount'))
                _logger.info('Crawler %s/%s' % (number, max_number))
                retry = 0
            except Exception as e:
                _logger.error('Get error at number %s' % number)
                _logger.error(e)
                retry += 1
                if retry > 3:
                    number += 100

    sleep(1)
