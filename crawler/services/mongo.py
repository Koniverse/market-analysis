import pymongo
from pymongo import MongoClient

mongo_client = MongoClient(host='mongo', port=27017, username='mongo', password='qweqwe123')
cdm_crypto_currency_data = mongo_client['cdm_crypto_currency_data']

if 'crypto_currency' not in cdm_crypto_currency_data.list_collection_names():
    crypto_currency_coll = cdm_crypto_currency_data['crypto_currency']
    crypto_currency_coll.create_index([('id', pymongo.ASCENDING),('name', pymongo.ASCENDING), ('slug', pymongo.ASCENDING), ('symbol', pymongo.ASCENDING)])

crypto_currency_coll = cdm_crypto_currency_data['crypto_currency']

if 'price_detail' not in cdm_crypto_currency_data.list_collection_names():
    price_col = cdm_crypto_currency_data['price_detail']
    price_col.create_index([('name', pymongo.ASCENDING), ('crypto_currency_id', pymongo.ASCENDING), ('lastUpdated', pymongo.DESCENDING), ('name', pymongo.ASCENDING), ('slug', pymongo.ASCENDING), ('symbol', pymongo.ASCENDING)])

price_coll = cdm_crypto_currency_data['price_detail']