import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent
from database.db_connection import SessionLocal
from database.models import Alert
from tools.geo_utils import calculate_haversine_distance

logger = logging.getLogger("disaster_assist.weather_agent")

# Pydantic structured schemas for Google ADK 2.0 Task Output
class WeatherAlert(BaseModel):
    alert_type: str = Field(description="Type of warning: flood, cyclone, storm_surge, heavy_rain, tsunami, none")
    severity: str = Field(description="Severity rating: ADVISORY, WATCH, WARNING, NONE")
    details: str = Field(description="Detailed weather advisory description")

class WeatherOutput(BaseModel):
    current_temperature_f: float = Field(description="Current temperature in Fahrenheit")
    sky_condition: str = Field(description="Description of sky status (e.g. Heavy Rain, Cyclonic Winds, Sunny)")
    humidity_percentage: float = Field(description="Humidity percentage level")
    wind_speed_mph: float = Field(description="Wind speed velocity in mph")
    alerts: List[WeatherAlert] = Field(default=[], description="Active weather warnings and emergency watches near the user")
    rainfall_24h_inches: float = Field(description="Rainfall accumulated or forecast in the next 24 hours (inches)")
    predicted_risks: List[str] = Field(description="Predicted environmental risks (e.g. flash floods, mudslides, structural roof failures)")
    safety_advisory: str = Field(description="Specific weather safety instructions")


def get_meteorological_data(latitude: float, longitude: float) -> dict:
    """Simulates weather telemetry and queries the database for local geofenced alerts.
    
    Args:
        latitude: User latitude coordinate
        longitude: User longitude coordinate
        
    Returns:
        A dictionary containing meteorological measurements and database warnings.
    """
    db = SessionLocal()
    try:
        # Check active alerts in database matching this location
        db_alerts = db.query(Alert).filter(Alert.active == True).all()
        active_warnings = []
        has_heavy_rain = False
        has_tsunami = False
        
        for a in db_alerts:
            dist = calculate_haversine_distance(latitude, longitude, a.latitude, a.longitude)
            if dist <= a.radius_km:
                alert_lower = a.title.lower()
                atype = "none"
                if "flood" in alert_lower or "tsunami" in alert_lower:
                    atype = "tsunami" if "tsunami" in alert_lower else "flood"
                    has_tsunami = "tsunami" in alert_lower
                    has_heavy_rain = "flood" in alert_lower
                elif "cyclone" in alert_lower or "wind" in alert_lower or "storm" in alert_lower:
                    atype = "cyclone"
                
                active_warnings.append({
                    "alert_type": atype,
                    "severity": a.severity,
                    "details": a.description
                })
        
        # Synthesize local meteorological measurements based on active warnings
        # This keeps the mock telemetry aligned with the database seed alerts
        if has_tsunami:
            temp = 58.0
            condition = "Overcast, Coastal Sea Disturbances"
            wind = 28.5
            humidity = 95.0
            rain = 0.5
        elif has_heavy_rain:
            temp = 62.0
            condition = "Torrential Downpour"
            wind = 35.0
            humidity = 98.0
            rain = 5.8
        else:
            # Default mild storm condition for testing
            temp = 68.5
            condition = "Scattered Showers, Breezy"
            wind = 15.0
            humidity = 80.0
            rain = 1.2
            
        return {
            "temperature_f": temp,
            "condition": condition,
            "wind_speed_mph": wind,
            "humidity": humidity,
            "rainfall_24h_inches": rain,
            "db_alerts": active_warnings
        }
    finally:
        db.close()

weather_agent = Agent(
    name="weather_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=WeatherOutput,
    tools=[get_meteorological_data],
    description="Checks weather alerts, evaluates flood and cyclone risks, analyzes rainfall rate, and returns environmental hazards assessment.",
    instruction="""
    You are the specialized Weather Worker agent.
    Your responsibility is to analyze weather conditions and assess immediate hazard risks.
    1. Read coordinates (latitude/longitude) from the task parameters or session history.
    2. Invoke the 'get_meteorological_data' tool using these coordinates.
    3. Analyze the output metrics:
       - If rainfall_24h_inches is > 3.0 inches, highlight high Flash Flooding risks.
       - If wind_speed_mph is > 30.0 mph, predict risk of falling power lines and flying debris.
       - Review any active warnings from the database alerts.
    4. Populate all attributes in the WeatherOutput schema:
       - List active warnings under the alerts list.
       - Set predicted_risks to include specific environmental dangers.
       - Compile actionable safety advisories.
    5. Call the finish_task tool to complete the task and return the structured JSON data.
    """
)
