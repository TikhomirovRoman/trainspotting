import psycopg2
import os

from datetime import datetime

DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_LOCAL = os.getenv('DB_PRODUCT')
DB_PRODUCT = os.getenv('DB_PRODUCT')
DEBUG = os.getenv("TRAINSPOTTING_DEBUG", default=False)
if DEBUG:
    DB_HOST = DB_LOCAL
else:
    DB_HOST = DB_PRODUCT

READY_TO_SEND = 1
ERROR = 2
SENT = 3
IN_PROGRESS = 4


def get_next_route():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_HOST, password=DB_PASSWORD)
    with conn:
        cur = conn.cursor()
        sql = """SELECT route.route_id, engineer.name, engineer.phone_number,
        route.chat_id, car.name
        FROM route 
        JOIN engineer ON engineer.id = route.engineer
        JOIN car ON car.id = route.command_car
        JOIN status ON status.id = route.status
        WHERE status.name = 'ready_to_send'
        LIMIT 1"""
        cur.execute(sql)
        result = cur.fetchone()
        data = {}
        if not result:
            return data
         
        data['command_car'] = result[4]
        data['route_id'] = str(result[0])
        data['chat_id'] = result[3]
        data['contact_name'] = result[1]
        data['contact_tel'] = str(result[2])
        data['report_status'] = 'ready_to_send'

        sql = f"SELECT car.name, photo.filename, photo_type.name\
        FROM photo\
        LEFT JOIN car ON car.id = photo.car\
        JOIN photo_type ON photo_type.id = photo.photo_type\
        WHERE photo.route = {data['route_id']}"
        cur.execute(sql)
        result = cur.fetchall()
        data['tests_photo'] = []
        data['known_photos'] = {}
        for line in result:
            if line[2] == 'journal':
                data['known_photos'][line[0]] = line[1]
            elif line[2] == 'passline':
                data['passline_photo'] = line[1]
            elif line[2] == 'test':
                data['tests_photo'].append(line[1])
    conn.close()
    return data


def save_info(info, departure_date, route_name, route_id):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_PRODUCT, password=DB_PASSWORD)
    with conn:
        cur = conn.cursor()

        cur.execute('SELECT * FROM route_name;')
        routes_cache = dict()
        for id, name in cur.fetchall():
            routes_cache[name] = id
        if route_name not in routes_cache:
            cur.execute("INSERT INTO route_name(route_name)\
                                VALUES (%s) RETURNING id;", (route_name,))
            route_name_id = cur.fetchone()
            routes_cache[route_name] = route_name_id
        else:
            route_name_id = routes_cache[route_name]

        sql = "UPDATE route SET info=%(info)s, departure_date=%(departure_date)s,\
               route_name=%(route_name_id)s\
               WHERE route_id=%(route_id)s;\
               INSERT INTO route (route_id, info, departure_date, route_name)\
               SELECT %(route_id)s, %(info)s,\
               %(departure_date)s, %(route_name_id)s\
               WHERE NOT EXISTS (SELECT 1 FROM route WHERE route_id=%(route_id)s);"
        try:
            cur.execute(
                sql,
                {'route_id': route_id,
                 'info': info,
                 'departure_date': departure_date,
                 'route_name_id': route_name_id}
                )
        except Exception as e:
            print(e)
            print(cur.query)
    conn.close()


def save_result(msg, route_id):
    date = datetime.now().strftime("%m-%d-%Y %H:%M")
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_HOST, password=DB_PASSWORD)
    with conn:
        cur = conn.cursor()
        sql = f"UPDATE route SET \
            status = {SENT}, date_sent=\'{date}\', result=\'{msg}\'\
            WHERE route_id = {route_id}"
        cur.execute(sql)
    conn.close()


if __name__ == '__main__':
    pass
    # conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
    #                         host=DB_HOST, password=DB_PASSWORD)
    # with conn:
    #     cur = conn.cursor()
    #     sql = """SELECT route_id, info FROM route"""
    #     cur.execute(sql)
    #     routes = cur.fetchall()        
    #     cur.execute('SELECT * FROM route_name;')
    #     routes_cache = dict()
    #     for id, route_name in cur.fetchall():
    #         routes_cache[route_name] = id
    #     for route_id, info in routes:
    #         route_name = re.search(r'<b>(.*?)</b>', info)
    #         if route_name:
    #             route_name = route_name.group(1)
    #             if route_name not in routes_cache:
    #                 cur.execute("INSERT INTO route_name(route_name)\
    #                             VALUES (%s) RETURNING id;", (route_name,))
    #                 route_name_id = cur.fetchone()
    #                 routes_cache[route_name] = route_name_id
    #             else:
    #                 route_name_id = routes_cache[route_name]
    #             cur.execute("UPDATE route SET route_name=(%s) WHERE route_id=(%s);", 
    #                         (route_name_id, route_id))
    #             print(route_name, route_id)
