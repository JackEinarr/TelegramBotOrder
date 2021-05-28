import telebot
from telebot import types
from contextlib import closing
import pymysql
from pymysql.cursors import DictCursor
import re
import os
import time
from datetime import datetime
import shutil

bot = telebot.TeleBot('1161134538:AAGfv6cFfnuIkKM1k64a6lT_FZRHZ_cihQw')
data_users_orders = {}
last_recorded_data = {}
autoexp_rating = {}
l_list = []
m_markup_menu = types.InlineKeyboardMarkup()
item1 = types.InlineKeyboardButton("Меню", callback_data='menu')
m_markup_menu.add(item1)

@bot.message_handler(commands=['start'])
def start(message):
    b = bot.send_message(message.chat.id,
        'Введите VIN или гос. номер автомобиля, чтобы получить отчёт автоэксперта о проверке автомобиля', reply_markup=m_markup_menu)
    bot.register_next_step_handler(b, Vin_mes)

@bot.message_handler(content_types='text')
def menu(message):
    bot.send_message(message.chat.id,
                     'Не пишите в чат лишнее...', reply_markup=m_markup_menu)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    print(query)
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    global autoexp_rating
    links = message.successful_payment.invoice_payload
    try:
            # Здесь подключаемся к БД и выводим данные по link
        with closing(pymysql.connect(host='127.0.0.1',
                                     user='admin',
                                     password='qwer1234',
                                     db='userstelegram',
                                     charset='utf8mb4',
                                     cursorclass=DictCursor)) as connection:
            with connection.cursor() as cursor:
                query = f"""SELECT id_autoexp, date from orders where link = '{links}';"""
                cursor.execute(query)
                for rows in cursor:
                    id_autoexp = rows.get("id_autoexp")
                query = f"""UPDATE orders SET buy=buy+1 where link = '{links}';"""
                cursor.execute(query)
                query = f"""UPDATE usbal SET bal=bal+120 where telegram_bal_id = '{id_autoexp}';"""
                cursor.execute(query)
                connection.commit()
        tg_id = message.chat.id
        autoexp_rating.update({tg_id:id_autoexp})
        bot.send_document(tg_id, open(f'Orders/{links}.zip', 'rb'))
        markup_2544 = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("1", callback_data='review1')
        item2 = types.InlineKeyboardButton("2", callback_data='review2')
        item3 = types.InlineKeyboardButton("3", callback_data='review3')
        item4 = types.InlineKeyboardButton("4", callback_data='review4')
        item5 = types.InlineKeyboardButton("5", callback_data='review5')
        item6 = types.InlineKeyboardButton("Жалоба", callback_data='review6')
        markup_2544.row(item1, item2, item3)
        markup_2544.row(item4, item5)
        markup_2544.row(item6)
        bot.send_message(message.chat.id, 'Оцените насколько отчёт автоэксперта полон и полезен:',
                                                            reply_markup=markup_2544)
    except Exception as e:
        print(repr(e))

@bot.callback_query_handler(lambda call: call.data[:6] == 'review')
def review_recording(call):
    global autoexp_rating
    print(call.message)
    try:
        if call.data == 'review6':
            bot.register_next_step_handler(bot.send_message(call.message.chat.id,
                                                            'Опишите текстом суть жалобы на отчёт автоэксперта:'), review_complaint)
        else:
            if call.data == 'review1':
                t_rating = 0.1
            if call.data == 'review2':
                t_rating = 0.2
            if call.data == 'review3':
                t_rating = 0.3
            if call.data == 'review4':
                t_rating = 0.4
            if call.data == 'review5':
                t_rating = 0.5
            id_autoexp = autoexp_rating.get(call.message.chat.id)

            with closing(pymysql.connect(host='127.0.0.1',
                                         user='admin',
                                         password='qwer1234',
                                         db='userstelegram',
                                         charset='utf8mb4',
                                         cursorclass=DictCursor)) as connection:
                with connection.cursor() as cursor:
                    query = f"""UPDATE usbal SET rating=rating-0.3+{t_rating} where telegram_bal_id= '{id_autoexp}';"""
                    cursor.execute(query)
                    connection.commit()
            autoexp_rating.pop(call.message.chat.id)
            bot.edit_message_text(
                'Можете вернуться в меню',
                call.message.chat.id, call.message.message_id, reply_markup=m_markup_menu)
    except Exception as e:
        print(repr(e))

@bot.callback_query_handler(lambda call: call.data == 'order')
def call_order(call):
    b = bot.edit_message_text(
        'Введите VIN или гос. номер автомобиля, чтобы получить отчёт автоэксперта о проверке автомобиля',
        call.message.chat.id, call.message.message_id, reply_markup=m_markup_menu)
    bot.register_next_step_handler(b, Vin_mes)

