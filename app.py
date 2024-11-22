from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)

# Retrieve API keys from environment variables
API_KEY = os.getenv('API_KEY')  # OpenWeatherMap API key
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # News API key

# Check if the API keys are loaded
if not API_KEY or not NEWS_API_KEY:
    raise ValueError("API_KEY and NEWS_API_KEY must be set in the .env file")

# Helper function to format datetime
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

# Register the custom filter for Jinja2 template formatting
app.jinja_env.filters['datetimeformat'] = datetimeformat

# Function to fetch current weather data
def get_weather_data(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()  # Will raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Weather API error: {e}")
        return None

# Function to fetch 5-day forecast
def get_forecast(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('list', [])
    except requests.exceptions.RequestException as e:
        print(f"Forecast API error: {e}")
        return []

# Function to fetch air quality data
def get_air_quality(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['list'][0]['main']['aqi']
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Air quality API error: {e}")
        return None

# Function to fetch UV index
def get_uv_index(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/uvi?lat={lat}&lon={lon}&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['value']
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"UV index API error: {e}")
        return None

# Function to fetch local weather news using NewsAPI
def get_local_weather_news(city):
    try:
        query = f"{city} weather alerts OR weather warnings OR storm OR weather forecast"
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()
        
        relevant_articles = [article for article in news_data['articles'] if 'weather' in article['title'].lower()]
        
        return relevant_articles[:5]  # Fetch top 5 news articles
    except requests.exceptions.RequestException as e:
        print(f"News API error: {e}")
        return []

# Function to generate activity suggestion based on weather
def get_activity_suggestion(weather_data):
    temp = weather_data['main']['temp']
    weather_desc = weather_data['weather'][0]['description']
    wind_speed = weather_data['wind']['speed']
    humidity = weather_data['main']['humidity']

    if "rain" in weather_desc or "thunderstorm" in weather_desc:
        return "It's rainy outside. Perfect time to stay indoors and enjoy a book or a movie!"
    elif "clear" in weather_desc and temp > 15 and temp < 25 and wind_speed < 5:
        return "It's a clear day. Great time for a walk in the park!"
    elif "snow" in weather_desc:
        return "Snowy day! Consider winter sports or stay cozy inside."
    elif temp > 25:
        return "It's warm outside! A perfect day for swimming or an ice cream outing."
    elif temp < 10:
        return "Cold weather! Bundle up if you're going out. Perfect for indoor activities."
    elif wind_speed > 15:
        return "It's quite windy. Outdoor activities might be challenging."
    else:
        return "It's a typical day. Perfect for a variety of activities!"

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data, forecast_data, air_quality, uv_index = None, [], None, None
    error_message = None
    activity_suggestion = None
    news_articles = []

    if request.method == 'POST':
        city = request.form['city']
        if not city.strip():
            error_message = "City name cannot be empty."
        else:
            weather_data = get_weather_data(city)
            if not weather_data or weather_data.get('cod') != 200:
                error_message = f"Could not fetch data for '{city}'. Please check the city name and try again."
            else:
                forecast_data = get_forecast(city)
                if 'coord' in weather_data:
                    lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']
                    air_quality = get_air_quality(lat, lon)
                    uv_index = get_uv_index(lat, lon)
                    activity_suggestion = get_activity_suggestion(weather_data)
                    news_articles = get_local_weather_news(city)

    return render_template(
        'index.html',
        weather=weather_data,
        forecast=forecast_data,
        air_quality=air_quality,
        uv_index=uv_index,
        error_message=error_message,
        activity_suggestion=activity_suggestion,
        news_articles=news_articles
    )

@app.route('/air_quality')
def air_quality_page():
    city = request.args.get('city', 'Southfield')  # default city if none is passed
    weather_data = get_weather_data(city)

    if not weather_data or weather_data.get('cod') != 200:
        return redirect(url_for('index'))

    lat, lon = weather_data['coord']['lat'], weather_data['coord']['lon']

    # Fetch air quality and UV index
    air_quality = get_air_quality(lat, lon)
    uv_index = get_uv_index(lat, lon)

    return render_template('air_quality.html', air_quality=air_quality, uv_index=uv_index)

@app.route('/extreme_weather')
def extreme_weather_page():
    city = request.args.get('city', 'Southfield')  # default city if none is passed
    weather_data = get_weather_data(city)

    if not weather_data or weather_data.get('cod') != 200:
        return redirect(url_for('index'))

    wind_speed = weather_data['wind']['speed']
    temperature = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']

    # Define basic extreme weather conditions
    weather_severity = "No storm indication"
    if wind_speed > 15:
        weather_severity = "Wind Advisory"
    elif temperature > 35:
        weather_severity = "Heat Warning"
    elif humidity > 80:
        weather_severity = "High Humidity Warning"

    return render_template('extreme_weather.html',
                           wind_speed=wind_speed,
                           temperature=temperature,
                           humidity=humidity,
                           weather_severity=weather_severity,
                           weather=weather_data,  # Pass weather data to the template
                           city=city)  # Pass city for navigation purposes
if __name__ == '__main__':
    app.run(debug=True, port=5000)
