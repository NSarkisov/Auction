import telebot
import json
import sqlite3 as sl
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton

with open("Config.json") as settings:
    config = json.load(settings)
    Token = config.get("telegram_token")
    database = config.get("database_path")
    geocoder_api = config.get("geocoder_api")
    queries = config.get("queries")
bot = telebot.TeleBot(Token)
con = sl.connect(database, check_same_thread=False)

texts_dict = {"/start for user": ('Привет ,я бот аукционов @NScourse_bot\n'
                                  'Я помогу вам следить за выбранными лотами ,и регулировать\n'
                                  'ход аукциона.А так же буду следить за вашими накопленными\n'
                                  'балами.\n'
                                  'Удачных торгов 🤝'),
              "/start for admin": ('в бот аукционов @NScourse_bot\n'
                                   'Выберите необходимы для вас действия'),
              "my_lots": "",
              "rules": ("После окончания торгов,победитель должен выйти на связь с\n"
                        "продавцом\n"
                        "самостоятельно в течении суток‼️\n"
                        "Победитель обязан выкупить лот в течении ТРЁХ дней,после\n"
                        "окончания аукциона🔥\n"
                        "НЕ ВЫКУП ЛОТА - ПЕРМАНЕНТНЫЙ БАН ВО ВСЕХ\n"
                        "НУМИЗМАТИЧЕСКИХ СООБЩЕСТВАХ И АУКЦИОНАХ🤬\n"
                        "Что бы узнать время окончания аукциона,нажмите на ⏰\n"
                        "Антиснайпер - Ставка сделанная за 10 минут до\n"
                        "конца,автоматически переносит\n"
                        "Аукцион на 10 минут вперёд ‼️\n\n"
                        "Работают только проверенные продавцы,их Отзывы сумарно\n"
                        "достигают 10000+ на различных площадках.\n"
                        "Дополнительные Фото можно запросить у продавца.\n"
                        "Случайно сделал ставку?🤔\n"
                        "Напиши продавцу‼️\n\n\n"
                        "Отправка почтой,стоимость пересылки указана под фото.\n"
                        "Лоты можно копить ,экономя при этом на почте.\n"
                        "Отправка в течении трёх дней после оплаты‼️"),
              "help_info": ("Свяжитесь с нами, если у вас возникли вопросы @opt_monet\n"
                            "При проблемах или нахождении ошибок пишите @csv666")
              }
administrators_dict = {}


def update(case):
    update_type = {"Обновить администраторов": queries['searching_admins']}

    with con:
        query = con.execute(update_type[case]).fetchall()

    if case == "Обновить администраторов":
        for admin in query:
            first_name, last_name, telegram_id, telegram_link, phone = admin[1], admin[2], admin[3], admin[4], admin[5]
            email, access_level, started_time, ended_time = admin[6], admin[7], admin[8], admin[9],
            administrators_dict.update({telegram_id: {"first_name": first_name, "last_name": last_name,
                                                      "telegram_link": telegram_link, "phone": phone,
                                                      "email": email, "access_level": access_level,
                                                      "started_time": started_time, "ended_time": ended_time}})

    print(administrators_dict)


def greetings(telegram_id, *args):
    type_of_message = args[0]
    message_id = args[1]
    with con:
        balance = str(con.execute(queries['get_balance'], [telegram_id]).fetchall()[0][0])

    text = texts_dict['/start for user']

    starting = InlineKeyboardMarkup()

    my_lots = InlineKeyboardButton("Мои лоты", callback_data=json.dumps(['/start', "my_lots"]))
    users_balance = InlineKeyboardButton('Баланс: ' + balance + " BYN",
                                         callback_data=json.dumps(['/start', "my_balance"]))
    rules = InlineKeyboardButton("Правила", callback_data=json.dumps(['/start', "rules"]))
    help_info = InlineKeyboardButton("Помощь", callback_data=json.dumps(['/start', "help_info"]))

    # buttons for administrators

    # if telegram_id in administrators_dict.keys():

    starting.row(users_balance, my_lots)
    starting.row(rules, help_info)

    send = {"send": [bot.send_message, {'chat_id': telegram_id, "text": text, "reply_markup": starting}],
            "edit": [bot.edit_message_text, {'chat_id': telegram_id, 'message_id': message_id, "text": text,
                                             "reply_markup": starting}]}

    function, kwargs = send[type_of_message][0], send[type_of_message][1]

    function(**kwargs)


def personal_cabinet(button_info, chat_id, message_id):
    cabinet = InlineKeyboardMarkup()
    main_menu = InlineKeyboardButton("Главное меню", callback_data=json.dumps(["/home", "menu"]))
    cabinet.add(main_menu)
    # button_info can be "my_lots", "my_balance", "rules", "help_info" for taking texts from texts_dict
    text = texts_dict[button_info]
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=cabinet)


@bot.message_handler(content_types=['text', 'photo'])
def start(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    telegram_id = message.from_user.id
    telegram_link = "@" + message.from_user.username

    menu = {"/start": greetings, "/help": ""}

    if message.text in menu.keys():

        with con:
            searching = con.execute(queries["searching_user"], [telegram_id]).fetchall()

            if not searching:
                con.execute(queries["adding_user"], [first_name, last_name, telegram_id, telegram_link])

        menu[message.text](telegram_id, "send", None)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    bot.answer_callback_query(callback_query_id=call.id, )
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    call.data = json.loads(call.data)
    flag = call.data[0]
    button_info = call.data[1]
    callback = {'/start': (personal_cabinet, (button_info, chat_id, message_id)),
                '/home': (greetings, (chat_id, "edit", message_id))}

    function = callback[flag][0]
    args = callback[flag][1]

    function(*args)


print("Started")
update(case="Обновить администраторов")
bot.infinity_polling()
