# messages handler
import telebot
from utils.config import getLogger
from utils.utils import save_message
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import utils.constants as constants
import sqlite3


logger = getLogger()

def register_message_handler(bot: telebot.TeleBot):
    
    # sticker handler
    @bot.message_handler(content_types=['sticker'])
    def sticker(msg: Message):
        save_message(msg, logger)
    
    # location change confirmer
    @bot.message_handler(content_types=['location'])
    def location(msg: Message):
        save_message(msg, logger)
        
        try:
            database = sqlite3.connect(constants.DATABASE_LOCATION)
            teleid = msg.from_user.id
            
            cursor = database.cursor()
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (teleid,))
            user_id = cursor.fetchone()
            
            if user_id:
                if location:
                    markup = InlineKeyboardMarkup()
                    # callback format: change-location:{user_id}:{msg_id}
                    yes = InlineKeyboardButton('Yes, change it', callback_data=f"change-location:{user_id[0]}:{msg.id}")
                    no = InlineKeyboardButton('No, cancel it', callback_data="cancel-location")
                    markup.row(yes, no)
                    bot.send_message(msg.chat.id, "Are you sure you want to change the forecast location?", reply_markup=markup)
                else:
                    change_location(None, msg.id, user_id[0])
        except Exception as e:
            logger.error(f"Error while handling location: {e}")
        finally:
            database.close()
            
    # save all messages
    @bot.message_handler()
    def message(msg: Message):
        save_message(msg, logger)