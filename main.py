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


@bot.message_handler(commands=['start'])
def start(message):
    # Inlinekeyboard
    markup_0 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Отчёт", callback_data='order')
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    markup_0.add(item1, item2)
    # FirstBotMessage before Start
    bot.send_message(message.chat.id,
                     text='Привет. Я могу тебе помочь узнать отчёт автоэксперта об автомобиле по гос. номеру или VIN. Выбери нужное действие.',
                     reply_markup=markup_0)


@bot.message_handler(content_types='text')
def menu(message):
    bot.send_message(message.chat.id,
                     'Не пишите в чат лишнее...')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    row = {}
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
                        markup_25.add(item1, item2)
                        # Личный кабинет
                        with closing(pymysql.connect(host='127.0.0.1',
                                                     user='admin',
                                                     password='qwer1234',
                                                     db='userstelegram',
                                                     charset='utf8mb4',
                                                     cursorclass=DictCursor)) as connection:
                            with connection.cursor() as cursor:
                                query = f"""select telegram_bal_id, bal from usbal where telegram_bal_id = {call.message.chat.id};
                                               """
                                cursor.execute(query)
                                for rows in cursor:
                                    row = rows
                        bot.send_message(call.message.chat.id,
                                         text=f"""Ваш никальный id: {row['telegram_bal_id']}\nВаш баланс: {row['bal']}""",
                                         reply_markup=markup_25)
                    if call.data == 'next':
                        bot.register_next_step_handler(bot.send_message(call.message.chat.id,
                                                                        'Загрузите отчёт о компьютерной диагностике в формате PDF, TXT или скриншоты. До 3 файлов.'),
                                                       Comp_deagnos)
                    if call.data == 'next2':
                        bot.register_next_step_handler(bot.send_message(call.message.chat.id,
                                                                        'Загрузите отчёт о проверке по базам данных. До 4 файлов.'),
                                                       proverka_po_bd)
                    if call.data == 'next4':
                        bot.register_next_step_handler(bot.send_message(call.message.chat.id,
                                                                        'Опишите текстом кратко выявленные проблемы, состояние автомобиля.'),
                                                       sostoianie)

                    if call.data == 'add_recording':
                        markup_01 = types.InlineKeyboardMarkup()
                        item1 = types.InlineKeyboardButton("Назад", callback_data='menu')
                        markup_01.add(item1)
                        a = bot.send_message(call.message.chat.id,
                                             'Введите VIN автомобиля текстом: ', reply_markup=markup_01)

                        # Проверяем наличие вин или гос номера в БД
                        bot.register_next_step_handler(a, Vin_reg)

                else:
                    markup_26 = types.InlineKeyboardMarkup()
                    item1 = types.InlineKeyboardButton("Назад", callback_data='menu')
                    markup_26.add(item1)
                    bot.send_message(call.message.chat.id,
                                     text=f"""У вас нет доступа, не являетесь автоэкспертом""",
                                     reply_markup=markup_26)
            except Exception as e:
                print(repr(e))

            if call.data == 'order':
                b = bot.send_message(call.message.chat.id,
                                     'Введите VIN или гос. номер автомобиля, чтобы получить отчёт автоэксперта о проверке автомобиля')
                # Проверяем наличие вин или гос номера в БД
                bot.register_next_step_handler(b, Vin_mes)

            if call.data == 'menu':
                # Inlinekeyboard
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
                # FirstBotMessage before Start
                bot.send_message(call.message.chat.id,
                                 text='Вы находитесь в главном меню, выберите действие...',
                                 reply_markup=markup_1)
            if call.data == 'admin':
                markup_11 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Добавить автоэксперта", callback_data='add_auto')
                item2 = types.InlineKeyboardButton("Понизить автоэксперта", callback_data='del_auto')
                markup_11.add(item1)
                markup_11.add(item2)
                # Admin menu add/del
                bot.send_message(call.message.chat.id,
                                 text='Хотите добавить или понизить автоэксперта?',
                                 reply_markup=markup_11)
                # b = bot.send_message(call.message.chat.id,
                #                     'Выберите данные ')
                # Проверяем наличие вин или гос номера в БД
                # bot.register_next_step_handler(b, Vin_mes)

            if call.data == 'add_auto':
                markup_12 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Назад", callback_data='admin')
                item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                markup_12.add(item1, item2)
                b = bot.send_message(call.message.chat.id,
                                     'Перешлите сюда любое сообщение пользователя, которого хотите добавить',
                                     reply_markup=markup_12)
                bot.register_next_step_handler(b, add_autoexp)
            if call.data == 'del_auto':
                markup_13 = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("Назад", callback_data='admin')
                item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
                markup_13.add(item1, item2)
                pb = bot.send_message(call.message.chat.id,
                                      'Перешлите сюда любое сообщение пользователя, которого хотите понизить',
                                      reply_markup=markup_13)
                bot.register_next_step_handler(pb, del_autoexp)
            if call.data == 'withdraw':
                pass



    except Exception as e:
        print(repr(e))


