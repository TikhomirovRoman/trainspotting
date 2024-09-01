import sqlite3
import json
from datetime import datetime


DB = 'base.db'
READY_TO_SEND = 1
ERROR = 2
SENT = 3
IN_PROGRESS = 4


def save_engineer(cur, name, phone_number):
    sql = 'SELECT "id" FROM "engineer" WHERE "phone_number"=?'
    cur.execute(sql, (phone_number,))
    result = cur.fetchone()
    if result:
        return result[0]

    sql = 'INSERT INTO "engineer" VALUES (NULL, ?, ?);'
    cur.execute(sql, (name, phone_number))
    return cur.lastrowid


def save_route(cur, route, engineer, command_car, chat_id):
    date = datetime.now().strftime("%m-%d-%Y %H:%M")
    sql = f'REPLACE INTO "route" \
        VALUES(?,\'info\',\'None\',?,1,\'{date}\', \'None\',\
              {command_car}, {chat_id})'
    cur.execute(sql, (route, engineer))
    return cur.lastrowid


def save_cars(cur, cars):
    result = {}
    for car in cars:
        sql = 'SELECT "id" FROM "car" WHERE "name"=?'
        cur.execute(sql, (car,))
        car_id = cur.fetchone()[0]
        if not car_id:
            sql = 'INSERT INTO "car" VALUES (NULL, ?)'
            cur.execute(sql, (car,))
            car_id = cur.lastrowid
        result[car] = car_id
    return result


def save_photos(cur, route, cars, journal_photos, tests, passline):
    print(cars)
    if passline:
        cur.execute(f'INSERT INTO "photo" \
                    VALUES (NULL, \'{passline}\', {route},\'None\', 3)')
    if tests:
        sql = f'INSERT INTO "photo" \
                VALUES (NULL, ?, {route},\'None\', 2)'
        for photo in tests:
            cur.execute(sql, (photo,))
    for car_number, photo in journal_photos.items():
        car = cars[car_number]
        sql = f'INSERT INTO "photo" \
                VALUES (NULL, \'{photo}\', {route}, {car},1)'
        cur.execute(sql)


def save(data):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        try:
            engineer = save_engineer(cur, data['contact_name'],
                                     data['contact_tel'])
            cars = save_cars(cur, data['known_photos'])
            command_car = cars[data['command_car']]
            route = save_route(cur, data['route_id'], engineer, command_car, data['chat_id'])
            save_photos(cur, route, cars, data['known_photos'],
                        data['tests_photo'], data['passline_photo'])
            con.commit()
            return True
        except sqlite3.Error as e:
            if con:
                con.rollback()
            print(e)
            return False


def get_next_route():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
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


def save_result(msg, route_id):
    date = datetime.now().strftime("%m-%d-%Y %H:%M")
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        sql = f"UPDATE route SET \
            status = {SENT}, date_sent=\'{date}\', result=\'{msg}\'\
            WHERE route_id = {route_id}"
        cur.execute(sql)


if __name__ == '__main__':
    pass
    # with sqlite3.connect(DB) as con:
    #     con.execute(
    #         """UPDATE route SET status = 1 WHERE route_id=6396246"""
    #     )
