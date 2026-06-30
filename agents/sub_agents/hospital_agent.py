import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent
from database.db_connection import SessionLocal
from database.models import Hospital
from tools.geo_utils import calculate_haversine_distance

logger = logging.getLogger("disaster_assist.hospital_agent")

class HospitalDetail(BaseModel):
    name: str = Field(description="Name of the hospital")
    distance_miles: float = Field(description="Estimated travel distance in miles from the user")
    status: str = Field(description="Hospital status: OPERATIONAL, OVERLOADED, or INOPERATIVE")
    emergency_services_active: bool = Field(description="Whether general emergency/ER services are currently active")
    is_trauma_center: bool = Field(description="True if the hospital is a designated Level 1 or Level 2 trauma center")
    directions: str = Field(description="Directions based on offset coordinates")
    contact_phone: str = Field(description="Emergency contact phone number")

class HospitalOutput(BaseModel):
    user_latitude: float = Field(description="Latitude coordinate used for search")
    user_longitude: float = Field(description="Longitude coordinate used for search")
    hospitals: List[HospitalDetail] = Field(default=[], description="List of nearby hospitals sorted by proximity and operational status")
    recommended_hospital: Optional[str] = Field(None, description="Recommended hospital name based on proximity and operational status")
    guidance: str = Field(description="Critical travel and medical resource safety advice")


def query_nearby_hospitals(latitude: float, longitude: float) -> list:
    """Queries the SQLite database for hospitals and calculates distance details.
    
    Args:
        latitude: User latitude coordinate
        longitude: User longitude coordinate
        
    Returns:
        List of hospital details dictionaries.
    """
    db = SessionLocal()
    try:
        db_hospitals = db.query(Hospital).all()
        results = []
        
        for h in db_hospitals:
            dist = calculate_haversine_distance(latitude, longitude, h.latitude, h.longitude)
            
            # Simple directions generator based on lat/lon offsets
            lat_diff = h.latitude - latitude
            lon_diff = h.longitude - longitude
            ns = "North" if lat_diff >= 0 else "South"
            ew = "East" if lon_diff >= 0 else "West"
            directions = f"Head {ns}-{ew} for approximately {dist} miles towards the hospital entrance."
            
            # Mock trauma center designation for seed hospitals:
            # SFG is Level 1 Trauma, others might not be
            is_trauma = "general" in h.name.lower() or "sf general" in h.name.lower()
            
            results.append({
                "name": h.name,
                "distance_miles": dist,
                "status": h.status,
                "emergency_services_active": h.emergency_services,
                "is_trauma_center": is_trauma,
                "directions": directions,
                "contact_phone": h.contact_info or "Emergency 911"
            })
            
        # Sort by distance
        results.sort(key=lambda x: x["distance_miles"])
        return results
    finally:
        db.close()

hospital_agent = Agent(
    name="hospital_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=HospitalOutput,
    tools=[query_nearby_hospitals],
    description="Finds nearby emergency hospitals, checks ER and trauma services availability, and compiles routing directions.",
    instruction="""
    You are the specialized Hospital Worker agent.
    Your responsibility is to locate active medical care facilities for injured individuals.
    1. Read coordinates (latitude/longitude) from the task parameters or session history.
    2. Invoke the 'query_nearby_hospitals' tool with these coordinates.
    3. Analyze the returned hospitals list:
       - Filter for hospitals marked as 'OPERATIONAL' and where emergency_services_active is True.
       - If the user reported severe injuries or hemorrhage, prioritize designated 'is_trauma_center' hospitals.
       - Select the best operational match and set recommended_hospital.
    4. Compile the results into the structured HospitalOutput schema.
    5. Deliver safety guidance regarding medical travel (e.g. instructing to call 911 first for life-threatening situations, avoiding flooded routes).
    6. Call the finish_task tool to complete the task and return the structured JSON data.
    """
)
