import telebot
from datetime import datetime, timedelta
import datetime
import time
import os
import shutil
import schedule
import json
import sqlite3 as sl
from Keyboards.InlineKeyboards import *
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton

with open("Config.json") as settings:
    config = json.load(settings)
    Token = config.get("telegram_token")
    database = config.get("database_path")
    geocoder_api = config.get("geocoder_api")
    chanel = config.get("chanel_id")
    queries = config.get("queries")
bot = telebot.TeleBot(Token)
con = sl.connect(database, check_same_thread=False)
message_lock = threading.Lock()

remaining_time = None
timer_thread = None

# Все текста которые используются в боте
texts_dict = {"/start for user": ('Привет ,я бот аукционов @NScourse_bot\n'
                                  'Я помогу вам следить за выбранными лотами ,и регулировать\n'
                                  'ход аукциона.А так же буду следить за вашими накопленными\n'
                                  'балами.\n'
                                  'Удачных торгов 🤝'),

              "/start for admin": ('в бот аукционов @NScourse_bot '
                                   'Выберите необходимы для вас действия'),

              "admins_settings": "Выберите необходимые действия с администраторами:",

              "admin_add": "Поиск пользователя по ссылке:",

              "admin_changes": "Выберите администратора которого хотите изменить",

              "admin_delete": "Выберите администратора которого хотите удалить",

              "changing_options": "Выберите необходимое что хотите изменить",

              "my_lots": "Выберите лот в котором вы участвуете",

              "no_lots": "Вы еще не участвовали в лотах",

              "show_finance": "Для пополнения баланса обратитесь к администратору @Nsarkisov",

              "rules": ("После окончания торгов,победитель должен выйти на связь с\n"
                        "продавцом\n"
                        "самостоятельно в течении суток‼️\n"
                        "Победитель обязан выкупить лот в течении ТРЁХ дней,после\n"
                        "окончания аукциона🔥\n"
                        "НЕ ВЫКУП ЛОТА - ПЕРМАНЕНТНЫЙ БАН ВО ВСЕХ\n"
                        "НУМИЗМАТИЧЕСКИХ СООБЩЕСТВАХ И АУКЦИОНАХ🤬\n"
                        "Что бы узнать время окончания аукциона,нажмите на ⏰\n"
                        "Анти-снайпер - Ставка сделанная за 10 минут до\n"
                        "конца,автоматически переносит\n"
                        "Аукцион на 10 минут вперёд ‼️\n\n"
                        "Работают только проверенные продавцы,их Отзывы суммарно\n"
                        "достигают 10000+ на различных площадках.\n"
                        "Дополнительные Фото можно запросить у продавца.\n"
                        "Случайно сделал ставку?🤔\n"
                        "Напиши продавцу‼️\n\n\n"
                        "Отправка почтой,стоимость пересылки указана под фото.\n"
                        "Лоты можно копить ,экономя при этом на почте.\n"
                        "Отправка в течении трёх дней после оплаты‼️"),

              "help_info": ("Свяжитесь с нами, если у вас возникли вопросы @nsarkisov\n"
                            "При проблемах или нахождении ошибок пишите @nsarkisov"),

              "create_lot": "Заполните всю необходимую информацию о новом лоте:\n",

              "title": "Укажите название",

              "media": ("Укажите количество отправляемых фотографий? \n"
                        "Максимально возможное количество: 4. \n"
                        "Обязательно выберите нужный вариант для правильного \n"
                        "сохранения ваших изображений"),

              "media_1": "Отправьте 1 изображение",
              "media_2": "Отправьте 2 изображения",
              "media_3": "Отправьте 3 изображения",
              "media_4": "Отправьте 4 изображения",

              "price": "Отправьте стартовую цену лота",

              "geolocation": "Укажите город",

              "description": "Укажите описание",

              "additional_info": "Укажите дополнительную информацию",

              "card_info": ("После окончания торгов,победитель\n"
                            "должен выйти на связь с продавцом\n"
                            "самостоятельно в течении\n"
                            "суток. Победитель обязан выкупить лот\n"
                            "в течении ТРЁХ дней,после окончания\n"
                            "аукциона.\n"
                            "НЕ ВЫКУП ЛОТА - БАН."),

              "notification_of_victory": ("💥Поздравляем с победой💥, напоминаем вам\n"
                                          "что вы должны выйти на связь с продавцом\n"
                                          "в течении суток, и вы обязаны выкупить лот\n"
                                          "в течении трёх дней, после получения этого\n"
                                          "сообщения, за нарушение этого правила:\n"
                                          "вы больше не сможете участвовать\n"
                                          "и пользоваться услугами площадки"),

              "save_lot": "Подтвердите сохранение",

              "selled_lots": "Выберите из проданных лотов:",

              "unselled_lots": "Выберите из не-проданных лотов:",

              "recreate_lot": "Выберите лоты из которых необходимо пересоздать лот",

              "customers": "Выберите лот у которого есть победитель: ",

              "no_customers": "Пока по вашим лотам победителей нет",

              "show_history": ("Вы можете посмотреть историю торгов для вашего лота:\n"
                               "Выберите название если вы добавляли лот"),

              "deleting_lot": ("Если вы удалите лот из текущего аукциона то площадка\n"
                               "отнимет от баланса комиссию в размере 5% от текущей\n"
                               "стоимости лота"),

              "start_auction": ("Короткий аукцион 🔥🤳\n"
                                "Окончание: "
                                f"{(datetime.datetime.now().date() + timedelta(days=1)).strftime('%d.%m.%Y')}💥\n"
                                "С 23:00-00:00\n"
                                "По МСК\n\n"
                                "Работают только проверенные продавцы,их Отзывы сумарно\n"
                                "достигают 10000+ на различных площадках.\n"
                                "Дополнительные Фото можно запросить у продавца.\n"
                                "Случайно сделал ставку?🤔\n"
                                "Напиши продавцу‼️\n\n\n"
                                "Отправка почтой только по РОССИИ,стоимость пересылки\n"
                                "указана под фото.\n"
                                "Лоты можно копить ,экономя при этом на почте.\n"
                                "Отправка в течении трёх дней после оплаты‼️\n\n"
                                "После окончания торгов,победитель должен выйти на связь\n"
                                "с продавцом\n"
                                "самостоятельно в течении суток‼️\n"
                                "Победитель обязан выкупить лот в течении ТРЁХ дней,после\n"
                                "окончания аукциона🔥\n"
                                "НЕ ВЫКУП ЛОТА - ПЕРМАНЕНТНЫЙ БАН ВО ВСЕХ\n"
                                "НУМИЗМАТИЧЕСКИХ СООБЩЕСТВАХ И АУКЦИОНАХ🤬\n"
                                "Что бы узнать время окончания аукциона,нажмите на ⏰\n\n"
                                "Для участия нажмите УЧАСТВОВАТЬ,\n"
                                "Далее вас перенёс в чат с ботом,\n"
                                "Нажмите СТАРТ и вам будет доступен калькулятор ставок.\n"
                                "Повторяйте эту процедуру при добавлении новых лотов.\n\n\n"
                                "Антиснайпер - Ставка сделанная за 10 минут до\n"
                                "конца,автоматически переносит\n"
                                "Аукцион на 10 минут вперёд ‼️"),

              "names": {
                  "title": "Название",
                  "images": "Изображение",
                  "price": "Стартовая цена",
                  "geolocation": "Геолокация",
                  "description": "Описание",
                  "additional_info": "Доп.Информация"
              }
              }

