from pydantic import BaseModel, Field
from google.adk.agents import Agent

class TriageOutput(BaseModel):
    is_critical_emergency: bool = Field(description="True if there is an active life-safety risk or direct request for rescue")
    priority: str = Field(description="Priority rating: CRITICAL, HIGH, NORMAL")
    recommended_immediate_action: str = Field(description="Safety instructions user must take right now")
    dispatch_needed: bool = Field(description="True if emergency responder dispatch is required")
    summary: str = Field(description="A brief summary of the distress situation")

triage_agent = Agent(
    name="triage_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=TriageOutput,
    description="Assesses active life-safety emergencies, determines priority, and recommends immediate survival actions.",
    instruction="""
    Analyze the user's situation and distress level. 
    Assess if there is an active, life-threatening emergency (e.g. trapped in rising water, injured and bleeding, structural collapse, fire, gas leak).
    If an active life-safety threat exists:
    - Set is_critical_emergency to True.
    - Set priority to CRITICAL or HIGH.
    - Set dispatch_needed to True.
    - Provide short, direct, actionable immediate instructions.
    If it is a general information query or low-risk situation:
    - Set is_critical_emergency to False.
    - Set priority to NORMAL.
    - Set dispatch_needed to False.
    - Provide standard safety advice.
    Always end by populating all fields of the TriageOutput schema.
    """
)