def Vin_reg(message):
    result = re.match(r'[0-9AaBbCcDdeEFfgGhHjJkKlLmMnNpPrRsStTuUvVwWxXyYzZ]{17}\b', message.text)
    try:
        if result == None:
            a = bot.send_message(message.chat.id,
                             'VIN автомобиля введён неверно, введите ещё раз: ')
            bot.register_next_step_handler(a, Vin_reg)
        else:
            bot.send_message(message.chat.id,
                                 'VIN автомобиля успешно сохранён.')
            path, dirs, files = next(os.walk("Orders"))
            os.chdir('Orders')

            now = datetime.now()
            os.mkdir(f'{message.text}_{len(files)}_{now.strftime("%d.%m.%Y")}')
            os.chdir(f'{message.text}_{len(files)}_{now.strftime("%d.%m.%Y")}')
            with open('VIN.txt', 'w', encoding='utf-8') as f:
                f.write(message.text)

            bot.register_next_step_handler(bot.send_message(message.chat.id,
                             'Введите гос номер автомобиля: '), Gos_reg)
    except Exception as e:
        print(repr(e))

def Gos_reg(message):
    text = message.text.upper()
    result = re.match(r'[AАBВEЕKКMМHНOОPРCСTТYУXХ]{1}[0-9]{3}[АBВEЕKКMМHНOОPРCСTТYУXХ]{2}[0-9]{2,3}\b', text)
    try:
        if result == None:
            a = bot.send_message(message.chat.id,
                                 'Гос. номер автомобиля введён неверно, введите ещё раз: ')
            bot.register_next_step_handler(a, Gos_reg)
        else:
            bot.send_message(message.chat.id,
                             'Гос. номер автомобиля успешно сохранён.')

            with open('Gos_nomer.txt', 'w', encoding='utf-8') as f:
                f.write(text)

            bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                            'Загрузите фотографию VIN на кузове автомобиля: '),
                                           Photo_vin)

    except Exception as e:
        print(repr(e))



def Photo_vin(message):
    file_info = bot.get_file(message.photo[0].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open('Photo_vin.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.send_message(message.chat.id,
                     'Фотография VIN номера автомобиля успешно сохранена.')
    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    'Введите пробег автомобиля: '), Probeg_car)

def Probeg_car(message):

    with open('probeg.txt', 'w', encoding='utf-8') as f:
        f.write(message.text)

    bot.send_message(message.chat.id,
                     'Пробег автомобиля успешно сохранён.')

    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    """Загрузите фотографию разворота автомобиля с отметками об окрасах, ремонтах, замене деталей. 
                                                    Либо опишите эти данные текстом. Либо вы можете загрузить одно голосовое сообщение."""), Kuzov_info)

def Kuzov_info(message):
    if message.photo != None:
        file_info = bot.get_file(message.photo[0].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open('Photo_kuzov_info.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id,
                         'Фотография успешно загружена.')
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        'Загрузите фотографии дефектов кузова, салона, техники. До 20 файлов.'), photo_deffect_kuzov)
    elif message.text != None:
        with open('kuzov_info.txt', 'w', encoding='utf-8') as f:
            f.write(message.text)

        bot.send_message(message.chat.id,
                         'Информация о состоянии кузова успешно записана.')
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    'Загрузите фотографии дефектов кузова, салона, техники. До 20 файлов.'), photo_deffect_kuzov)
    elif message.voice != None:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('kuzov_info.mp3', 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id,
                         'Голосовое сообщение о состоянии кузова успешно записано.')
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        'Загрузите фотографии дефектов кузова, салона, техники. До 20 файлов.'), photo_deffect_kuzov)
    else:
        a = bot.send_message(message.chat.id,
                             'Я не могу разобрать, что вы мне отправили, введите ещё раз: ')
        bot.register_next_step_handler(a, Kuzov_info)

def photo_deffect_kuzov(message):
    try:

        i = message.photo[0]
        file_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(f'Photo_kuzov_info_{i.file_id}.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id,
                         f'Загружено: {i.file_id}')
        markup_222 = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Далее", callback_data='next')
        markup_222.add(item1)

        # FirstBotMessage before Start
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                         text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                         reply_markup=markup_222), photo_deffect_kuzov)
    except Exception as e:
        print(repr(e))
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        text='Что то пошло не так, загрузите ещё раз'), photo_deffect_kuzov)

