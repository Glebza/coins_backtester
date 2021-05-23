import csv, talib, websocket, backtrader as bt
import config
from glebza.tradeapp.src.strategies.OnBalanceVolume import OnBalanceVolume
from backtrader import Order
from binance import Client
import psycopg2


class RSIStrategy(bt.Strategy):
    params = (('period', 14),
              ('maperiod', 15),
              )

    def __init__(self):

        self.plotinfo.plotyhlines = [0]
        self.rsi = bt.indicators.RSI(self.data, period=self.params.period)
        self.obv = OnBalanceVolume(self.data)
        self.sma = bt.indicators.SimpleMovingAverage(self.data, period=self.params.maperiod, plotname='sma')

    def nextstart(self):
        self.order = None

    def next(self):

        # print("{}: Close cond: {}: sma cond: {}, obv cond: {} RSI: {}".format(
        #     self.data.datetime.datetime(),
        #     self.data.close[-1] < self.data.close[0],
        #     self.data.close[0] >= self.sma[0],
        #     self.obv.lines.obv[-1] < self.obv.lines.obv[0],
        #     self.rsi[0],
        # ))

        if not self.position:
            if (not self.order) and self.rsi[0] > 40 and self.rsi[-1] < 40 \
                    and self.data.close >= self.sma \
                    and (self.obv.lines.obv[-1] < self.obv.lines.obv[0] and self.data.close[-1] < self.data.close[0]):
                self.order = self.buy(size=1)

        else:
            if not self.order:
                pos = self.getposition()
                pos_len = len(pos)
                diff = 0
                if pos_len > 0:
                    diff = (self.data.close - pos.price) / pos.price
                    print(' {} : (close {} -  prev{} )/ prev {}  = {}'
                          .format(self.data.datetime.datetime(), self.data.close[0], pos.price, pos.price, diff))

                if diff < float(-0.05) or self.rsi > 70 and self.data.close < self.sma:
                    print('close at {} with close {}'.format(self.data.datetime.datetime(), self.data.close[0]))
                    self.order = self.sell(size=-1, price=self.data.close[0]*0.99, exectype=Order.Limit,)

    def log(self, txt, dt=None, doprint=False):
        dt = dt or self.data.datetime.datetime()
        # dt_object = datetime.fromtimestamp(dt)
        print('{0},{1}'.format(dt, txt))

    def notify_order(self, order):
        # 1. If order is submitted/accepted, do nothing
        if order.status in [order.Submitted, order.Accepted]:
           # print('order {} '.format(order.status))
            return
        # 2. If order is buy/sell executed, report price executed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: {0:8.2f}, Size: {1:8.2f} Cost: {2:8.2f}, Comm: {3:8.2f}'.format(
                    order.executed.price,
                    order.executed.size,
                    order.executed.value,
                    order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL EXECUTED, {0:8.2f}, Size: {1:8.2f} Cost: {2:8.2f}, Comm{3:8.2f}'.format(
                    order.executed.price,
                    order.executed.size,
                    order.executed.value,
                    order.executed.comm))

            self.bar_executed = len(self)  # when was trade executed
        # 3. If order is canceled/margin/rejected, report order canceled
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def stop(self):
        self.log('MA Period: {0:8.2f} Ending Value: {1:8.2f}'.format(
            self.params.maperiod,
            self.broker.getvalue()),
            doprint=True)
