from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import uuid
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory storage of ping/post data (simple)
db = {}

@app.get("/")
def index(request: Request):
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
    landing_page: str = Form(...),

    # Optional fields for dynamic categories
    incident_date: str = Form(""),
    injury_type: str = Form(""),
    were_you_at_fault: str = Form(""),
    doctor_treatment: str = Form("")
):
    lead_id = str(uuid.uuid4())

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
        "Trusted_Form_URL": trusted_form_url,
        "Landing_Page": landing_page
    }

    # Add dynamic required fields per category
    if filter_1 in [
        "Auto Accident Injury",
        "Personal Injury",
        "Workers Comp",
        "Medical Malpractice",
        "Product Liability"
    ]:
        ping_payload["Incident_Date"] = incident_date
        ping_payload["Injury_Type"] = injury_type
        ping_payload["Were_You_At_Fault"] = were_you_at_fault
        ping_payload["Doctor_Treatment"] = doctor_treatment

    # Send Ping Request
    ping_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=ping_payload)
    try:
        ping_response_json = ping_response.json()
    except Exception:
        ping_response_json = {"error": f"Invalid JSON response: {ping_response.text}"}

    # Prepare Post Payload
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
        "App_ID": "888",
        "Landing_Page": landing_page,
        "Start_Date_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Lead_ID": ping_response_json.get("response", {}).get("lead_id", "")
    }

    # Add dynamic required fields per category
    if filter_1 in [
        "Auto Accident Injury",
        "Personal Injury",
        "Workers Comp",
        "Medical Malpractice",
        "Product Liability"
    ]:
        post_payload["Incident_Date"] = incident_date
        post_payload["Injury_Type"] = injury_type
        post_payload["Were_You_At_Fault"] = were_you_at_fault
        post_payload["Doctor_Treatment"] = doctor_treatment

    # Send Post Request
    post_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=post_payload)
    try:
        post_response_json = post_response.json()
    except Exception:
        post_response_json = {"error": f"Invalid JSON response: {post_response.text}"}

    # Store in DB
    db[lead_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_json,
        "post_payload": post_payload,
        "post_response": post_response_json
    }

    return RedirectResponse(url=f"/view/{lead_id}", status_code=302)

@app.get("/view/{lead_id}")
def view(request: Request, lead_id: str):
    data = db.get(lead_id)
    if not data:
        return templates.TemplateResponse("view.html", {"request": request, "error": "Lead ID not found."})
    return templates.TemplateResponse("view.html", {"request": request, "lead_id": lead_id, **data})