# @bot.callback_query_handler(lambda call: call.data == 'my_orders')
# def call_pers_orders(call):
#     try:
#         tg_id = call.message.chat.id
#         with closing(pymysql.connect(host='127.0.0.1',
#                                      user='admin',
#                                      password='qwer1234',
#                                      db='userstelegram',
#                                      charset='utf8mb4',
#                                      cursorclass=DictCursor)) as connection:
#             with connection.cursor() as cursor:
#                 query = f"""SELECT link, date from orders where id_autoexp = '{tg_id}';"""
#                 cursor.execute(query)
#                 res = cursor
#         if res == None:
#             # Inlinekeyboard
#             markup_2 = types.InlineKeyboardMarkup()
#             item1 = types.InlineKeyboardButton("Назад", callback_data='personal_area')
#             item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
#             markup_2.add(item1, item2)
#             # FirstBotMessage before Start
#             bot.edit_message_text(f"""У вас нет ни одног автоотчёта""",
#                                   call.message.chat.id, call.message.message_id, reply_markup=markup_2)
#         else:
#             bot.send_message(message.chat.id,
#                              text=f'По данному VIN (гос. номеру) найдено отчётов: {cursor.rowcount}')
#             for rows in cursor:
#                 date = rows.get('date')
#                 link = rows.get("link")
#                 tg_id = message.chat.id
#                 bot.send_invoice(tg_id, title=f'Отчёт: {link[:-11]}',
#                                  description=f'Дата добавления отчёта: {date.strftime("%d-%m-%Y")}',
#                                  provider_token='381764678:TEST:26151',  # ТЕСТОВЫЙ ТОКЕН (TEST)
#                                  currency='RUB',
#                                  prices=[types.LabeledPrice(label='Руб', amount=12000)],
#                                  start_parameter='start_parameter',
#                                  invoice_payload=f'{link}')
#
#     except Exception as e:
#         print(repr(e))
#         else:
#         bot.send_message(message.chat.id,
#                      text=f'По данному VIN (гос. номеру) найдено отчётов: {cursor.rowcount}')
#         for rows in cursor:
#         date = rows.get('date')
#         link = rows.get("link")
#         tg_id = message.chat.id

@bot.callback_query_handler(lambda call: call.data in ['menu', 'personal_area','next','next2','next4','back',
                                                       'back1','back2','back3','back4','back5','back6','back7','back8','back9',
                                                       'add_recording', 'admin', 'add_auto', 'del_auto', 'withdraw'])
