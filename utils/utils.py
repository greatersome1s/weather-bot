from time import sleep
import telebot
from telebot.types import Message
from typing import Any
import sqlite3
import logging
import requests
import utils.constants as constants

def action_sleep(chat_id, bot: telebot.TeleBot, delay: float = 0.15):
    bot.send_chat_action(chat_id, "typing")
    sleep(delay)
    
# create all necessary database records for a new user
def check_database(msg: Message, logger: logging.Logger):
    try:
        database = sqlite3.connect(constants.DATABASE_LOCATION)
        # get data
        teleid = msg.from_user.id
        username = msg.from_user.username
        first_name = msg.from_user.first_name
        last_name = msg.from_user.last_name
        chat_id = msg.chat.id
        
        cursor = database.cursor()
        
        
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (teleid,))
        users = cursor.fetchone()
        
        if users:
            # check for records in other tables, in case of an old user
            
            # user_preferences table
            cursor.execute("SELECT id FROM user_preferences WHERE user_id = ?", users)
            if cursor.fetchone():
                pass
            else: 
                cursor.execute("""
                INSERT INTO user_preferences(user_id) VALUES (?)
                """, users)
                logger.info("Found no record of user in user_preferences. Sucessfully created a new record.")
                
            return True
        else:
            # users table
            cursor.execute("""
                           INSERT INTO users (telegram_id, username, first_name, last_name, chat_id)
                           VALUES (?, ?, ?, ?, ?)
                           """, (teleid, username, first_name, last_name, chat_id))
            
            # get user_id for future tables
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (teleid,))
            user_id = cursor.fetchone()[0]
            
            # user_preferences table
            cursor.execute("""
                           INSERT INTO user_preferences(user_id) VALUES (?)
                           """, (user_id,))
            
            logger.info(f"Succesfully created new user {msg.from_user.first_name}")
            return False
    except Exception as e:
        logger.error(f"Error while initializing a user: {e}")
        return None
    finally:
        database.commit()
        database.close()
    
# fetch something in database
def database_fetch(table: str, logger: logging.Logger, columns: list[str] = '*', conditions: dict[str, Any] | None = None):
    try:
        database = sqlite3.connect(constants.DATABASE_LOCATION)
        cursor = database.cursor()
        print(columns)
        # generate query
        query = "SELECT "
        
        # get columns into query
        for column in columns:
            if len(columns) - 1 == columns.index(column):
                query = query + column
            else:
                query = query + f"{column}, "
                
        # add the table into query
        query = query + f" FROM {table}"
                
        # get condition names and values
        condition_values = []
        
        if conditions:
            query = query + " WHERE "
            for index, (key, value) in enumerate(conditions.items()):
                if len(conditions) - 1 == index:
                    query = query + f"{key} = ?"
                else:
                    query = query + f"{key} = ? AND "
                condition_values.append(value)
                
        cursor.execute(query, (*condition_values,))
        if (result := cursor.fetchone()) != None:
            return result
        else:
            raise Exception(f"Found nothing.\nConditions: {conditions}\nColumns: {columns}")
    except Exception as e:
        logger.error(f"Error while fetching from database: {e}")
    finally:
        database.close()
                
        
        

# insert something into a table
def database_change(table: str, id: int, info: dict[str, Any], logger: logging.Logger):
    try: 
        database = sqlite3.connect(constants.DATABASE_LOCATION)
        cursor = database.cursor()
        
        set_query = "SET "
        set_info = []
        # generate query
        for index, (key, value) in enumerate(info.items()):
            if len(info) - 1 == index:
                set_query = set_query + f"{key} = ?"
            else:
                set_query = set_query + f"{key} = ?,"
                
            set_info.append(value)
            
        query = f"UPDATE {table} {set_query} WHERE id = ?"
        cursor.execute(query, (*set_info, id))
    except Exception as e:
        logger.error(f"Error while inserting value into a database: {e}")
    finally:
        database.commit()
        database.close()
    
def save_message(msg: Message, logger: logging.Logger):
    try:
        database = sqlite3.connect(constants.DATABASE_LOCATION)
        cursor = database.cursor()
        
        # get user id 
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (msg.from_user.id,))
        user_id = cursor.fetchone()[0]
        
        # required
        required_records = [msg.id, user_id, msg.date, msg.chat.id, msg.content_type]
        
        # depending on type
        if required_records[-1] == "text":
            cursor.execute("""
                           INSERT INTO messages (id, user_id, date, chat_id, content_type, text)
                           VALUES (?, ?, ?, ?, ?, ?)
                           """, (*required_records, msg.text))
        elif required_records[-1] == "location":
            cursor.execute("""
                           INSERT INTO messages (id, user_id, date, chat_id, content_type, lat, lon)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           """, (*required_records, msg.location.latitude, msg.location.longitude))
        # if message is a sticker
        elif msg.content_type == "sticker":
            cursor.execute("""
                           INSERT INTO messages (id, user_id, date, chat_id, content_type, file_id)
                           VALUES (?, ?, ?, ?, ?, ?)
                           """, (*required_records, msg.sticker.file_id))
        
            
    except Exception as e:
        logger.error(f"Error while saving a message {msg.id}: {e}")
    else:
        logger.debug(f"Saved message {required_records[0]} into message table.")
    finally:
        database.commit()
        database.close()
        
# get id in table from telegram id
def get_id_teleid(table:str, teleid: int, logger: logging.Logger) -> int:
    try:
        database = sqlite3.connect(constants.DATABASE_LOCATION)
        cursor = database.cursor()
        
        query = f"SELECT id FROM {table} WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)"
        cursor.execute(query, (teleid,))
        if (result := cursor.fetchone()) != None:
            return result[0]
        else:
            raise Exception(f"Failed to get id from teleid({teleid}) in table {table}")  
    except Exception as e:
        logger.error(e)
    finally:
        database.close()

# fetching weather from api. requests version
def get_weather_requests(lat: float, lon: float, measure: str, logger: logging.Logger):
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={constants.TOKEN_WEATHER}&units={measure}")
    
    if response:
        return response.json()
    else:
        logger.critical("got no response from weather server!")
        return None