# Словарь администраторов, который также будет содержать создание лота
administrators_dict = {}

buffer = {
    "Lots_to_add": [],  # Перед постом добавляются id лотов для проверки через "Moderation"
    "Moderation": {},  # Лоты которые, отправляются всем админам со статусом SUPER_ADMIN или SUPPORT
    "Approved": [],  # Лоты которые, будут отправляться на канал
    "Active": {}  # Лоты которые уже находятся на канале
}

# Для регистрации обработчика текста
handler_register = ["title", "price", "geolocation", "description", "additional_info"]

# Словарь который, содержит в себе ссылки на объекты Inline клавиатур telebot.types
actions = {
    # Просмотр всех Лотов в которых участвует пользователь
    "my_lots": lambda lots: TradingHistory(lots).user_participated_lots().keyboard,
    # Текст по обращению к супер админу для пополнения баланса и кнопка главное меню
    "my_balance": "",
    # Здесь только главное меню
    "rules": MainMenu().getMenu().keyboard,
    # Здесь только главное меню и написать в поддержку
    "help_info": MainMenu().getMenu().keyboard,
    "admins_settings": SuperAdmin().options().keyboard,
    "create_lot": Lot().creating_lot().keyboard,
    "recreate_lot": Lot().recreate_lot().keyboard,
    "title": None,
    "media": Lot().quantity_of_images().keyboard,
    "media_1": None,
    "media_2": None,
    "media_3": None,
    "media_4": None,
    "price": None,
    "geolocation": None,
    "description": None,
    "additional_info": None,
    "save_lot": Lot().saving_confirmation().keyboard,
    "customers": lambda lots: TradingHistory(lots).won_lot().keyboard,
    "show_history": lambda lots: TradingHistory(lots).show().keyboard,
    "show_finance": MainMenu().getMenu().keyboard,
    "deleting_lot": lambda lots: TradingHistory(lots).delete_lot().keyboard,
    "selled_lots": lambda lots: TradingHistory(lots).recreate_lot().keyboard,
    "unselled_lots": lambda lots: TradingHistory(lots).recreate_lot().keyboard
}


# Функция которая, срабатывает при запуске бота и обновляет словарь администраторов
def update(case):
    if case == "Обновить администраторов":
        with con:
            admins = con.execute(queries['searching_admins']).fetchall()
        for admin in admins:
            first_name, last_name, telegram_id, telegram_link, = admin[9], admin[10], admin[11], admin[12]
            phone, email, access_level, started_time, ended_time = admin[2], admin[3], admin[4], admin[5], admin[6]
            balance = admin[13]
            administrators_dict.update({telegram_id: {"first_name": first_name,
                                                      "last_name": last_name,
                                                      "telegram_link": telegram_link,
                                                      "phone": phone,
                                                      "email": email,
                                                      "access_level": access_level,
                                                      "started_time": started_time,
                                                      "ended_time": ended_time,
                                                      "balance": balance}})


