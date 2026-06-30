from google.adk.agents import Agent
from database.db_connection import SessionLocal
from database.models import Alert
from tools.geo_utils import calculate_haversine_distance

def get_active_alerts(latitude: float, longitude: float) -> list:
    """Queries the database for active geofenced warning and watch alerts.
    
    Args:
        latitude: User latitude coordinate
        longitude: User longitude coordinate
        
    Returns:
        A list of dict alerts matching coordinates.
    """
    db = SessionLocal()
    try:
        db_alerts = db.query(Alert).filter(Alert.active == True).all()
        matching_alerts = []
        for a in db_alerts:
            dist = calculate_haversine_distance(latitude, longitude, a.latitude, a.longitude)
            if dist <= a.radius_km:
                matching_alerts.append({
                    "title": a.title,
                    "description": a.description,
                    "severity": a.severity,
                    "distance_miles": dist
                })
        return matching_alerts
    finally:
        db.close()

info_agent = Agent(
    name="info_worker",
    model="gemini-2.5-flash",
    mode="chat", # Runs in standard chat mode for dialog
    tools=[get_active_alerts],
    description="Provides evacuation advice, general disaster safety rules, and real-time hazard alerts.",
    instruction="""
    You are the Disaster Info & Advice Worker.
    Your responsibility is to inform users about evacuation safety rules and real-time weather/alert advisories.
    1. Check if the user location (latitude/longitude) is available in context.
    2. If coordinates are present, invoke the 'get_active_alerts' tool to check if the user is in an active watch or warning zone.
    3. Synthesize the safety rules and instructions for the specific type of disaster discussed (e.g. floods, earthquakes, hurricanes, wildfires).
    4. Speak in a clear, authoritative, yet reassuring tone. Always highlight official guidelines (like following local authorities' orders).
    """
)
