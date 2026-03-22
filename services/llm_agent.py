"""
services/llm_agent.py — Groq-powered LLM integration.
Features: incident analysis, severity scoring, resource dispatch,
          congestion advisory, signal re-timing, public alerts, chat.
"""

import base64
import json
import os
from groq import Groq
from config import GROQ_MODEL

VISION_MODEL = "llama-3.2-90b-vision-preview"


def _get_client():
    """Initialise the Groq client using the API key."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Set it in .streamlit/secrets.toml or as an environment variable."
        )
    return Groq(api_key=api_key)


def _call_llm(system_prompt: str, user_message: str,
              temperature: float = 0.3, max_tokens: int = 2000,
              expect_json: bool = True):
    """
    Generic LLM call wrapper. Returns parsed JSON dict or raw string.
    """
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content.strip()

        if expect_json:
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(content)
        return content
    except json.JSONDecodeError:
        return {"error": "LLM returned invalid JSON", "raw": content}
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════
#  1) INCIDENT ANALYSIS (original feature, enhanced)
# ═══════════════════════════════════════════════════════════════

INCIDENT_ANALYSIS_PROMPT = """You are an expert traffic incident management AI co-pilot for Ahmedabad, India.

Given crash details and alternate route data, produce a JSON response with EXACTLY this structure:
{
  "incident_summary": "1-2 sentence summary of the incident",
  "signal_retiming": [
    {
      "intersection": "Name of intersection",
      "current_phase": "e.g. 60s green / 30s red",
      "recommended_phase": "e.g. 90s green / 20s red",
      "reason": "brief reason"
    }
  ],
  "route_recommendations": [
    {
      "rank": 1,
      "route_description": "Via Street A → Street B → Street C",
      "estimated_redistribution_pct": 45,
      "notes": "Suitable for heavy vehicles"
    }
  ],
  "public_alerts": {
    "vms_text": "Short variable message sign text (max 50 words)",
    "radio_script": "Ready-to-read radio broadcast script (max 100 words)",
    "social_media": "Social media post with hashtags (max 280 chars)"
  },
  "estimated_clearance_minutes": 30,
  "additional_notes": "Any other important observations"
}

Rules:
- Use real Ahmedabad street names and landmarks wherever possible.
- Be specific with intersection names and phase timings.
- Keep VMS text concise for electronic sign boards.
- Make the radio script ready to read aloud.
- Return ONLY valid JSON, no markdown, no explanation outside the JSON.
"""


def analyze_incident(crash_details: dict, routes: list, crash_street: str) -> dict:
    """Send crash details + route data to Groq and get structured analysis."""
    user_message = f"""
INCIDENT DETAILS:
- Crash location: {crash_details.get('crash_location', 'Unknown')}
- Crashed street: {crash_street}
- Vehicle type: {crash_details.get('vehicle_type', 'Unknown')}
- Lanes affected: {crash_details.get('lanes_affected', 'Unknown')}
- Traffic density: {crash_details.get('traffic_density', 'Unknown')}
- Weather: {crash_details.get('weather', 'Clear')}
- Additional notes: {crash_details.get('notes', 'None')}
- Time of incident: {crash_details.get('time', 'Unknown')}

ALTERNATE ROUTES COMPUTED:
"""
    for r in routes:
        user_message += f"""
Route {r['rank']}:
  - Streets: {r['street_summary']}
  - Distance: {r['distance_m']} metres
  - ETA: {r.get('eta_minutes', 'N/A')} minutes
"""
    return _call_llm(INCIDENT_ANALYSIS_PROMPT, user_message)


# ═══════════════════════════════════════════════════════════════
#  2) SEVERITY SCORING (new AI feature)
# ═══════════════════════════════════════════════════════════════

SEVERITY_PROMPT = """You are a traffic incident severity assessment expert.

Given the incident details below, rate the severity on a scale of 1-10 and provide your reasoning.

Return ONLY valid JSON:
{
  "severity_score": 7,
  "severity_label": "High",
  "reason": "Multi-vehicle collision blocking all lanes during peak hours in heavy rain",
  "color": "#EF4444"
}

