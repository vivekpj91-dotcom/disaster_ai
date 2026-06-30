import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent
from database.db_connection import SessionLocal
from database.models import Shelter
from tools.geo_utils import calculate_haversine_distance

logger = logging.getLogger("disaster_assist.shelter_agent")

class ShelterDetail(BaseModel):
    name: str = Field(description="Name of the shelter")
    distance_miles: float = Field(description="Estimated travel distance in miles from the user")
    capacity: int = Field(description="Total maximum capacity of the shelter")
    occupancy: int = Field(description="Current occupancy inside the shelter")
    spots_remaining: int = Field(description="Number of open spots left")
    status: str = Field(description="Shelter capacity status: OPEN, FULL, or CLOSED")
    address: str = Field(description="Street address of the shelter")
    directions: str = Field(description="Basic routing directions based on relative coordinate position")
    contact_phone: str = Field(description="Helpline contact number")

class ShelterOutput(BaseModel):
    user_latitude: float = Field(description="Latitude coordinate used for search")
    user_longitude: float = Field(description="Longitude coordinate used for search")
    shelters: List[ShelterDetail] = Field(default=[], description="List of nearby shelters sorted by proximity")
    recommended_shelter: Optional[str] = Field(None, description="The name of the best recommended open shelter nearest to the user")
    general_guidance: str = Field(description="Safety travel advice and alerts regarding routes")


def query_nearby_shelters(latitude: float, longitude: float) -> list:
    """Queries the SQLite database for shelters and calculates details.
    
    Args:
        latitude: User latitude coordinate
        longitude: User longitude coordinate
        
    Returns:
        List of shelter details dictionaries.
    """
    db = SessionLocal()
    try:
        db_shelters = db.query(Shelter).all()
        results = []
        
        for s in db_shelters:
            dist = calculate_haversine_distance(latitude, longitude, s.latitude, s.longitude)
            # Calculate open spots
            spots = max(0, s.capacity - s.occupancy)
            
            # Simple directions generator based on lat/lon offsets
            lat_diff = s.latitude - latitude
            lon_diff = s.longitude - longitude
            ns = "North" if lat_diff >= 0 else "South"
            ew = "East" if lon_diff >= 0 else "West"
            directions = f"Head {ns}-{ew} for approximately {dist} miles towards {s.address}."
            
            results.append({
                "name": s.name,
                "distance_miles": dist,
                "capacity": s.capacity,
                "occupancy": s.occupancy,
                "spots_remaining": spots,
                "status": s.status,
                "address": s.address or "Address not provided",
                "directions": directions,
                "contact_phone": s.contact_info or "Emergency Service Dispatcher"
            })
            
        # Sort by distance
        results.sort(key=lambda x: x["distance_miles"])
        return results
    finally:
        db.close()

shelter_agent = Agent(
    name="shelter_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=ShelterOutput,
    tools=[query_nearby_shelters],
    description="Finds nearby evacuation shelters, calculates travel distance, checks capacity availability, and compiles routing directions.",
    instruction="""
    You are the specialized Shelter Worker agent.
    Your responsibility is to locate safe evacuation zones for displaced citizens.
    1. Read coordinates (latitude/longitude) from the task parameters or session history.
    2. Invoke the 'query_nearby_shelters' tool with these coordinates.
    3. Analyze the returned shelters list:
       - Identify the nearest shelter that has status 'OPEN' and spots_remaining > 0.
       - Set it as the recommended_shelter.
       - Compile the list of shelters into the output schema format.
    4. Provide safety travel advice in the general_guidance field (e.g. warning against driving through flood waters, checking local traffic updates).
    5. Call the finish_task tool to complete the task and return the structured JSON data.
    """
)
