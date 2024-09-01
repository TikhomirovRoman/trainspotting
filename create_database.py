import sqlite3

with open('base.db.sql', 'r') as f:
    sql = f.read()


def insert_states(cur):
    photo_types = [('journal',),
                   ('test',),
                   ('passline',)
                   ]
    sql = "INSERT INTO photo_type VALUES (NULL, ?)"
    try:
        cur.executemany(sql, photo_types)
    except Exception:
        print("Типы фото не добавлены")

def insert_statuses(cur):
    statuses = [
        ['ready_to_send'],
        ['error'],
        ['sent']
    ]
    try:
        cur.executemany("INSERT INTO status VALUES (NULL, ?)", statuses)
    except Exception:
        print("статусы не добавлены")


with sqlite3.connect("base.db") as con:
    cur = con.cursor()
    cur.executescript(sql)
    insert_states(cur)
    insert_statuses(cur)
