import psycopg2 as psycopg2

class PostgresqlService(object):
    _connection = False
    _cr = False

    def __init__(self):
        self._connection = psycopg2.connect(dbname="cc_crawler", user="postgres", password="qweqwe123",
                                            host='postgresql')
        self._cr = self._connection.cursor()

    def check_table_exists(self, table_name):
        query = f"SELECT to_regclass('public.{table_name}');"
        self._cr.execute(query)
        rs = self._cr.fetchone()
        return bool(rs[0])

    def create_crypto_currency_table(self):
        table_existed = self.check_table_exists('crypto_currency')
        if not table_existed:
            query = """
            CREATE TABLE IF NOT EXISTS crypto_currency (
                id serial
                    CONSTRAINT crypto_currency_pk
                        PRIMARY KEY,
                coinbase_id INT,
                name VARCHAR,
                slug VARCHAR,
                symbol VARCHAR,
                tags VARCHAR[],
                date_added TIMESTAMP,
                last_updated TIMESTAMP,
                is_active BOOLEAN,
                circulating_supply BIGINT,
                total_supply BIGINT,
                max_supply BIGINT,
                cmc_rank INT,
                market_pair_count INT,
                ath FLOAT,
                atl FLOAT,
                high_24h FLOAT,
                low_24h FLOAT
            );
            """
            self._cr.execute(query)
            self._connection.commit()

            query2 = """
                CREATE INDEX crypto_currency_coinbase_id_index
                ON crypto_currency (coinbase_id);
                CREATE INDEX crypto_currency_name_index
                ON crypto_currency (name);
                CREATE INDEX crypto_currency_slug_index
                ON crypto_currency (slug);
            """
            self._cr.execute(query2)
            self._connection.commit()

    def create_price_detail_table(self):
        table_existed = self.check_table_exists('price_detail')
        if not table_existed:
            query = """
            CREATE TABLE IF NOT EXISTS price_detail (
                id bigserial
                    CONSTRAINT price_detail_pk
                        PRIMARY KEY,
                crypto_currency_id INT,
                price FLOAT,
                last_updated TIMESTAMP,
                turnover FLOAT 
            );
            """
            self._cr.execute(query)
            self._connection.commit()

            query2 = """
                CREATE INDEX price_detail_crypto_currency_id_index
                ON price_detail (crypto_currency_id);
                CREATE INDEX price_detail_last_updated_name_index
                ON price_detail (last_updated);
            """
            self._cr.execute(query2)
            self._connection.commit()

    def select_data(self, table, fields, where="", order=None, limit=100, offset=0):
        fields_str = ','.join(fields)
        order_str = f'ORDER BY {order}' if order else ''
        limit_str = f'LIMIT {limit}' if limit else ''
        offset_str = f'OFFSET {offset}' if offset else ''
        query = f"SELECT {fields_str} FROM {table} {where} {order_str} {limit_str} {offset_str}"

        self._cr.execute(query)
        records = []
        for rs in self._cr.fetchall():
            record = {}
            for index, field in enumerate(fields):
                record[field] = rs[index]
            records.append(record)
        return records


    def update_data(self, table, where_key, datalist):
        if datalist:
            col_list = list(datalist[0].keys())
            col_list_str = ','.join(col_list)
            insert_str = '(' + ','.join(list(f'%({c})s' for c in col_list)) + ')'
            insert_str += f' WHERE {where_key} = %({where_key})s;'
            query_list = []
            for data in datalist:
                args_str = self._cr.mogrify(insert_str, data).decode('utf-8')
                query_list.append(f"UPDATE {table} SET ({col_list_str}) = {args_str}")
            self._cr.execute('\n'.join(query_list))
            self._connection.commit()

    def insert_data(self, table, datalist):
        if datalist:
            col_list = list(datalist[0].keys())
            col_list_str = ','.join(col_list)
            insert_str = '(' + ','.join(list(f'%({c})s' for c in col_list)) + ')'
            args_list = []
            for data in datalist:
                args_list.append(self._cr.mogrify(insert_str, data))
            args_str = b','.join(args_list).decode('utf-8')
            query = f"INSERT INTO {table} ({col_list_str}) VALUES " + args_str
            self._cr.execute(query)
            self._connection.commit()

postgresql_service = PostgresqlService()
