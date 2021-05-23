import psycopg2

conn = psycopg2.connect(
        host=config.dbhost,
        database=config.dbname,
        port=config.dbport,
        user=config.dbuser,
        password=config.dbpassword)
cur = conn.cursor()

cur.execute('''
create table strategy (
id serial primary key,
strategy_name varchar
) 
''')
cur.execute('''
create table stock_strategy (
id serial primary key,
stock_id integer  references stocks(id), 
strategy_id integer references strategy(id)

) 
''')

cur.execute('''
create table coins (
id serial primary key,
ticker varchar
) 
''')

cur.execute('''
create table minute_klines (
id serial primary key,
ticker_id integer references coins(id),
interval timestamp,
open_price numeric,
high_price numeric,
low_price numeric,
close_price numeric,
value numeric
) 
''')

strategies = ['opening_range_breakout','opening_range_breakdown']

for strategy in strategies:
        cur.execute('''insert into strategy (strategy_name) values(%s)''',(strategy,))
