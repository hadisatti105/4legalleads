# app.py
import uuid
import json
import os
from datetime import datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

API_URL = "https://leads.4legalleads.com/new_api/api.php"
API_KEY = "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716"
TERMINATING_PHONE = "2534870338"
MATCH_WITH_PARTNER_ID = "20827"
SRC = "DurationLKC120Transfer"

# In-memory storage for responses
responses_db = {}

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def submit(
    request: Request,
    filter_1: str = Form(...),
    zip_code: str = Form(...),
    language: str = Form(...),
    origin_phone_area_code: str = Form(...),
    origin_phone_prefix: str = Form(...),
    origin_phone_suffix: str = Form(...),
    sub_id: str = Form(...),
    have_attorney: str = Form(...),
    trusted_form_url: str = Form(...),
    tc_id: str = Form(...),
    degree_of_interest: str = Form(...),
    landing_page: str = Form(...),
    incident_date: str = Form(...),
    injury_type: str = Form(...),
    were_you_at_fault: str = Form(...),
    doctor_treatment: str = Form(...),
):

    # ----- PING -----
    ping_payload = {
        "Mode": "ping",
        "Format": "JSON",
        "Key": API_KEY,
        "API_Action": "custom4llIprSubmitLeadWithComboCheck",
        "Match_With_Partner_ID": MATCH_WITH_PARTNER_ID,
        "TYPE": "9",
        "SRC": SRC,
        "ZIP": zip_code,
        "Language": language,
        "Origin_Phone_Country_Code": "1",
        "Origin_Phone_Area_Code": origin_phone_area_code,
        "Origin_Phone_Prefix": origin_phone_prefix,
        "Origin_Phone_Suffix": origin_phone_suffix,
        "Terminating_Phone_Country_Code": "1",
        "Terminating_Phone": TERMINATING_PHONE,
        "Filter_1": filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": sub_id,
        "Have_Attorney": have_attorney,
        "Trusted_Form_URL": trusted_form_url,
        "tc_id": tc_id,
        "Degree_Of_Interest": degree_of_interest,
        "Landing_Page": landing_page,
        "Incident_Date": incident_date,
        "Injury_Type": injury_type,
        "Were_You_At_Fault": were_you_at_fault,
        "Doctor_Treatment": doctor_treatment,
    }

    ping_response = requests.post(API_URL, data=ping_payload)
    ping_response_json = ping_response.json()

    lead_id = ping_response_json.get("response", {}).get("lead_id")

    # ----- POST -----
    if lead_id:
        post_payload = ping_payload.copy()
        post_payload.update({
            "Mode": "post",
            "Format": "JSON",
            "App_ID": "888",
            "Start_Date_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Lead_ID": lead_id,
        })

        post_response = requests.post(API_URL, data=post_payload)
        post_response_json = post_response.json()
    else:
        post_payload = {}
        post_response_json = {}

    # Save to in-memory db
    record_id = str(uuid.uuid4())
    responses_db[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_json,
        "post_payload": post_payload,
        "post_response": post_response_json,
    }

    # Redirect to view page
    return RedirectResponse(f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}")
async def view_result(request: Request, record_id: str):
    data = responses_db.get(record_id)
    if not data:
        return templates.TemplateResponse("view.html", {"request": request, "error": "Record not found."})
    return templates.TemplateResponse("view.html", {"request": request, "record_id": record_id, **data})
