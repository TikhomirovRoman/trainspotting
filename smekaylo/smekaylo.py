# from settings import api_hash, api_id
from pyrogram import Client, filters
import asyncio
import os
import logging
from database import get_next_route, save_result

api_hash = os.getenv('api_hash')
api_id = os.getenv('api_id')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename="py_log.log",
    filemode="w",
    )

FPK_TOPRED_BOT = 6234691100
TRAINSPOTTING = 7262275274

PHOTOS_PATH = 'photos'


def update_data():
    data = get_next_route()
    if data:
        data['cars_iterator'] = iter(data['known_photos'])
        data['extra_photos_iterator'] = iter(data['tests_photo'])
    print(data)
    return data


data = update_data()
# data = {}
logging.info('Smekaylo started')
if data:
    logging.info(f'get data from DB {data}')


app = Client("my_account", api_id=api_id, api_hash=api_hash)


async def send_contact(client, message):
    logging.info('get request to authorize')
    global data
    if data and data['report_status'] == 'ready_to_send':
        logging.info(f'there is pending route {data["route_id"]}')
        data['report_status'] = 'sending_in_progress'
        await client.send_contact(FPK_TOPRED_BOT,
                                  data['contact_tel'],
                                  data['contact_name'])
        logging.info('contact to auth was sent')
    else:
        logging.info('there is no pending route or it is in progress')


async def send_route(client, message):
    global data
    if data['report_status'] == 'sent':
        logging.info("prev route was sent, requesting for next")
        data = update_data()
        if data:
            logging.info('get next route, send "/start" command')
            data['report_status'] == 'sending_in_progress'
            await client.send_message(FPK_TOPRED_BOT, "/start")
        return
    if data['report_status'] == 'sending_in_progress':
        logging.info('current route sending is in progress')
        logging.info(f'sending route_id {data["route_id"]}')
        await client.send_message(FPK_TOPRED_BOT, data['route_id'])


async def send_start_topred(client, message):
    data['route_info'] = message.text
    logging.info(f'get route info: {message.text}')
    logging.info('choosing to start TO_PRED')
    await client.send_message(FPK_TOPRED_BOT,
                              'Предрейсовое техническое обслуживание')


async def analize_trainset(client, message):
    logging.info(f'getting next car from data')
    data['current_trainset'] = message.text
    try:
        data['next_car'] = next(data['cars_iterator'])
        logging.info('got next car from trainset')
        await client.send_message(FPK_TOPRED_BOT,
                                  'Добавить вагон')
    except StopIteration:
        logging.info('no next car in current trainset')
        await client.send_message(FPK_TOPRED_BOT,
                                  'Отправить диспетчеру')
        data['next_car'] = ''


async def send_car_number(client, message):
    if 'next_car' not in data:
        data['next_car'] = next(data['cars_iterator'])
    logging.info(f'sending next car number: {data["next_car"]}')
    await client.send_message(FPK_TOPRED_BOT,
                              data['next_car'])


async def send_photo(client, message):
    logging.info(f'sending photo for current car')
    await client.send_photo(
        FPK_TOPRED_BOT,
        f'{PHOTOS_PATH}/{data["known_photos"][data["next_car"]]}')


async def send_yes(client, message):
    logging.info('sending YES')
    await client.send_message(FPK_TOPRED_BOT,
                              'Да')


async def send_extra_photo(client, message):
    logging.info('got request to add extra photos')
    if len(message.text) <= 50:
        return
    if data['next_car'] == data['command_car']:
        logging.info(f'current car is command_car: {data["command_car"]}')
        try:
            await client.send_photo(
                FPK_TOPRED_BOT,
                f'{PHOTOS_PATH}/{next(data["extra_photos_iterator"])}')
            logging.info('send extra photo')
            return
        except StopIteration:
            logging.info('there are no next extra photos in data')
            pass
    await client.send_message(FPK_TOPRED_BOT,
                              '.')
    logging.info('"." was sent to jump over')


async def send_comment(client, message):
    logging.info('comment sent')
    await client.send_message(FPK_TOPRED_BOT,
                              'Без замечаний')


async def send_final_comment(client, message):
    global data
    logging.info('final command was sent')
    await client.send_message(FPK_TOPRED_BOT,
                              'Без замечаний')
    data['report_status'] = 'sent'


async def send_add_car(client, message):
    logging.info('sending "add car" command')
    await client.send_message(FPK_TOPRED_BOT,
                              'Добавить вагон')


async def send_passline(client, message):
    logging.info('sending passline photo')
    await client.send_photo(FPK_TOPRED_BOT,
                            f'{PHOTOS_PATH}/{data["passline_photo"]}')


async def do_nothing(client, message):
    logging.info('nothing to do')
    pass


async def stop_report(client, message):
    msg = str(data['route_id']) + '\n' + \
        data['route_info'] + '\n' + \
        data['current_trainset']
    logging.info('sending report to TRAINSPOTTING bot')
    await client.send_message(TRAINSPOTTING, msg)
    data['report_status'] = 'sent'
    logging.info('saving data to database')
    save_result(msg, data['route_id'])


schema = {
    'Авторизация  Пожалуйста авторизуйтесь             ': send_contact,
    "Выбор рейса  Укажите ID рейса:                    ": send_route,
    "Главное меню  Данный бот поможет провести Вам Пред": send_start_topred,
    "Предрейсовое техническое обслуживание  Добавьте ва": send_add_car,
    "Выбор вагона  Формат: XXX-XXXXX (X - любая цифра о": send_car_number,
    "Фотография журнала ВУ-8  Проведите Предрейсовое те": send_photo,
    "Предрейсовое техническое обслуживание   Оборудован": send_yes,
    'Комментарий по журналу ВУ-8  СВНР - IP адрес напис': send_comment,
    "Загрузка дополнительный фотографий  Пришлите допол": send_extra_photo,
    'Обработка комментария  Ваш комментарий сохранен.  ': do_nothing,
    'Обработка ответа  Ваш ответ сохранен.             ': do_nothing,
    'Фотография акта проверки портала "Попутчик"  Прило': send_passline,
    "Обработка изображения  Ваша фотография сохранена. ": send_extra_photo,
    "Комментарий по журналу ВУ-8  Напишите Ваш коммента": send_comment,
    "Предрейсовое техническое обслуживание  ❌ - по ваго": analize_trainset,
    "Предрейсовое техническое обслуживание  Напишите за": send_final_comment,
    "Предрейсовое техническое обслуживание завершено  Б": stop_report
}


@app.on_message(filters.incoming & filters.chat(FPK_TOPRED_BOT))
async def fpk_topred_chat(client, message):
    logging.info('got answer from to_pred_bot')
    await asyncio.sleep(0.5)
    reply = message.text.replace('\n', ' ')[0:50]
    reply += ' '*(50-len(reply))
    try:
        await schema[reply](client, message)
    except KeyError:
        pass


@app.on_message(filters.incoming & filters.chat(TRAINSPOTTING))
async def trainspotting(client, message):
    logging.info('got message from Trainspotting bot')
    global data
    if message.text == '/send_report':
        logging.info('SEND REPORT handler')

        if not data or not data['report_status'] == 'sending_in_progress':
            data = update_data()
            await asyncio.sleep(0.5)
            logging.info('sending /start command to to_pred_bot')
            await client.send_message(FPK_TOPRED_BOT, '/start')
        else:
            logging.info('got /send_report while in progress')

app.run()
