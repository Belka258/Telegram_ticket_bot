import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Token

token = Token.token

base = sqlite3.connect('tickets.db', check_same_thread=False)
cur = base.cursor()

base.execute('CREATE TABLE IF NOT EXISTS data(user_id, text, date_time, answer)')
base.commit()

log = sqlite3.connect('logs.db', check_same_thread=False)
logs_cur = log.cursor()

log.execute('CREATE TABLE IF NOT EXISTS data(user_id, text, answer, admin_id, date_get_question, date_get_answer)')
log.commit()

admins_base = sqlite3.connect('admins.db', check_same_thread=False)
admins_cur = admins_base.cursor()

admins_base.execute('CREATE TABLE IF NOT EXISTS data(admin_id)')
admins_base.commit()

ans_q_btn = types.InlineKeyboardButton('Ответить', callback_data='answer')
red_q_btn = types.InlineKeyboardButton('Перенаправить', callback_data='redirect')
dec_q_btn = types.InlineKeyboardButton('Отклонить', callback_data='decline')

ikm = types.InlineKeyboardMarkup().add(ans_q_btn).add(red_q_btn, dec_q_btn)

start_job_btn = types.KeyboardButton(text="✅ Начать работу")
stop_job_btn = types.KeyboardButton(text="❌ Закончить работу")
add_ticket_btn = types.KeyboardButton(text="❔ Ввести заявку")
find_ticket_btn = types.KeyboardButton(text="💬 Найти заявку")
stop_ticket_btn = types.KeyboardButton(text="❌ Остановить заполнение заявки")
add_admin_btn = types.KeyboardButton(text="➕ Добавить администратора")

rmk_offline = types.ReplyKeyboardMarkup(resize_keyboard=True)
rmk_offline.add(add_ticket_btn).add(start_job_btn).add(add_admin_btn)

rmk_online = types.ReplyKeyboardMarkup(resize_keyboard=True)
rmk_online.add(find_ticket_btn).add(stop_job_btn)

rmk_user = types.ReplyKeyboardMarkup(resize_keyboard=True).add(add_ticket_btn)

rmk_user_quest = types.ReplyKeyboardMarkup(resize_keyboard=True).add(add_ticket_btn).add(stop_ticket_btn)

types_admin_offline_buttons = {"✅ Начать работу",
                               "❔ Ввести заявку",
                               "➕ Добавить администратора"}

types_admin_online_buttons = {"💬 Найти заявку",
                              "❌ Закончить работу"}

types_user_buttons = {"❌ Остановить заполнение заявки"}

admins = {}

bot = telebot.TeleBot(token)

def update_admins():
    rows = admins_cur.execute('SELECT * FROM data').fetchall()
    for row in rows:
        admins[int(row[0])] = 'offline'
    print(admins)

