"""
services/notifications.py — Send SMS and WhatsApp notifications via Twilio.
"""

import os
from twilio.rest import Client


def _get_client():
    """Initialise the Twilio client using credentials from secrets or env."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        try:
            import streamlit as st
            account_sid = account_sid or st.secrets.get("TWILIO_ACCOUNT_SID")
            auth_token = auth_token or st.secrets.get("TWILIO_AUTH_TOKEN")
        except Exception:
            pass

    if not account_sid or not auth_token:
        raise ValueError(
            "Twilio credentials not found. "
            "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .streamlit/secrets.toml "
            "or as environment variables."
        )
    return Client(account_sid, auth_token)


def _get_from_number():
    """Get the Twilio phone number for sending SMS."""
    number = os.environ.get("TWILIO_PHONE_NUMBER")
    if not number:
        try:
            import streamlit as st
            number = st.secrets.get("TWILIO_PHONE_NUMBER")
        except Exception:
            pass
    if not number:
        raise ValueError(
            "TWILIO_PHONE_NUMBER not found. "
            "Set it in .streamlit/secrets.toml or as an environment variable."
        )
    return number


def _get_whatsapp_number():
    """Get the Twilio WhatsApp sender number."""
    number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    if not number:
        try:
            import streamlit as st
            number = st.secrets.get("TWILIO_WHATSAPP_NUMBER")
        except Exception:
            pass
    # Fall back to the regular Twilio number with whatsapp: prefix
    if not number:
        number = _get_from_number()
    return number


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


def send_sms(to_numbers: list[str], message: str) -> list[dict]:
    """
    Send an SMS to one or more phone numbers.

    Args:
        to_numbers: List of E.164 formatted numbers (e.g. ["+919876543210"])
        message: The message body

    Returns:
        List of dicts with {number, status, sid} or {number, error}
    """
    client = _get_client()
    from_number = _get_from_number()
    results = []

    for number in to_numbers:
        number = number.strip()
        if not number:
            continue
        try:
            msg = client.messages.create(
                body=message,
                from_=from_number,
                to=number,
            )
            results.append({"number": number, "status": msg.status, "sid": msg.sid})
        except Exception as e:
            results.append({"number": number, "error": str(e)})

    return results


def send_whatsapp(to_numbers: list[str], message: str) -> list[dict]:
    """
    Send a WhatsApp message to one or more phone numbers.

    Args:
        to_numbers: List of E.164 formatted numbers (e.g. ["+919876543210"])
        message: The message body

    Returns:
        List of dicts with {number, status, sid} or {number, error}
    """
    client = _get_client()
    from_number = f"whatsapp:{_get_whatsapp_number()}"
    results = []

    for number in to_numbers:
        number = number.strip()
        if not number:
            continue
        try:
            msg = client.messages.create(
                body=message,
                from_=from_number,
                to=f"whatsapp:{number}",
            )
            results.append({"number": number, "status": msg.status, "sid": msg.sid})
        except Exception as e:
            results.append({"number": number, "error": str(e)})

    return results
