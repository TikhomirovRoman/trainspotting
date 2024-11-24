import datetime
import os
import re
from pyrogram import Client, filters, enums
import asyncio
import database

week = ('понедельник', 'вторник',
        'среда', 'четверг', 'пятница',
        'суббота', 'воскресенье')

api_hash = os.getenv('api_hash')
api_id = os.getenv('api_id')

SMEKAYLO_PHONE = os.getenv('SMEKAYLO_PHONE')
SMEKAYLO_NAME = os.getenv('SMEKAYLO_NAME')

ADMIN_CHAT = int(os.getenv('ADMIN_CHAT'))
FPK_TOPRED_BOT = 6234691100
TRAINSPOTTING = 7262275274
print(datetime.datetime.now())

app = Client("my_account", api_id=api_id, api_hash=api_hash)


class routes_generator(object):
    def __init__(self, start_pos, stop_pos):
        self.start_pos = start_pos
        self.stop_pos = stop_pos
        self.current_route = start_pos
        self.stop_flag = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self.stop_flag and self.current_route <= self.stop_pos:
            self.current_route += 1
            return self.current_route
        raise StopIteration()


routes = iter(routes_generator(1000000, 1000001))
results = {}


@app.on_message(filters.incoming & filters.chat(ADMIN_CHAT))
async def trainspotting_chat(client, message):
    global routes
    if message.text[:5] == '/poll':
        pool = re.findall(r'\d{7}', message.text)
        if len(pool) != 2:
            await client.send_message(ADMIN_CHAT,
                                      'укажите диапазон в формате /poll 1234567 7654321')
        else:
            routes = iter(routes_generator(int(pool[0]), int(pool[1])))
            await client.send_message(FPK_TOPRED_BOT, '/start')


def parse_message(message):
    schema = {
        'Авторизация': 'auth request',
        'Выбор рейса': 'route_id request',
        'Главное меню': 'route info',
        'Предрейсовое техническое обслуживание': 'to_pred_in_process',
        'Несуществующий ID рейса': 'unknown'
    }
    try:
        msg = message.text.split('\n')
        return schema[msg[0]]
    except Exception as e:
        print(e)


async def send_contact(client, message):
    await client.send_contact(FPK_TOPRED_BOT,
                              SMEKAYLO_PHONE,
                              SMEKAYLO_NAME)


async def send_id(client, message):
    global routes
    global results
    try:
        next_id = next(routes)
        await asyncio.sleep(0.2)
        await client.send_message(FPK_TOPRED_BOT, next_id)
    except StopIteration:
        await client.send_message(ADMIN_CHAT, results[routes.current_route],
                                  parse_mode=enums.ParseMode.HTML)


async def save_route(client, message):
    global results
    global routes
    route_name = re.findall(r'рейса: (\w+)', message.text)[0]
    departure_date = re.findall(
        r'Время отправки:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
        message.text)[0]
    date = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M')
    weekday = (week[date.weekday()])
    if departure_date[0:10] == '2024-11-01':
        routes.stop_flag = True
    route_info = f'<b>{route_name}</b>\n{departure_date} <b>{weekday}</b>'
    print(routes.current_route, route_info)
    results[routes.current_route] = route_info
    database.save_info(route_info, departure_date[0:10],
                       route_name, routes.current_route)
    await client.send_message(FPK_TOPRED_BOT,
                              'Предрейсовое техническое обслуживание')


async def select_another_route(client, message):
    await client.send_message(FPK_TOPRED_BOT,
                              'Выбрать другой рейс')


async def log_message(client, message):
    pass

schema = {
    'auth request': send_contact,
    'route_id request': send_id,
    'route info': save_route,
    'to_pred_in_process': select_another_route,
    'unknown': log_message
}


@app.on_message(filters.incoming & filters.chat(FPK_TOPRED_BOT))
async def fpk_topred_chat(client, message):
    await schema[parse_message(message)](client, message)


app.run()
