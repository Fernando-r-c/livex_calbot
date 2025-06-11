import requests
import json
import os
from datetime import datetime

from langchain_core.tools import tool

# --- Configuration (Moved from main app for modularity) ---
CAL_API_BASE_URL = "https://api.cal.com/v1/"

CAL_API_KEY_ENV = os.getenv("CAL_API_KEY")

def _get_cal_api_key():
    """
    Helper to get the API key from the environment variable.
    """
    return CAL_API_KEY_ENV

def _make_cal_request(endpoint, method="GET", params=None, json_data=None):
    """
    Helper function to make requests to the Cal.com API.
    It retrieves the API key using the callback.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return {"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."}

    if params is None:
        params = {}
    params['apiKey'] = api_key
    url = f"{CAL_API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.request(method, url, params=params, json=json_data, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        if response.status_code == 204:
            return {"message": "Operation successful, no content returned."}
        
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if e.response is not None else "No response body"
        return {"error": f"HTTP error: {e.response.status_code} - {error_detail}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {e}"}

@tool
def list_event_types() -> str:
    """
    Lists the available event types for the Cal.com account associated with the API key.
    Useful for understanding what kind of events can be booked.
    Returns a JSON string of event types, including their ID, title, and slug.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."})
    response = _make_cal_request("event-types")
    if "error" in response:
        return json.dumps(response)
    
    event_types_summary = [{"id": et.get("id"), "title": et.get("title"), "slug": et.get("slug")} for et in response.get("eventTypes", [])]
    return json.dumps({"eventTypes": event_types_summary})

@tool
def get_available_slots(event_type_slug: str, start_date_str: str, end_date_str: str) -> str:
    """
    Checks for available slots for a specific event type within a date range.
    The start_date_str and end_date_str should be in 'YYYY-MM-DD' format.
    Returns a JSON string of available slots.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."})
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return json.dumps({"error": "Invalid date format for start_date_str or end_date_str. Please use YYYY-MM-DD."})

    params = {
        "eventType": event_type_slug,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat()
    }
    response = _make_cal_request("slots", params=params)
    return json.dumps(response)

@tool
def book_cal_event(event_type_id: int, start_time_iso: str, end_time_iso: str, email: str, name: str, title: str, description: str = "") -> str:
    """
    Books a new event in Cal.com.
    event_type_id: The ID of the event type to book. You can obtain this from the `list_event_types` tool.
    start_time_iso: The start time of the event in ISO 8601 format (e.g., '2024-06-15T10:00:00Z' for UTC or '2024-06-15T10:00:00-07:00' for a specific offset).
    end_time_iso: The end time of the event in ISO 8601 format (e.g., '2024-06-15T11:00:00Z' for UTC or '2024-06-15T11:00:00-07:00' for a specific offset).
    email: The email address of the person booking the event (the attendee).
    name: The full name of the person booking the event (the attendee).
    title: The title or brief subject of the event.
    description: (Optional) A detailed description for the event.
    Returns a JSON string with the booking details upon success or an error message.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."})
    
    payload = {
        "eventTypeId": event_type_id,
        "start": start_time_iso,
        "end": end_time_iso,
        "timeZone": "America/Los_Angeles",
        "responses": {
            "email": email,
            "name": name,
            "metadata": {},
            "location": "integrations:cal"
        },
        "metadata": {
            "title": title,
            "description": description
        },
        "language": "en"
    }

    response = _make_cal_request("bookings", method="POST", json_data=payload)
    return json.dumps(response)

@tool
def list_cal_events(email: str = None) -> str:
    """
    Retrieves a list of scheduled events for the Cal.com account.
    If an 'email' is provided, it filters events by that attendee's email.
    If no email is provided, it returns all accessible scheduled events.
    Returns a JSON string containing a summary of scheduled events.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."})
    
    response = _make_cal_request("bookings") 
    
    if "error" in response:
        return json.dumps(response)

    bookings = response.get("bookings", [])
    
    filtered_bookings = []
    if email:
        for booking in bookings:
            attendees = booking.get("attendees", [])
            for attendee in attendees:
                if attendee.get("email", "").lower() == email.lower():
                    filtered_bookings.append(booking)
                    break
    else:
        filtered_bookings = bookings

    summarized_bookings = []
    for booking in filtered_bookings:
        start_time = booking.get("startTime")
        end_time = booking.get("endTime")
        title = booking.get("title")
        description = booking.get("description")
        id_ = booking.get("id")
        attendee_emails = [a.get("email") for a in booking.get("attendees", []) if a.get("email")]
        
        summarized_bookings.append({
            "id": id_,
            "title": title,
            "description": description,
            "startTime": start_time,
            "endTime": end_time,
            "attendees": attendee_emails
        })
        
    return json.dumps({"bookings": summarized_bookings})

@tool
def cancel_cal_event(booking_id: int) -> str:
    """
    Cancels a specific event in Cal.com by its unique booking ID.
    booking_id: The integer ID of the event to cancel. This ID can be obtained from the `list_cal_events` tool.
    Returns a JSON string indicating the success or failure of the cancellation.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."})
    
    response = _make_cal_request(f"bookings/{booking_id}", method="DELETE")
    
    if "error" in response:
        return json.dumps(response)
    
    return json.dumps({"status": "success", "message": f"Event with ID {booking_id} cancelled successfully."})

