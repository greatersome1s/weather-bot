# messages handler
import telebot
from utils.config import getLogger
from utils.utils import save_message, database_fetch
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import utils.constants as constants
import sqlite3


logger = getLogger()

def register_message_handler(bot: telebot.TeleBot):
    
    # sticker handler
    @bot.message_handler(content_types=['sticker'])
    def sticker(msg: Message):
        save_message(msg, logger)
    
    # location change or favorite adder confirmer
    @bot.message_handler(content_types=['location'])
    def location(msg: Message):
        save_message(msg, logger)
        
        try:
            teleid = msg.from_user.id
            user_id = database_fetch("users", logger, ['id'], {'telegram_id': teleid})
            
            if user_id:
                if location:
                    markup = InlineKeyboardMarkup()
                    # callback format: change-location:{user_id}:{msg_id}
                    yes = InlineKeyboardButton('Yes, change it', callback_data=f"change-location:{user_id[0]}:{msg.id}")
                    no = InlineKeyboardButton('No, cancel it', callback_data="cancel-location")
                    favorite = InlineKeyboardButton('Add as favorite', callback_data=f"add-favorite:{msg.id}") # args: msg.id
                    markup.row(yes, no)
                    markup.row(favorite)
                    bot.send_message(msg.chat.id, "Are you sure you want to change the forecast location?", reply_markup=markup)
                else:
                    change_location(None, msg.id, user_id[0])
        except Exception as e:
            logger.error(f"Error while handling location: {e}")
            
    # save all messages
    @bot.message_handler()
    def message(msg: Message):
        save_message(msg, logger)