import websocket, json, pprint, numpy, talib, psycopg2
import config
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance import ThreadedWebsocketManager
from binance.enums import *
from binance.exceptions import BinanceAPIException


def enrich_close_prices(ticker):
    print(ticker)
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    cur.execute('select id from coins where ticker=%s', (ticker,))
    ticker_id = cur.fetchone()
    cur.execute('select close_price from minute_klines where ticker_id = %s', (ticker_id,))
    prices = cur.fetchall()
    result = []
    for price in prices:
        result.append(price[0])
    return result


def get_historical_data():
    global close
    dbklines = []
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "1 May, 2021", "20 May, 2021")
    start_interval = 0
    open_p = 1
    high = 2
    low = 3
    close = 4
    value = 5
    for kline in klines:
        dbklines.append((kline[start_interval], kline[open_p], kline[high], kline[low], kline[close], kline[value]))
    print(dbklines)
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    cur.executemany('''
insert into minute_klines (ticker_id, k_interval, open_price, high_price, low_price, close_price, k_value)
values (1,%s, %s, %s, %s, %s, %s);
''', dbklines)
    conn.commit()


symbol = 'BTCUSDT'
close_prices = enrich_close_prices(symbol)
print(close_prices)
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
in_position = False


def place_order(client, symbol, side, price, quantity):
    try:
        order = client.create_test_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity,
            )
        print(order)
        return True
    except Exception as e:
        print(e)
        return False


# start is required to initialise its internal loop
def handle_socket_message(msg):
    global in_position
    candle = msg['k']
    is_candle_closed = candle['x']
    closed_price = candle['c']

    if is_candle_closed:
        close_prices.append(float(closed_price))
        # print(candle)

        if len(close_prices) > RSI_PERIOD:
            np_closes = numpy.array(close_prices)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            # print('all rsis calculated so far  {}'.format(rsi))
            last_rsi = rsi[-1]
            print('last rsi {}'.format(last_rsi))
            if last_rsi > RSI_OVERBOUGHT:
                if not in_position:
                    print('it is overbought, but we dont own it. nothing to do ')
                else:
                    print('sell!')
                    is_succeeded = place_order(client, symbol, Client.SIDE_SELL,closed_price, float(0.001))
                    if is_succeeded:
                        in_position = False

            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print('it is oversold, but we already own it. nothing to do ')
                else:
                    print('buy!')
                    is_succeeded = place_order(client, symbol, Client.SIDE_BUY,closed_price, float(0.001))
                    if is_succeeded:
                        in_position = True


client = Client(config.api_key, config.api_secret)
# get_historical_data()
print('start listening {}'.format(symbol))

place_order(client, symbol, Client.SIDE_BUY,38336.2, 0.001)
fees = client.get_trade_fee(symbol='BTCUSDT')
print(fees)
#twm = ThreadedWebsocketManager(api_key=config.api_key, api_secret=config.api_secret)
#twm.start()
#twm.start_kline_socket(callback=handle_socket_message, symbol=symbol, interval=KLINE_INTERVAL_1MINUTE)
