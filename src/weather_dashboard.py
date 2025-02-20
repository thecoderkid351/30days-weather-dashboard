import os  # To interact with the operating system, like reading environment variables.
import json  # To handle the weather data in JSON format.
import boto3  # To interact with AWS and store the weather data in an S3 bucket.
import requests  # To send HTTP requests and fetch weather data from the web.
import matplotlib.pyplot as plt  # type: ignore # To plot visualizations of the weather data.
import seaborn as sns  # To enhance the visualization with styles.
from datetime import datetime  # To get the current date and time.
from dotenv import load_dotenv  # To load environment variables from a .env file safely.

# Load environment variables from the .env file (it contains secrets like your API key and AWS bucket name).
load_dotenv()

class WeatherDashboard:
    def __init__(self):
        # These are sensitive keys, so we load them securely from the .env file.
        self.api_key = os.getenv('OPENWEATHER_API_KEY')  # The API key for the weather service.
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')  # The name of the AWS bucket to store the data.
        self.s3_client = boto3.client('s3')  # This allows us to interact with AWS and save data to the bucket.

    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if the bucket already exists by trying to access it.
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket {self.bucket_name} exists")
        except:
            # If the bucket doesn't exist, create it.
            print(f"Creating bucket {self.bucket_name}")
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f"Successfully created bucket {self.bucket_name}")
            except Exception as e:
                print(f"Error creating bucket: {e}")

    def fetch_weather(self, city):
        """Fetch weather data from OpenWeather API"""
        # The URL for the weather API endpoint.
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        # Parameters to send in the request: city name, API key, and units (imperial means Fahrenheit).
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "imperial"
        }
        
        try:
            # Send a request to the weather service.
            response = requests.get(base_url, params=params)
            # Check if the response is successful (status code 200).
            response.raise_for_status()
            return response.json()  # If successful, return the data in JSON format.
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None  # If there's an error, return None.

    def save_to_s3(self, weather_data, city):
        """Save weather data to S3 bucket"""
        if not weather_data:
            return False  # If there is no weather data, return False.
            
        # Create a timestamp so we can save the data with the current time.
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        # Format the file name to include the city name and timestamp.
        file_name = f"weather-data/{city}-{timestamp}.json"
        
        try:
            # Add the timestamp to the weather data so we know when it was saved.
            weather_data['timestamp'] = timestamp
            # Save the weather data to the S3 bucket as a JSON file.
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(weather_data),  # Convert the data to JSON format before saving.
                ContentType='application/json'  # Tell AWS the file is JSON.
            )
            print(f"Successfully saved data for {city} to S3")
            return True
        except Exception as e:
            print(f"Error saving to S3: {e}")
            return False

    def plot_weather_data(self, weather_data, city):
        """Plot weather data (e.g., temperature, humidity)"""
        # Extract relevant weather data: temperature, feels like temperature, and humidity.
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        
        # Categories for the plot: the weather parameters we want to display.
        categories = ['Temperature (°F)', 'Feels Like (°F)', 'Humidity (%)']
        values = [temp, feels_like, humidity]
        
        # Set up a nice style for the plot using seaborn.
        sns.set(style="whitegrid")
        
        # Create a bar chart to visualize the weather data.
        plt.figure(figsize=(8, 5))
        plt.bar(categories, values, color=['#ff9999','#66b3ff','#99ff99'])
        
        # Title and labels for the chart.
        plt.title(f"Weather Data for {city}", fontsize=16)
        plt.ylabel('Value', fontsize=12)
        
        # Show the plot on the screen.
        plt.show()

def main():
    # Create a WeatherDashboard object to interact with the weather API and AWS.
    dashboard = WeatherDashboard()
    
    # Create the S3 bucket if it doesn't already exist.
    dashboard.create_bucket_if_not_exists()
    
    # List of cities to fetch the weather for.
    cities = ["Philadelphia", "Seattle", "New York"]
    
    for city in cities:
        print(f"\nFetching weather for {city}...")
        # Fetch the weather data for the city.
        weather_data = dashboard.fetch_weather(city)
        if weather_data:
            # If we got the weather data, print some details about it.
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            description = weather_data['weather'][0]['description']
            
            print(f"Temperature: {temp}°F")
            print(f"Feels like: {feels_like}°F")
            print(f"Humidity: {humidity}%")
            print(f"Conditions: {description}")
            
            # Save the weather data to the S3 bucket.
            success = dashboard.save_to_s3(weather_data, city)
            if success:
                print(f"Weather data for {city} saved to S3!")
                
            # Visualize the weather data in a bar chart.
            dashboard.plot_weather_data(weather_data, city)
        else:
            print(f"Failed to fetch weather data for {city}")

# This part runs the main function when the script is executed.
if __name__ == "__main__":
    main()
