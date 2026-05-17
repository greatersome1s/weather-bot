# callback button handler
import telebot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.util import quick_markup
import utils.constants as constants
import sqlite3
from utils.config import getLogger
from utils.utils import check_database, get_weather_requests, database_change, get_id_teleid, database_fetch, database_insert, database_delete
from handlers.commands import register_command_handler
from pycountry import countries

logger = getLogger()

def register_callback_handler(bot: telebot.TeleBot):
    # for button from /menu markup
    @bot.callback_query_handler(func = lambda callback: callback.data == "settings")
    def settings_callback(callback):
        register_command_handler(bot, "settings")(callback.message)
        bot.answer_callback_query(callback.id)

    # for button from /settings markup
    @bot.callback_query_handler(func = lambda callback: callback.data.startswith("edit-preferences"))
    def preferences(callback: CallbackQuery = None, msg_id: int = None, chat_id: int = None):
        data = callback.data.split(":")
        chat_id = data[1]
        
        if callback:
            # open database
            try:
                database = sqlite3.connect(constants.DATABASE_LOCATION)
                cursor = database.cursor()
                cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (chat_id,))
                user_id = cursor.fetchone()

                
                if user_id:
                    cursor.execute("SELECT * FROM user_preferences where user_id = ?", user_id)
                    if (user_preferences := cursor.fetchone()) != None:
                        # setup markup
                        buttons = {
                            "Measurement System": {'callback_data': f'change-preferences:{chat_id}:MEASURE'}
                        }
                        markup = quick_markup(buttons)
                        message = [f"Forecast location: {user_preferences[constants.DATABASE_INDEX_USER_PREFERENCES['location_desc']]} --> send geolocation to change\n" +
                                    f"Measurement system: {str.lower(user_preferences[constants.DATABASE_INDEX_USER_PREFERENCES['measure']])}\n" +
                                    f"Click buttons below to change your preferences"]
                        bot.send_message(callback.message.chat.id, message[0], reply_markup=markup)
                    else:
                        bot.send_message(chat_id, "Failed to fetch records for you in database. Use /start to fix this and try again.")
                        raise Exception("Failed to fetch records for user preferences")
                else:
                    # create a user
                    bot.send_message(chat_id, "Failed to fetch records for you in database. Use /start to fix this and try again.")
                    raise Exception("Failed to fetch records for user id")
                bot.answer_callback_query(callback.id)
            except Exception as e:
                logger.error(f"Error fetching from the database: {e}")
                bot.answer_callback_query(callback.id, "error fetching from the database")
            finally:
                database.close()
        elif callback == None and msg:
            buttons = {
                "Measurement System": {'callback_data': f'change-preferences:{msg.chat.id}:MEASURE'}
            }
            user_preferences = database_fetch('user_preferences', logger,
                                              conditions={"user_id": database_fetch("users", logger, ['id'], {'telegram_id': (msg.chat.id,)})})
            markup = quick_markup(buttons)
            message = [f"Forecast location: {user_preferences[constants.DATABASE_INDEX_USER_PREFERENCES['location_desc']]} --> send geolocation to change\n" +
                        f"Measurement system: {str.lower(user_preferences[constants.DATABASE_INDEX_USER_PREFERENCES['measure']])}\n" +
                        f"Click buttons below to change your preferences"]
            bot.edit_message_text(message, chat_id, msg_id, reply_markup=markup)
            
    # preference changer: choicer + handler
    # gets the callback to activate choicer from preferences function. After that user gets to choose option for change.
    # it checks if the callback args are in constants.PREFERENCE_CALLBACKS, if not --> check if they are args for the callbacks in constants.PREFERENCE_CALLBACKS_ARGS
    # if args, then handle the database data change, if callbacks, then handle the choicer
    @bot.callback_query_handler(func = lambda callback: callback.data.startswith("change-preferences"))
    def change_preferences(callback: CallbackQuery):
        # get the thing to change
        data = callback.data.split(':')
        chat_id = data[1]
        
        # if data in callbacks
        if data[2] in constants.PREFERENCE_CALLBACKS:
            # iterate over the callback args and make dict for buttons
            buttons = {}
            for arg in constants.PREFERENCE_CALLBACKS_ARGS[data[2]]:
                buttons[str.capitalize(arg)] = {'callback_data': f'change-preferences:{chat_id}:{arg}:{data[2]}:{callback.message.id}'}
            markup = quick_markup(buttons)
            bot.send_message(chat_id, f"Choose an option to change your preference for: *{str.capitalize(data[2])}*", "Markdown", reply_markup=markup)
            bot.answer_callback_query(callback.id)
        elif data[2] in constants.PREFERENCE_CALLBACKS_ARGS[data[3]]:
            bot.delete_message(chat_id, callback.message.id)
            database_change("user_preferences", get_id_teleid('user_preferences', chat_id, logger), {str.lower(data[3]): data[2]}, logger)
            # print(data)
            # preferences(msg_id=data[4], chat_id=data[3])
  
    # location related   
  
    # the location changer itself for the geolocation send (function below that one)
    @bot.callback_query_handler(func = lambda callback: callback.data.startswith("change-location"))
    def change_location(callback: CallbackQuery = None, msg_id:int = None, user_id:int = None):
        lat = None
        lon = None
        
        # get geo info from the callback query itself if there's one
        # get lattitude and longitude from message
        if callback:
            _, user_id, msg_id = callback.data.split(':')
        
        try:
            database = sqlite3.connect(constants.DATABASE_LOCATION)
            cursor = database.cursor()
            
            #extract info about message from table and insert
            if user_id and msg_id:
                lat, lon = database_fetch("messages", logger, ['lat', 'lon'], {'id': msg_id})
                measure = database_fetch("user_preferences", logger, ['measure'],
                                         {'user_id': user_id})
                
                # get location description
                json = get_weather_requests(lat, lon, measure, logger)
                flag_emoji = countries.get(alpha_2=json['sys']['country']).flag
                location_desc = f"{json['name']} {flag_emoji}"
                
                if lat and lon:
                    database_change("user_preferences", get_id_teleid('user_preferences', callback.message.chat.id, logger),
                                    {"lat": lat, "lon": lon, "location_desc": location_desc}, logger)
            
            logger.info(f"Changed user`s {user_id} forecast location to {lat, lon}")
        except Exception as e:
            logger.error(f"Error while changing location: {e}")
            bot.answer_callback_query(callback.id, "Error while changing location!")
            bot.edit_message_text("Error. Try again.", callback.message.chat.id, callback.message.id)
        else:
            bot.answer_callback_query(callback.id, "Success!")
            bot.edit_message_text("Sucessfully changed your prefered forecast location!" ,callback.message.chat.id, callback.message.id)
        finally:
            database.commit()
            database.close()
            
    # cancel location change
    @bot.callback_query_handler(lambda callback: callback.data == "cancel-location")
    def cancel_location(callback: CallbackQuery):
        bot.edit_message_text("Sucessfully canceled", callback.message.chat.id, callback.message.id)
        bot.answer_callback_query(callback.id, "Cancelled")
    
    # add favorite location
    @bot.callback_query_handler(lambda callback: callback.data.startswith("add-favorite"))
    def add_favorite(callback: CallbackQuery):
        # check if its within favorite limit
        fav = database_fetch("favorites", logger, conditions={'user_id': callback.message.chat.id})
        fav_num = 0
        if fav:
            fav_num = len(fav)
            
        if fav_num < constants.WEATHER_FAVORITE_LOCATIONS_MAX:
            # get data into the database
            msg_id = callback.data.split(':')[1]
            
            # fetch info on message
            info = database_fetch("messages", logger, ['lat', 'lon'], {'id': msg_id})[0]
            lat, lon = info
            
            json_array = get_weather_requests(lat, lon, logger)
            
            database_insert('favorites', logger, ['user_id', 'lat', 'lon', 'country', 'city'], [callback.message.chat.id, lat, lon, json_array['sys']['country'], json_array['name']])
            bot.answer_callback_query(callback.id, "Sucessfully added a favorite!")
            bot.delete_message(callback.message.chat.id, callback.message.id)
        else:
            bot.send_message(callback.message.chat.id, "Reached favorites limit. You can delete some favorite locations to add new ones.")
            bot.answer_callback_query(callback.id, "Reached limit!")
            bot.delete_message(callback.message.chat.id, callback.message.id)
    
    # remove favorite location
    @bot.callback_query_handler(lambda callback: callback.data.startswith('remove-favorite'))
    def remove_favorite(callback: CallbackQuery):
        args = callback.data.split(':')
        
        def remove_panel():
            favorites = database_fetch('favorites', logger, conditions={'user_id': callback.message.chat.id})
            
            buttons_array = []
            if favorites:
                for favorite in favorites:
                    flag_emoji = countries.get(alpha_2=favorite[constants.DATABASE_INDEX_FAVORITES['country']]).flag
                    country_title = countries.get(alpha_2=favorite[constants.DATABASE_INDEX_FAVORITES['country']]).name
                    title = f"{flag_emoji} {country_title}, {favorite[constants.DATABASE_INDEX_FAVORITES['city']]}"
                    buttons_array.append(InlineKeyboardButton(title, callback_data=f"remove-favorite:{favorite[constants.DATABASE_INDEX_FAVORITES['id']]}"))
                    
            markup = InlineKeyboardMarkup()
            markup.add(*buttons_array, row_width=2)
            bot.send_message(callback.message.chat.id, "*Remove favorite location*\nClick on the corresponding button below to delete a favorite location:", "Markdown", reply_markup=markup)
            bot.answer_callback_query(callback.id)
            
        def remove_favorite_instance(fav_id: int):
            city_name = database_fetch('favorites', logger, ['city'], {'id': fav_id})[0][0]
            if database_delete('favorites', {'id': fav_id}, logger):
                bot.edit_message_text(f"Sucessfully deleted favorite location '{city_name}'", callback.message.chat.id, callback.message.id)
                bot.answer_callback_query(callback.id)
            else:
                bot.edit_message_text(f"Failed to delete favorite: '{city_name}'.", callback.message.chat.id, callback.message.id)
                bot.answer_callback_query(callback.id)
                
        if len(args) == 1:
            remove_panel()
        elif len(args) == 2:
            remove_favorite_instance(args[1])
        else:
            logger.error(f"Got {len(args)} arguments on callback, while expecting 1 at most.")
            
    # weather for favorites panel
    @bot.callback_query_handler(lambda callback: callback.data.startswith('weather'))
    def weather_callback(callback: CallbackQuery):
        _, lat, lon = callback.data.split(":")
        weatherFunc = register_command_handler(bot, "weather")
        weatherFunc(latC=lat, lonC=lon, user_id=callback.message.chat.id)
        bot.answer_callback_query(callback.id)