def callback_inline(call):
    row = {}
    global data_users_orders, last_recorded_data, l_list
    try:
        if call.message:
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

            try:
                with closing(pymysql.connect(host='127.0.0.1',
                                             user='admin',
                                             password='qwer1234',
                                             db='userstelegram',
                                             charset='utf8mb4',
                                             cursorclass=DictCursor)) as connection:
                    with connection.cursor() as cursor:
                        query = f"""
                        SELECT
                            autoexp, uadmin
                        FROM
                            uschar
                        WHERE
                            telegram_id = {call.message.chat.id};
                        """
                        cursor.execute(query)
                        for rows in cursor:
                            row = rows

                if row['autoexp'] != 0:
                    if call.data == 'personal_area':
                        markup_25 = types.InlineKeyboardMarkup()
                        item1 = types.InlineKeyboardButton("Назад", callback_data='menu')
                        item2 = types.InlineKeyboardButton("Вывести", callback_data='withdraw')
                        item3 = types.InlineKeyboardButton("Мои отчёты", callback_data='my_orders')
                        markup_25.row(item3)
                        markup_25.row(item1, item2)
                        # Личный кабинет
                        with closing(pymysql.connect(host='127.0.0.1',
                                                     user='admin',
                                                     password='qwer1234',
                                                     db='userstelegram',
                                                     charset='utf8mb4',
                                                     cursorclass=DictCursor)) as connection:
                            with connection.cursor() as cursor:
                                query = f"""select telegram_bal_id, bal from usbal where telegram_bal_id = {call.message.chat.id};"""
                                cursor.execute(query)
                                for rows in cursor:
                                    row = rows

                        bot.edit_message_text(f"""Ваш уникальный id: {row['telegram_bal_id']}\nВаш баланс: {row['bal']}""",
                                              call.message.chat.id, call.message.message_id, reply_markup=markup_25)
                    if call.data == 'next':
                        l_list.clear()
                        markup_254 = types.InlineKeyboardMarkup()
                        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                        item3 = types.InlineKeyboardButton("Назад", callback_data='back6')
                        markup_254.add(item3, item2)
                        b = bot.edit_message_text('Шаг 7 из 10\nЗагрузите отчёт о компьютерной диагностике в формате PDF, TXT или скриншоты. До 3 файлов.',
                            call.message.chat.id, call.message.message_id, reply_markup=markup_254)
                        bot.register_next_step_handler(b, Comp_deagnos)
                    if call.data == 'next2':
                        l_list.clear()
                        markup_253 = types.InlineKeyboardMarkup()
                        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                        item3 = types.InlineKeyboardButton("Назад", callback_data='back7')
                        markup_253.add(item3, item2)
                        b = bot.edit_message_text(
                            'Шаг 8 из 10\nЗагрузите отчёт о проверке по базам данных. До 4 файлов.',
                            call.message.chat.id, call.message.message_id, reply_markup=markup_253)
                        bot.register_next_step_handler(b, proverka_po_bd)
                    if call.data == 'next4':
                        l_list.clear()
                        markup_252 = types.InlineKeyboardMarkup()
                        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                        item3 = types.InlineKeyboardButton("Назад", callback_data='back8')
                        markup_252.add(item3, item2)
                        b = bot.edit_message_text(
                            'Шаг 9 из 10\nОпишите текстом кратко выявленные проблемы, состояние автомобиля.',
                            call.message.chat.id, call.message.message_id, reply_markup=markup_252)
                        bot.register_next_step_handler(b, sostoianie)
                    if call.data[:4] == 'back':
                        try:
                            deletes = last_recorded_data.get(call.message.chat.id)
                            for rem in deletes:
                                os.remove(os.path.join(data_users_orders.get(call.message.chat.id), rem))
                            last_recorded_data.update({call.message.chat.id: ''})
                        except Exception as e:
                            print(repr(e))

                        if call.data == 'back1':
                            os.rmdir(data_users_orders.get(call.message.chat.id))
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 1 из 10\nВведите VIN автомобиля текстом: ', reply_markup=m_markup_menu)

                            # Проверяем наличие вин или гос номера в БД
                            bot.register_next_step_handler(a, Vin_reg)

                        if call.data == 'back2':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 2 из 10\nВведите гос номер автомобиля: ', reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, Gos_reg)

                        if call.data == 'back3':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 3 из 10\nЗагрузите фотографию VIN на кузове автомобиля: ',
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, Photo_vin)

                        if call.data == 'back4':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 4 из 10\nВведите пробег автомобиля: ',
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, Probeg_car)

                        if call.data == 'back5':
                            a = bot.send_message(call.message.chat.id,
                                                 """Шаг 5 из 10\nЗагрузите фотографию разворота автомобиля с отметками об окрасах, ремонтах, замене деталей. 
                                                    Либо опишите эти данные текстом. Либо вы можете загрузить одно голосовое сообщение.""",
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, Kuzov_info)

                        if call.data == 'back6':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 6 из 10\nЗагрузите фотографии дефектов кузова, салона, техники. До 20 файлов.',
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, photo_deffect_kuzov)

                        if call.data == 'back7':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 7 из 10\nЗагрузите отчёт о компьютерной диагностике в формате PDF, TXT или скриншоты. До 3 файлов.',
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, Comp_deagnos)

                        if call.data == 'back8':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 8 из 10\nЗагрузите отчёт о проверке по базам данных. До 4 файлов.',
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, proverka_po_bd)

                        if call.data == 'back9':
                            a = bot.send_message(call.message.chat.id,
                                                 'Шаг 9 из 10\nОпишите текстом кратко выявленные проблемы, состояние автомобиля.',
                                                 reply_markup=m_markup_menu)
                            bot.register_next_step_handler(a, sostoianie)



                    if call.data == 'add_recording':
                        a = bot.edit_message_text('Шаг 1 из 10\nВведите VIN автомобиля текстом: ',
                                              call.message.chat.id, call.message.message_id, reply_markup=m_markup_menu)

                        # Проверяем наличие вин или гос номера в БД
                        bot.register_next_step_handler(a, Vin_reg)

                else:
                    bot.send_message(call.message.chat.id,
                                     text=f"""У вас нет доступа, не являетесь автоэкспертом""",
                                     reply_markup=m_markup_menu)
            except Exception as e:
                print(repr(e))

            if call.data == 'menu':
                # Inlinekeyboard
                try:
                    if data_users_orders.get(call.message.chat.id) != None:
                        shutil.rmtree(data_users_orders.get(call.message.chat.id))
                        data_users_orders.pop(call.message.chat.id)
                    if last_recorded_data.get(call.message.chat.id) != None:
                        last_recorded_data.pop(call.message.chat.id)
                except Exception as e:
                    print(repr(e))
                markup_1 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Отчёт", callback_data='order')
                # подключаем базу данных
                try:
                    with closing(pymysql.connect(host='127.0.0.1',
                                                 user='admin',
                                                 password='qwer1234',
                                                 db='userstelegram',
                                                 charset='utf8mb4',
                                                 cursorclass=DictCursor)) as connection:
                        with connection.cursor() as cursor:
                            query = f"""
                            SELECT
                                autoexp, uadmin
                            FROM
                                uschar
                            WHERE
                                telegram_id = {call.message.chat.id};
                            """
                            cursor.execute(query)
                            for rows in cursor:
                                row = rows

                    if row['autoexp'] != 0:
                        item2 = types.InlineKeyboardButton("Добавить запись", callback_data='add_recording')
                        item3 = types.InlineKeyboardButton("Личный кабинет", callback_data='personal_area')
                        markup_1.add(item2, item3)
                        if row['uadmin'] != 0:
                            item4 = types.InlineKeyboardButton("Админка", callback_data='admin')
                            markup_1.add(item4)
                except Exception as e:
                    print(repr(e))
                markup_1.add(item1)
                # FirstBotMessage menu
                bot.edit_message_text('Вы находитесь в главном меню, выберите действие...',
                                      call.message.chat.id, call.message.message_id, reply_markup=markup_1)
            if call.data == 'admin':
                markup_11 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Добавить автоэксперта", callback_data='add_auto')
                item2 = types.InlineKeyboardButton("Понизить автоэксперта", callback_data='del_auto')
                item3 = types.InlineKeyboardButton("Меню", callback_data='menu')
                markup_11.row(item1)
                markup_11.row(item2)
                markup_11.row(item3)
                # Admin menu add/del
                bot.edit_message_text('Хотите добавить или понизить автоэксперта?',
                                      call.message.chat.id, call.message.message_id, reply_markup=markup_11)

            if call.data == 'add_auto':
                markup_12 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Назад", callback_data='admin')
                item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                markup_12.add(item1, item2)
                b = bot.edit_message_text('Перешлите сюда любое сообщение пользователя, которого хотите добавить',
                                      call.message.chat.id, call.message.message_id, reply_markup=markup_12)
                bot.register_next_step_handler(b, add_autoexp)
            if call.data == 'del_auto':
                markup_13 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Назад", callback_data='admin')
                item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                markup_13.add(item1, item2)
                pb = bot.edit_message_text('Перешлите сюда любое сообщение пользователя, которого хотите понизить',
                                          call.message.chat.id, call.message.message_id, reply_markup=markup_13)
                bot.register_next_step_handler(pb, del_autoexp)
            if call.data == 'withdraw':
                pass



    except Exception as e:
        print(repr(e))