@tool
def reschedule_cal_event(booking_id: int, new_start_time_iso: str, new_end_time_iso: str) -> str:
    """
    Reschedules an existing Cal.com event. This process involves two steps:
    1. Canceling the original event.
    2. Creating a new event with the same details but updated start and end times.
    
    booking_id: The integer ID of the event to reschedule. This ID can be obtained from `list_cal_events`.
    new_start_time_iso: The new start time for the event in ISO 8601 format (e.g., '2024-06-15T10:00:00Z' for UTC or '2024-06-15T10:00:00-07:00' for a specific offset).
    new_end_time_iso: The new end time for the event in ISO 8601 format (e.g., '2024-06-15T11:00:00Z' for UTC or '2024-06-15T11:00:00-07:00' for a specific offset).
    
    Returns a JSON string with the details of the new booking upon success or an error message.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set. Please set it in the Streamlit UI."})
    
    single_booking_response = _make_cal_request(f"bookings/{booking_id}")
    if "error" in single_booking_response or not single_booking_response.get("booking"):
        return json.dumps({"error": f"Could not fetch full details for event with ID {booking_id} for rescheduling."})
    
    full_booking_details = single_booking_response["booking"]

    event_type_id = full_booking_details.get("eventTypeId")
    attendee_email = full_booking_details.get("attendees")[0].get("email") if full_booking_details.get("attendees") else None
    attendee_name = full_booking_details.get("attendees")[0].get("name") if full_booking_details.get("attendees") else None
    
    if not event_type_id or not attendee_email or not attendee_name:
        return json.dumps({"error": "Missing crucial information (event type ID, attendee email, or attendee name) from original booking to reschedule."})

    title = full_booking_details.get("title")
    description = full_booking_details.get("description", "")

    # Step 2: Cancel the old event
    cancel_status = json.loads(cancel_cal_event(booking_id))
    if cancel_status.get("status") != "success":
        return json.dumps({"error": f"Failed to cancel old event with ID {booking_id} during reschedule: {cancel_status.get('message', 'Unknown error')}"})

    # Step 3: Book a new event with the updated times and original details
    new_booking_response = json.loads(book_cal_event(event_type_id, new_start_time_iso, new_end_time_iso, attendee_email, attendee_name, title, description))

    if "error" in new_booking_response:
        return json.dumps({"error": f"Event cancelled, but failed to book new event during reschedule: {new_booking_response.get('error', 'Unknown error')}. Please try booking a new event manually."})
    
    return json.dumps({"status": "success", "message": f"Event {booking_id} successfully rescheduled.", "new_booking": new_booking_response})

@tool
def create_cal_event_type(title: str, slug: str, length: int, description: str = "", hidden: bool = False) -> str:
    """
    Creates a new event type in Cal.com.
    title: The title of the new event type (e.g., "30 Minute Meeting").
    slug: A URL-friendly identifier for the event type (e.g., "30min-meeting"). Must be unique.
    length: The duration of the event type in minutes (e.g., 30 for 30 minutes).
    description: (Optional) A detailed description for the event type.
    hidden: (Optional) A boolean indicating if the event type should be hidden (true) or public (false). Defaults to false.
    Returns a JSON string with the new event type details upon success or an error message.
    """
    api_key = _get_cal_api_key()
    if not api_key:
        return json.dumps({"error": "Cal.com API Key is not set in environment variables. Please set CAL_API_KEY in your .env file."})

    payload = {
        "title": title,
        "slug": slug,
        "length": length, # Duration in minutes
        "description": description,
        "hidden": hidden
    }

    response = _make_cal_request("event-types", method="POST", json_data=payload)
    return json.dumps(response)