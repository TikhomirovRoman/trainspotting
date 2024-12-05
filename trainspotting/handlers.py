import uuid
import database
import re
from datetime import datetime
from telegram import (Update, ReplyKeyboardMarkup, constants,
                      InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton)
from telegram.ext import (CallbackQueryHandler, ContextTypes, CommandHandler,
                          MessageHandler, filters)
from config import PHOTOS_PATH, SMEKAYLO_CHAT


buttons = ReplyKeyboardMarkup([['/identify', '/show', '/send']],
                              resize_keyboard=True)


async def show(update, context):
    route_id = context.user_data['route_id']
    unknown = len(context.user_data['unknown_photos'])
    known = '\n' + '\n'.join(list(context.user_data['known_photos'].keys()))
    commander = context.user_data['command_car']
    tests = len(context.user_data['tests_photo'])
    passline = context.user_data['passline_photo']

    await update.message.reply_text(
        f'Рейс: {route_id}\n'
        f'Нераспознано: {unknown} шт.\n'
        f'Добавлены вагоны ({len(context.user_data["known_photos"].keys())}'
        f' шт.): {known}\n'
        f'Штаб: {commander}\n'
        f'Тесты: {tests}\n'
        f'Попутчик: {bool(passline)}\n'
        )


async def send_route_info(update, context, route_id):
    context.user_data['route_id'] = route_id
    route = database.get_route(route_id)
    if route:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=route,
                                       parse_mode=constants.ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Новый рейс')
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Номер рейса: {route_id},'
        )
    await ask_photo(update, context)


def format_car_number(car_number):
    if len(car_number) == 8:
        car_number = car_number[:3] + '-' + car_number[3:]
    return car_number


def save_car(car_number, context):
    photo = context.user_data['unknown_photos'][-1]
    known_photos = context.user_data['known_photos']
    known_photos[car_number] = photo
    context.user_data['unknown_photos'].pop()


def save_command_car(car_number, context):
    if context.user_data.get('current_car_is_COMMAND', False):
        context.user_data['command_car'] = car_number
        context.user_data['current_car_is_COMMAND'] = False
    return True


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(file_id)
    file_name = str(uuid.uuid4()) + '.jpg'
    await new_file.download_to_drive(f'./{PHOTOS_PATH}/{file_name}')
    context.user_data.setdefault('unknown_photos', []).append(file_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f'фото сохранено ('
            f'{len(context.user_data["unknown_photos"])} шт.)'
            ),
        reply_markup=buttons)
    context.user_data['current_state'] = 'photo'
    return 'photo'


async def identify(update, context):
    count = len(context.user_data.get('unknown_photos', []))
    if count == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='нет фото для идентификации')
        context.user_data['current_state'] = 'photo'
        return 'photo'

    await send_next_unknown_photo(update, context)
    context.user_data['current_state'] = 'car_number'
    return 'car_number'


async def date_input(update, context):
    requested_date = update.message.text
    if len(requested_date.split('.')) == 2:
        day, month = requested_date.split('.')
        if int(month) > datetime.now().month:
            year = str(datetime.now().year - 1)
        else:
            year = str(datetime.now().year)
        requested_date = '.'.join((day, month, year))
    routes = database.get_routes(requested_date)
    week = ('понедельник', 'вторник',
            'среда', 'четверг', 'пятница',
            'суббота', 'воскресенье')
    status_ico = {0: '\u2728', 1: '\u1F4E', 2: '\u274C', 3: '\u2705'}
    date = datetime.strptime(requested_date, '%d.%m.%Y')
    weekday = (week[date.weekday()])
    keyboard = [[]]
    current_line = 0
    for route in routes:
        if len(keyboard[current_line]) > 1:
            keyboard.append([])
            current_line += 1
        keyboard[current_line].append(
            InlineKeyboardButton(
                f"{status_ico.get(route[2], status_ico[0])} {route[1]} ({route[0]})",
                callback_data=route[0],
                ),
            )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"{requested_date} <b>{weekday}</b>",
                                    reply_markup=reply_markup,
                                    parse_mode=constants.ParseMode.HTML)


async def route_id(update, context):
    if not re.match(r"^\d{7}$", update.message.text):
        await ask_route_id(update, context)
        context.user_data['current_state'] = 'route_id'
        return 'route_id'
    send_route_info(update, context, update.message.text)
    context.user_data['current_state'] = 'photo'
    return 'photo'