@bot.message_handler(content_types=["photo"])
def sand_photo(message):
    try:
        global data_users_orders, last_recorded_data, l_list
        i = message.photo[len(message.photo) - 1]
        file_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f'{i.file_id}.jpg'), 'wb') as new_file:
            new_file.write(downloaded_file)
        l_list.append(f'{i.file_id}.jpg')
        last_recorded_data.update({message.chat.id: l_list})
    except Exception as e:
        bot.send_message(message.chat.id, text='Не возможна отправка фото', reply_markup=m_markup_menu)

@bot.message_handler(content_types=["document"])
def document(message):
    try:
        global data_users_orders, last_recorded_data, l_list
        i = message.document
        file_name = i.file_name
        file_id = i.file_name
        file_id_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_id_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f"{file_name}"), 'wb') as new_file:
            new_file.write(downloaded_file)
        l_list.append(f"{file_name}")
        last_recorded_data.update({message.chat.id: l_list})

    except Exception as e:
        bot.send_message(message.chat.id, text='Не возможна отправка документа', reply_markup=m_markup_menu)

def Vin_reg(message):
    vin = transliterate(message.text.upper())
    result = re.match(r'[0-9AaBbCcDdeEFfgGhHjJkKlLmMnNpPrRsStTuUvVwWxXyYzZ]{17}\b', vin)

    if result == None:
        a = bot.send_message(message.chat.id,
                             'VIN автомобиля введён неверно, введите ещё раз: ', reply_markup=m_markup_menu)
        bot.register_next_step_handler(a, Vin_reg)
    else:
        try:
            with closing(pymysql.connect(host='127.0.0.1',
                                         user='admin',
                                         password='qwer1234',
                                         db='userstelegram',
                                         charset='utf8mb4',
                                         cursorclass=DictCursor)) as connection:
                with connection.cursor() as cursor:
                    now = datetime.now()
                    query = f"""SELECT COUNT(*) as count from orders where vin = '{vin}';"""
                    cursor.execute(query)
                    res = cursor.fetchone()
                    res = res['count']
                now = datetime.now()
                global data_users_orders, last_recorded_data
                data_users_orders.update({message.chat.id:os.path.join(os.getcwd(), 'Orders', f'{vin}_{res}_{now.strftime("%d.%m.%Y")}')})
                os.mkdir(data_users_orders.get(message.chat.id))
                with open(os.path.join(data_users_orders.get(message.chat.id), 'VIN.txt'), 'w', encoding='utf-8') as f:
                    f.write(vin)
                b_list = []
                b_list.append('VIN.txt')
                last_recorded_data.update({message.chat.id:b_list})
                markup_011 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Назад", callback_data='back1')
                item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                markup_011.add(item1, item2)
                bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                                'Шаг 2 из 10\nВведите гос номер автомобиля: ', reply_markup=markup_011), Gos_reg)
        except Exception as e:
            print(repr(e))

