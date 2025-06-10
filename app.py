from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import uuid
import json
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# In-memory store for pings & posts (for /view/ page)
PING_POST_STORE = {}

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
def submit(
    request: Request,
    zip_code: str = Form(...),
    language: str = Form(...),
    origin_area_code: str = Form(...),
    origin_prefix: str = Form(...),
    origin_suffix: str = Form(...),
    terminating_phone: str = Form(...),
    filter_1: str = Form(...),
    sub_id: str = Form(...),
    have_attorney: str = Form(...),
    trusted_form_url: str = Form(...),
    tc_id: str = Form(...),
):

    # Build Ping payload
    payload = {
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
        "Terminating_Phone": terminating_phone,
        "Filter_1": filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": sub_id,
        "Have_Attorney": have_attorney,
        "Trusted_Form_URL": trusted_form_url,
        "tc_id": tc_id,
        "Key": "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716",
        "Format": "JSON",
        "Mode": "ping"
    }

    # Send Ping request
    ping_response = requests.post(
        "https://leads.4legalleads.com/new_api/api.php",
        data=payload
    )
    try:
        ping_json = ping_response.json()
    except:
        ping_json = {"error": "Invalid JSON response"}

    # Save Ping payload + response
    record_id = str(uuid.uuid4())
    PING_POST_STORE[record_id] = {
        "ping_payload": payload,
        "ping_response": ping_json
    }

    # Redirect to /view/ page
    return RedirectResponse(url=f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}")
def view(request: Request, record_id: str):
    record = PING_POST_STORE.get(record_id)
    if not record:
        return templates.TemplateResponse("view.html", {
            "request": request,
            "record_id": record_id,
            "ping_payload": None,
            "ping_response": None
        })

    return templates.TemplateResponse("view.html", {
        "request": request,
        "record_id": record_id,
        "ping_payload": json.dumps(record["ping_payload"], indent=4),
        "ping_response": json.dumps(record["ping_response"], indent=4)
    })
