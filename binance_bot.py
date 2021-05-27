from datetime import datetime, timedelta

import websocket, json, pprint, numpy, talib, psycopg2
import config
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance import ThreadedWebsocketManager
from binance.enums import *
from glebza.tradeapp.src.tradebot.repository.binance_bot_repository import BinanceBotRepository as repository
from binance.exceptions import BinanceAPIException


def warm_up(ticker):
    print(ticker)
    client = Client(config.api_key, config.api_secret)
    volumes = []
    closes = []
    end_date = datetime.now()
    start_date = (end_date - timedelta(days=1)).strftime("%d/%m/%Y, %H:%M:%S")
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE, start_date,
                                          end_date.strftime("%d/%m/%Y, %H:%M:%S"))
    start_interval = 0
    open_p = 1
    high = 2
    low = 3
    close = 4
    volume = 5
    for kline in klines:
        volumes.append(float(kline[volume]))
        closes.append(float(kline[close]))
    return (closes, volumes)


symbol = 'BTCUSDT'
warm_data = warm_up(symbol)
volumes = warm_data[1]
close_prices = warm_data[0]
print(close_prices)
RSI_PERIOD = 14
RSI_OVERSOLD = 40
RSI_OVERBOUGHT = 70
in_position = False
order = None
start_cash = 200


def place_order(client, symbol, side, price, quantity):
    order = None
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=price
        )
        print(order)
    except Exception as e:
        print(e)
    return order


# start is required to initialise its internal loop
def handle_socket_message(msg):
    global in_position
    global order
    print(msg)
    candle = msg['k']
    is_candle_closed = candle['x']
    closed_price = candle['c']
    volume = candle['v']

    if order is not None:
        order = client.get_order(symbol=symbol, orderId=order.orderId)
        if order.status == ORDER_STATUS_FILLED:
            repository.update_order_status(order.orderId, ORDER_STATUS_FILLED)
            if order.side == SIDE_BUY:
                in_position = True
            else:
                order = None

    if is_candle_closed:
        close_prices.append(float(closed_price))
        volumes.append(float(volume))
        print(close_prices)
        np_closes = numpy.array(close_prices)
        np_volumes = numpy.array(volumes)
        rsi = talib.RSI(np_closes, RSI_PERIOD)
        obv = talib.OBV(np_closes, np_volumes)
        sma = talib.MA(np_closes, RSI_PERIOD)
        last_rsi = rsi[-1]
        print('last rsi {}'.format(last_rsi))
        if in_position:
            diff = (closed_price - order.price) / order.price
            if diff < float(-0.05) or rsi[0] > RSI_OVERBOUGHT and closed_price < sma[0]:
                print('sell!')
                order = place_order(client, symbol, Client.SIDE_SELL, closed_price * 0.99, order.executedQty)
                repository.save_order(order)
                in_position = False
        else:
            if last_rsi < RSI_OVERSOLD < rsi[0] and closed_price >= sma[0] \
                    and obv[-1] < obv[0] and close_prices[-1] < closed_price:
                qty = start_cash / closed_price
                print('buy! qty = {}'.format(qty))
                order = place_order(client, symbol, Client.SIDE_BUY, closed_price, float(qty))
                repository.save_order(order)


client = Client(config.api_key, config.api_secret)
print('start listening {}'.format(symbol))

# order = place_order(client, symbol, Client.SIDE_BUY,float(38900), 0.001684)
# {'symbol': 'BTCUSDT', 'orderId': 6183087675, 'orderListId': -1, 'clientOrderId': 'hzf8ut8BgIrCUh7Ey4kdgC', 'transactTime': 1622133593112, 'price': '38900.00000000', 'origQty': '0.00168400', 'executedQty': '0.00168400', 'cummulativeQuoteQty': '65.42289480', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'fills': [{'price': '38849.70000000', 'qty': '0.00168400', 'commission': '0.00000168', 'commissionAsset': 'BTC', 'tradeId': 875740731}]}
#twm = ThreadedWebsocketManager(api_key=config.api_key, api_secret=config.api_secret)
# twm.start()
# twm.start_kline_socket(callback=handle_socket_message, symbol=symbol, interval=KLINE_INTERVAL_1MINUTE)