def personal_cabinet(telegram_id, type_of_message, message_id, call_id):
    if call_id is not None:
        bot.answer_callback_query(callback_query_id=call_id, )

    if telegram_id in administrators_dict.keys():
        if administrators_dict[telegram_id]["access_level"] == "SUPER_ADMIN":
            starting = Starting().super_admin().keyboard
        else:
            starting = Starting().for_admin().keyboard
        name = administrators_dict[telegram_id]['first_name']
        telegram_link = administrators_dict[telegram_id]['telegram_link']
        text = f"Добро пожаловать {name}, {telegram_link} " + texts_dict['/start for admin']

    else:
        starting = Starting().for_user().keyboard
        text = texts_dict['/start for user']

    # Использование нового подхода для отправки типа сообщений send или edit
    # Хотя можно было и традиционно используя конструкцию if elif else, использовал в целях эксперимента
    send = {"send": [bot.send_message, {'chat_id': telegram_id, "text": text, "reply_markup": starting}],
            "edit": [bot.edit_message_text, {'chat_id': telegram_id, 'message_id': message_id, "text": text,
                                             "reply_markup": starting}]}

    function, kwargs = send[type_of_message][0], send[type_of_message][1]

    function(**kwargs)


def cabinet_actions(button_info, telegram_id, message_id, type_of_message, call_id):
    lots, text = None, None

    if call_id is not None:
        bot.answer_callback_query(callback_query_id=call_id, )

    lot_info_queries = {"customers": "lot_id_title-winners",
                        "show_history": "lot_id_title",
                        "selled_lots": "get_selled_lots",
                        "unselled_lots": "get_unselled_lots"}

    if button_info in lot_info_queries.keys():
        with con:
            lots = con.execute(queries[lot_info_queries[button_info]], [telegram_id]).fetchall()

    if button_info == "my_lots":  # Лоты которые, открыл пользователь
        lots = []
        if buffer["Active"] is not None:
            for lot_id in buffer['Active'].keys():
                if "bids" in buffer["Active"][str(lot_id)].keys():
                    if telegram_id in buffer["Active"][str(lot_id)]['bids'].keys():
                        with con:
                            title = con.execute(queries["lot_title"], [int(lot_id)]).fetchall()[0][0]
                        lots.append([lot_id, title])
    elif button_info == "deleting_lot":  # Лоты которые админ хочет удалить
        lots = []
        if buffer["Active"] is not None:
            for lot_id in buffer['Active'].keys():
                with con:
                    users_telegram_id = con.execute(queries["lot_is_users?"], [int(lot_id)]).fetchall()[0][0]
                    if users_telegram_id == telegram_id:
                        title = con.execute(queries["lot_title"], [int(lot_id)]).fetchall()[0][0]
                        lots.append([lot_id, title])

    selected_action = actions[button_info]
    if callable(selected_action):  # Если в ссылку необходимо отправить информацию используя lambda
        selected_action = selected_action(lots)

    if button_info == "customers":  # текст если победителей нет, путём проверки длины клавиатуры
        if len(selected_action.keyboard) == 1:
            text = texts_dict["no_customers"]
    elif button_info == "my_lots":  # текст если лотов нет, путём проверки длины клавиатуры
        if len(selected_action.keyboard) == 1:
            text = texts_dict["no_lots"]
    else:
        text = texts_dict[button_info]

    if button_info == "create_lot":
        if "new_lot" not in administrators_dict[telegram_id].keys():
            administrators_dict[telegram_id].update(
                {
                    "new_lot":
                        {
                            "title": None,
                            "images": None,
                            "price": None,
                            "geolocation": None,
                            "description": None,
                            "additional_info": None
                        }
                }
            )

        # Цикл который, подсчитывает количество добавленных изображений
        for key, value in administrators_dict[telegram_id]["new_lot"].items():
            if key != "images" and value is None:
                value = "Нет"
            elif key == "images":
                image_directory = f"Media/{telegram_id}"
                if os.path.exists(image_directory):
                    image_quantity = len(os.listdir(image_directory))
                    value = image_quantity
                else:
                    value = "Нет"
            text += f"{texts_dict['names'][key]}: {value}\n"

    elif button_info == "show_finance":
        with con:
            balance = con.execute(queries['get_balance'], [telegram_id]).fetchall()[0][0]
        text += f"\nВаш текущий баланс: {balance}"

    # Использование нового подхода для отправки типа сообщений send или edit
    # Хотя можно было и традиционно используя конструкцию if elif else, использовал в целях эксперимента
    send = {"send": [bot.send_message, {'chat_id': telegram_id, "text": text, "reply_markup": selected_action}],
            "edit": [bot.edit_message_text, {'chat_id': telegram_id, 'message_id': message_id, "text": text,
                                             "reply_markup": selected_action}]}

    function, kwargs = send[type_of_message][0], send[type_of_message][1]
    function(**kwargs)


