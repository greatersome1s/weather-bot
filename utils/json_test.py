# used to get json files so I can analyze them comfortably later

import requests
import os
import json

lat = 50.490389
lon = 30.336228

response = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={os.environ.get("WEATHER_API_KEY")}")

data = response.json()

with open('example.json', 'w', newline='', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)