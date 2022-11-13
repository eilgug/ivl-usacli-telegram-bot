import os
import telebot as tb
import callback_handler as ch
from telebot import types
from telebot.types import InlineKeyboardButton
from telebot.callback_data import *
import prettytable as pt
from dotenv import load_dotenv
from datetime import date, datetime
from ivl_services import IVLServices

from flask import Flask, request
from api import blueprint

server = Flask(__name__)
server.register_blueprint(blueprint)

ivl_service = IVLServices()

load_dotenv()
API_KEY = os.getenv('API_KEY')
HOST = os.getenv('HOST');
bot = tb.TeleBot(API_KEY);


@bot.message_handler(commands=['alive'])
def test(message):
    bot.send_message(message.chat.id, "Hey! Sono vivo!");


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Ciao, ' + message.from_user.first_name + '!')


@bot.message_handler(commands=['classifica'])
def get_classifica(message):
    territory_data = ivl_service.get_territory()

    options = {}
    for territory in territory_data:
        callback_data = f"classifica|territory|{territory['id']}"
        options[territory['name']] = {'callback_data' : callback_data}

    reply_markup = tb.util.quick_markup(options, 2)
    bot.send_message(message.chat.id, "Che classifica vuoi conoscere?", reply_markup=reply_markup)

# --- OLD ---

# esegue le query inline
@bot.inline_handler(func=lambda query: query.query == 'test')
def query(inline_query):
    print("asdas")

@bot.chosen_inline_handler(func=lambda chosen_inline_result: '1')
def test_chosen(chosen_inline_result):
    print("asdadf")

#@bot.callback_query_handler(func=lambda call: call.data)

@bot.message_handler(commands=['nextmatch'])
def get_next_match(message):
    id_squadra = 509 #santa valeria
    from_today = date.today()

    data = IVLServices.get_calendar(from_today, id_squadra)

    next_match_team = pt.PrettyTable(['CASA','OSPITI'], max_width=10)
    next_match_team.add_row([data[0]['SquadraCasa'], data[0]['SquadraOspite']])

    res_message = f"<pre>{next_match_team}</pre>\n\n"
    d = datetime.strptime(data[0]['DataGioco'], "%Y-%m-%d %H:%M:%S")
    hour = d.strftime('%H:%M')
    day = d.strftime('%d/%m/%Y')
    res_message += f"<b>Data:</b> {day}\n"
    res_message += f"<b>Ora:</b> {hour}\n"

    print(next_match_team)
    bot.send_message(message.chat.id, res_message, parse_mode='html')

    print(f"LAT:{data[0]['Palestra_lat']} | LONG: {data[0]['Palestra_long']}")
    bot.send_location(message.chat.id, data[0]['Palestra_lat'],data[0]['Palestra_long'])

@bot.message_handler(commands=['calendario'])
def get_calendario(message):
    id_squadra = 509
    date_from = '2022-09-01T00:00:00.000Z'

    data = IVLServices.get_calendar(date_from, id_squadra)

    res_message = "Calendario <b>Oratorio Santa Valeria</b>:\n\n"
    calendar_table = pt.PrettyTable(['VS', "DATA/ORA"], max_width = 10)
    calendar_table.hrules = pt.ALL

    for row in data:
        d = datetime.strptime(row['DataGioco'], "%Y-%m-%d %H:%M:%S")
        hour = d.strftime('%H:%M')
        day = d.strftime('%d/%m/%Y')

        if row['squadra_casa_id'] == id_squadra:
            calendar_table.add_row([row['SquadraOspite'], f"{day}\n{hour}"])
        else:
            calendar_table.add_row([row['SquadraCasa'], f"{day}\n{hour}"])

    res_message += f"<pre>{calendar_table}</pre>"

    print(res_message)
    bot.send_message(message.chat.id, res_message, parse_mode='html')



# ---API---

@server.route('/' + API_KEY, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = tb.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=HOST + API_KEY)
    return "!", 200

@server.route("/stop")
def stop_webhook():
    bot.remove_webhook()
    bot.close()
    return "Bot stopped", 200


if __name__ == "__main__":
    bot.register_callback_query_handler(callback=ch.callback_leaderboard, func=lambda call: str(call.data).split(sep='|')[0] == 'classifica', pass_bot=True )
    bot.delete_webhook()
    bot.infinity_polling()
    #server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