def Gos_reg(message):
    text = message.text.upper()
    result = re.match(r'[AАBВEЕKКMМHНOОPРCСTТYУXХ]{1}[0-9]{3}[AАBВEЕKКMМHНOОPРCСTТYУXХ]{2}[0-9]{2,3}\b', text)
    try:
        if result == None:
            a = bot.send_message(message.chat.id,
                                 'Гос. номер автомобиля введён неверно, введите ещё раз: ', reply_markup=m_markup_menu)
            bot.register_next_step_handler(a, Gos_reg)
        else:
            global data_users_orders,  last_recorded_data
            with open(os.path.join(data_users_orders.get(message.chat.id), 'Gos_nomer.txt'), 'w', encoding='utf-8') as f:
                f.write(transliterate(text))
            b_list = []
            b_list.append('Gos_nomer.txt')
            last_recorded_data.update({message.chat.id: b_list})

            markup_231 = types.InlineKeyboardMarkup()
            item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
            item1 = types.InlineKeyboardButton("Назад", callback_data='back2')
            markup_231.add(item1, item2)

            bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                            'Шаг 3 из 10\nЗагрузите фотографию VIN на кузове автомобиля: ', reply_markup=markup_231),
                                           Photo_vin)

    except Exception as e:
        print(repr(e))

def Photo_vin(message):
    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    global data_users_orders, last_recorded_data
    with open(os.path.join(data_users_orders.get(message.chat.id), 'Photo_vin.jpg'), 'wb') as new_file:
        new_file.write(downloaded_file)
    b_list = []
    b_list.append('Photo_vin.jpg')
    last_recorded_data.update({message.chat.id: b_list})

    markup_230 = types.InlineKeyboardMarkup()
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    item1 = types.InlineKeyboardButton("Назад", callback_data='back3')
    markup_230.add(item1, item2)

    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    'Шаг 4 из 10\nВведите пробег автомобиля: ', reply_markup=markup_230), Probeg_car)

def Probeg_car(message):
    global data_users_orders, last_recorded_data
    with open(os.path.join(data_users_orders.get(message.chat.id), 'probeg.txt'), 'w', encoding='utf-8') as f:
        f.write(message.text)
    b_list = []
    b_list.append('probeg.txt')
    last_recorded_data.update({message.chat.id: b_list})

    markup_229 = types.InlineKeyboardMarkup()
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    item1 = types.InlineKeyboardButton("Назад", callback_data='back4')
    markup_229.add(item1, item2)

    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    """Шаг 5 из 10\nЗагрузите фотографию разворота автомобиля с отметками об окрасах, ремонтах, замене деталей. 
                                                    Либо опишите эти данные текстом. Либо вы можете загрузить одно голосовое сообщение.""", reply_markup=markup_229),
                                   Kuzov_info)

