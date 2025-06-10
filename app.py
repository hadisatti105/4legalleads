from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import requests
import hashlib
import json
import os
from uuid import uuid4

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_URL = "https://leads.4legalleads.com/apiJSON.php"
API_KEY = "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716"
SRC = "DurationLKC120Transfer"

RESPONSES_DIR = "responses"
os.makedirs(RESPONSES_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/view/{uid}", response_class=HTMLResponse)
async def view_payloads(request: Request, uid: str):
    ping_file = os.path.join(RESPONSES_DIR, f"{uid}-ping.json")
    post_file = os.path.join(RESPONSES_DIR, f"{uid}-post.json")

    ping_data = {}
    post_data = {}

    if os.path.exists(ping_file):
        with open(ping_file, "r") as f:
            ping_data = json.load(f)

    if os.path.exists(post_file):
        with open(post_file, "r") as f:
            post_data = json.load(f)

    return templates.TemplateResponse("view.html", {
        "request": request,
        "uid": uid,
        "ping_data": ping_data,
        "post_data": post_data
    })

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    zip_code: str = Form(...),
    comments: str = Form(...),
    trusted_form_url: str = Form(...),
    type_of_legal_problem: str = Form(...),
    user_agent: str = Form(...),
    incident_date: str = Form(...),
    doctor_treatment: str = Form(...),
    injury_type: str = Form(...),
    were_you_at_fault: str = Form(...),
    have_insurance: str = Form(...),
    have_attorney: str = Form(...),
    language: str = Form(...),
    ip_address: str = Form(...),
    sub_id: str = Form(...)
):
    uid = str(uuid4())
    email_hash = hashlib.md5(email.encode()).hexdigest()
    phone_hash = hashlib.md5(phone.encode()).hexdigest()

    form_data = {
        "Key": API_KEY,
        "SRC": SRC,
        "API_Action": "pingPostLead",
        "Format": "JSON",
        "Mode": "ping",
        "Return_Best_Price": "1",
        "Language": language,
        "TYPE": "31",
        "Trusted_Form_URL": trusted_form_url,
        "TCPA": "Yes",
        "Hash_Type": "md5",
        "Email_Hash": email_hash,
        "Phone_Hash": phone_hash,
        "Have_Attorney": have_attorney,
        "Comments": comments,
        "Zip": zip_code,
        "Type_Of_Legal_Problem": type_of_legal_problem,
        "User_Agent": user_agent,
        "Incident_Date": incident_date,
        "Doctor_Treatment": doctor_treatment,
        "Injury_Type": injury_type,
        "Were_You_At_Fault": were_you_at_fault,
        "Have_Insurance": have_insurance,
        "Landing_Page": "LandingPage",
        "IP_Address": ip_address,
        "Sub_ID": sub_id
    }

    payload = {"Request": form_data}
    response = requests.post(API_URL, json=payload)
    ping_result = response.json()

    with open(os.path.join(RESPONSES_DIR, f"{uid}-ping.json"), "w") as f:
        json.dump({"payload": payload, "response": ping_result}, f, indent=4)

    with open(os.path.join(RESPONSES_DIR, f"{uid}-form.json"), "w") as f:
        json.dump(form_data, f, indent=4)

    return RedirectResponse(f"/view/{uid}", status_code=302)

@app.post("/post-lead", response_class=HTMLResponse)
async def post_lead(request: Request, uid: str = Form(...), lead_id: str = Form(...)):
    form_path = os.path.join(RESPONSES_DIR, f"{uid}-form.json")

    if not os.path.exists(form_path):
        return HTMLResponse("Form data not found.", status_code=400)

    with open(form_path, "r") as f:
        form_data = json.load(f)

    form_data["Mode"] = "post"
    form_data["Lead_ID"] = lead_id
    payload = {"Request": form_data}

    response = requests.post(API_URL, json=payload)
    post_result = response.json()

    with open(os.path.join(RESPONSES_DIR, f"{uid}-post.json"), "w") as f:
        json.dump({"payload": payload, "response": post_result}, f, indent=4)

    return RedirectResponse(f"/view/{uid}", status_code=302)
