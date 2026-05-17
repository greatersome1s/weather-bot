import os
from pathlib import Path

# utils

util_parent_location = Path(__file__).resolve() # current file path
util_mainDirectory_location = util_parent_location.parent.parent # weather-bot directory location

def util_get_globals():
    return globals()

# USED TO SAVE FREQUENTLY USED THINGIES

# DATABASE

DATABASE_LOCATION = util_mainDirectory_location / "database" / "data.db"

# database indexes, used when working with cursor.fetch functions - because they return tuples, not dicts
DATABASE_INDEX_USER_PREFERENCES = {
    'id': 0,
    'user_id': 1,
    'lat': 2,
    'lon': 3,
    'measure': 4,
    'broadcast_delay': 5,
    'location_desc': 6
}

DATABASE_INDEX_FAVORITES = {
    'id': 0,
    'user_id': 1,
    'lat': 2,
    'lon': 3,
    'country': 4,
    'city': 5
}

# TOKENS

TOKEN_TELEGRAM = os.environ.get("TOKEN")
TOKEN_WEATHER = os.environ.get("WEATHER_API_KEY")

# LOGGER

# log locations
LOGGER_APP = util_mainDirectory_location / "logs" / "app.log"
LOGGER_DEBUG = util_mainDirectory_location / "logs" / "debug.log"

# WEATHER RELATED

WEATHER_FAVORITE_LOCATIONS_MAX = 10

WEATHER_CLEAR = "\U00002600\uFE0F"
WEATHER_CLOUDS = "\U00002601\uFE0F"
WEATHER_RAIN = "\U0001F327\uFE0F"

WEATHER_METRIC = {
    "speed": "m/s",
    "temp": "°C",
    "distance": "m"
}
WEATHER_IMPERIAL = {
    "speed": "mph",
    "temp": "°F",
    "distance": "m"
}

# PREFERENCES

pref_util_callback = "change-preferences:"

PREFERENCE_CALLBACKS = ['MEASURE']
PREFERENCE_CALLBACKS_ARGS = {'MEASURE': ['IMPERIAL', 'METRIC']}