def Kuzov_info(message):
    global data_users_orders, last_recorded_data
    markup_228 = types.InlineKeyboardMarkup()
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    item1 = types.InlineKeyboardButton("Назад", callback_data='back5')
    markup_228.add(item1, item2)
    if message.text != None:
        with open(os.path.join(data_users_orders.get(message.chat.id), 'kuzov_info.txt'), 'w', encoding='utf-8') as f:
            f.write(message.text)

        b_list = []
        b_list.append('kuzov_info.txt')
        last_recorded_data.update({message.chat.id: b_list})

    elif message.voice != None:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), 'kuzov_info.mp3'), 'wb') as new_file:
            new_file.write(downloaded_file)
        b_list = []
        b_list.append('kuzov_info.mp3')
        last_recorded_data.update({message.chat.id: b_list})

    elif message.photo != None:
        i = message.photo[len(message.photo) - 1]
        file_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f'{i.file_id}.jpg'), 'wb') as new_file:
            new_file.write(downloaded_file)
        b_list = []
        b_list.append(f'{i.file_id}.jpg')
        last_recorded_data.update({message.chat.id: b_list})

    elif message.document != None:
        i = message.document
        file_name = i.file_name
        file_id = i.file_name
        file_id_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_id_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f"{file_name}"), 'wb') as new_file:
            new_file.write(downloaded_file)
        b_list = []
        b_list.append(f"{file_name}")
        last_recorded_data.update({message.chat.id: b_list})

    else:
        a = bot.send_message(message.chat.id,
                             'Я не могу разобрать, что вы мне отправили, введите ещё раз: ')
        bot.register_next_step_handler(a, Kuzov_info)

    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    'Шаг 6 из 10\nЗагрузите фотографии дефектов кузова, салона, техники. До 20 файлов.',
                                                    reply_markup=markup_228),
                                   photo_deffect_kuzov)

def photo_deffect_kuzov(message):
    global data_users_orders, last_recorded_data, l_list
    i = message.photo[len(message.photo) - 1]
    file_info = bot.get_file(i.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(os.path.join(data_users_orders.get(message.chat.id), f'{i.file_id}.jpg'), 'wb') as new_file:
        new_file.write(downloaded_file)
    l_list.append(f'{i.file_id}.jpg')
    last_recorded_data.update({message.chat.id: l_list})
    markup_222 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Далее", callback_data='next')
    markup_222.add(item1)

    # FirstBotMessage before Start
    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                                                    reply_markup=markup_222), photo_deffect_kuzov)

def Comp_deagnos(message):
    global data_users_orders, last_recorded_data, l_list
    markup_228 = types.InlineKeyboardMarkup()
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    item1 = types.InlineKeyboardButton("Назад", callback_data='back5')
    markup_228.add(item1, item2)
    if message.document != None:
        i = message.document
        file_name = i.file_name
        file_id = i.file_name
        file_id_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_id_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f"{file_name}"), 'wb') as new_file:
            new_file.write(downloaded_file)
        l_list.append(f"{file_name}")
        last_recorded_data.update({message.chat.id: l_list})

    elif message.photo != None:
        i = message.photo[len(message.photo) - 1]
        file_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f'{i.file_id}.jpg'), 'wb') as new_file:
            new_file.write(downloaded_file)
        l_list.append(f'{i.file_id}.jpg')
        last_recorded_data.update({message.chat.id: l_list})
    else:
        a = bot.send_message(message.chat.id,
                             'Я не могу разобрать, что вы мне отправили, введите ещё раз: ')
        bot.register_next_step_handler(a, Comp_deagnos)


    markup_222 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Далее", callback_data='next2')
    markup_222.add(item1)
    # FirstBotMessage before Start
    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                                                    reply_markup=markup_222), Comp_deagnos)

def proverka_po_bd(message):
    global data_users_orders, last_recorded_data, l_list
    markup_228 = types.InlineKeyboardMarkup()
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    item1 = types.InlineKeyboardButton("Назад", callback_data='back5')
    markup_228.add(item1, item2)
    if message.document != None:
        i = message.document
        file_name = i.file_name
        file_id = i.file_name
        file_id_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_id_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f"{file_name}"), 'wb') as new_file:
            new_file.write(downloaded_file)
        l_list.append(f"{file_name}")
        last_recorded_data.update({message.chat.id: l_list})

    elif message.photo != None:
        i = message.photo[len(message.photo) - 1]
        file_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), f'{i.file_id}.jpg'), 'wb') as new_file:
            new_file.write(downloaded_file)
        l_list.append(f'{i.file_id}.jpg')
        last_recorded_data.update({message.chat.id: l_list})
    else:
        a = bot.send_message(message.chat.id,
                             'Я не могу разобрать, что вы мне отправили, введите ещё раз: ')
        bot.register_next_step_handler(a, proverka_po_bd)


    markup_222 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Далее", callback_data='next4')
    markup_222.add(item1)
    # FirstBotMessage before Start
    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                                                    reply_markup=markup_222), proverka_po_bd)

def sostoianie(message):
    try:
        global data_users_orders, last_recorded_data
        with open(os.path.join(data_users_orders.get(message.chat.id), 'Sostoianie.txt'), 'w', encoding='utf-8') as f:
            f.write(message.text)
        b_list = []
        b_list.append('Sostoianie.txt')
        last_recorded_data.update({message.chat.id: b_list})
        markup_227 = types.InlineKeyboardMarkup()
        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
        item1 = types.InlineKeyboardButton("Назад", callback_data='back9')
        markup_227.add(item1, item2)
        bot.register_next_step_handler(bot.send_message(message.chat.id,'Шаг 10 из 10\nЗапишите голосовое сообщение о состоянии автомобиля в целом и что не указали.',
                                                        reply_markup=markup_227), golosovoe_sotoianie)
    except Exception as e:
        print(repr(e))