def creating_lot(button_info, telegram_id, message_id, message, call_id):
    if call_id is not None:
        bot.answer_callback_query(callback_query_id=call_id, )

    if button_info.startswith("media_"):
        folder_path = f"Media/{str(telegram_id)}"
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        administrators_dict[telegram_id]["new_lot"]["images"] = int(button_info[-1])

    selected_action = actions[button_info]
    text = texts_dict[button_info]

    bot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=text, reply_markup=selected_action)

    if button_info in handler_register:
        bot.register_next_step_handler(message, get_info, button_info)


def recreate_lot(telegram_id, lot_id, message_id, call_id):
    if lot_id not in buffer["Lots_to_add"]:

        bot.answer_callback_query(callback_query_id=call_id, text="Лот добавлен на проверку")
        info = "Лот добавлен на проверку модераторам"

    else:

        bot.answer_callback_query(callback_query_id=call_id, text="Лот уже в очереди")
        info = "Лот находится на проверке"

    main_menu = MainMenu().getMenu().keyboard
    bot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=info, reply_markup=main_menu)


def save_lot(telegram_id, message_id, call_id):
    title = administrators_dict[telegram_id]["new_lot"]["title"]
    price = administrators_dict[telegram_id]["new_lot"]["price"]
    geolocation = administrators_dict[telegram_id]["new_lot"]["geolocation"]
    description = administrators_dict[telegram_id]["new_lot"]["description"]
    add_info = administrators_dict[telegram_id]["new_lot"]["additional_info"]

    if title is None or price is None or geolocation is None or description is None:
        bot.answer_callback_query(callback_query_id=call_id, text="Заполните все данные")
    else:

        with con:
            users_id = con.execute(queries["searching_user"], [telegram_id]).fetchall()[0][0]
            admin_id = con.execute(queries["admin_id"], [users_id]).fetchall()[0][0]
            con.execute(queries["save_lot"], [admin_id, title, geolocation, price, description, add_info])
            lot_id = con.execute(queries["lot_id"], [admin_id]).fetchall()[-1][0]

        source_directory = f"Media/{str(telegram_id)}"

        directory = "Lots/"
        folder_name = str(lot_id)
        folder_path = os.path.join(directory, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        target_directory = f"Lots/{str(lot_id)}"
        file_list = os.listdir(source_directory)

        for file_name in file_list:
            source_path = os.path.join(source_directory, file_name)
            target_path = os.path.join(target_directory, file_name)
            shutil.move(source_path, target_path)

        if os.path.exists(source_directory):
            shutil.rmtree(source_directory)

        image_links = []

        for filename in os.listdir(target_directory):
            if filename.endswith('.jpg') or filename.endswith('.png'):
                image_link = f"{target_directory}/{filename}"
                image_links.append(image_link)

        with con:
            for link in image_links:
                con.execute(queries["lot_upload_links"], [lot_id, link])

        del administrators_dict[telegram_id]["new_lot"]

        bot.answer_callback_query(callback_query_id=call_id, text="Лот успешно сохранён")

        buffer["Lots_to_add"].append(lot_id)

        personal_cabinet(telegram_id, "edit", message_id, None)


@bot.message_handler(content_types=['photo'])
def handle_image(message):
    telegram_id = message.from_user.id
    message_id = message.chat.id
    if "new_lot" in administrators_dict[telegram_id].keys():
        message_lock.acquire()
        directory = "Media/"
        folder_name = str(telegram_id)
        folder_path = os.path.join(directory, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if administrators_dict[telegram_id]["new_lot"]["images"] is not None:
            try:
                count = administrators_dict[telegram_id]["new_lot"]["images"]
                photo = message.photo[-1]
                file_info = bot.get_file(photo.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_name = f'image_{photo.file_unique_id}.jpg'
                file_path = os.path.join(folder_path, file_name)

                with open(file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)

                bot.reply_to(message, 'Изображение успешно сохранено.')

                count -= 1
                administrators_dict[telegram_id]["new_lot"]["images"] = count
                if count == 0:
                    administrators_dict[telegram_id]["new_lot"]["images"] = None
                    print(administrators_dict)
                    cabinet_actions("create_lot", telegram_id, message_id, "send", None)
            finally:
                message_lock.release()
        else:
            message_lock.release()


@bot.message_handler(content_types=['text'])
def start(message):
    first_name, last_name = message.from_user.first_name, message.from_user.last_name
    telegram_id, telegram_link = message.from_user.id, "@" + message.from_user.username

    menu = {"/start": personal_cabinet, "/help": ""}

    # Проверяем есть ли пользователь в базе
    with con:
        searching = con.execute(queries["searching_user"], [telegram_id]).fetchall()

        if not searching:
            con.execute(queries["adding_user"], [first_name, last_name, telegram_id, telegram_link])

    if message.text in menu.keys():
        buffer["Lots_to_add"].append(1), buffer["Lots_to_add"].append(2)

        menu[message.text](telegram_id, "send", None, None)

    elif message.text.startswith("/start "):

        lot_id = message.text.split()[-1]

        keyboard = Card(lot_id).bot_card().keyboard

        with con:
            image_links = con.execute(queries["get_images_link"], [lot_id]).fetchall()[0]
            lot_price = con.execute(queries["lot_price"], [lot_id]).fetchall()[0][0]

        text = lot_information(lot_id)

        if "bids" in buffer["Active"][str(lot_id)].keys():
            last_bid = max(buffer["Active"][str(lot_id)]["bids"].values())
            for user_id, user_bid in buffer["Active"][str(lot_id)]["bids"].items():
                if user_bid == last_bid:
                    with con:
                        users_link = con.execute(queries['users_link'], [user_id]).fetchall()[0][0]

            text += "Следующая ставка: " + str(last_bid + 100) + "₽" + "\n\n"
            text += f"\n\n🥇 {last_bid}₽ {users_link[1:3]}***"

        else:
            text += "Следующая ставка: " + str(lot_price) + "₽" + "\n\n"

        if "user_opened" in buffer["Active"][str(lot_id)].keys():
            if telegram_id in buffer["Active"][str(lot_id)]["user_opened"].keys():
                bot.delete_message(telegram_id, buffer["Active"][str(lot_id)]["user_opened"][telegram_id])

        with open(image_links[0], 'rb') as image:
            message = bot.send_photo(chat_id=telegram_id, photo=image, caption=text, reply_markup=keyboard)

        if "user_opened" not in buffer["Active"][str(lot_id)].keys():
            buffer["Active"][str(lot_id)].update({"user_opened": {telegram_id: message.id}})
        else:
            buffer["Active"][str(lot_id)]["user_opened"].update({telegram_id: message.id})


def get_info(message, button_info):
    telegram_id = message.from_user.id
    message_id = message.chat.id
    administrators_dict[telegram_id]["new_lot"][button_info] = message.text
    cabinet_actions("create_lot", telegram_id, message_id, "send", None)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    call.data = json.loads(call.data)
    flag, button_info = call.data[0], call.data[1]

    callback = {'/home': (personal_cabinet, (chat_id, "edit", message_id, call.id)),
                '/start': (cabinet_actions, (button_info, chat_id, message_id, "edit", call.id)),
                '/SuperAdmin': (super_admin, (chat_id, message_id, button_info, call.id)),
                '/admin_add': (add_admin, (chat_id, message_id, button_info, call.id)),
                '/admin_changes': (change_admin, (chat_id, message_id, button_info, call.id, "options")),
                '/change_status': (change_admin, (chat_id, message_id, button_info, call.id, "status")),
                '/change_balance': (change_admin, (chat_id, message_id, button_info, call.id, "balance")),
                '/admin_delete': (delete_admin, (chat_id, message_id, button_info, call.id)),
                '/lot': (creating_lot, (button_info, chat_id, message_id, call.message, call.id)),
                '/recreate': (recreate_lot, (chat_id, button_info, message_id, call.id)),
                '/save': (save_lot, (chat_id, message_id, call.id)),
                '/delete': (delete_lot, (chat_id, message_id, button_info, call.id)),
                '/card': (card_info, (call.id, button_info)),
                '/card_media': (card_media, (chat_id, message_id, button_info, call.id)),
                '/card_bids': (card_bids, (chat_id, button_info, call.id)),
                '/history': (show_history, (chat_id, message_id, button_info, call.id)),
                '/accept': (approvement, (button_info, call.id, 'accept')),
                '/decline': (approvement, (button_info, call.id, 'decline')),
                '/customer': (winner_info, (chat_id, message_id, button_info, call.id))}

    function, args = callback[flag][0], callback[flag][1]

    function(*args)


def super_admin(telegram_id, message_id, button_info, call_id):
    bot.answer_callback_query(callback_query_id=call_id, )
    text = None
    if button_info == "add_admin":
        text = texts_dict[button_info]
        keyboard = SuperAdmin().add().keyboard
        # Вызов клавиатуры с кнопкой поиск по Telegram_link

    elif button_info == "change_admin":
        text = texts_dict[button_info]
        with con:
            admins = con.execute(queries['admins_settings']).fetchall()
            keyboard = SuperAdmin().changes(admins).keyboard

        # Найти всех администраторов и передать в клавиатуру
        # Нужны данные ADMINISTRATORS.ID USERS.TELEGRAM_LINK

    elif button_info == "delete_admin":
        text = texts_dict[button_info]
        with con:
            admins = con.execute(queries['admins_settings']).fetchall()
            keyboard = SuperAdmin().delete(admins).keyboard

        # Найти всех администраторов и передать в клавиатуру
        # Нужны данные ADMINISTRATORS.ID USERS.TELEGRAM_LINK

    bot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=text, reply_markup=keyboard)


def add_admin(telegram_id, message_id, button_info, call_id):
    bot.answer_callback_query(callback_query_id=call_id, )
    return ""


def change_admin(telegram_id, message_id, admin_id, call_id, case):
    bot.answer_callback_query(callback_query_id=call_id, )
    register_handler = []
    if case == "options":
        keyboard = SuperAdmin().changes_in_admin(admin_id).keyboard
        text = texts_dict['changing_options']

    # bot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=text, reply_markup=keyboard)

    if case == "status":
        print("")
    if case == "balance":
        print("")


def delete_admin(telegram_id, message_id, admin_id, call_id):
    bot.answer_callback_query(callback_query_id=call_id, )
    return ""


# Функция lot_information для получения всего текста по лоту
def lot_information(lot_id):
    with con:
        lot_info = con.execute(queries["get_lot_info"], [lot_id]).fetchall()[0]
        lot_title, lot_price, lot_geolocation = lot_info[0], str(lot_info[1]), lot_info[2]
        lot_description, lot_additional_info, sellers_link = lot_info[3], lot_info[4], lot_info[5]

    if lot_additional_info is not None:
        text = (lot_title + "\n" +
                lot_geolocation + "\n" +
                lot_description + "\n" +
                lot_additional_info + "\n" +
                ("Продавец " + sellers_link) + "\n\n")
    else:
        text = (lot_title + "\n" +
                lot_price + "\n" +
                lot_geolocation + "\n" +
                lot_description + "\n" +
                ("Продавец " + sellers_link) + "\n\n")
    return text


# Функция approvement для отмены или одобрения лота перед постом в канал
def approvement(lot_id, call_id, case):
    if case == "accept":

        message = "Вы одобрили лот"
        bot.answer_callback_query(callback_query_id=call_id, text=message)

        buffer['Approved'].append(lot_id)

        for user_id, message in buffer["Moderation"][str(lot_id)].items():
            bot.delete_message(user_id, message)

        del buffer["Moderation"][str(lot_id)]

        send_lot(case="start_auction")

    elif case == "decline":

        message = "Вы отменили лот"
        bot.answer_callback_query(callback_query_id=call_id, text=message)

        for user_id, message in buffer["Moderation"][str(lot_id)].items():
            bot.delete_message(user_id, message)

        with con:
            user_id = con.execute(queries['get_tg-id_by_lot-id'], [lot_id]).fetchall()[0][0]
            lot_title = con.execute(queries['lot_title'], [lot_id]).fetchall()[0][0]

        message = f"К сожалению ваш лот {lot_title} не прошёл проверку, свяжитесь с поддержкой"
        bot.send_message(user_id, message)

        del buffer["Moderation"][str(lot_id)]


# Функция send_lot используются планировщиком для отправки и остановки лотов в канал
def send_lot(case):
    # Сообщение которое, отправляется перед стартом аукциона и закрепляется ежедневно
    if case == "notification":
        pinned_message = bot.send_message(chanel, texts_dict["start_auction"])
        bot.pin_chat_message(chanel, pinned_message.id)

    # Проверка админами со статусом SUPER_ADMIN или SUPPORT лотов перед постом
    elif case == "approvement":
        for lot_id in buffer["Lots_to_add"]:
            keyboard = Support(lot_id).approvement().keyboard

            with con:
                lot_price = con.execute(queries["lot_price"], [lot_id]).fetchall()[0][0]
                image_links = con.execute(queries["get_images_link"], [lot_id]).fetchall()[0]

            text = lot_information(lot_id)
            text += "Следующая ставка: " + str(lot_price) + "₽"

            for user_id, values in administrators_dict.items():

                for key, value in values.items():

                    if value == "SUPER_ADMIN" or value == "SUPPORT":

                        with open(image_links[0], 'rb') as image:

                            message = bot.send_photo(chat_id=user_id,
                                                     photo=image,
                                                     caption=text,
                                                     reply_markup=keyboard)

                        if str(lot_id) not in buffer['Moderation'].keys():
                            buffer['Moderation'].update({str(lot_id): {user_id: message.id}})
                        else:
                            buffer['Moderation'][str(lot_id)].update({user_id: message.id})

        buffer['Lots_to_add'].clear()

    # Отправка лота в канал в случае одобрение администратором
    elif case == "start_auction":

        for lot_id in buffer["Approved"]:
            keyboard = Card(lot_id).chanel_card().keyboard

            with con:
                lot_price = con.execute(queries["lot_price"], [lot_id]).fetchall()[0][0]
                image_links = con.execute(queries["get_images_link"], [lot_id]).fetchall()[0]

            text = lot_information(lot_id)
            text += "Следующая ставка: " + str(lot_price) + "₽"

            with open(image_links[0], 'rb') as image:
                message = bot.send_photo(chat_id=chanel, photo=image, caption=text, reply_markup=keyboard)

            buffer["Active"].update({str(lot_id): {"message": message.id}})

        buffer["Approved"].clear()

        global timer_thread
        if timer_thread is None or not timer_thread.is_alive():
            timer_thread = threading.Thread(target=timer)
            timer_thread.start()

    # Завершение аукциона по истечению времени потока счетчика времени
    if case == "stop_auction":
        for lot_id in buffer["Active"].keys():
            lot_message = buffer["Active"][str(lot_id)]["message"]

            with con:
                lot_price = con.execute(queries["lot_price"], [lot_id]).fetchall()[0][0]

            text = lot_information(lot_id)
            text += "Следующая ставка: " + str(lot_price) + "₽"

            if "bids" not in buffer["Active"][lot_id].keys() or buffer["Active"][lot_id]["bids"] is None:
                text += "\n\n🏁 Аукцион закончен. Победителей нет.."

            else:
                sorted_items = sorted(buffer["Active"][lot_id]["bids"].items(), key=lambda x: x[1], reverse=True)[0]
                with con:
                    user_id = con.execute(queries["user_id"], [sorted_items[0]]).fetchall()[0][0]
                    user_link = con.execute(queries["users_link"], [sorted_items[0]]).fetchall()[0][0]
                    sellers_link = con.execute(queries["lot_sellers_link"], [lot_id]).fetchall()[0][0]
                    bid_id = con.execute(queries["get_bid_id"], [user_id, sorted_items[1]]).fetchall()[0][0]
                    lot_title = con.execute(queries["lot_title"], [lot_id]).fetchall()[0][0]
                    con.execute(queries["set_winner"], [user_id, lot_id, bid_id])

                text_to_winner = texts_dict['notification_of_victory']

                text_to_winner += ("\n\nИнформация о лоте:\n"
                                   f"Название: {lot_title}\n"
                                   f"Ваша ставка: {sorted_items[1]}₽\n"
                                   f"Продавец: 👉 {sellers_link}")

                bot.send_message(chat_id=sorted_items[0], text=text_to_winner)

                text += f"\n\n🏆{sorted_items[1]}₽ {user_link[1:3]}***"

            bot.edit_message_reply_markup(chat_id=chanel, message_id=lot_message, reply_markup=None)
            bot.edit_message_caption(caption=text, chat_id=chanel, message_id=lot_message)

            if "user_opened" in buffer["Active"][str(lot_id)].keys():
                for user_id, message_id in buffer["Active"][str(lot_id)]["user_opened"].items():
                    bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=None)
                    bot.edit_message_caption(caption=text, chat_id=user_id, message_id=message_id)

            buffer["Active"].clear()


def delete_lot(telegram_id, message_id, lot_id, call_id):
    message = "🚫Вы удалили лот"
    bot.answer_callback_query(callback_query_id=call_id, text=message)

    lot_message = buffer["Active"][str(lot_id)]["message"]
    text = lot_information(lot_id)

    if 'bids' in buffer["Active"][str(lot_id)].keys():
        lot_price = max(buffer["Active"][str(lot_id)]["bids"].values())
        text += "Следующая ставка: " + str(lot_price + 100) + "₽"

    else:
        with con:
            lot_price = con.execute(queries['lot_price'], [lot_id]).fetchall()[0][0]
        text += "Следующая ставка: " + str(lot_price) + "₽"

    with con:
        balance = con.execute(queries['get_balance'], [telegram_id]).fetchall()[0][0]
        commission = lot_price / 100 * 5
        new_balance = balance - commission
        con.execute(queries['set_balance'], [new_balance, telegram_id])

    text += "\n\n👮‍♀️Лот был удалён администратором"

    bot.edit_message_reply_markup(chat_id=chanel, message_id=lot_message, reply_markup=None)
    bot.edit_message_caption(caption=text, chat_id=chanel, message_id=lot_message)

    if "user_opened" in buffer["Active"][str(lot_id)].keys():
        for user_id, message_id in buffer["Active"][str(lot_id)]["user_opened"].items():
            bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=None)
            bot.edit_message_caption(caption=text, chat_id=user_id, message_id=message_id)

    personal_cabinet(telegram_id, 'edit', message_id, None)


