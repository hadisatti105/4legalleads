# app.py FINAL CLEAN FULL VERSION with Ping/Post + CSS

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import uuid
from datetime import datetime
import re

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# In-memory storage for ping/post records
records = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit", response_class=HTMLResponse)
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
    # Dynamic fields
    incident_date: str = Form(None),
    injury_type: str = Form(None),
    were_you_at_fault: str = Form(None),
    doctor_treatment: str = Form(None)
):
    record_id = str(uuid.uuid4())

    # Build Ping Payload
    ping_payload = {
        "Mode": "ping",
        "Key": "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716",
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
        "Terminating_Phone": "2534870338",
        "Filter_1": filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": sub_id,
        "Have_Attorney": have_attorney,
        "Trusted_Form_URL": trusted_form_url.strip(),
        "Landing_Page": landing_page
    }

    # Add dynamic fields if required by category
    if filter_1 in [
        "Auto Accident Injury",
        "Personal Injury",
        "Medical Malpractice",
        "Workers Comp",
        "Product Liability"
    ]:
        ping_payload["Incident_Date"] = incident_date
        ping_payload["Injury_Type"] = injury_type
        ping_payload["Were_You_At_Fault"] = were_you_at_fault
        ping_payload["Doctor_Treatment"] = doctor_treatment

    # Send Ping Request
    ping_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=ping_payload)
    ping_response_text = ping_response.text

    # Default empty Post Payload & Response
    post_payload = {}
    post_response_text = ""

    # If Ping Matched → do POST
    if "<status>Matched</status>" in ping_response_text:
        # Extract Lead_ID
        lead_id_match = re.search(r"<lead_id>(.*?)</lead_id>", ping_response_text)
        lead_id = lead_id_match.group(1) if lead_id_match else ""

        # Build Post Payload
        post_payload = {
            "Mode": "post",
            "Key": "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716",
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
            "Terminating_Phone": "2534870338",
            "Filter_1": filter_1,
            "Sub_ID": sub_id,
            "Have_Attorney": have_attorney,
            "Trusted_Form_URL": trusted_form_url.strip(),
            "Landing_Page": landing_page,
            "App_ID": "888",
            "Start_Date_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Lead_ID": lead_id
        }

        # Add dynamic fields again
        if filter_1 in [
            "Auto Accident Injury",
            "Personal Injury",
            "Medical Malpractice",
            "Workers Comp",
            "Product Liability"
        ]:
            post_payload["Incident_Date"] = incident_date
            post_payload["Injury_Type"] = injury_type
            post_payload["Were_You_At_Fault"] = were_you_at_fault
            post_payload["Doctor_Treatment"] = doctor_treatment

        # Send Post Request
        post_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=post_payload)
        post_response_text = post_response.text

    # Save record
    records[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_text,
        "post_payload": post_payload,
        "post_response": post_response_text
    }

    # Redirect to view page
    return RedirectResponse(url=f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}", response_class=HTMLResponse)
async def view_record(request: Request, record_id: str):
    record = records.get(record_id, {})
    return templates.TemplateResponse("view.html", {
        "request": request,
        "record_id": record_id,
        "ping_payload": record.get("ping_payload", {}),
        "ping_response": record.get("ping_response", ""),
        "post_payload": record.get("post_payload", {}),
        "post_response": record.get("post_response", "")
    })
