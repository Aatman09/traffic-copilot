"""
llm_agent.py — Groq-powered LLM integration for incident analysis,
               signal re-timing, public alerts, and conversational chat.
"""

import json
import os
from groq import Groq
from config import GROQ_MODEL


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


# ── System prompts ────────────────────────────────────────────

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

CHAT_SYSTEM_PROMPT = """You are an expert traffic incident management AI co-pilot assisting an officer in Ahmedabad, India.

You have access to the current incident context provided below. Answer the officer's questions concisely and actionably. Refer to specific streets, intersections, and routes by name. If you don't have enough information, say so clearly.

Be direct, professional, and focused on operational decisions. The officer is under time pressure.
"""


def analyze_incident(crash_details: dict, routes: list, crash_street: str) -> dict:
    """
    Send crash details + route data to Groq and get structured analysis.
    Returns parsed JSON dict, or a dict with an 'error' key on failure.
    """
    client = _get_client()

    user_message = f"""
INCIDENT DETAILS:
- Location: {crash_details.get('location', 'Unknown')}
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
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": INCIDENT_ANALYSIS_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
        # Try to parse JSON (handle potential markdown wrapping)
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "LLM returned invalid JSON", "raw": content}
    except Exception as e:
        return {"error": str(e)}


def chat_query(conversation_history: list, incident_context: str, user_question: str) -> str:
    """
    Multi-turn conversational query about the current incident.
    Returns the assistant's reply as a string.
    """
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
        return f"⚠️ Error communicating with Groq: {e}"