def golosovoe_sotoianie(message):
    global data_users_orders, last_recorded_data
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(data_users_orders.get(message.chat.id), 'sostoianie.mp3'), 'wb') as new_file:
            new_file.write(downloaded_file)
        directory_name = os.path.basename(data_users_orders.get(message.chat.id))
        # Create 'path\to\zip_file.zip'
        with open(os.path.join(data_users_orders.get(message.chat.id), 'VIN.txt'), 'r', encoding='utf-8') as f:
            vins = f.read()
        with open(os.path.join(data_users_orders.get(message.chat.id), 'Gos_nomer.txt'), 'r', encoding='utf-8') as f:
            gos_number = f.read()

        with closing(pymysql.connect(host='127.0.0.1',
                                     user='admin',
                                     password='qwer1234',
                                     db='userstelegram',
                                     charset='utf8mb4',
                                     cursorclass=DictCursor)) as connection:
            with connection.cursor() as cursor:
                query = f"""INSERT into orders(id_autoexp, vin, gos_nomer, buy, date, link)
                values({message.chat.id}, '{vins}', '{gos_number}', 0, CURRENT_DATE(), '{directory_name}');"""
                cursor.execute(query)
                connection.commit()
        # Make zip archive file
        shutil.make_archive(os.path.join('Orders', directory_name), 'zip', os.path.join('Orders', directory_name))
        # Deleted file when loading order
        shutil.rmtree(os.path.join(data_users_orders.get(message.chat.id)))

        data_users_orders.pop(message.chat.id)
        last_recorded_data.pop(message.chat.id)

        bot.send_message(message.chat.id, 'Отчёт успешно записан', reply_markup=m_markup_menu)

    except Exception as e:
        print(repr(e))
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        'Произошла ошибка, попробуйте ещё раз.'),
                                       golosovoe_sotoianie)

def transliterate(name):
    # Слоаврь с заменами
    slovar = {'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
              'З': 'Z', 'И': 'I', 'Й': 'I', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
              'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Ф': 'F', 'Х': 'X',
              'Ц': 'C', 'Ю': 'U'}

    # Циклически заменяем все буквы в строке
    for key in slovar:
        name = name.replace(key, slovar[key])
    return name

def Vin_mes(message):
    try:
        vins = transliterate(message.text.upper())
        result = re.match(r'[0-9AАBВCСDДЕEFФГGНHJКKLМMNPRSTUVWXYZ]{17}\b', vins)
        result_gos_nomer = re.match(r'[AАBВEЕKКMМHНOОPРCСTТYУXХ]{1}[0-9]{3}[АBВEЕKКMМHНOОPРCСTТYУXХ]{2}[0-9]{2,3}\b', vins)

        if result == None and result_gos_nomer == None:
            a = bot.send_message(message.chat.id, 'VIN или гос. номер автомобиля введён неверно, введите ещё раз: ', reply_markup=m_markup_menu)
            bot.register_next_step_handler(a, Vin_mes)
        elif result != None:
            # Здесь подключаемся к БД и ищем наш VIN или гос. номер
            with closing(pymysql.connect(host='127.0.0.1',
                                         user='admin',
                                         password='qwer1234',
                                         db='userstelegram',
                                         charset='utf8mb4',
                                         cursorclass=DictCursor)) as connection:
                with connection.cursor() as cursor:
                    query = f"""SELECT link, date, rating FROM orders AS A LEFT JOIN usbal AS B ON (A.id_autoexp = B.telegram_bal_id) WHERE A.vin = '{vins}';"""
                    cursor.execute(query)
                    res = cursor
        else:
            with closing(pymysql.connect(host='127.0.0.1',
                                         user='admin',
                                         password='qwer1234',
                                         db='userstelegram',
                                         charset='utf8mb4',
                                         cursorclass=DictCursor)) as connection:
                with connection.cursor() as cursor:
                    query = f"""SELECT link, date, rating FROM orders AS A LEFT JOIN usbal AS B ON (A.id_autoexp = B.telegram_bal_id) WHERE A.gos_nomer = '{vins}';"""
                    cursor.execute(query)
                    res = cursor
        if cursor.rowcount == 0 or res == None:
            # Inlinekeyboard
            markup_2 = types.InlineKeyboardMarkup()
            item1 = types.InlineKeyboardButton("Отчёт", callback_data='order')
            item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
            markup_2.add(item1, item2)
            # FirstBotMessage before Start
            bot.send_message(message.chat.id, f"""По данному VIN (гос. номеру) пока нет отчёта автоэксперта. 
            Заказать выездную проверку автомобиля автоэкспертом в любом регионе России: +7 (926) 266-42-2""", reply_markup=markup_2)
        else:
            bot.send_message(message.chat.id,
                             text=f'По данному VIN (гос. номеру) найдено отчётов: {cursor.rowcount}')
            for rows in cursor:
                date = rows.get('date')
                link = rows.get("link")
                rating = rows.get("rating")
                tg_id = message.chat.id
                bot.send_invoice(tg_id, title=f'Отчёт: {link[:-11]}',
                                 description=f"""Дата добавления отчёта: {date.strftime("%d-%m-%Y")}
                                 
                                 Рейтинг автоэксперта: {rating}/10.0""",
                                 provider_token='381764678:TEST:26151', # ТЕСТОВЫЙ ТОКЕН (TEST)
                                 currency='RUB',
                                 prices=[types.LabeledPrice(label='Руб', amount=12000)],
                                 start_parameter='start_parameter',
                                 invoice_payload=f'{link}')

            bot.send_message(message.chat.id, 'Вернуться',
                         reply_markup=m_markup_menu)

    except Exception as e:
        print(repr(e))