async def ask_contact(update, context):
    contact_keyboard = KeyboardButton(text="поделиться контактом",
                                      request_contact=True)
    custom_keyboard = [[contact_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Требуется авторизация. Нажмите "поделиться контактом"',
        reply_markup=reply_markup)


async def ask_route_id(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Укажите ID рейса или дату в формате ДД.ММ",
        )


async def ask_photo(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="прикрепите фото"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['unknown_photos'] = []
    context.user_data['known_photos'] = {}
    context.user_data['command_car'] = ''
    context.user_data['tests_photo'] = []
    context.user_data['passline_photo'] = ''
    context.user_data['route_id'] = ''
    if 'contact_tel' not in context.user_data:
        await ask_contact(update, context)
        context.user_data['current_state'] = 'get_contact'
        return 'get_contact'

    await ask_route_id(update, context)
    context.user_data['current_state'] = 'route_id'
    return 'route_id'


async def send_next_unknown_photo(update, context):
    buttons = [
        [
            InlineKeyboardButton(text="Штаб", callback_data=str('COMMANDER')),
            InlineKeyboardButton(
                text="Попутчик", callback_data=str('PASSLINE')),
            InlineKeyboardButton(text="Тесты", callback_data=str('TESTS')),
            InlineKeyboardButton(text="Удалить", callback_data=str('DEL')),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    count = len(context.user_data['unknown_photos'])
    await context.bot.send_message(update.effective_chat.id,
                                   f'нераспознано {count} шт.')
    next_photo = context.user_data['unknown_photos'][-1]
    msg = await context.bot.send_photo(chat_id=update.effective_chat.id,
                                       photo=f'./{PHOTOS_PATH}/{next_photo}',
                                       reply_markup=keyboard)
    context.user_data['last_sent_photo'] = msg.id


async def remove_buttons(update, context):
    await context.bot.editMessageReplyMarkup(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['last_sent_photo'],
        reply_markup='')


async def car_number_input(update, context):
    await remove_buttons(update, context)
    car_number = format_car_number(update.message.text)
    save_car(car_number, context)
    if save_command_car(car_number, context):
        await update.message.reply_text(f'Штабной вагон: {car_number}')

    count = len(context.user_data['unknown_photos'])
    if count == 0:
        await update.message.reply_text('все фото распознаны')
        context.user_data['current_state'] = 'photo'
        return 'photo'
    await send_next_unknown_photo(update, context)
    context.user_data['current_state'] = 'car_number'
    return 'car_number'


async def photo_type_button(update, context):
    query = update.callback_query
    if query.data == 'DEL':
        context.user_data['unknown_photos'].pop()
        await remove_buttons(update, context)
        await context.bot.send_message(update.effective_chat.id,
                                       'удалено')
        await query.answer()
        return await identify(update, context)
    elif query.data == 'PASSLINE':
        context.user_data[
            'passline_photo'] = context.user_data['unknown_photos'][-1]
        context.user_data['unknown_photos'].pop()
        await remove_buttons(update, context)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='попутчик')
        await query.answer()
        return await identify(update, context)
    elif query.data == 'TESTS':
        context.user_data.setdefault(
            'tests_photo', []).append(context.user_data['unknown_photos'][-1])
        context.user_data['unknown_photos'].pop()
        await remove_buttons(update, context)
        await query.answer()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='тесты')
        return await identify(update, context)
    elif query.data == 'COMMANDER':
        context.user_data['current_car_is_COMMAND'] = True
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Введите номер штабного вагона')
        await query.answer()


async def send(update, context):
    car_list = context.user_data.get('known_photos', {}).keys()
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=list(car_list))

    if context.user_data.get('unknown_photos'):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='не все фото распознаны')
    elif not context.user_data.get('tests_photo'):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='нет фото тестов')
    elif not context.user_data.get('command_car'):
        context.user_data['current_car_is_COMMAND'] = True
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='укажите штабной вагон')
        context.user_data['current_state'] = 'set_command_car'
        return 'set_command_car'
    else:
        if database.save(context.user_data):
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Данные сохранены")
            await notify_smekaylo(update, context)
            return await start(update, context)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Ошибка базы данных")


async def set_command_car(update, context):
    car_number = update.message.text
    if len(car_number) == 8:
        car_number = car_number[:3] + '-' + car_number[3:]
    context.user_data['command_car'] = car_number
    context.user_data['current_car_is COMMAND'] = False
    await update.message.reply_text(f'Штабной вагон: {car_number}')


async def notify_smekaylo(update, context):
    await context.bot.send_message(SMEKAYLO_CHAT,
                                   text='/send_report')


async def ask_missing_info(update, context):
    print(context.user_data)
    if context.user_data.get('current_state', 'Unknown') == 'route_id':
        await ask_route_id(update, context)
    elif context.user_data.get('current_state', 'Unknown') == 'get_contact':
        await ask_contact(update, context)
    elif context.user_data.get('current_state', 'Unknown') == 'photo':
        await ask_photo(update, context)
    else:
        await update.message.reply_text('непонятно. введите номер вагона')


async def check_contact(update, context):
    if update.message.contact:
        context.user_data['contact_name'] = update.message.contact.first_name
        context.user_data['contact_tel'] = update.message.contact.phone_number
        context.user_data['chat_id'] = update.effective_chat.id
        await context.bot.send_message(
            update.effective_chat.id,
            'Котакт сохранен'
            )
        await ask_route_id(update, context)
        context.user_data['current_state'] = 'route_id'
        return 'route_id'

    await context.bot.send_message(
        update.effective_chat.id,
        'Требуется авторизация. Нажмите "поделиться контактом".')
    context.user_data['current_state'] = 'get_contact'
    return 'get_contact'


async def route_button(update, context):
    await update.callback_query.answer()
    await send_route_info(update, context, update.callback_query.data)
    context.user_data['current_state'] = 'photo'
    return 'photo'


contact_handler = MessageHandler(filters.ALL, check_contact)
start_handler = CommandHandler('start', start)
route_id_handler = MessageHandler(filters.Regex(r"^\d{7}$"), route_id)
date_handler = MessageHandler(filters.Regex(r"^\d{2}\.\d{2}(?:\.\d{4})?$"),
                              date_input)
photo_handler = MessageHandler(filters.PHOTO, photo)
identify_handler = CommandHandler('identify', identify)
show_handler = CommandHandler('show', show)
send_handler = CommandHandler('send', send)
# auth_handler = CommandHandler('auth', get_contact)
car_number_handler = MessageHandler(filters.Regex(r"^\d{3}-?\d{5}$"),
                                    car_number_input)
type_buttons_handler = CallbackQueryHandler(photo_type_button)
route_buttons_handler = CallbackQueryHandler(route_button)
report_handler = CommandHandler('report', notify_smekaylo)
set_command_car_handler = MessageHandler(filters.Regex(r"^\d{3}[ -]?\d{5}$"),
                                         set_command_car)
