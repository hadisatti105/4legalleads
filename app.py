from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Store submissions in memory (for demo)
submission_store = {}

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def submit(
    request: Request,
    filter_1: str = Form(...),
    zip_code: str = Form(...),
    language: str = Form(...),
    origin_area_code: str = Form(...),
    origin_prefix: str = Form(...),
    origin_suffix: str = Form(...),
    have_attorney: str = Form(...),
    trusted_form_url: str = Form(...),
    sub_id: str = Form(...),
    incident_date: str = Form(...),
    injury_type: str = Form(...),
    were_you_at_fault: str = Form(...),
    doctor_treatment: str = Form(...),
    landing_page: str = Form(...),
):
    # Constants
    API_KEY = "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716"
    TERMINATING_PHONE = "2534870338"

    # Build Ping Payload
    ping_payload = {
        "Mode": "ping",
        "Key": API_KEY,
        "API_Action": "custom4llIprSubmitLeadWithComboCheck",
        "Match_With_Partner_ID": "20827",
        "TYPE": "9",
        "SRC": "DurationLKC120Transfer",
        "ZIP": zip_code,
        "Language": language,
        "Origin_Phone_Country_Code": "1",
        "Origin_Phone_Area_Code": origin_area_code,
        "Origin_Phone_Prefix": origin_prefix,
        "Origin_Phone_Suffix": origin_suffix,
        "Terminating_Phone_Country_Code": "1",
        "Terminating_Phone": TERMINATING_PHONE,
        "Filter_1": filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": sub_id,
        "Have_Attorney": have_attorney,
        "Trusted_Form_URL": trusted_form_url,
        "ZIP": zip_code,
    }

    # Send Ping
    ping_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=ping_payload)

    # Parse Ping Response (JSON or XML fallback)
    try:
        ping_response_json = ping_response.json()
    except Exception:
        try:
            root = ET.fromstring(ping_response.text)
            ping_response_json = {}
            for child in root:
                ping_response_json[child.tag] = child.text
        except Exception:
            ping_response_json = {"error": f"Invalid response format: {ping_response.text}"}

    # Extract Lead_ID if matched
    lead_id = ping_response_json.get("lead_id") if "lead_id" in ping_response_json else None
    if not lead_id:
        # Check inside XML structure fallback
        lead_id = ping_response_json.get("lead_id", None)

    # Build Post Payload
    post_payload = {
        "Mode": "post",
        "Key": API_KEY,
        "API_Action": "custom4llIprSubmitLeadWithComboCheck",
        "Match_With_Partner_ID": "20827",
        "TYPE": "9",
        "SRC": "DurationLKC120Transfer",
        "ZIP": zip_code,
        "Language": language,
        "Origin_Phone_Country_Code": "1",
        "Origin_Phone_Area_Code": origin_area_code,
        "Origin_Phone_Prefix": origin_prefix,
        "Origin_Phone_Suffix": origin_suffix,
        "Terminating_Phone_Country_Code": "1",
        "Terminating_Phone": TERMINATING_PHONE,
        "Filter_1": filter_1,
        "Sub_ID": sub_id,
        "Have_Attorney": have_attorney,
        "Trusted_Form_URL": trusted_form_url,
        "App_ID": "888",
        "Landing_Page": landing_page,
        "Start_Date_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Lead_ID": lead_id or "",
    }

    # Add category specific required fields
    if filter_1 in [
        "Auto Accident Injury",
        "Personal Injury",
        "Workers Comp",
        "Medical Malpractice",
        "Product Liability",
    ]:
        post_payload["Incident_Date"] = incident_date
        post_payload["Injury_Type"] = injury_type
        post_payload["Were_You_At_Fault"] = were_you_at_fault
        post_payload["Doctor_Treatment"] = doctor_treatment

    # Send Post
    post_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=post_payload)

    # Parse Post Response (JSON or fallback)
    try:
        post_response_json = post_response.json()
    except Exception:
        try:
            root = ET.fromstring(post_response.text)
            post_response_json = {}
            for child in root:
                post_response_json[child.tag] = child.text
        except Exception:
            post_response_json = {"error": f"Invalid response format: {post_response.text}"}

    # Store the submission
    record_id = str(uuid.uuid4())
    submission_store[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_json,
        "post_payload": post_payload,
        "post_response": post_response_json,
    }

    return RedirectResponse(f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}")
def view_submission(record_id: str, request: Request):
    record = submission_store.get(record_id)
    if not record:
        return templates.TemplateResponse("view.html", {"request": request, "error": "Record not found."})
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "record_id": record_id,
            "ping_payload": record["ping_payload"],
            "ping_response": record["ping_response"],
            "post_payload": record["post_payload"],
            "post_response": record["post_response"],
        },
    )
