import os
import logging
from pydantic import BaseModel, Field
from typing import List
from google.adk.agents import Agent
from google import genai
from google.genai import types
from config.settings import settings

logger = logging.getLogger("disaster_assist.damage_agent")

class ImageAnalysisOutput(BaseModel):
    building_damage_detected: bool = Field(description="True if structural, wall, roof, or window damage is visible on buildings")
    flooding_detected: bool = Field(description="True if standing water, mudslides, or high water is visible")
    fire_detected: bool = Field(description="True if active flames, sparks, or smoke plumes are visible")
    blocked_roads_detected: bool = Field(description="True if debris, fallen trees, collapsed structures, or water is blocking streets/paths")
    severity: str = Field(description="Calculated danger rating: CRITICAL (active fire/floods/collapse), HIGH (major damage/blocked roads), MEDIUM (moderate cracks), LOW (minor/cosmetic)")
    recommendations: List[str] = Field(description="Actionable safety recommendations for the user based on visual findings")
    observations_summary: str = Field(description="Detailed textual description of what is visually observed in the photograph")


def analyze_scene_image(file_path: str) -> dict:
    """Invokes Gemini Multimodal Vision API to analyze disaster images for hazards.
    
    Args:
        file_path: Path to the image file in local system or GCS
        
    Returns:
        A dictionary containing the parsed hazard assessment details.
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found for scene analysis: {file_path}")
        return {
            "building_damage": False,
            "flooding": False,
            "fire": False,
            "blocked_roads": False,
            "severity": "LOW",
            "summary": "No image was available for inspection.",
            "recommendations": ["Re-upload a clear photograph of the disaster area."]
        }
        
    try:
        with open(file_path, "rb") as f:
            image_bytes = f.read()
            
        ext = os.path.splitext(file_path)[1].lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY missing. Returning mock hazard analysis.")
            # Return high-quality mock values for local testing
            return {
                "building_damage": True,
                "flooding": True,
                "fire": False,
                "blocked_roads": True,
                "severity": "HIGH",
                "summary": "Mock Scene Analysis: Building exterior has flooded ground floor. Power poles and fallen trees are blocking the adjacent driveway.",
                "recommendations": [
                    "Evacuate to higher floors of the building immediately.",
                    "Do not step into the flooded driveway, high risk of electrocution from fallen wires.",
                    "Stay clear of structural elements showing visible stress cracks."
                ]
            }
            
        client = genai.Client(api_key=api_key)
        
        prompt = """
        Analyze this disaster scene photograph. 
        Identify if you see any of the following hazards:
        - Building damage (walls, windows, roof, collapsed structures)
        - Flooding or mudslides (standing water, overflowing creeks)
        - Fire or smoke (flames, plumes of black/grey smoke)
        - Blocked roads (fallen trees, debris blocking path/street)
        
        Evaluate the overall severity level: CRITICAL, HIGH, MEDIUM, or LOW.
        
        Answer using this exact checklist format so it is easy to parse:
        [BUILDING_DAMAGE: YES/NO]
        [FLOODING: YES/NO]
        [FIRE: YES/NO]
        [BLOCKED_ROADS: YES/NO]
        [SEVERITY: CRITICAL/HIGH/MEDIUM/LOW]
        
        Provide a brief description of findings, followed by a list of 3 safety recommendations.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ]
        )
        
        text = response.text or ""
        logger.info(f"Gemini Hazard Vision analysis response: {text}")
        
        # Simple extraction parser
        text_lower = text.lower()
        
        building = "[building_damage: yes]" in text_lower
        flooding = "[flooding: yes]" in text_lower
        fire = "[fire: yes]" in text_lower
        blocked = "[blocked_roads: yes]" in text_lower
        
        severity = "LOW"
        for rating in ["critical", "high", "medium"]:
            if f"[severity: {rating}]" in text_lower:
                severity = rating.upper()
                break
                
        # Parse recommendations (lines starting with dashes or numbers)
        recommendations = []
        summary_lines = []
        parsing_recs = False
        
        for line in text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            if "recommendation" in line_str.lower() or "safety" in line_str.lower():
                parsing_recs = True
                continue
            if parsing_recs:
                clean_line = line_str.lstrip("-*123. ")
                if clean_line:
                    recommendations.append(clean_line)
            else:
                if not line_str.startswith("["):
                    summary_lines.append(line_str)
                    
        if not recommendations:
            recommendations = ["Avoid unstable structures.", "Follow local authority directions.", "Keep emergency communications open."]
            
        return {
            "building_damage": building,
            "flooding": flooding,
            "fire": fire,
            "blocked_roads": blocked,
            "severity": severity,
            "summary": " ".join(summary_lines[:3]),
            "recommendations": recommendations[:3]
        }
        
    except Exception as e:
        logger.error(f"Failed to execute scene hazard analysis: {str(e)}", exc_info=True)
        return {
            "building_damage": False,
            "flooding": False,
            "fire": False,
            "blocked_roads": False,
            "severity": "LOW",
            "summary": "Error parsing image: " + str(e),
            "recommendations": ["Evacuate to safety immediately if you feel threatened."]
        }

damage_agent = Agent(
    name="damage_worker",
    model="gemini-2.5-flash",
    mode="task",
    output_schema=ImageAnalysisOutput,
    tools=[analyze_scene_image],
    description="Analyzes uploaded disaster images to check for building damage, flooding, fire, and blocked roads, returning structured hazard telemetry.",
    instruction="""
    You are the specialized Image Analysis worker (damage_worker).
    Your task is to analyze photographs uploaded by users during active disasters.
    1. Read the image artifact file path from inputs or parameters.
    2. Invoke the 'analyze_scene_image' tool with the file path.
    3. Process the findings and populate the ImageAnalysisOutput schema fields:
       - Set building_damage_detected (True/False).
       - Set flooding_detected (True/False).
       - Set fire_detected (True/False).
       - Set blocked_roads_detected (True/False).
       - Set severity level.
       - Compile the list of safety recommendations and summarize observations.
    4. Call the finish_task tool to complete the task and return the structured JSON data.
    """
)
