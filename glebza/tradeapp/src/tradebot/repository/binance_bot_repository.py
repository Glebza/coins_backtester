import psycopg2
import config
from datetime import datetime


class BinanceBotRepository:

    def __get_connection(self):
        connection = psycopg2.connect(
            host=config.dbhost,
            database=config.dbname,
            port=config.dbport,
            user=config.dbuser,
            password=config.dbpassword)
        return connection

    def save_order(self, order):
        con = self.__get_connection()
        cur = con.cursor()
        cur.execute('select id from coins where ticker = %s', (order.symbol))
        ticker_id = cur.fetchone()
        transact_time = datetime.fromtimestamp(order.transacttime)
        cur.execute('''
        insert into orders (id
        ,ticker_id
        ,orderlistid
        ,clientorderid
        ,transacttime
        ,price
        ,origqty
        ,executedqty
        ,status
        ,type
        ,side)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (order.orderId
                                  , ticker_id
                                  , order.orderlistid
                                  , order.clientorderid
                                  , transact_time
                                  , order.price
                                  , order.origqty
                                  , order.executedqty
                                  , order.status
                                  , order.type
                                  , order.side
              ))
        con.commit()
        con.close()

    def update_order_status(self, order_id, status):
        con = self.__get_connection()
        cur = con.cursor()
        cur.execute('''
        update orders set status=%s 
        where id =%s
        ''', (status, order_id))
        con.commit()
        con.close()