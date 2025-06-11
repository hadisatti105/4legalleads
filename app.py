# app.py

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import json
import uuid
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for displaying results
results_db = {}

@app.get("/")
def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
def submit(
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
    tc_id: str = Form(""),  # Optional
):

    # Build PING payload
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
        "Trusted_Form_URL": trusted_form_url,
        "tc_id": tc_id,  # optional
    }

    # Add Filter_1 category-specific required fields (Auto Accident Injury / Personal Injury / etc.)
    # These are required for the example categories you mentioned
    ping_payload["Incident_Date"] = incident_date
    ping_payload["Injury_Type"] = injury_type
    ping_payload["Were_You_At_Fault"] = were_you_at_fault
    ping_payload["Doctor_Treatment"] = doctor_treatment

    # Send PING request
    ping_response = requests.post(
        "https://leads.4legalleads.com/new_api/api.php", data=ping_payload
    )

    try:
        ping_response_json = ping_response.json()
    except Exception:
        ping_response_json = {"error": "Invalid response", "raw": ping_response.text}

    # If PING Matched → Proceed with POST
    post_response_json = {}
    if (
        "response" in ping_response_json
        and ping_response_json["response"].get("status") == "Matched"
    ):
        lead_id = ping_response_json["response"].get("lead_id", "")

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
            "Trusted_Form_URL": trusted_form_url,
            "tc_id": tc_id,  # optional
            "App_ID": "888",
            "Landing_Page": landing_page,
            "Start_Date_Time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "Lead_ID": lead_id,
            "Incident_Date": incident_date,
            "Injury_Type": injury_type,
            "Were_You_At_Fault": were_you_at_fault,
            "Doctor_Treatment": doctor_treatment,
        }

        # Send POST request
        post_response = requests.post(
            "https://leads.4legalleads.com/new_api/api.php", data=post_payload
        )

        try:
            post_response_json = post_response.json()
        except Exception:
            post_response_json = {"error": "Invalid response", "raw": post_response.text}

    # Save result in in-memory DB for redirect
    record_id = str(uuid.uuid4())
    results_db[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_json,
        "post_response": post_response_json,
    }

    return RedirectResponse(f"/view/{record_id}", status_code=302)


@app.get("/view/{record_id}")
def view_result(request: Request, record_id: str):
    data = results_db.get(record_id, {})
    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "record_id": record_id,
            "ping_payload": json.dumps(data.get("ping_payload", {}), indent=2),
            "ping_response": json.dumps(data.get("ping_response", {}), indent=2),
            "post_response": json.dumps(data.get("post_response", {}), indent=2),
        },
    )