# Добавляем в базу MySQL данные для повышения в автоэксперта
def add_autoexp(message):
    try:
        with closing(pymysql.connect(host='127.0.0.1',
                                     user='admin',
                                     password='qwer1234',
                                     db='userstelegram',
                                     charset='utf8mb4',
                                     cursorclass=DictCursor)) as connection:
            with connection.cursor() as cursor:
                query = f"""select autoexp from uschar where telegram_id = {message.forward_from.id};"""
                cursor.execute(query)
                for rows in cursor:
                    row = rows
                try:
                    if row['autoexp'] == 0:
                        query = f"""Update uschar set autoexp = 1 where telegram_id = {message.forward_from.id}"""
                        cursor.execute(query)
                        connection.commit()

                except Exception as e:
                    query = f"""INSERT into uschar(telegram_id, user, autoexp, uadmin)
                                                               values({message.forward_from.id}, 1, 1, 0);"""
                    cursor.execute(query)
                    connection.commit()
                    query = f"""INSERT into usbal(telegram_bal_id, bal) values({message.forward_from.id}, 0);"""
                    cursor.execute(query)
                    connection.commit()
                    print(repr(e))

        markup_20 = types.InlineKeyboardMarkup()
        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
        markup_20.add(item2)
        bot.send_message(message.chat.id,
                         text='Пользователь успешно добавлен в автоэксперты', reply_markup=markup_20)
    except Exception as e:
        markup_22 = types.InlineKeyboardMarkup()
        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
        markup_22.add(item2)
        bot.send_message(message.chat.id,
                         text='Произошла непредвиденная ошибка при добавлении', reply_markup=markup_22)
        print(repr(e))

# Изменяем autuexp с 1 на 0 в MySQL данные для понижения автоэксперта
def del_autoexp(message):
    try:
        with closing(pymysql.connect(host='127.0.0.1',
                                     user='admin',
                                     password='qwer1234',
                                     db='userstelegram',
                                     charset='utf8mb4',
                                     cursorclass=DictCursor)) as connection:
            with connection.cursor() as cursor:
                query = f"""UPDATE uschar SET autoexp = 0 WHERE telegram_id = '{message.forward_from.id}';
                               """
                cursor.execute(query)
                connection.commit()
        markup_23 = types.InlineKeyboardMarkup()
        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
        markup_23.add(item2)
        bot.send_message(message.chat.id,
                         text='Пользователь успешно понижен', reply_markup=markup_23)

    except Exception as e:
        markup_24 = types.InlineKeyboardMarkup()
        item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
        markup_24.add(item2)
        bot.send_message(message.chat.id,
                         text='Произошла непредвиденная ошибка при понижении', reply_markup=markup_24)
        print(repr(e))

def review_complaint(message):
    global autoexp_rating
    try:
        bot.send_message(message.chat.id,
                         f'Жалоба отправлена администратору на рассмотрение', reply_markup=m_markup_menu)
        id_autoexp = autoexp_rating.get(message.chat.id)
        bot.send_message(495629375, f'Жалоба пользователя: {message.chat.id}\nна автоэксперта:{id_autoexp}\nСообщение: {message.text}')
        autoexp_rating.pop(message.chat.id)
    except Exception as e:
        print(repr(e))

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True)
