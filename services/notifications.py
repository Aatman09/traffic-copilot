"""
services/notifications.py — Send WhatsApp and SMS notifications via Twilio.
"""

import os
from twilio.rest import Client


def _get_secret(key: str) -> str | None:
    """Read a secret from env or Streamlit secrets."""
    val = os.environ.get(key)
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(key)
        except Exception:
            pass
    return val or None


def _get_client():
    """Initialise the Twilio client."""
    sid = _get_secret("TWILIO_ACCOUNT_SID")
    token = _get_secret("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        raise ValueError("Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .streamlit/secrets.toml")
    return Client(sid, token)


def format_alert_message(crash_details: dict, severity: dict | None = None,
                         routes: list | None = None) -> str:
    """Build a concise alert message from incident data."""
    street = crash_details.get("blocked_street", "Unknown")
    vehicle = crash_details.get("vehicle_type", "Unknown")
    traffic = crash_details.get("traffic_density", "Unknown")
    time = crash_details.get("time", "")

    lines = [
        f"TRAFFIC ALERT — {street}",
        f"Time: {time}",
        f"Vehicle: {vehicle} | Traffic: {traffic}",
    ]

    if severity and isinstance(severity, dict):
        score = severity.get("severity_score", "?")
        label = severity.get("severity_label", "Unknown")
        lines.append(f"Severity: {score}/10 ({label})")

    if routes:
        n = len(routes)
        fastest = min(r.get("eta_minutes", 999) for r in routes)
        lines.append(f"{n} alternate route(s) available, fastest ETA: {fastest} min")

    lines.append("Avoid the area. Follow traffic police instructions.")
    return "\n".join(lines)


def send_whatsapp(to_numbers: list[str], message: str) -> list[dict]:
    """Send WhatsApp messages via Twilio sandbox."""
    wa_number = _get_secret("TWILIO_WHATSAPP_NUMBER")
    if not wa_number:
        return [{"number": n, "error": "TWILIO_WHATSAPP_NUMBER not set"} for n in to_numbers]

    client = _get_client()
    from_wa = f"whatsapp:{wa_number}"
    results = []

    for number in to_numbers:
        number = number.strip().replace(" ", "").replace("-", "")
        if not number:
            continue
        if not number.startswith("+"):
            number = f"+{number}"
        try:
            msg = client.messages.create(
                body=message,
                from_=from_wa,
                to=f"whatsapp:{number}",
            )
            results.append({"number": number, "status": msg.status, "sid": msg.sid})
        except Exception as e:
            results.append({"number": number, "error": str(e)})

    return results


def send_sms(to_numbers: list[str], message: str) -> list[dict]:
    """Send SMS via Twilio."""
    from_number = _get_secret("TWILIO_PHONE_NUMBER")
    if not from_number:
        return [{"number": n, "error": "TWILIO_PHONE_NUMBER not set (buy a number from Twilio)"} for n in to_numbers]

    client = _get_client()
    results = []

    for number in to_numbers:
        number = number.strip().replace(" ", "").replace("-", "")
        if not number:
            continue
        if not number.startswith("+"):
            number = f"+{number}"
        try:
            msg = client.messages.create(body=message, from_=from_number, to=number)
            results.append({"number": number, "status": msg.status, "sid": msg.sid})
        except Exception as e:
            results.append({"number": number, "error": str(e)})

    return results
