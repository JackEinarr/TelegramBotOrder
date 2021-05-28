import telebot
from telebot import types

bot = telebot.TeleBot('1794397770:AAEQxxOMw2HDLE9uFOxbzP1hVtY8qo3SHQ0')

@bot.message_handler(commands=['start'])
def start(message):
    # Inlinekeyboard
    markup_0 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Отчёт", callback_data='order')
    item2 = types.InlineKeyboardButton("Меню", callback_data='menu')
    markup_0.add(item1, item2)
    # FirstBotMessage before Start
    a = bot.send_message(message.chat.id,
                     text='Привет. Я могу тебе помочь узнать отчёт автоэксперта об автомобиле по гос. номеру или VIN. Выбери нужное действие.',
                     reply_markup=markup_0)
    bot.register_next_step_handler(a, photo)

@bot.message_handler(content_types=["photo"])
def popo(message):
    try:
        i = message.photo[len(message.photo) - 1]
        file_info = bot.get_file(i.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f'Photo_kuzov_info_{i.file_id}.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id,
                         f'Загружено: {i.file_id}')
    except Exception as e:
        print(repr(e))
        bot.send_message(message.chat.id, text='Что то пошло не так, загрузите ещё раз')

def photo(message):
    markup_222 = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton("Далее", callback_data='next')
    markup_222.add(item1)

    # FirstBotMessage before Start
    bot.register_next_step_handler(bot.send_message(message.chat.id,
                                                    text='Чтобы продлжить нажмите "Далее", либо продолжайте закгрузку файлов',
                                                    reply_markup=markup_222), photo)

bot.polling(none_stop=True)

