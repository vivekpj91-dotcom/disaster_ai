import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from google.adk.agents import Agent

logger = logging.getLogger("disaster_assist.checklist_agent")

class EmergencyKit(BaseModel):
    water_gallons: float = Field(description="Quantity of drinking water recommended in gallons (1 gallon/person/day)")
    food_rations: str = Field(description="Non-perishable food specifications based on household size")
    medical_supplies: List[str] = Field(description="Medical items and customized prescription medication advice")
    documents_to_secure: List[str] = Field(description="Important papers, identity documents, and cash to protect in waterproof sleeves")
    power_and_backup: List[str] = Field(description="Batteries, flashlights, solar chargers, backup energy packs, and communication gear")
    pet_supplies: List[str] = Field(default=[], description="Food, water, leash, identification, and medical records for pets")
    children_needs: List[str] = Field(default=[], description="Baby formula, diapers, baby wipes, medication, and comfort toys")

class PreparednessOutput(BaseModel):
    disaster_type: str = Field(description="The disaster type: flood, cyclone, earthquake, wildfire, heatwave")
    household_size: int = Field(description="Target family size used for planning")
    personalized_kit: EmergencyKit = Field(description="Tailored list of kit items")
    disaster_checklist: List[str] = Field(description="Step-by-step preparation checklist specific to this hazard")
    advisory_guidance: str = Field(description="Actionable preparation safety advice")


def get_personalized_preparation_logic(
    disaster_type: str,
    household_size: int,
    has_pets: bool,
    has_children: bool
) -> dict:
    """Computes personalized emergency kit listings and disaster specific tasks.
    
    Args:
        disaster_type: Type of disaster (flood, cyclone, earthquake, wildfire, heatwave)
        household_size: Number of people in the house
        has_pets: Whether user has pets
        has_children: Whether user has children
        
    Returns:
        Structured dictionary.
    """
    dt = disaster_type.lower().strip()
    
    # 1. Calculate water and food base amounts (standard 3 days rule)
    water_needed = household_size * 3.0 # 3 gallons per person
    food = f"Provide at least {household_size * 3} meals of non-perishable canned food, high-energy bars, and freeze-dried items."
    
    # 2. Base lists
    meds = ["Bandages, gauze, surgical tape", "Antiseptic wipes, hand sanitizer", "Thermometer", "Assembled 7-day supply of personal prescription medications"]
    docs = ["Passport, Driver Licenses, Social Security cards", "Property deed, home insurance policies", "Emergency cash ($100-$200 in small bills)", "Medication list and emergency contacts list"]
    power = ["High-capacity USB power bank (charged)", "Battery-operated flashlights", "Spare AA/AAA batteries", "NOAA solar/hand-crank emergency radio"]
    
    # 3. Add personal adjustments
    pets = []
    if has_pets:
        pets = [
            "3-day supply of dry/wet pet food and water",
            "Pet collar with ID tag, leash, and harness",
            "Copy of vaccination records",
            "Pet carrier crate"
        ]
        
    kids = []
    if has_children:
        kids = [
            "Diapers (15-20 per child), baby wipes, rash cream",
            "Infant formula (powder/liquid) and sterile bottles",
            "Baby food jars, juices, and snacks",
            "Pedialyte rehydration fluid",
            "2 comfort toys or coloring books to ease anxiety"
        ]
        
    # 4. Disaster checklists
    checklists = {
        "flood": [
            "Move expensive electronics, appliances, and valuables to upper floors.",
            "Seal vents and lower openings with sandbags or plywood.",
            "Clear gutters, downspouts, and check sump pump operation.",
            "Unplug major electrical appliances if water enters your home.",
            "Familiarize yourself with local high-ground escape routes."
        ],
        "cyclone": [
            "Install storm shutters or securely board windows with thick plywood.",
            "Bring all outdoor furniture, trash bins, and toys indoors.",
            "Trim overhanging tree branches close to rooflines.",
            "Anchor heavy yard assets and secure garage doors.",
            "Check storm surge maps and evacuate immediately if order is issued."
        ],
        "earthquake": [
            "Secure bookshelves, cabinets, and mirrors to wall studs.",
            "Install safety latches on cabinet doors to prevent contents flying out.",
            "Identify safe drop-cover-hold spots in each room (under heavy tables).",
            "Ensure water heater is securely bolted to wall framing.",
            "Check gas shut-off valve location and ensure wrench is nearby."
        ],
        "wildfire": [
            "Clear dry leaves, twigs, and flammable vegetation within 30 feet of structure (defensible space).",
            "Close all windows, vents, and doors to keep smoke out.",
            "Shut off gas supply line valve at the tank or meter.",
            "Pack all valuable documents and emergency kits into your vehicle.",
            "Wear long pants, long sleeve shirts, and leather gloves to protect from embers."
        ],
        "heatwave": [
            "Cover windows with reflective curtains, cardboard, or aluminum foil to deflect sun.",
            "Set thermostat to safe level; check ventilation flow.",
            "Identify nearby public air-conditioned cooling centers.",
            "Plan strenuous activities for early morning or late evening hours.",
            "Review heat stroke warning signs: dizziness, nausea, hot red dry skin."
        ]
    }
    
    selected_checklist = checklists.get(dt, checklists["flood"])
    
    return {
        "disaster_type": dt,
        "household_size": household_size,
        "water_gallons": water_needed,
        "food": food,
        "meds": meds,
        "docs": docs,
        "power": power,
        "pets": pets,
        "kids": kids,
        "checklist": selected_checklist
    }

checklist_agent = Agent(
    name="checklist_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=PreparednessOutput,
    tools=[get_personalized_preparation_logic],
    description="Generates personalized disaster-specific supply kits (water, food, meds, pets, children) and emergency checklists.",
    instruction="""
    You are the specialized Emergency Preparedness Worker agent (checklist_worker).
    Your responsibility is to assemble personalized safety checklists.
    1. Parse disaster parameters (disaster_type, household_size, has_pets, has_children) from inputs.
    2. Invoke the 'get_personalized_preparation_logic' tool passing these parameters.
    3. Analyze the results:
       - Populate the PreparednessOutput schema.
       - Assemble the personalized_kit sub-schema (EmergencyKit) details.
       - Include the disaster specific task lists.
    4. Provide clear preparation tips and warnings in the advisory_guidance field.
    5. Call the finish_task tool to complete the task and return the structured JSON data.
    """
)
