from binance import Client
import psycopg2
import config
import datetime


class BacktestRepository:

    def __get_connection(self):
        connection = psycopg2.connect(
            host=config.dbhost,
            database=config.dbname,
            port=config.dbport,
            user=config.dbuser,
            password=config.dbpassword)
        return connection

    def enrich_history_data(self, interval) -> object:
        table_name = "kline_{s}".format(s=interval)
        sql_insert = '''
insert into {table_name} (ticker_id, k_interval, open_price, high_price, low_price, close_price, volume)
values (1,%s, %s, %s, %s, %s, %s);
'''.format(table_name=table_name)
        print(sql_insert)
        client = Client(config.api_key, config.api_secret)
        symbol = 'BTCUSDT'
        conn = self.__get_connection()
        cur = conn.cursor()
        dbrows = []
        #date in mm-dd-yyyy format
        klines = client.get_historical_klines(symbol, interval, "11.01.2022 00:00:00",
                                              "11.30.2022 23:59:59")

        start_interval = 0
        open_p = 1
        high = 2
        low = 3
        close = 4
        volume = 5
        for kline in klines:
            print(kline[start_interval] / 1000)
            interval = datetime.datetime.fromtimestamp(kline[start_interval] / 1000)
            print(interval.strftime('%Y-%d-%m %H:%M:%S'))
            dbrows.append((interval, kline[open_p], kline[high], kline[low], kline[close], kline[volume]))

        cur.executemany(sql_insert,  dbrows)
        conn.commit()
        conn.close()

    def get_kline_period_id(self, period_descr):
        conn = self.__get_connection()
        cur = conn.cursor()
        cur.execute('select id from backtest_periods where period_descr=%s ', period_descr)
        period_id = cur.fetchone()
        conn.close()
        return period_id

    def save_strategy_results(self, results):

        conn = self.__get_connection()
        cur = conn.cursor()
        cur.executemany('''insert into backtests(launch_time,period_from,period_to,backtest_interval_id,start_sum,result_sum,kline_period,status, error_descr,launch_id)
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', results)
        conn.commit()
        conn.close()

    def get_backtest_interavals(self):
        conn = self.__get_connection()
        cur = conn.cursor()
        cur.execute('select id,period_descr from backtest_periods')
        periods = cur.fetchall()
        conn.close()
        return periods

    def get_backtest_period(self, interval):
        table_name = "kline_{s}".format(s=interval)
        conn = self.__get_connection()
        cur = conn.cursor()
        sql_insert = '''(select k_interval from {table_name} order by k_interval limit 1)
        union all
        (select k_interval from {table_name} order by k_interval desc limit 1)
        '''.format(table_name=table_name)
        cur.execute(sql_insert)
        intervals = cur.fetchall()
        print('intervals for backtesting from {} to {}'.format(intervals[0], intervals[1]))
        conn.close()
        return intervals


    def get_next_launch_id(self):
        conn = self.__get_connection()
        cur = conn.cursor()
        cur.execute('select nextval(\'public.backtests_launch_id_seq\')')
        return cur.fetchone()

#bt = BacktestRepository()
#bt.enrich_history_data(Client.KLINE_INTERVAL_1MINUTE)
