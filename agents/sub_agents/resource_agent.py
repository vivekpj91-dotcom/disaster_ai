import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent
from tools.geo_utils import calculate_haversine_distance

logger = logging.getLogger("disaster_assist.resource_agent")

class ResourcePoint(BaseModel):
    name: str = Field(description="Name of the relief point or distribution station")
    resource_type: str = Field(description="Category: food_center, water_station, charging_station, fuel_station, relief_camp, government_service")
    distance_miles: float = Field(description="Calculated distance in miles from user coordinates")
    status: str = Field(description="Operational status: OPERATIONAL, LIMITED, CLOSED")
    address: str = Field(description="Physical address or local area marker")
    operational_hours: str = Field(description="Active operating hours or distribution schedules")
    details: str = Field(description="Available items (e.g. dry food rations, drinking water refills, diesel fuel, mobile device chargers)")

class ResourceWorkerOutput(BaseModel):
    user_latitude: float = Field(description="Latitude coordinate used for search")
    user_longitude: float = Field(description="Longitude coordinate used for search")
    resources: List[ResourcePoint] = Field(default=[], description="Nearby disaster relief points sorted by proximity")
    critical_advice: str = Field(description="Important safety alerts regarding travel and relief queues")


def query_relief_resources(latitude: float, longitude: float) -> list:
    """Simulates localized relief distribution resources near coordinates.
    
    Args:
        latitude: User latitude coordinate
        longitude: User longitude coordinate
        
    Returns:
        List of nearby resource dictionaries.
    """
    # Dynamic mock database containing distribution centers relative to coordinate zones
    catalog = [
        {
            "name": "Civic Center Food Distribution Hub",
            "resource_type": "food_center",
            "lat": 37.7794,
            "lon": -122.4174,
            "status": "OPERATIONAL",
            "address": "150 Larkins St, San Francisco, CA 94102",
            "operational_hours": "08:00 AM - 06:00 PM",
            "details": "Hot meals, dry rations, infant nutritional formula"
        },
        {
            "name": "Mission District Safe Water Refill Station",
            "resource_type": "water_station",
            "lat": 37.7604,
            "lon": -122.4194,
            "status": "OPERATIONAL",
            "address": "24th St & Mission St, San Francisco, CA 94110",
            "operational_hours": "24/7 Autopumps",
            "details": "Clean potable water tap, bring own container limit 5 gal/day"
        },
        {
            "name": "Chevron Emergency Fuel & Diesel",
            "resource_type": "fuel_station",
            "lat": 37.7654,
            "lon": -122.4094,
            "status": "LIMITED",
            "address": "2301 Market St, San Francisco, CA 94114",
            "operational_hours": "06:00 AM - 10:00 PM",
            "details": "Fuel limits: Max $50 per vehicle, generator canisters filled"
        },
        {
            "name": "Red Cross Relief Camp & Generator Station",
            "resource_type": "relief_camp",
            "lat": 37.7854,
            "lon": -122.4394,
            "status": "OPERATIONAL",
            "address": "Presidio Parade Ground, San Francisco, CA 94129",
            "operational_hours": "24 Hours",
            "details": "Temporary shelter beds, medical clinic triage, power charging strip bank"
        },
        {
            "name": "FEMA/City Crisis Services Office",
            "resource_type": "government_service",
            "lat": 37.7749,
            "lon": -122.4194,
            "status": "OPERATIONAL",
            "address": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
            "operational_hours": "08:00 AM - 08:00 PM",
            "details": "Disaster grant paperwork, emergency displacement vouchers, satellite communications"
        },
        {
            "name": "SoMa Public Charging & Solar Station",
            "resource_type": "charging_station",
            "lat": 37.7774,
            "lon": -122.3994,
            "status": "OPERATIONAL",
            "address": "4th St & King St, San Francisco, CA 94107",
            "operational_hours": "07:00 AM - 09:00 PM",
            "details": "Solar power arrays, standard USB and USB-C port availability"
        }
    ]
    
    results = []
    for c in catalog:
        dist = calculate_haversine_distance(latitude, longitude, c["lat"], c["lon"])
        if dist <= 15.0: # filter resources within 15 miles
            results.append({
                "name": c["name"],
                "resource_type": c["resource_type"],
                "distance_miles": dist,
                "status": c["status"],
                "address": c["address"],
                "operational_hours": c["operational_hours"],
                "details": c["details"]
            })
            
    results.sort(key=lambda x: x["distance_miles"])
    return results

resource_agent = Agent(
    name="resource_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=ResourceWorkerOutput,
    tools=[query_relief_resources],
    description="Locates nearby water, food, fuel, charging stations, relief camps, and government emergency services based on user location coordinates.",
    instruction="""
    You are the specialized Resource Worker agent.
    Your responsibility is to guide users to essential survival items and relief points.
    1. Read coordinates (latitude/longitude) from the task parameters or session history.
    2. Invoke the 'query_relief_resources' tool with these coordinates.
    3. Process the returned relief list:
       - Populate the ResourceWorkerOutput schema with nearby distribution points.
       - Focus recommendations based on what the user explicitly requested (e.g. charging ports, clean water, diesel).
    4. Compile the critical_advice field warning users of queue times, safety checks (avoiding travel near fallen wires or flooded roads), and supply limit constraints.
    5. Call the finish_task tool to complete the task and return the structured JSON data.
    """
)
