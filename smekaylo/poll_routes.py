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


# class routes_generator(object):
#     def __init__(self, start_pos, stop_pos):
#         self.start_pos = start_pos
#         self.stop_pos = stop_pos
#         self.current_route = start_pos
#         self.next_route = self.current_route
#         self.stop_flag = False

#     def __iter__(self):
#         return self

#     def __next__(self):
#         if not self.stop_flag and self.current_route < self.stop_pos:
#             self.current_route = self.next_route
#             self.next_route += 1
#             return self.current_route
#         raise StopIteration()


routes = iter([])
current_route = ''
results = {}


def validate_request(data):
    for route_id in data.split(','):
        if not re.match(r'\d{7}$', route_id.strip()):
            return False
    return True


@app.on_message(filters.incoming & filters.chat(ADMIN_CHAT))
async def trainspotting_chat(client, message):
    global routes
    global current_route
    print('current_route id: ', id(current_route))
    if message.text[:5] == '/poll':
        if not validate_request(message.text[5:]):
            await client.send_message(ADMIN_CHAT,
                                      'отправьте /poll и список рейсов через запятую')
        else:
            routes = iter(message.text[5:].split(','))
            await client.send_message(FPK_TOPRED_BOT, '/start')
    else:
        await client.sent_message(message.chat.id,
                                  'отправьте /poll и список рейсов через запятую')


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
    global current_route
    global results
    try:
        next_id = next(routes).strip()
        current_route = next_id
        print('current_route id: ', id(current_route))
        await asyncio.sleep(0.2)
        await client.send_message(FPK_TOPRED_BOT, next_id)
    except StopIteration:
        await client.send_message(ADMIN_CHAT, results[current_route],
                                  parse_mode=enums.ParseMode.HTML)


async def save_route(client, message):
    global results
    global current_route
    global routes
    route_name = re.findall(r'рейса: (\w+)', message.text)[0]
    departure_date = re.findall(
        r'Время отправки:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
        message.text)[0]
    date = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M')
    weekday = (week[date.weekday()])
    route_info = f'<b>{route_name}</b>\n{departure_date} <b>{weekday}</b>'
    print(route_info)
    results[current_route] = route_info
    database.save_info(route_info, departure_date[0:10],
                       route_name, current_route)
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