Scoring guide:
- 1-3 (Low/Green/#22C55E): Minor fender-bender, 1 lane, light traffic, clear weather
- 4-6 (Medium/Amber/#F59E0B): Moderate crash, 2 lanes, moderate-heavy traffic
- 7-9 (High/Red/#EF4444): Serious crash, multiple lanes, heavy/gridlock, poor weather, injuries
- 10 (Critical/Purple/#7C3AED): Full road closure, mass casualty, hazmat spill

Return ONLY valid JSON.
"""


def assess_severity(crash_details: dict) -> dict:
    """AI-powered severity scoring for the incident."""
    user_msg = f"""
Vehicle type: {crash_details.get('vehicle_type', 'Car')}
Lanes affected: {crash_details.get('lanes_affected', '1')}
Traffic density: {crash_details.get('traffic_density', 'Moderate')}
Weather: {crash_details.get('weather', 'Clear')}
Time: {crash_details.get('time', 'Unknown')}
Notes: {crash_details.get('notes', 'None')}
"""
    return _call_llm(SEVERITY_PROMPT, user_msg, temperature=0.2, max_tokens=500)


# ═══════════════════════════════════════════════════════════════
#  3) RESOURCE DISPATCH SUGGESTIONS (new AI feature)
# ═══════════════════════════════════════════════════════════════

DISPATCH_PROMPT = """You are an emergency resource dispatch coordinator for Ahmedabad, India.

Given the incident severity and details, recommend which resources to deploy.

Return ONLY valid JSON:
{
  "resources": [
    {
      "type": "Ambulance",
      "priority": "High",
      "count": 1,
      "reason": "Potential injuries reported",
      "icon": "🚑"
    },
    {
      "type": "Traffic Police",
      "priority": "High",
      "count": 2,
      "reason": "Traffic management at blocked intersection",
      "icon": "👮"
    }
  ],
  "coordination_notes": "Brief coordination instructions for responders"
}

Available resource types: Ambulance, Traffic Police, Fire Truck, Tow Truck, Hazmat Team, Road Maintenance.
Priority levels: Critical, High, Medium, Low.
Return ONLY valid JSON.
"""


def suggest_dispatch(crash_details: dict, severity: dict) -> dict:
    """AI-powered resource dispatch suggestions."""
    user_msg = f"""
Severity score: {severity.get('severity_score', 5)}/10 ({severity.get('severity_label', 'Medium')})
Vehicle type: {crash_details.get('vehicle_type', 'Car')}
Lanes affected: {crash_details.get('lanes_affected', '1')}
Traffic density: {crash_details.get('traffic_density', 'Moderate')}
Weather: {crash_details.get('weather', 'Clear')}
Crashed street: {crash_details.get('blocked_street', 'Unknown')}
Notes: {crash_details.get('notes', 'None')}
"""
    return _call_llm(DISPATCH_PROMPT, user_msg, temperature=0.2, max_tokens=800)


# ═══════════════════════════════════════════════════════════════
#  4) CONGESTION ADVISORY (new AI feature)
# ═══════════════════════════════════════════════════════════════

CONGESTION_PROMPT = """You are a traffic congestion prediction expert for Ahmedabad, India.
You know Ahmedabad's road network well: SG Highway, Ashram Road, CG Road, Relief Road, Nehru Bridge, Ellis Bridge, SP Ring Road, 132 Ft Ring Road, Sarkhej-Gandhinagar Highway, Drive-In Road, Law Garden, Vastrapur, Satellite, Paldi, Navrangpura, Maninagar, etc.

Given the incident details (including GPS coordinates), predict the congestion impact.
Use the GPS coordinates to identify the actual neighborhood and nearby landmarks.

Return ONLY valid JSON:
{
  "predicted_congestion_duration_minutes": 45,
  "peak_congestion_window": "18:30 - 19:15",
  "affected_areas": [
    {
      "area": "SG Highway towards Vastrapur",
      "impact": "Heavy delays, 15-20 min added travel time",
      "alternative": "Use SP Ring Road via Thaltej"
    },
    {
      "area": "Ashram Road near Income Tax",
      "impact": "Moderate spillover congestion",
      "alternative": "Use Riverfront Road"
    }
  ],
  "congestion_level": "Severe",
  "advice": "Specific actionable advisory mentioning real streets and landmarks"
}

Rules:
- Use REAL Ahmedabad street names, areas, and landmarks — never say "adjacent roads" or "surrounding areas".
- Each affected area must name a specific road or intersection.
- Each alternative must name a specific bypass route.
- The advice must be actionable with real directions.
- Return ONLY valid JSON.
"""


def predict_congestion(crash_details: dict, severity: dict) -> dict:
    """AI-powered congestion prediction and advisory."""
    user_msg = f"""
Severity: {severity.get('severity_score', 5)}/10
Time of incident: {crash_details.get('time', 'Unknown')}
Crashed street: {crash_details.get('blocked_street', 'Unknown')}
Crash GPS: {crash_details.get('crash_location', 'Unknown')}
Start point GPS: {crash_details.get('start_location', 'Unknown')}
End point GPS: {crash_details.get('end_location', 'Unknown')}
Lanes affected: {crash_details.get('lanes_affected', '1')}
Traffic density: {crash_details.get('traffic_density', 'Moderate')}
Weather: {crash_details.get('weather', 'Clear')}
Vehicle type: {crash_details.get('vehicle_type', 'Unknown')}
Notes: {crash_details.get('notes', 'None')}
"""
    return _call_llm(CONGESTION_PROMPT, user_msg, temperature=0.3, max_tokens=800)


# ═══════════════════════════════════════════════════════════════
#  5) CHAT (enhanced)
# ═══════════════════════════════════════════════════════════════

CHAT_SYSTEM_PROMPT = """You are an expert traffic incident management AI co-pilot assisting an officer in Ahmedabad, India.

You have access to the current incident context provided below. Answer the officer's questions concisely and actionably. Refer to specific streets, intersections, and routes by name. If you don't have enough information, say so clearly.

Be direct, professional, and focused on operational decisions. The officer is under time pressure.
"""


def chat_query(conversation_history: list, incident_context: str, user_question: str) -> str:
    """Multi-turn conversational query about the current incident."""
    client = _get_client()

    system_msg = CHAT_SYSTEM_PROMPT + f"\n\nCURRENT INCIDENT CONTEXT:\n{incident_context}"

    messages = [{"role": "system", "content": system_msg}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_question})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error communicating with Groq: {e}"


# ═══════════════════════════════════════════════════════════════
#  6) VISION: CRASH PHOTO ANALYSIS
# ═══════════════════════════════════════════════════════════════

VISION_PROMPT = """You are a traffic accident analyst. Analyze this crash scene photo and extract structured information.

Return ONLY valid JSON:
{
  "vehicle_type": "Car / Truck / Two-Wheeler / Bus / Auto-Rickshaw / Multi-Vehicle",
  "vehicle_count": 2,
  "estimated_severity": 7,
  "severity_label": "High",
  "lanes_blocked": "2",
  "road_condition": "Wet / Dry / Damaged",
  "weather_visible": "Clear / Rain / Fog / Night",
  "visible_damage": "Brief description of visible damage",
  "injuries_likely": true,
  "hazards": "Fuel spill, debris, fire, etc. or 'None visible'",
  "recommended_response": "Brief recommendation for first responders"
}

Return ONLY valid JSON. Be accurate based on what you can see.
"""


def analyze_crash_photo(image_data: bytes | str) -> dict:
    """
    Analyze a crash scene photo using vision LLM.

    Args:
        image_data: Either raw bytes of the image, or a base64-encoded string.

    Returns:
        Dict with vehicle_type, severity, lanes_blocked, etc.
    """
    client = _get_client()

    # Convert to base64 if raw bytes
    if isinstance(image_data, bytes):
        b64 = base64.b64encode(image_data).decode("utf-8")
    else:
        b64 = image_data

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=800,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Vision LLM returned invalid JSON", "raw": content}
    except Exception as e:
        return {"error": str(e)}
