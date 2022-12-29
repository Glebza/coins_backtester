import backtrader as bt
from glebza.tradeapp.src.backtests.strategies.OnBalanceVolume import OnBalanceVolume
from backtrader import Order


class MACDStrategy(bt.Strategy):
    params = (('period', 14),
              ('maperiod', 12),
              ('macd1', 12),
              ('macd2', 26),
              ('macdsig', 9),
              ('atrperiod', 2),  # ATR Period (standard)
              ('atrdist', 3.0),  # ATR distance for stop price
              ('dirperiod', 10),  # Lookback period to consider SMA trend direction

              )


    def __init__(self):

        self.plotinfo.plotyhlines = [0]
        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)

        bt.indicators.MACDHisto(self.macd.macd)

        # Cross of macd.macd and macd.signal
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal,plot=False)

        # To set the stop price
        self.atr = bt.indicators.ATR(self.data, period=self.p.atrperiod)

        self.rsi = bt.indicators.RSI(self.data, period=self.params.period,plot=False)
        self.obv = OnBalanceVolume(self.data)
        self.sma = bt.indicators.ExponentialMovingAverage(self.data, period=self.p.macd1, plotname='ema')
        self.sma = bt.indicators.ExponentialMovingAverage(self.data, period=self.p.macd2, plotname='ema26')
        # Control market trend
        self.smadir = self.sma - self.sma(-self.p.dirperiod)

    def nextstart(self):
        self.order = None

    def next(self):
        if not self.position:
            if (not self.order) and self.rsi[0] < 45 and self.mcross[0] > 0.0 and self.macd < 0:
                self.order = self.buy(size=1)
                pdist = self.atr[0] * self.p.atrdist
                self.pstop = self.data.close[0] - pdist
        else:
            if not self.order:
                pos = self.getposition()
                pos_len = len(pos)
                diff = 0
                pclose = self.data.close[0]
                pstop = self.pstop

                if pos_len > 0:
                    diff = self.data.close - pos.price
                   # print(' {} : (close {} -  prev{} )/ prev {}  = {}'
                    #      .format(self.data.datetime.datetime(), self.data.close[0], pos.price, pos.price, diff))

                if pos_len > 0 and diff >= 5:
                    print('close at {} with close {}'.format(self.data.datetime.datetime(), self.data.close[0]))
                    self.order = self.sell(size=-1, price=self.data.close[0], exectype=Order.Limit,)

                else:
                    pdist = self.atr[0] * self.p.atrdist
                    # Update only if greater than
                    self.pstop = max(pstop, pclose - pdist)

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
