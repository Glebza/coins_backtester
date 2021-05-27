import backtrader as bt


class OnBalanceVolume(bt.Indicator):
    alias = 'OBV'
    lines = ('obv',)

    plotlines = dict(
        obv=dict(
            _name='OBV',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):
        # Plot a horizontal Line
        self.plotinfo.plotyhlines = [0]

    def nextstart(self):
        # We need to use next start to provide the initial value. This is because
        # we do not have a previous value for the first calcuation. These are
        # known as seed values.

        # Create some aliases
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = v[0]
            obv[-1] = 0
        else:
            if c[0] < c[-1]:
                obv[0] = -v[0]
                obv[-1] = 0
            else:
                obv[0] = 0
                obv[-1] = 0

    def next(self):

        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv
        if c[0] > c[-1]:
            obv[0] = obv[-1] + v[0]
        else:
            if c[0] < c[-1]:
                obv[0] = obv[-1] - v[0]
            else:
                obv[0] = obv[-1]
