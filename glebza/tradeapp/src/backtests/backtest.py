import csv, backtrader as bt
import config
import psycopg2
from glebza.tradeapp.src.backtests.strategies.RSIStrategy import RSIStrategy
from glebza.tradeapp.src.backtests.strategies.MACDStrategy import MACDStrategy

TIMEFRAME_MINUTES = 4


def create_data_file(ticker, time_from, time_to,kline_interval):
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    filename = '/Users/ruasyg4/PycharmProjects/BacktestApp/backtest_data.csv'
    f = open(filename, 'w')
    writer = csv.writer(f)
    start_interval = 0
    open_p = 1
    high = 2
    low = 3
    close = 4
    volume = 5
    cur.execute('''select id from coins where ticker = %s''', (ticker,))
    ticker_id = cur.fetchone()
    sql_select = '''select k_interval, open_price,high_price,low_price,close_price,volume
     from  kline_{kline_interval} where ticker_id = %s  and k_interval between %s and %s 
    '''.format(kline_interval=kline_interval)
    cur.execute(sql_select, (ticker_id, time_from, time_to,))
    klines = cur.fetchall()
    size = len(klines)
    for kline in klines:
        row = (
            kline[start_interval], kline[open_p], kline[high], kline[low], kline[close], kline[volume],
            float('NaN')
        )
        writer.writerow(row)
    # close the file
    f.close()
    return {'filename':filename,'size':size}


def do_backtest(ticker, time_from, time_to, start_cash,kline_interval, need_plot):
    print('start test. ticker {} from {} to {}'.format(ticker,time_from,time_to))
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(start_cash)
    file = create_data_file(ticker, time_from, time_to,kline_interval)
    if file['size'] == 0:
        raise RuntimeError('there is no data!')

    datas = bt.feeds.GenericCSVData(dataname=file['filename'], timeframe=TIMEFRAME_MINUTES)
    cerebro.adddata(datas)
    cerebro.addstrategy(MACDStrategy)
    cerebro.run()
    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - start_cash
    print(cerebro.broker.get_cash())
    print('Final Portfolio Value: ${}'.format(portvalue))
    print('P/L: ${}'.format(pnl))
    print('End test.')
    if need_plot:
        cerebro.plot(style='candlestick')

    return portvalue