def telegram_bot():
    @bot.message_handler(commands=['start', 'help'])
    def start_help(message):
        user_id = message.chat.id
        user_name = message.from_user.first_name

        if user_id in admins:
            msg = bot.send_message(user_id, user_name + ", вы имеете права администратора, что хотите сделать?",
                                   reply_markup=rmk_offline)
            bot.register_next_step_handler(msg, define_text)
        else:
            msg = bot.send_message(user_id,
                                   "Здравствуйте, " + user_name + "!\nНажмите, чтобы ввести заявку с вопросом или "
                                                            "предложением.\n(Первый оператор ответит на вашу заявку)",
                                   reply_markup=rmk_user)
            bot.register_next_step_handler(msg, define_text)

    @bot.message_handler(commands=['start_job'])
    def admin_start_job(message):
        user_id = message.chat.id
        user_name = message.from_user.first_name
        if user_id in admins:
            admin_id = message.chat.id
            admin_name = message.from_user.first_name
            admins[admin_id] = 'online'

            bot.send_message(admin_id, "Привет, " + admin_name + "!\nПриятной работы!", reply_markup=rmk_online)
            print(admins)
        else:
            bot.send_message(user_id, "Здравствуйте, " + user_name + "!\nВы не имеете прав администратора.",
                             reply_markup=rmk_user)

    @bot.message_handler(commands=['stop_job'])
    def admin_stop_job(message):
        user_id = message.chat.id
        user_name = message.from_user.first_name
        if user_id in admins:
            admin_id = message.chat.id
            admin_name = message.from_user.first_name
            admins[admin_id] = 'offline'

            cur.execute('UPDATE data SET answer == ? WHERE answer == ?',
                        ('0', str(admin_id)))
            base.commit()

            bot.send_message(admin_id, "Удачи, " + admin_name + "!\nПриятного отдыха!", reply_markup=rmk_offline)
            print(admins)
        else:
            bot.send_message(user_id, "Здравствуйте, " + user_name + "!\nвы не имеете прав администратора.",
                             reply_markup=rmk_user)

    def choice_admin_buttons(message):
        msg_text = message.text
        if msg_text == "✅ Начать работу":
            admin_start_job(message)
        elif msg_text == "❌ Закончить работу":
            admin_stop_job(message)
        elif msg_text == "❔ Ввести заявку":
            bot.send_message(message.chat.id,
                             "Введите заявку с вопросом или предложением.\n(Первый освободившийся оператор ответит на вашу заявку)",
                             reply_markup=rmk_user_quest)
            bot.register_next_step_handler(message, add_ticket)
        elif msg_text == "➕ Добавить администратора":
            bot.send_message(message.chat.id, "Введите id нового администратора",
                             reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, add_admin)
        else:
            find_ticket(message)

    @bot.message_handler(content_types=['text'])
    def define_text(message):
        user_id = message.chat.id
        msg_text = message.text

        if msg_text == "❔ Ввести заявку":
            bot.send_message(message.chat.id,
                             "Введите заявку с вопросом или предложением.\n(Первый освободившийся оператор ответит на вашу заявку)",
                             reply_markup=rmk_user_quest)
            bot.register_next_step_handler(message, add_ticket)
        elif user_id in admins and msg_text in types_admin_offline_buttons:
            choice_admin_buttons(message)
        elif user_id in admins and admins[user_id] == 'online' and msg_text in types_admin_online_buttons:
            choice_admin_buttons(message)
        else:
            bot.send_message(user_id, "Введите /start или нажмите на кнопку для продолжения", reply_markup=rmk_user)

    def add_ticket(message):
        user_id = message.chat.id
        date_time = datetime.now()
        text = message.text

        if text not in types_user_buttons:

            cur.execute('INSERT INTO data VALUES(?, ?, ?, ?)', (user_id, text, date_time, '0'))
            base.commit()

            bot.send_message(user_id, "Ваша заявка: \n\"" + text + "\"\n\nОбрабатывается, первый освободившийся оператор вам ответит!")

        else:
            define_text(message)

    def find_ticket(message):
        admin_id = message.chat.id

        row = cur.execute('SELECT * FROM data WHERE answer == ?', ('0',)).fetchone()
        if row is not None:
            user_id = row[0]
            text = row[1]
            date_time = row[2]

            cur.execute('UPDATE data SET answer == ? WHERE user_id == ? AND text == ? AND date_time == ?',
                        (str(admin_id), user_id, text, date_time))
            base.commit()

            bot.send_message(admin_id, "Заявка с вопросом: \n\"" + text + "\"\n\nХотите на неё ответить?",
                             reply_markup=ikm)

            @bot.callback_query_handler(func=lambda call: True)
            def callback_inline(call):

                if call.data == 'answer':
                    _text = call.message.text.replace("Заявка с вопросом: \n\"", '').replace(
                        "\"\n\nХотите на неё ответить?", '')

                    bot.delete_message(call.message.chat.id, call.message.id)

                    temp = bot.send_message(call.message.chat.id, "Введите ответ на заявку: \n\"" + _text + "\"")

                    bot.register_next_step_handler(call.message, answer_question_admin, _text, call.from_user.id, temp)

                elif call.data == 'redirect':
                    bot.delete_message(call.message.chat.id, call.message.id)

                    find_ticket(message)

                    cur.execute('UPDATE data SET answer == ? WHERE user_id == ? AND text == ? AND date_time == ? AND '
                                'answer == ?',
                                ('0', user_id, text, date_time, str(call.message.chat.id)))
                    base.commit()

                else:
                    bot.delete_message(call.message.chat.id, call.message.id)
                    bot.send_message(user_id,
                                     "Ваша заявка: \n\"" + text + "\"\n\nБыла отклонена")
                    cur.execute('DELETE FROM data WHERE user_id == ? AND text == ?',
                                (user_id, text))
                    base.commit()
                    logs_cur.execute("INSERT INTO data VALUES(?, ?, ?, ?, ?, ?)",
                                     (user_id, text, 'отклонено', admin_id, date_time, datetime.now()))
                    log.commit()

        else:
            bot.send_message(admin_id, "Нет записей в базе данных.\nПопробуйте снова через определенное время.")
            cur.execute('UPDATE data SET answer == ? WHERE answer == ?',
                        ('0', str(admin_id))).fetchone()
            base.commit()

    def answer_question_admin(message, text, admin_id, temp):
        answer = message.text

        row = cur.execute('SELECT * FROM data WHERE answer == ? and text == ?', (str(admin_id), text)).fetchone()
        if row is not None:
            user_id = row[0]
            text = row[1]
            date_time = row[2]

            if answer in types_admin_online_buttons:
                cur.execute('UPDATE data SET answer == ? WHERE user_id == ? AND text == ? AND date_time == ?',
                            (str(admin_id), user_id, text, date_time))
                base.commit()
                bot.delete_message(admin_id, temp.id)
                define_text(message)
                return

            cur.execute('UPDATE data SET answer == ? WHERE user_id == ? AND text == ? AND date_time == ?',
                        (answer, user_id, text, date_time))
            base.commit()

            bot.send_message(admin_id, "Отправлен ответ на заявку: \n\"" + text + "\"\n\nОтвет: \n\"" + answer + "\"")
            bot.delete_message(admin_id, temp.id)

            answer_question_user(user_id, text, answer, admin_id, date_time)

    def answer_question_user(user_id, text, answer, admin_id, date_time):
        bot.send_message(user_id, "На вашу заявку: \n\"" + text + "\"\n\nБыл дан ответ: \n\"" + answer + "\"")
        cur.execute('DELETE FROM data WHERE user_id == ? AND text == ? AND answer == ?',
                    (user_id, text, answer))
        base.commit()

        logs_cur.execute("INSERT INTO data VALUES(?, ?, ?, ?, ?, ?)", (user_id, text, answer, admin_id, date_time, datetime.now()))
        log.commit()

    def add_admin(message):
        rows = admins_cur.execute('SELECT * FROM data').fetchall()
        new_admin_id = message.text

        if 7 <= len(new_admin_id) <= 12:
            count = 0
            for row in rows:
                if str(row[0]) == str(new_admin_id):
                    bot.send_message(message.chat.id, "Такой id админа уже существует.", reply_markup=rmk_offline)
                    break
                elif str(row[0]) != str(new_admin_id):
                    count += 1

                if count == len(rows):
                    admins_cur.execute('INSERT INTO data VALUES(?)', (int(new_admin_id),))
                    admins_base.commit()
                    bot.send_message(message.chat.id, "Администратор успешно добавлен!", reply_markup=rmk_offline)
                    admins[int(new_admin_id)] = 'offline'
                    logs_cur.execute("INSERT INTO data VALUES(?, ?, ?, ?, ?, ?)",
                                     (new_admin_id, '', 'добавлен администратор', message.chat.id, '', datetime.now()))
                    log.commit()

        else:
            bot.send_message(message.chat.id, "Попробуйте ещё раз, длина id админа должна быть от 7 до 12",
                             reply_markup=rmk_offline)

    try:
        bot.infinity_polling()
    except:
        pass

if __name__ == '__main__':
    update_admins()
    telegram_bot()
