import os
import sys
import logging
from typing import List, Dict, Any

# Ensure project root is in path for relative database imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from mcp.server.fastmcp import FastMCP
from database.db_connection import SessionLocal
from database.models import Shelter, Hospital
from tools.geo_utils import calculate_haversine_distance

# Initialize FastMCP Server
mcp = FastMCP("DisasterAssist AI MCP Server")
logger = logging.getLogger("mcp_server")

# 1. Content Repositories for grounding manual checks
GUIDELINES_DB = {
    "flood": "FEMA Flood Evacuation Guidelines:\n- Move to high ground immediately. Do not wait for instructions.\n- Do not walk, swim, or drive through moving water. Just 6 inches of moving water can knock you down, and 1 foot can sweep your vehicle away.\n- Keep children and pets away from drainage ditches, storm drains, and flooded zones.",
    "cyclone": "National Hurricane / Cyclone Safety Manual:\n- Locate the safest room in your residence (interior room, hallway, closet, or basement on the lowest floor) away from glass doors or windows.\n- If in a storm surge zone, evacuate immediately along official designated routes.\n- Keep a battery-operated NOAA weather radio active.",
    "earthquake": "USGS Earthquake Survival Steps:\n- DROP down onto your hands and knees.\n- COVER your head and neck under a sturdy table or desk.\n- HOLD ON to your shelter until shaking stops.\n- If outdoors, move to a clear area away from buildings, power lines, and streetlights.",
    "wildfire": "National Wildfire Prep & Evacuation Guide:\n- Clear a 30-foot defensible perimeter around your home by removing dry brush and leaves.\n- Evacuate immediately if local authorities issue an evacuation warning or order.\n- Close all windows, doors, and shut off gas supply valves at the main meter before leaving.",
    "heatwave": "CDC Heatwave and Extreme Heat Guide:\n- Stay in air-conditioned buildings. If air conditioning is unavailable, go to a public cooling center.\n- Drink more water than usual; do not wait until you are thirsty. Avoid caffeine and alcohol.\n- Never leave children or pets in a parked vehicle under any circumstances."
}

FIRST_AID_DB = {
    "bleeding": "Bleeding Control Protocol:\n1. Apply direct pressure to the wound using a clean sterile bandage or cloth.\n2. Keep pressure firm and constant until bleeding stops.\n3. Elevate the wound above the level of the heart if possible.\n4. If bleeding is life-threatening and doesn't stop, apply a tourniquet high and tight on the limb.",
    "burns": "First Aid for Thermal Burns:\n1. Cool the burn immediately with cool, running tap water for 10 to 20 minutes (do not use ice or freezing water).\n2. Remove any rings or tight clothing from the area before swelling begins.\n3. Cover the burn loosely with a clean, non-stick sterile dressing.\n4. Do not apply ointments, butter, or puncture blisters.",
    "cpr": "Hands-Only CPR Steps:\n1. Verify safety, tap the victim, and call 911 immediately.\n2. Place hands in the center of the chest and push hard and fast (100 to 120 compressions per minute to the beat of 'Staying Alive').\n3. Allow the chest to return to its normal position between compressions.",
    "choking": "Choking First Aid (Heimlich Maneuver):\n1. Stand behind the person, wrap your arms around their waist.\n2. Make a fist, place it slightly above the navel.\n3. Grasp the fist with your other hand and press hard into the abdomen with quick, upward thrusts.\n4. For infants, deliver 5 back blows followed by 5 chest thrusts.",
    "fracture": "First Aid for Fractures / Broken Bones:\n1. Do not try to realign the bone or push a protruding bone back in.\n2. Immobilize the limb using a splint or sling to prevent movement.\n3. Apply a cold pack wrapped in a cloth to reduce swelling.\n4. Elevate the extremity and seek emergency medical assistance."
}

MANUALS_DB = {
    "water_purification": "Emergency Water Purification Manual:\n- Boil water vigorously for at least 1 full minute to kill pathogens.\n- Alternatively, add 8 drops of regular, unscented 6% liquid chlorine bleach per gallon of water, stir well, and let stand for 30 minutes before drinking.",
    "power_outage": "Emergency Power Outage Manual:\n- Keep refrigerators and freezers closed. A closed refrigerator keeps food cold for 4 hours; a full freezer for 48 hours.\n- Never use a generator, camp stove, or charcoal grill inside your home, garage, or near vents to prevent fatal carbon monoxide poisoning.\n- Unplug sensitive electronics to avoid damage from power surge spikes when grid is restored.",
    "emergency_contacts": "National Emergency Contacts Directory:\n- General Emergencies: Dial 911\n- FEMA Response Helpline: (800) 621-3362\n- American Red Cross Disaster Services: (800) 733-2767\n- Poison Control Helpline: (800) 222-1222"
}


