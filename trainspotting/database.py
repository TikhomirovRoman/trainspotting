import psycopg2
from datetime import datetime
from config import DB_NAME, DB_HOST, DB_PASSWORD, DB_USER

READY_TO_SEND = 1
ERROR = 2
SENT = 3
IN_PROGRESS = 4


def get_route(route_id):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_HOST, password=DB_PASSWORD)
    sql = 'SELECT info, result FROM route WHERE route_id = %s;'
    with conn:
        cur = conn.cursor()
        cur.execute(sql, (route_id,))
        result = cur.fetchone()
        if result:
            return result[0]


def get_routes(date):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_HOST, password=DB_PASSWORD)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT route.route_id, route_name.route_name, \
                    route.status FROM route\
                    JOIN route_name ON route.route_name=route_name.id\
                    WHERE route.departure_date = TO_DATE(%s, 'DD.MM.YYYY');",
                    (date,))
        return (cur.fetchall())


def get_next_route():
    with psycopg2.connect(
            dbname=DB_NAME, user=DB_USER,
            host=DB_HOST, password=DB_PASSWORD) as conn:
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
    return data


def save_engineer(cur, name, phone_number):
    sql = 'SELECT "id" FROM "engineer" WHERE "phone_number"=%s;'
    cur.execute(sql, (phone_number,))
    result = cur.fetchone()
    if result:
        return result[0]

    sql = 'INSERT INTO engineer(name, phone_number) VALUES (%s, %s);'
    cur.execute(sql, (name, phone_number))
    return cur.fetchone()[0]


def save_route(cur, route, engineer, command_car, chat_id):
    date = datetime.now().strftime("%m-%d-%Y %H:%M")
    sql = 'INSERT INTO route(route_id, info, result, engineer, status,\
        date_created, date_sent, command_car, chat_id) \
        VALUES(%(route_id)s,\'info\',\'None\',%(engineer)s,1,%(date_created)s,\'None\',\
               %(command_car)s, %(chat_id)s)\
        ON CONFLICT (route_id) DO UPDATE SET \
        date_created = %(date_created)s, status = 1, chat_id = %(chat_id)s, \
        engineer=%(engineer)s, command_car=%(command_car)s;'
    cur.execute(sql,
                {'route_id': route, 'engineer': engineer,
                 'date_created': date, 'command_car': command_car,
                 'chat_id': chat_id})
    return


def save_cars(cur, cars):
    result = {}
    for car in cars:
        sql = 'SELECT "id" FROM "car" WHERE "name"=%s;'
        cur.execute(sql, (car,))
        car_id = cur.fetchone()
        if car_id is not None:
            result[car] = car_id[0]
        else:
            sql = "INSERT INTO car(name) VALUES (%s) RETURNING id;"
            cur.execute(sql, (car,))
            car_id = cur.fetchone()[0]
            result[car] = car_id
    return result


def save_photos(cur, route, cars, journal_photos, tests, passline):
    if passline:
        cur.execute('INSERT INTO photo(filename, route, photo_type) \
                    VALUES (%s, %s, 3);', [passline, route])
    if tests:
        sql = 'INSERT INTO photo(filename, route, photo_type) \
                VALUES (%s, %s, 2);'
        for photo in tests:
            cur.execute(sql, (photo, route))
    for car_number, photo in journal_photos.items():
        car = cars[car_number]
        sql = 'INSERT INTO photo(filename, route, car, photo_type) \
                VALUES (%s, %s, %s, 1);'
        cur.execute(sql, [photo, route, car])


def save(data):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_HOST, password=DB_PASSWORD)
    with conn:
        with conn.cursor() as cur:
            try:
                engineer = save_engineer(cur, data['contact_name'],
                                         data['contact_tel'])
                print('engineer saved')
                cars = save_cars(cur, data['known_photos'])
                print('cars saved')
                command_car = cars[data['command_car']]
                save_route(cur, data['route_id'],
                           engineer, command_car, data['chat_id'])
                print('route saved')
                save_photos(cur, data['route_id'], cars, data['known_photos'],
                            data['tests_photo'], data['passline_photo'])
                print('photos saved')
                return True
            except psycopg2.Error as e:
                print('DB ERROR')
                print(e)
                print(type(e))
                return False


if __name__ == '__main__':

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            host=DB_HOST, password=DB_PASSWORD)

    with conn:
        with conn.cursor() as cur:
            save_cars(cur, ('004-21513',))
