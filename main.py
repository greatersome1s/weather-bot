import telebot
import utils.constants as constants
from handlers.callbacks import register_callback_handler
from handlers.commands import register_command_handler
from handlers.messages import register_message_handler

# get token for da bot

bot = telebot.TeleBot(constants.TOKEN_TELEGRAM)

register_command_handler(bot)
register_message_handler(bot)
register_callback_handler(bot)
    
if __name__ == "__main__":
    bot.infinity_polling()