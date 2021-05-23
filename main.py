from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse

import config
import psycopg2
import datetime
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get('/')
def index(request: Request):
    stock_filter = request.query_params.get('filter', False)
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    if stock_filter == 'new_intraday_highs':

        cur.execute("""
                   SELECT id,ticker, name,primaryExch, max(close),date_from FROM stocks s 
                   join stock_price sp on s.id = sp.stock_id
                   where date_from = %s
                   group by id
                   order by ticker
               """, (datetime.strptime('2021-05-05', '%Y-%m-%d'),))
    else:
        cur.execute("""
            SELECT ticker, name,primaryExch FROM stocks
        """)
    stocks = cur.fetchall()

    return templates.TemplateResponse("index.html", {"request": request, "stocks": stocks})


@app.get('/stock/{ticker}')
def stock(request: Request, ticker):
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    cur.execute(""" select id,ticker,name,primaryexch from stocks where ticker = %s
       """, (ticker,))
    selected_stock = cur.fetchall()
    print(selected_stock[0][0])
    selected_stock_data = {
        'id': selected_stock[0][0],
        'ticker': selected_stock[0][1],
        'name': selected_stock[0][2],
        'exchange': selected_stock[0][3]
    }
    cur.execute('''
    select id,strategy_name from strategy
    ''')
    strategies = cur.fetchall()
    cur.execute('''
    select * from stock_price where stock_id= %s
    ''', (selected_stock_data['id'],))
    prices = cur.fetchall()
    cur.close()
    conn.close()
    return templates.TemplateResponse("stock.html",
                                      {"request": request,
                                       "stock": selected_stock_data,
                                       "prices": prices,
                                       'strategies': strategies})


@app.post('/strategy')
def apply_strategy(strategy_id: int  = Form(...), stock_id: int = Form(...)):
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    cur.execute('''insert into stock_strategy (stock_id,strategy_id) values(%s,%s)''',(stock_id,strategy_id,))
    conn.commit()
    return RedirectResponse(url=f'/strategy/{strategy_id}', status_code=303)


@app.get('/strategy/{strategy_id}')
def get_strategy(Request):
    conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
    cur = conn.cursor()
    cur.execute('''select id,ticker from stocks''')
    stocks = cur.fetchall()
    

    return templates.TemplateResponse("strategy.html",
                                      {"request": request,
                                       "strategies": strategies,
                                       'ticker':stocks.ticker})