# Спец функция для обработки двух кнопок которые, не отправляют текст, а содержат информацию
def card_info(call_id, button_info):
    if button_info == "timer":

        global remaining_time

        if remaining_time is not None:
            days = remaining_time.days
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            message = f"Осталось {days} дней {hours} часов {minutes} минут {seconds} секунд"
            bot.answer_callback_query(callback_query_id=call_id, text=message)

    elif button_info == "card_info":
        message = texts_dict[button_info]
        bot.answer_callback_query(callback_query_id=call_id, text=message, show_alert=True)


# Обработка нажатие кнопки отправить фото/видео, в которой, создаётся медиа группа
def card_media(telegram_id, message_id, lot_id, call_id):
    message = "✅Отправили вам фото и видео"
    bot.answer_callback_query(callback_query_id=call_id, text=message)

    with con:
        image_links = con.execute(queries["get_images_link"], [lot_id]).fetchall()[0]
        lot_price = con.execute(queries["lot_price"], [lot_id]).fetchall()[0][0]

    text = lot_information(lot_id)

    if "bids" in buffer["Active"][str(lot_id)].keys():
        last_bid = max(buffer["Active"][str(lot_id)]["bids"].values())
        text += "Следующая ставка: " + str(last_bid) + "₽"
    else:
        text += "Следующая ставка: " + str(lot_price) + "₽"

    media_group = []
    for link in image_links:
        if link is image_links[0]:
            media_group.append(telebot.types.InputMediaPhoto(open(link, 'rb'), caption=text))
        else:
            media_group.append(telebot.types.InputMediaPhoto(open(link, 'rb')))

    bot.send_media_group(chat_id=telegram_id, media=media_group, reply_to_message_id=message_id)


