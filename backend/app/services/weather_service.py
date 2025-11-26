"""
Weather Data Service
Integrates with OpenWeatherMap API for current and historical weather data
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import httpx
import logging
from cachetools import TTLCache

from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching and processing weather data"""

    def __init__(self):
        """Initialize weather service with API configuration"""
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.historical_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"

        # Cache for weather data (1 hour TTL)
        self.cache = TTLCache(maxsize=1000, ttl=3600)

    async def get_current_weather(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict]:
        """
        Get current weather conditions for coordinates

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Weather data dictionary or None if error
        """
        cache_key = f"current_{lat}_{lon}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric"
                    },
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()

                weather_data = {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "wind_speed": data["wind"]["speed"],
                    "clouds": data["clouds"]["all"],
                    "description": data["weather"][0]["description"],
                    "timestamp": datetime.fromtimestamp(data["dt"]),
                }

                # Add precipitation if available
                if "rain" in data:
                    weather_data["rain_1h"] = data["rain"].get("1h", 0)
                    weather_data["rain_3h"] = data["rain"].get("3h", 0)

                if "snow" in data:
                    weather_data["snow_1h"] = data["snow"].get("1h", 0)

                self.cache[cache_key] = weather_data
                return weather_data

        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None

    async def get_weather_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7
    ) -> Optional[List[Dict]]:
        """
        Get weather forecast for next N days

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast (max 7 for free tier)

        Returns:
            List of daily forecast dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
                    },
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                forecasts = []

                for item in data["list"]:
                    forecast = {
                        "timestamp": datetime.fromtimestamp(item["dt"]),
                        "temperature": item["main"]["temp"],
                        "temp_min": item["main"]["temp_min"],
                        "temp_max": item["main"]["temp_max"],
                        "humidity": item["main"]["humidity"],
                        "precipitation_probability": item.get("pop", 0),
                        "description": item["weather"][0]["description"],
                    }

                    if "rain" in item:
                        forecast["rain_3h"] = item["rain"].get("3h", 0)

                    forecasts.append(forecast)

                return forecasts

        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return None

    async def get_historical_weather(
        self,
        lat: float,
        lon: float,
        date: datetime
    ) -> Optional[Dict]:
        """
        Get historical weather data for a specific date

        Args:
            lat: Latitude
            lon: Longitude
            date: Date to fetch weather for

        Returns:
            Historical weather data or None
        """
        try:
            timestamp = int(date.timestamp())

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.historical_url,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "dt": timestamp,
                        "appid": self.api_key,
                        "units": "metric"
                    },
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                current = data["current"]

                return {
                    "temperature": current["temp"],
                    "humidity": current["humidity"],
                    "pressure": current["pressure"],
                    "wind_speed": current["wind_speed"],
                    "clouds": current["clouds"],
                    "timestamp": datetime.fromtimestamp(current["dt"]),
                    "rain": current.get("rain", {}).get("1h", 0),
                }

        except Exception as e:
            logger.error(f"Error fetching historical weather: {e}")
            return None

    async def calculate_growing_degree_days(
        self,
        lat: float,
        lon: float,
        start_date: datetime,
        end_date: datetime,
        base_temp: float = 10.0,
        max_temp: float = 30.0
    ) -> float:
        """
        Calculate Growing Degree Days (GDD) for a period

        GDD is used to estimate plant growth and development

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date
            end_date: End date
            base_temp: Base temperature (°C)
            max_temp: Maximum effective temperature (°C)

        Returns:
            Total GDD for the period
        """
        total_gdd = 0.0
        current_date = start_date

        while current_date <= end_date:
            weather = await self.get_historical_weather(lat, lon, current_date)

            if weather:
                temp = weather["temperature"]

                # Calculate daily GDD
                if temp > base_temp:
                    daily_gdd = min(temp, max_temp) - base_temp
                    total_gdd += daily_gdd

            current_date += timedelta(days=1)

        return total_gdd

    def calculate_drought_risk(
        self,
        precipitation_60days: float,
        temperature_avg: float,
        humidity_avg: float,
        soil_type: str
    ) -> float:
        """
        Calculate drought risk probability (0-1)

        Args:
            precipitation_60days: Total precipitation in last 60 days (mm)
            temperature_avg: Average temperature (°C)
            humidity_avg: Average humidity (%)
            soil_type: Soil type classification

        Returns:
            Drought risk probability (0-1)
        """
        # Base risk from precipitation deficit
        # Normal precipitation for Serbia: ~60mm/month (120mm/60days)
        expected_precipitation = 120.0
        precip_ratio = precipitation_60days / expected_precipitation

        if precip_ratio >= 1.0:
            precip_risk = 0.0
        elif precip_ratio >= 0.7:
            precip_risk = 0.3
        elif precip_ratio >= 0.5:
            precip_risk = 0.6
        else:
            precip_risk = 0.9

        # Temperature stress factor
        if temperature_avg > 30:
            temp_factor = 1.3
        elif temperature_avg > 25:
            temp_factor = 1.1
        else:
            temp_factor = 1.0

        # Humidity factor
        if humidity_avg < 40:
            humidity_factor = 1.2
        elif humidity_avg < 60:
            humidity_factor = 1.1
        else:
            humidity_factor = 1.0

        # Soil water retention factor
        soil_factors = {
            "clay": 0.8,  # Good water retention
            "loam": 1.0,  # Medium retention
            "sandy": 1.3,  # Poor retention
        }
        soil_factor = soil_factors.get(soil_type, 1.0)

        # Calculate final risk
        risk = precip_risk * temp_factor * humidity_factor * soil_factor

        return min(risk, 1.0)

    def calculate_frost_risk(
        self,
        forecast_temps: List[float],
        crop_growth_stage: str
    ) -> float:
        """
        Calculate frost risk probability

        Args:
            forecast_temps: List of forecasted minimum temperatures (°C)
            crop_growth_stage: Growth stage (germination, vegetative, flowering, etc.)

        Returns:
            Frost risk probability (0-1)
        """
        # Critical temperatures by growth stage
        critical_temps = {
            "germination": 5,
            "vegetative": 0,
            "flowering": 3,
            "fruiting": 2,
            "ripening": 5,
        }

        critical_temp = critical_temps.get(crop_growth_stage, 0)

        # Find minimum temperature in forecast
        min_temp = min(forecast_temps)

        # Calculate risk
        if min_temp <= critical_temp:
            # Below critical temperature - high risk
            risk = 0.8 + (critical_temp - min_temp) * 0.05
        elif min_temp <= critical_temp + 3:
            # Within 3°C of critical - moderate risk
            risk = 0.4 + (critical_temp + 3 - min_temp) / 3 * 0.4
        else:
            # Well above critical - low risk
            risk = 0.1

        return min(risk, 1.0)

    async def get_weather_summary_for_parcel(
        self,
        lat: float,
        lon: float
    ) -> Dict:
        """
        Get comprehensive weather summary for a parcel

        Args:
            lat: Parcel centroid latitude
            lon: Parcel centroid longitude

        Returns:
            Weather summary dictionary
        """
        # Get current weather
        current = await self.get_current_weather(lat, lon)

        # Get 7-day forecast
        forecast = await self.get_weather_forecast(lat, lon, days=7)

        # Calculate aggregates
        if forecast:
            forecast_temps = [f["temp_min"] for f in forecast]
            total_precipitation = sum(f.get("rain_3h", 0) for f in forecast)
            avg_humidity = sum(f["humidity"] for f in forecast) / len(forecast)
        else:
            forecast_temps = []
            total_precipitation = 0
            avg_humidity = 0

        # Get historical data (last 60 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)

        # Calculate GDD
        gdd = await self.calculate_growing_degree_days(lat, lon, start_date, end_date)

        return {
            "current": current,
            "forecast": forecast,
            "forecast_precipitation_7days": total_precipitation,
            "forecast_avg_humidity": avg_humidity,
            "forecast_min_temp": min(forecast_temps) if forecast_temps else None,
            "forecast_max_temp": max(forecast_temps) if forecast_temps else None,
            "growing_degree_days_60d": gdd,
        }


# Singleton instance
weather_service = WeatherService()