# 2. MCP Tool Registrations

@mcp.tool()
def search_guidelines(query: str) -> str:
    """Searches official government disaster safety guidelines by hazard keyword (flood, cyclone, earthquake, wildfire, heatwave).
    
    Args:
        query: The hazard keyword to search for.
    """
    q = query.lower().strip()
    # Simple search resolver
    for key, content in GUIDELINES_DB.items():
        if key in q or q in key:
            return content
    return f"No direct guidelines found matching '{query}'. Available hazards: {', '.join(GUIDELINES_DB.keys())}"


@mcp.tool()
def search_first_aid(query: str) -> str:
    """Searches first aid manuals by injury keyword (bleeding, burns, cpr, choking, fracture).
    
    Args:
        query: The injury or treatment query keyword.
    """
    q = query.lower().strip()
    for key, content in FIRST_AID_DB.items():
        if key in q or q in key:
            return content
    return f"No medical treatment guidelines found matching '{query}'. Available topics: {', '.join(FIRST_AID_DB.keys())}"


@mcp.tool()
def search_disaster_manuals(query: str) -> str:
    """Searches emergency manuals by keyword (water_purification, power_outage, emergency_contacts).
    
    Args:
        query: The manual topic query keyword.
    """
    q = query.lower().strip()
    for key, content in MANUALS_DB.items():
        if key in q or q in key:
            return content
    return f"No manual sections found matching '{query}'. Available topics: {', '.join(MANUALS_DB.keys())}"


@mcp.tool()
def search_shelters(latitude: float, longitude: float, radius_miles: float = 15.0) -> List[Dict[str, Any]]:
    """Queries the SQLite database for nearby open shelters within a radius.
    
    Args:
        latitude: Search center latitude coordinate.
        longitude: Search center longitude coordinate.
        radius_miles: Maximum radius distance in miles.
    """
    db = SessionLocal()
    try:
        db_shelters = db.query(Shelter).all()
        results = []
        for s in db_shelters:
            dist = calculate_haversine_distance(latitude, longitude, s.latitude, s.longitude)
            if dist <= radius_miles:
                results.append({
                    "id": s.id,
                    "name": s.name,
                    "distance_miles": dist,
                    "capacity": s.capacity,
                    "occupancy": s.occupancy,
                    "spots_remaining": max(0, s.capacity - s.occupancy),
                    "status": s.status,
                    "address": s.address,
                    "contact": s.contact_info
                })
        results.sort(key=lambda x: x["distance_miles"])
        return results
    except Exception as e:
        logger.error(f"Error querying shelters in MCP tool: {str(e)}")
        return [{"error": f"Shelters lookup failed: {str(e)}"}]
    finally:
        db.close()


@mcp.tool()
def search_hospitals(latitude: float, longitude: float, radius_miles: float = 15.0) -> List[Dict[str, Any]]:
    """Queries the SQLite database for nearby operational hospitals within a radius.
    
    Args:
        latitude: Search center latitude coordinate.
        longitude: Search center longitude coordinate.
        radius_miles: Maximum search radius in miles.
    """
    db = SessionLocal()
    try:
        db_hospitals = db.query(Hospital).all()
        results = []
        for h in db_hospitals:
            dist = calculate_haversine_distance(latitude, longitude, h.latitude, h.longitude)
            if dist <= radius_miles:
                results.append({
                    "id": h.id,
                    "name": h.name,
                    "distance_miles": dist,
                    "status": h.status,
                    "emergency_services": h.emergency_services,
                    "contact": h.contact_info
                })
        results.sort(key=lambda x: x["distance_miles"])
        return results
    except Exception as e:
        logger.error(f"Error querying hospitals in MCP tool: {str(e)}")
        return [{"error": f"Hospitals lookup failed: {str(e)}"}]
    finally:
        db.close()


if __name__ == "__main__":
    from database.init_db import init_database

    init_database()
    # Start the FastMCP server (standard stdio link for local development integration)
    mcp.run()