# Функция для ставок
def card_bids(telegram_id, lot_id, call_id):
    message = "Ставка принята"
    bot.answer_callback_query(callback_query_id=call_id, text=message)

    with con:
        lot_price = con.execute(queries['lot_price'], [lot_id]).fetchall()[0][0]
        users_link = con.execute(queries['users_link'], [telegram_id]).fetchall()[0][0]

    if "bids" not in buffer["Active"][str(lot_id)].keys():
        buffer["Active"][lot_id].update({"bids": {telegram_id: lot_price}})
    else:
        last_bid = max(buffer["Active"][str(lot_id)]["bids"].values())
        buffer["Active"][str(lot_id)]["bids"].update({telegram_id: last_bid + 100})

    last_bid = max(buffer["Active"][str(lot_id)]["bids"].values())
    new_bid = last_bid + 100
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with con:
        user_id = con.execute(queries["user_id"], [telegram_id]).fetchall()[0][0]
        con.execute(queries["insert_bid_to_lot"], [lot_id, user_id, last_bid, current_datetime])

    second_place, third_place = None, None

    if len(buffer["Active"][str(lot_id)]["bids"].items()) == 2:  # Если есть 2 место
        sorted_items = sorted(buffer["Active"][str(lot_id)]["bids"].items(), key=lambda x: x[1], reverse=True)[1]
        with con:
            second_place_users_link = con.execute(queries["users_link"], [sorted_items[0]]).fetchall()[0][0]

        second_place = f"\n🥈 {sorted_items[1]}₽ {second_place_users_link[1:3]}***"
        third_place = None

    elif len(buffer["Active"][str(lot_id)]["bids"].items()) > 2:  # Если есть и 2 место и 3 место
        sorted_items = sorted(buffer["Active"][str(lot_id)]["bids"].items(), key=lambda x: x[1], reverse=True)[1:3]
        with con:
            second_place_users_link = con.execute(queries["users_link"], [sorted_items[0][0]]).fetchall()[0][0]
            third_place_users_link = con.execute(queries["users_link"], [sorted_items[1][0]]).fetchall()[0][0]

        second_place = f"\n🥈 {sorted_items[0][1]}₽ {second_place_users_link[1:3]}***"
        third_place = f"\n🥉 {sorted_items[1][1]}₽ {third_place_users_link[1:3]}***"

    text = lot_information(lot_id)
    text += "Следующая ставка: " + str(new_bid) + "₽"

    # ("Ваша скрытая ставка: " + "0" + "₽"))

    liders = f"\n\n🥇 {last_bid}₽ {users_link[1:3]}***"

    if second_place is not None:
        liders += second_place

    if third_place is not None:
        liders += third_place

    keyboard_for_chanel = Card(lot_id).chanel_card().keyboard
    keyboard_for_bot = Card(lot_id).bot_card().keyboard

    chanel_message_id = buffer["Active"][str(lot_id)]["message"]

    print(buffer)

    bot.edit_message_caption(caption=(text +
                                      liders),
                             chat_id=chanel,
                             message_id=chanel_message_id,
                             reply_markup=keyboard_for_chanel)

    for user_id, users_message in buffer["Active"][str(lot_id)]["user_opened"].items():
        # здесь необходимо учитывать скрытую ставку
        bot.edit_message_caption(caption=(text +
                                          liders),  # прямо здесь добавлять скрытую ставку и лидеров
                                 chat_id=user_id,
                                 message_id=users_message,
                                 reply_markup=keyboard_for_bot)


