import logging
from datetime import datetime, date
from time import sleep

import pymongo

from services.database import postgresql_service
from services.mongo import crypto_currency_coll, price_coll

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-30s %(levelname)-6s %(message)s',
                    filemode='a')
_logger = logging.getLogger(__name__)

postgresql_service.create_crypto_currency_table()
postgresql_service.create_price_detail_table()


def datetime_converter(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except Exception:
        return None

def datetime_converter2(timeobj):
    try:
        return timeobj.strftime( "%Y-%m-%dT%H:%M:%S.%fZ")
    except Exception:
        return None

def bool_converter(input):
    if input == '0' or input == 0:
        return False
    return bool(input)

cc_convert_map = {
    'coinbase_id': ('id', None),
    'name': ('name', None),
    'slug': ('slug', None),
    'symbol': ('symbol', None),
    'tags': ('tags', None),
    'date_added': ('dateAdded', datetime_converter),
    'last_updated': ('lastUpdated', datetime_converter),
    'is_active': ('isActive', bool_converter),
    'circulating_supply': ('circulatingSupply', None),
    'total_supply': ('totalSupply', None),
    'max_supply': ('maxSupply', None),
    'cmc_rank': ('cmcRank', None),
    'market_pair_count': ('marketPairCount', None)
}

price_convert_map = {
    'crypto_currency_id': ('crypto_currency_id', None),
    'price': ('price', None),
    'last_updated': ('lastUpdated', datetime_converter),
    'turnover': ('turnover', None),
}

def convert_record(record_map, data):
    rs = {}
    for f1, f2 in record_map.items():
        field, converter = f2
        if converter:
            rs[f1] = converter(data.get(field))
        else:
            rs[f1] = data.get(field)
    return rs



# Update info 01
existed_cc = postgresql_service.select_data(table='crypto_currency', fields=['coinbase_id', 'name'], limit=20000)
existed_cc_ids = list(r['coinbase_id'] for r in existed_cc)

cc_update_list = []
cc_create_list = []
for cc_data in crypto_currency_coll.find({}):
    cc_id = cc_data.get('id')
    if cc_id:
        if cc_id not in existed_cc_ids:
            cc_create_list.append(convert_record(cc_convert_map, cc_data))
        else:
            cc_update_list.append(convert_record(cc_convert_map, cc_data))

if cc_create_list:
    _logger.info('Insert data for crypto currency')
    postgresql_service.insert_data('crypto_currency', cc_create_list)
if cc_update_list:
    _logger.info('Update data for crypto currency')
    postgresql_service.update_data('crypto_currency', 'coinbase_id', cc_update_list)

etl_interval = 60*60 #1hour
while True:
    price_find_obj = {'name': 'USD'}
    last_update = None
    existed_price_data = postgresql_service.select_data(table='price_detail', fields=['last_updated'], order='last_updated DESC', limit=1)
    if existed_price_data:
        last_update = existed_price_data[0]['last_updated']
        if last_update:
            price_find_obj['lastUpdated'] = {'$gte': datetime_converter2(last_update)}

    counter = 0
    price_data_list = []
    for price_record in price_coll.find(price_find_obj).sort([('lastUpdated', pymongo.ASCENDING)]):
        counter += 1
        price_data_list.append(convert_record(price_convert_map, price_record))
        if counter >= 1000:
            postgresql_service.insert_data('price_detail', price_data_list)
            price_data_list = []
            counter = 0

    if price_data_list:
        postgresql_service.insert_data('price_detail', price_data_list)

    sleep(etl_interval)