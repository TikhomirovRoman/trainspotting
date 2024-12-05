import logging
import os

from telegram.ext import (ApplicationBuilder,
                          ConversationHandler,
                          filters,
                          MessageHandler,
                          )
from config import BOT_TOKEN
from handlers import (start_handler, contact_handler, route_id_handler,
                      date_handler, route_buttons_handler, photo_handler,
                      identify_handler, show_handler,
                      report_handler, send_handler, set_command_car_handler,
                      car_number_handler, type_buttons_handler,
                      ask_missing_info)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[start_handler],
        states={
            'get_contact': [contact_handler],
            'route_id': [route_id_handler, date_handler,
                         route_buttons_handler],
            'photo': [photo_handler, identify_handler],
            'car_number': [photo_handler, car_number_handler,
                           type_buttons_handler, identify_handler,
                           ],
            'set_command_car': [set_command_car_handler],
        },
        fallbacks=[send_handler, start_handler, show_handler,
                   MessageHandler(filters.ALL, ask_missing_info),]
    )
    # application.add_handler(auth_handler)
    # application.add_handlers([show_handler,])
    application.add_handler(conv_handler)
    application.add_handler(report_handler)

    application.run_polling()