# Функция для просмотра истории
def show_history(telegram_id, message_id, lot_id, call_id):
    bot.answer_callback_query(callback_query_id=call_id, )

    if str(lot_id) in buffer["Active"].keys():
        keyboard = TradingHistory("ACTIVE_LOT").delete_bid().keyboard
    else:
        keyboard = TradingHistory(None).delete_bid().keyboard

    with con:
        bids_info = con.execute(queries["get_bids_by_lot"], [lot_id]).fetchall()

    if bids_info:
        text = "История ставок от пользователей по вашему лоту:\n"
        for info in bids_info:
            users_link, bid_amount, bid_date = info[0], info[1], info[2]
            text += f"{users_link}: {bid_amount} - {bid_date}\n"
    else:
        text = "Ставок по вашему лоту пока нет"

    bot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=text, reply_markup=keyboard)


# Информация о победителе лота
def winner_info(telegram_id, message_id, lot_id, call_id):
    bot.answer_callback_query(callback_query_id=call_id, )

    with con:
        winners_link = con.execute(queries["get_winners_link"], [lot_id]).fetchall()[0][0]
        user_id = con.execute(queries["get_winners_id"], [lot_id]).fetchall()[0][0]
        lot_title = con.execute(queries["lot_title"], [lot_id]).fetchall()[0][0]

    text = f"Победителем лота: \n {lot_title} \n является: {winners_link}"

    keyboard = TradingHistory(user_id).winner().keyboard

    bot.edit_message_text(chat_id=telegram_id, message_id=message_id, text=text, reply_markup=keyboard)


def timer():
    global remaining_time
    end_time = datetime.datetime.now() + timedelta(hours=24)

    while datetime.datetime.now() < end_time:
        remaining_time = end_time - datetime.datetime.now()

        time.sleep(1)

    send_lot("stop_auction")


def run_scheduler():
    while True:
        schedule.run_pending()


print("Started")
schedule.every().day.at('13:58').do(send_lot, "notification")
schedule.every().day.at('13:58').do(send_lot, "approvement")
update(case="Обновить администраторов")
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    bot.infinity_polling()
