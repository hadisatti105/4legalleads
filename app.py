from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import json
import uuid
import datetime

app = FastAPI()

# Templates & static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage of ping/post records
records = {}

# API constants
PING_URL = "https://leads.4legalleads.com/new_api/api.php"
POST_URL = "https://leads.4legalleads.com/new_api/api.php"
API_KEY = "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716"
SRC = "DurationLKC120Transfer"
MATCH_WITH_PARTNER_ID = "20827"
TERMINATING_PHONE = "2534870338"
TERMINATING_PHONE_COUNTRY_CODE = "1"

@app.get("/")
async def index(request: Request):
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
    landing_page: str = Form(...),
    # Conditional fields:
    incident_date: str = Form(None),
    injury_type: str = Form(None),
    were_you_at_fault: str = Form(None),
    doctor_treatment: str = Form(None)
):
    # Prepare PING payload
    ping_payload = {
        "Mode": "ping",
        "Key": API_KEY,
        "API_Action": "custom4llIprSubmitLeadWithComboCheck",
        "Match_With_Partner_ID": MATCH_WITH_PARTNER_ID,
        "TYPE": "9",
        "SRC": SRC,
        "ZIP": zip_code,
        "Language": language,
        "Origin_Phone_Country_Code": "1",
        "Origin_Phone_Area_Code": origin_area_code,
        "Origin_Phone_Prefix": origin_prefix,
        "Origin_Phone_Suffix": origin_suffix,
        "Terminating_Phone_Country_Code": TERMINATING_PHONE_COUNTRY_CODE,
        "Terminating_Phone": TERMINATING_PHONE,
        "Filter_1": filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": sub_id,
        "Have_Attorney": have_attorney,
        "Trusted_Form_URL": trusted_form_url,
        "Landing_Page": landing_page,
    }

    # Add conditional fields based on Filter_1
    if filter_1 in ["Auto Accident Injury", "Personal Injury", "Workers Comp", "Medical Malpractice", "Product Liability"]:
        if incident_date: ping_payload["Incident_Date"] = incident_date
        if injury_type: ping_payload["Injury_Type"] = injury_type
        if were_you_at_fault: ping_payload["Were_You_At_Fault"] = were_you_at_fault
        if doctor_treatment: ping_payload["Doctor_Treatment"] = doctor_treatment

    # Send PING
    ping_response = requests.post(PING_URL, data=ping_payload)
    try:
        ping_response_json = ping_response.json()
    except json.JSONDecodeError:
        ping_response_json = {"error": f"Invalid JSON response: {ping_response.text}"}

    # Extract Lead_ID if Matched
    lead_id = None
    if "response" in ping_response_json and ping_response_json["response"].get("status") == "Matched":
        lead_id = ping_response_json["response"].get("lead_id")

    # Prepare POST payload if lead_id available
    post_payload = {}
    post_response_json = {}
    if lead_id:
        post_payload = {
            "Mode": "post",
            "Key": API_KEY,
            "API_Action": "custom4llIprSubmitLeadWithComboCheck",
            "Match_With_Partner_ID": MATCH_WITH_PARTNER_ID,
            "TYPE": "9",
            "SRC": SRC,
            "ZIP": zip_code,
            "Language": language,
            "Origin_Phone_Country_Code": "1",
            "Origin_Phone_Area_Code": origin_area_code,
            "Origin_Phone_Prefix": origin_prefix,
            "Origin_Phone_Suffix": origin_suffix,
            "Terminating_Phone_Country_Code": TERMINATING_PHONE_COUNTRY_CODE,
            "Terminating_Phone": TERMINATING_PHONE,
            "Filter_1": filter_1,
            "Sub_ID": sub_id,
            "Have_Attorney": have_attorney,
            "Trusted_Form_URL": trusted_form_url,
            "Landing_Page": landing_page,
            "App_ID": "888",
            "Start_Date_Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Lead_ID": lead_id,
        }

        # Add conditional fields
        if filter_1 in ["Auto Accident Injury", "Personal Injury", "Workers Comp", "Medical Malpractice", "Product Liability"]:
            if incident_date: post_payload["Incident_Date"] = incident_date
            if injury_type: post_payload["Injury_Type"] = injury_type
            if were_you_at_fault: post_payload["Were_You_At_Fault"] = were_you_at_fault
            if doctor_treatment: post_payload["Doctor_Treatment"] = doctor_treatment

        # Send POST
        post_response = requests.post(POST_URL, data=post_payload)
        try:
            post_response_json = post_response.json()
        except json.JSONDecodeError:
            post_response_json = {"error": f"Invalid JSON response: {post_response.text}"}

    # Save record
    record_id = str(uuid.uuid4())
    records[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_json,
        "post_payload": post_payload,
        "post_response": post_response_json
    }

    return RedirectResponse(url=f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}")
async def view_record(request: Request, record_id: str):
    record = records.get(record_id)
    if not record:
        return templates.TemplateResponse("view.html", {"request": request, "error": "Record not found."})
    return templates.TemplateResponse("view.html", {
        "request": request,
        "record_id": record_id,
        "ping_payload": record["ping_payload"],
        "ping_response": record["ping_response"],
        "post_payload": record["post_payload"],
        "post_response": record["post_response"],
    })
