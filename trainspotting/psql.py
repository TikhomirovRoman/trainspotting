import psycopg2
import os
from psycopg2.extras import execute_values

DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('DB_HOST')


with open('trainspotting_db.sql', 'r') as f:
    sql = f.read()


def insert_types(cur):
    photo_types = [['journal'], ['test'], ['passline']]
    sql = "INSERT INTO photo_type(name) VALUES %s;"
    try:
        execute_values(cur, sql, photo_types)
        cur.execute('SELECT * FROM photo_type')
    except Exception as e:
        print(e)
        print("Типы фото не добавлены")


def insert_statuses(cur):
    statuses = [['ready_to_send'],
                ['error'],
                ['sent']
                ]
    try:
        execute_values(cur, "INSERT INTO status(name) VALUES %s", statuses)
    except Exception as e:
        print(e)
        print("статусы не добавлены")


conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        host=DB_HOST, password=DB_PASSWORD)

with conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        insert_types(cur)
        insert_statuses(cur)

conn.close()
