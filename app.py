from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = '75d56929d092065857cffe81fb38afea'  # Replace with your API key

# Helper function to format the datetime
def datetimeformat(value):
    """Convert Unix timestamp to readable datetime."""
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['datetimeformat'] = datetimeformat

# Function to get current weather data for a city
def get_weather_data(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Weather API error: {e}")
        return None

# Function to get 5-day weather forecast for a city
def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('list', [])
    except requests.exceptions.RequestException as e:
        print(f"Forecast API error: {e}")
        return []

# Function to get air quality data for coordinates
def get_air_quality(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['list'][0]['main']['aqi']
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Air quality API error: {e}")
        return None

# Function to get UV index data for coordinates
def get_uv_index(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['value']
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"UV index API error: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data, forecast_data, air_quality, uv_index = None, [], None, None
    alerts = {}

    if request.method == 'POST':
        city = request.form['city']
        weather_data = get_weather_data(city)
        forecast_data = get_forecast(city)

        if weather_data and 'coord' in weather_data:
            lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']
            air_quality = get_air_quality(lat, lon)
            uv_index = get_uv_index(lat, lon)

            # Retrieve necessary data points for prediction criteria
            wind_speed = weather_data['wind']['speed']  # in m/s
            humidity = weather_data['main']['humidity']  # in %
            pressure = weather_data['main'].get('pressure')  # in hPa
            rainfall = weather_data.get('rain', {}).get('1h', 0)  # rainfall in mm for the last hour

            # Storm Prediction
            if wind_speed > 20 and humidity > 70 and pressure < 1000:
                alerts['storm'] = 'Storm alert: High winds and low pressure detected!'
            else:
                alerts['storm'] = 'No storm detected.'

            # Hurricane Prediction
            if wind_speed > 33 and pressure < 980:
                alerts['hurricane'] = 'Hurricane warning: Extremely high winds and low pressure!'
            else:
                alerts['hurricane'] = 'No hurricane detected.'

            # Flood Prediction
            if rainfall > 50 or (rainfall > 100 and humidity > 85):
                alerts['flood'] = 'Flood risk alert: Heavy rainfall detected!'
            else:
                alerts['flood'] = 'No flood detected.'

    return render_template(
        'index.html',
        weather=weather_data,
        forecast=forecast_data,
        air_quality=air_quality,
        uv_index=uv_index,
        alerts=alerts
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
