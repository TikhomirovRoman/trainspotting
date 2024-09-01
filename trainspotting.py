import logging
import json
import re

import database

from telegram import (Update, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, InlineKeyboardButton,
                      InlineKeyboardMarkup, KeyboardButton)
from telegram.ext import (ApplicationBuilder,
                          CallbackQueryHandler,
                          ContextTypes,
                          ConversationHandler,
                          CommandHandler,
                          filters,
                          MessageHandler)

from settings import bot_token

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
PHOTOS_PATH = 'photos'
SMEKAYLO_CHAT = 7500531360

buttons = ReplyKeyboardMarkup([['/identify', '/show', '/start', '/send']],
                              resize_keyboard=True)


async def get_contact(update, context):
    contact_keyboard = KeyboardButton(text="поделиться контактом",
                                      request_contact=True)
    custom_keyboard = [[contact_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Требуется авторизация. Нажмите "поделиться контактом"',
        reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['unknown_photos'] = []
    context.user_data['known_photos'] = {}
    context.user_data['command_car'] = ''
    context.user_data['tests_photo'] = []
    context.user_data['passline_photo'] = ''
    context.user_data['route_id'] = ''
    if 'contact_tel' not in context.user_data:
        await get_contact(update, context)
        return 'get_contact'
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Укажите ID рейса",)
    return 'route_id'


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.photo[-1].file_id
    new_file = await context.bot.get_file(file_id)
    file_name = file_id + '.jpg'
    await new_file.download_to_drive(f'{PHOTOS_PATH}/{file_name}')
    context.user_data.setdefault('unknown_photos', []).append(file_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'фото сохранено ({len(context.user_data["unknown_photos"])} шт.)',
        reply_markup=buttons)
    return 'photo'


async def text(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="TEXT")


async def show(update, context):
    route_id = context.user_data['route_id']
    unknown = len(context.user_data['unknown_photos'])
    known = ' ,'.join(list(context.user_data['known_photos'].keys()))
    commander = context.user_data['command_car']
    tests = len(context.user_data['tests_photo'])
    passline = context.user_data['passline_photo']

    await update.message.reply_text(
        f'Нераспознано: {unknown} шт.\n \
        Добавлены вагоны: {known}\n\
        Штаб: {commander}\n\
        Тесты: {tests}\n\
        Попутчик: {passline}\n\
        Рейс: {route_id}')


async def route_id(update, context):
    if not re.match(r"^\d{7}$", update.message.text):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Укажите ID рейса",)
        return 'route_id'
    context.user_data['route_id'] = update.message.text
    await update.message.reply_text(f'Номер рейса: {update.message.text}, \n прикрепите фото')
    return 'photo'


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


async def send_next_unknown_photo(update, context):
    buttons = [
        [
            InlineKeyboardButton(text="Штаб", callback_data=str('COMMANDER')),
            InlineKeyboardButton(text="Попутчик", callback_data=str('PASSLINE')),
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
                                       photo=f'{PHOTOS_PATH}/{next_photo}',
                                       reply_markup=keyboard)
    context.user_data['last_sent_photo'] = msg.id


async def identify(update, context):
    count = len(context.user_data.get('unknown_photos', []))
    if count == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='нет фото для идентификации')
        return 'photo'

    await send_next_unknown_photo(update, context)
    return 'car_number'


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
        return 'photo'
    await send_next_unknown_photo(update, context)
    return 'car_number'


async def button(update, context):
    query = update.callback_query
    if query.data == 'DEL':
        context.user_data['unknown_photos'].pop()
        await remove_buttons(update, context)
        await context.bot.send_message(update.effective_chat.id,
                                       'удалено')
        await query.answer()
        return await identify(update, context)
    elif query.data == 'PASSLINE':
        context.user_data['passline_photo'] = context.user_data['unknown_photos'][-1]
        context.user_data['unknown_photos'].pop()
        await remove_buttons(update, context)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='попутчик')
        await query.answer()
        return await identify(update, context)
    elif query.data == 'TESTS':
        context.user_data.setdefault('tests_photo', []).append(context.user_data['unknown_photos'][-1])
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
        return 'set_command_car'
    else:
        with open('base.json', 'w') as file:
            json.dump(context.user_data, file)

        if database.save(context.user_data):
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Данные сохранены")
            return await start(update, context)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Ошибка базы данных")
        
        
        await context.bot.send_message(SMEKAYLO_CHAT,
                                       text='/send_report')


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


async def ask_number(update, context):
    await update.message.reply_text('непонятно. введите номер вагона')


async def check_contact(update, context):
    if update.message.contact:
        context.user_data['contact_name'] = update.message.contact.first_name
        context.user_data['contact_tel'] = update.message.contact.phone_number
        context.user_data['chat_id'] = update.effective_chat.id
        await context.bot.send_message(update.effective_chat.id,
                                       'Котакт сохранен.\nУкажите ID рейса')
        return 'route_id'
    await context.bot.send_message(
        update.effective_chat.id,
        'Требуется авторизация. Нажмите "поделиться контактом".')
    return 'get_contact'


if __name__ == '__main__':
    application = ApplicationBuilder().token(bot_token).build()

    contact_handler = MessageHandler(filters.ALL, check_contact)
    start_handler = CommandHandler('start', start)
    show_handler = CommandHandler('show', show)
    send_handler = CommandHandler('send', send)
    auth_handler = CommandHandler('auth', get_contact)
    photo_handler = MessageHandler(filters.PHOTO, photo)
    identify_handler = CommandHandler('identify', identify)
    text_handler = MessageHandler(filters.TEXT, text)
    car_number_handler = MessageHandler(filters.Regex(r"^\d{3}-?\d{5}$"),
                                        car_number_input)
    route_id_handler = MessageHandler(filters.Regex(r"^\d{7}$"),
                                      route_id)
    inline_buttons_handler = CallbackQueryHandler(button)
    report_handler = CommandHandler('report', notify_smekaylo)
    set_command_car_handler = MessageHandler(filters.Regex(r"^\d{3}-?\d{5}$"),
                                             set_command_car)

    conv_handler = ConversationHandler(
        entry_points=[start_handler],
        states={
            'get_contact': [start_handler, contact_handler],
            'route_id': [route_id_handler],
            'photo': [photo_handler, identify_handler],
            'car_number': [photo_handler, car_number_handler,
                           inline_buttons_handler, identify_handler,
                           ],
            'set_command_car': [set_command_car_handler],
        },
        fallbacks=[send_handler, start_handler, show_handler,
                   MessageHandler(filters.ALL, ask_number),]
    )
    application.add_handler(auth_handler)
    # application.add_handler(universal_handler)
    application.add_handlers([show_handler,])
    application.add_handler(conv_handler)
    application.add_handler(report_handler)

    application.run_polling()