def Comp_deagnos(message):
    try:
        if message.document != None:
            i = message.document
            file_name = i.file_name
            file_id = i.file_name
            file_id_info = bot.get_file(i.file_id)
            downloaded_file = bot.download_file(file_id_info.file_path)
            with open(f"Computer diagnostics{file_name}", 'wb') as new_file:
                new_file.write(downloaded_file)
                bot.send_message(message.chat.id, f'Загружено: {file_name}')
        elif message.photo != None:
            i = message.photo[0]
            file_info = bot.get_file(i.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            with open(f'Computer diagnostics{i.file_id}.jpg', 'wb') as new_file:
                new_file.write(downloaded_file)
            bot.send_message(message.chat.id,
                             f'Загружено: {i.file_id}')
        markup_222 = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Далее", callback_data='next2')
        markup_222.add(item1)
        # FirstBotMessage before Start
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                                                        reply_markup=markup_222), Comp_deagnos)
    except Exception as e:
        print(repr(e))
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        text='Что то пошло не так, загрузите ещё раз'), Comp_deagnos)

def proverka_po_bd(message):
    try:
        if message.document != None:
            i = message.document
            file_name = i.file_name
            file_id = i.file_name
            file_id_info = bot.get_file(i.file_id)
            downloaded_file = bot.download_file(file_id_info.file_path)
            with open(f"Computer diagnostics{file_name}", 'wb') as new_file:
                new_file.write(downloaded_file)
                bot.send_message(message.chat.id, f'Загружено: {file_name}')
        elif message.photo != None:
            i = message.photo[0]
            file_info = bot.get_file(i.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            with open(f'Computer diagnostics{i.file_id}.jpg', 'wb') as new_file:
                new_file.write(downloaded_file)
            bot.send_message(message.chat.id,
                             f'Загружено: {i.file_id}')
        markup_222 = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Далее", callback_data='next4')
        markup_222.add(item1)
        # FirstBotMessage before Start
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                                                        reply_markup=markup_222), proverka_po_bd)
    except Exception as e:
        print(repr(e))
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        text='Что то пошло не так, загрузите ещё раз', reply_markup=markup_222), proverka_po_bd)

def sostoianie(message):
    try:
        bot.send_message(message.chat.id,
                         'Состояние автомобиля успешно записано.')

        with open('Sostoianie.txt', 'w', encoding='utf-8') as f:
            f.write(message.text)

        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        'Запишите голосовое сообщение о состоянии автомобиля в целом и что не указали.'), golosovoe_sotoianie)
    except Exception as e:
        print(repr(e))

def golosovoe_sotoianie(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('sostoianie.mp3', 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.send_message(message.chat.id,
                         'Голосовое сообщение о состоянии кузова успешно записано.')
        directory_name = os.path.basename(os.getcwd())
        os.chdir('..')
        zip_name = directory_name
        # Create 'path\to\zip_file.zip'
        shutil.make_archive(zip_name, 'zip', directory_name)
        os.chdir(directory_name)
        with open('VIN.txt', 'r', encoding='utf-8') as f:
            print(f.read())
        with open('Gos_nomer.txt', 'r', encoding='utf-8') as f:
            print(f.read())
        time.sleep(2)
        path = os.path.join(os.path.abspath(os.path.dirname(os.getcwd())), directory_name)
        shutil.rmtree(path)

        markup_2223 = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Меню", callback_data='menu')
        markup_2223.add(item1)
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        'Отчёт успешно записан'),
                                       photo_deffect_kuzov, reply_markup=markup_2223)
    except Exception as e:
        print(repr(e))
        bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                        'Произошла ошибка, попробуйте ещё раз.'),
                                       golosovoe_sotoianie)
def Vin_mes(message):
    # Здесь подключаемся к БД и ищем наш VIN или гос. номер
    text = message.text
    bot.send_message(message.chat.id,
                     text.format(
                         message.from_user, bot.get_me()), parse_mode='html')
    # Inlinekeyboard
    markup_2 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Отчёт", callback_data='order')
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    markup_2.add(item1, item2)
    # FirstBotMessage before Start
    bot.send_message(message.chat.id,
                     text='По данному VIN (гос. номеру) пока нет отчёта автоэксперта. Заказать выездную проверку автомобиля автоэкспертом в любом регионе России: +7 (926) 266-42-22',
                     reply_markup=markup_2)


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


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.polling(none_stop=True)
