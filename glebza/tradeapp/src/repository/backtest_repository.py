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

    def enrich_history_data(self):
        client = Client(config.api_key, config.api_secret)
        symbol = 'BTCUSDT'
        conn = self.__get_connection()
        cur = conn.cursor()
        dbrows = []
        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE, "01.01.2021 03:00:00",
                                              "24.05.2021 23:59:59")

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

        cur.executemany('''
insert into minutes_kline_15 (ticker_id, k_interval, open_price, high_price, low_price, close_price, volume)
values (1,%s, %s, %s, %s, %s, %s);
''', dbrows)
        conn.commit()
        conn.close()

    def save_strategy_results(self, results):
        conn = self.__get_connection()
        cur = conn.cursor()
        cur.executemany('''insert into backtests(launch_time,period_from,period_to,backtest_interval_id,start_sum,result_sum,kline_period,status, error_descr)
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s)''', results)
        conn.commit()
        conn.close()

    def get_backtest_interavals(self):
        conn = self.__get_connection()
        cur = conn.cursor()
        cur.execute('select id,period_descr from backtest_periods')
        periods = cur.fetchall()
        conn.close()
        return periods

    def get_backtest_period(self):
        conn = self.__get_connection()
        cur = conn.cursor()
        cur.execute('''(select k_interval from minutes_kline_15 order by k_interval limit 1)
        union all
        (select k_interval from minutes_kline_15 order by k_interval desc limit 1)
        ''')
        intervals = cur.fetchall()
        print('intervals for backtesting from {} to {}'.format(intervals[0], intervals[1]))
        conn.close()
        return intervals


#bt = BacktestRepository()
#bt.enrich_history_data()
