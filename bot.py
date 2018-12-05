import logging
import praw
import os
import telebot
import time
from dotenv import load_dotenv
import requests
import json

welcome_message = """
Hi there, I am Medicaldss Bot.
I am here to help you with leptospirosis!
Type /lepto to begin
"""

load_dotenv()

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(os.getenv("TG_API_TOKEN"))

if os.getenv("USE_PROXY"):
    telebot.apihelper.proxy = {'https': os.getenv("PROXY_STRING")}

class LabData:
    def __init__(self, *args, **kwargs):
        self.tromb = {"name": "Тромбоциты", "value": None}
        self.pti = {"name": "ПТИ", "value": None}
        self.fibr = {"name": "Фибриноген", "value": None}
        self.achtv = {"name": "АЧТВ", "value": None}
        self.sag = {"name": "Sag", "value": None}
        self.fv = {"name": "ФВ", "value": None}
        self.rkfm = {"name": "РКФМ", "value": None}

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, welcome_message)

@bot.message_handler(commands=['lepto'])
def calculate_diagnosis(message):
    lab_data = LabData()
    lab_data_gen = _get_lab_data_gen(lab_data)
    current_param = next(lab_data_gen)
    bot.reply_to(message, "{}?".format(
        _get_param_name(lab_data, current_param)
    ))
    bot.register_next_step_handler(
        message, get_step_handler(lab_data, lab_data_gen, current_param)
    )

def get_step_handler(lab_data, lab_gen, current_param):
    
    def handler(message):
        nonlocal lab_data, lab_gen, current_param
        
        try:
            _set_param(lab_data, current_param, float(message.text))
        except ValueError:
            msg = bot.reply_to(message, "Параметр {} должен быть числом. Заполните еще раз!".format(
                _get_param_name(lab_data, current_param)
            ))
            bot.register_next_step_handler(
                msg,
                get_step_handler(lab_data, lab_gen, current_param)
            )
            return
        
        try:
            current_param = next(lab_gen)
            msg = bot.send_message(message.chat.id, "{}?".format(
                _get_param_name(lab_data, current_param)
            ))
            bot.register_next_step_handler(
                msg,
                get_step_handler(lab_data, lab_gen, current_param)
            )
        except StopIteration:
            bot.send_message(message.chat.id, "Вариант коагулопатии: {}".format(
                _get_result(lab_data)
            ))

    return handler

def _get_result(lab_data):
    try:
        r = requests.post(
            "https://api.medicaldss.com/api/leptospirosis/neuralnetwork",
            json={
                param: getattr(lab_data, param)['value'] for param in dir(lab_data) if not param.startswith("_")
            }
        )
        return r.json()['coagulopathy_option']
    except Exception as e:
        logger.info(e)
        return "возникла ошибка при запросе данных"
        

def _get_lab_data_gen(lab_data):
    return (param for param in dir(lab_data) if not param.startswith("_"))

def _get_param_name(lab_data, param):
    return getattr(lab_data, param)['name']

def _set_param(lab_data, param, value):
    getattr(lab_data, param).update({"value": value})

if os.getenv("MODE") == "polling":
    bot.polling()

else:
    raise TypeError("Invalid MODE for telegram bot")