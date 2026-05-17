import telebot
from telebot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.util import quick_markup
from utils.utils import check_database, action_sleep, get_weather_requests, save_message, database_fetch
from utils.config import getLogger
import sqlite3
import utils.constants as constants
from emoji import emojize
from pycountry import countries
from datetime import datetime

logger = getLogger()

def register_command_handler(bot: telebot.TeleBot, get_function: str = None):
    
    # main menu /menu
    @bot.message_handler(commands=["menu"])
    def menu(msg: Message):
        menu_markup = InlineKeyboardMarkup()
        see_weather = InlineKeyboardButton("See weather", callback_data="see-weather")
        settings = InlineKeyboardButton("Settings", callback_data="settings")
        menu_markup.add(see_weather, settings)
        bot.send_message(msg.chat.id, "Menu! In progress...", reply_markup=keyboard_markup)
        save_message(msg, logger)
            
    # /start
    @bot.message_handler(commands=["start"])
    def start(msg: Message):
        action_sleep(msg.chat.id, bot)
        bot.send_message(msg.chat.id, "hey! welcome to yet another weather bot. learning purposes.")
        action_sleep(msg.chat.id, bot, .1)
        bot.send_message(msg.chat.id, "Fetching data from database...")
        
        database_result = check_database(msg, logger)
        
        if database_result == True:
            bot.send_message(msg.chat.id, f"Welcome, {msg.from_user.first_name}!")
        elif database_result == False:
            bot.send_message(msg.chat.id, "Successfully created new user in database!")
        else:
            bot.send_message(msg.chat.id, "Oops! An error happened! Try again please!")
            
        menu(msg)
        save_message(msg, logger)
        
    # settings panel /settings
    @bot.message_handler(commands=["settings"])
    def settings(msg: Message):
        markup = InlineKeyboardMarkup()
        edit_preferences = InlineKeyboardButton("Preferences", callback_data=f"edit-preferences:{msg.chat.id}") # args: chat_id
        markup.add(edit_preferences)
        bot.send_message(msg.chat.id, f"""
                        data from database TO DO

                        """, reply_markup=markup)
        save_message(msg, logger)
        
    # get weather by forecast location
    @bot.message_handler(commands=['weather'])
    def weather(msg: Message = None, latC = None, lonC = None, user_id = None):
        def weather_message(lat: float, lon: float, measure_sys, chat_id):
            # in requests for now
                json_array = get_weather_requests(lat, lon, logger, measure_sys)
                
                # get measurement system from constants
                measure_sys_const = constants.util_get_globals()[f'WEATHER_{measure_sys}']
                temp_const = measure_sys_const['temp']
                speed_const = measure_sys_const['speed']
                
                # extract everything from that array
                header_info = json_array['weather'][0]
                main_info = json_array['main']
                visibility = json_array['visibility']
                wind_info = json_array['wind']
                cloud_info = json_array['clouds']
                location_info = json_array['sys']
                
                # some variables for formatting
                main_emoji = constants.__dict__[f"WEATHER_{str.upper(header_info["main"])}"]
                flag_emoji = countries.get(alpha_2=location_info['country']).flag
                sunrise = datetime.fromtimestamp(location_info['sunrise']).strftime("%H:%M")
                sunset = datetime.fromtimestamp(location_info['sunset']).strftime("%H:%M")
                
                # concatenate everything here so you don't have to fuck your eyes over in the function call. \n for newline
                message_text = [f"{main_emoji} {header_info["main"]}, {header_info["description"]} {main_info["temp"]:.1f}{temp_const}\n" +
                                f"\U0001F4CD {json_array['name']} {flag_emoji}\n" +
                                f"\U0001F321\uFE0F Max: {main_info["temp_max"]:.1f}{temp_const}; Min: {main_info["temp_min"]:.1f}{temp_const}\n" +
                                f"Feels like: {main_info["feels_like"]:.1f}{temp_const}\n" +
                                f"\U0001F4A8 Wind speed: {wind_info['speed']} {speed_const}\n" +
                                f"\U0001F301 Visibility: {visibility} meters\n" +
                                f"\U0001F4C3 General information:\n" +
                                f"Pressure: {main_info['pressure']} hPa; Humidity: {main_info['humidity']}%\n" +
                                f"Sunrise: {sunrise}; Sunset: {sunset}"]
                
                
                bot.send_message(chat_id, message_text[0])
        
        # latC and lonC are used for weather callbacks
        if latC and lonC and user_id:
            measure = database_fetch('user_preferences', logger, ['measure'], {'user_id': database_fetch('users', logger, ['id'], {'telegram_id': user_id})[0][0]})[0][0] # user id from users table
            weather_message(latC, lonC, measure, user_id)
        else:
            # get lat lon from database
            lat = None
            lon = None
            measure_sys = None
            
            try:
                database = sqlite3.connect(constants.DATABASE_LOCATION)
                cursor = database.cursor()
                
                cursor.execute("""SELECT lat, lon, measure FROM user_preferences WHERE user_id = (
                    SELECT id FROM users WHERE telegram_id = ?
                )
                            """, (msg.from_user.id,))
                
                try:
                    lat, lon, measure_sys = cursor.fetchone()
                    
                    if lat == None or lon == None:
                        bot.send_message(msg.chat.id, "No prefered location found in database for you.\nSend your geolocation and confirm the change.")
                # if no user found in user_preferences
                except TypeError:
                    bot.reply_to(msg, "Failed to fetch your preferences from database!")
                    if check_database(msg, logger):
                        bot.send_message(msg.chat.id, "Sucesfully created all required records in database. Now you can try again!")
                    
                    
            except Exception as e:
                logger.error(f"Exception raised while acessing location preferences for user: {e}")
                
            # get weather    
            if lat and lon and measure_sys:
                weather_message(lat, lon, measure_sys, msg.chat.id)  
            save_message(msg, logger)
        
    # favorite locations
    @bot.message_handler(commands=['favorites'])
    def favorites(msg: Message):
        # max favorite locations
        favmax = constants.WEATHER_FAVORITE_LOCATIONS_MAX
        
        # get favorites
        favorites = database_fetch("favorites", logger, conditions={'user_id': msg.from_user.id})
        
        message_text = f"""
        *Favorite locations*\nClick on locations below to see current weather in that location.\nMaximum favorites = {favmax}
        """
                
        buttons_array = []
        
        if favorites:
            for favorite in favorites:
                flag_emoji = countries.get(alpha_2=favorite[constants.DATABASE_INDEX_FAVORITES['country']]).flag
                country_title = countries.get(alpha_2=favorite[constants.DATABASE_INDEX_FAVORITES['country']]).name
                title = f"{flag_emoji} {country_title}, {favorite[constants.DATABASE_INDEX_FAVORITES['city']]}"
                buttons_array.append(InlineKeyboardButton(title, callback_data=f"weather:{favorite[constants.DATABASE_INDEX_FAVORITES['lat']]}:{favorite[constants.DATABASE_INDEX_FAVORITES['lon']]}"))

        markup = InlineKeyboardMarkup()
        markup.add(*buttons_array, row_width=2)
        removebtn = InlineKeyboardButton("Remove favorite", callback_data='remove-favorite')
        markup.row(removebtn)
        bot.send_message(msg.chat.id, message_text, reply_markup=markup, parse_mode="Markdown")
                   
    # # weather settings
    # @bot.message_handler(commands=['weather_settings'])
    # def weather_settings(msg: Message):
    #     # send info and options regarding the weather: forecast setup; favorite locations; current prefered location (for /weather)
    #     reply_markup = quick_markup({
    #         "Forecast": {'callback_data: "forecast-setup"'},
    #         "Favorites": {'callback_data: "favorites'}
    #     })
    
    # get functions for callbacks
    if get_function:
        return locals()[get_function]