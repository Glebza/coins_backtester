from glebza.tradeapp.src.backtest import do_backtest
from glebza.tradeapp.src.repository.backtest_repository import BacktestRepository
from datetime import datetime,  timedelta


def launch_backtest(launch_time, increment, interval_id, date_from, date_to, end_date, start_cash,need_plot):
    rows = []
    while date_to <= end_date:
        date_to += timedelta(days=increment)
        status = 'success'
        error_descr = None
        result_cash = 0
        try:
            result_cash = do_backtest(ticker, date_from, date_to, start_cash,need_plot)
        except Exception as e:
            status = 'error'
            error_descr = str(e)
            print(e)
        kline_period_15_minutes = 1
        result = (launch_time, date_from, date_to, interval_id, start_cash, result_cash, kline_period_15_minutes, status, error_descr)
        rows.append(result)
        date_from += timedelta(days=increment)
    return rows


br = BacktestRepository()
ticker = 'BTCUSDT'
start_cash = 100000
period = br.get_backtest_period()
# full periods for backtests
# start_date = period[0][0]
# end_date = period[1][0]
# intervals = br.get_backtest_interavals()
#custom periods
start_date = datetime(2018, 1, 29, 3, 0, 0)
end_date = datetime(2018, 2, 5, 3, 0, 0)
intervals = [(2,'other')]
launch_time = datetime.now()
for interval in intervals:
    interval_id = interval[0]
    date_from = start_date
    date_to = start_date
    if interval[1] == 'day':
        results = launch_backtest(launch_time, 1, interval_id, date_from, date_to, end_date, start_cash, False)
        br.save_strategy_results(results)
    if interval[1] == 'week':
        results = launch_backtest(launch_time, 7, interval_id, date_from, date_to, end_date, start_cash, False)
        br.save_strategy_results(results)
    if interval[1] == 'month':
        results = launch_backtest(launch_time, 30, interval_id, date_from, date_to, end_date, start_cash, False)
        br.save_strategy_results(results)
    if interval[1] == 'quart':
        results = launch_backtest(launch_time, 90, interval_id, date_from, date_to, end_date, start_cash, False)
        br.save_strategy_results(results)
    if interval[1] == 'half-year':
        results = launch_backtest(launch_time, 180, interval_id, date_from, date_to, end_date, start_cash, False)
        br.save_strategy_results(results)
    if interval[1] == 'year':
        results = launch_backtest(launch_time, 365, interval_id, date_from, date_to, end_date, start_cash, False)
        br.save_strategy_results(results)
    if interval[1] == 'other':
        results = launch_backtest(launch_time, 7, interval_id, date_from, date_to, end_date, start_cash, True)
        br.save_strategy_results(results)
