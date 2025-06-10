# app.py
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
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory store for Ping/Post payloads
ping_post_store = {}

@app.get("/")
def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
def form_post(
    request: Request,
    ZIP: str = Form(...),
    Language: str = Form(...),
    Origin_Phone_Area_Code: str = Form(...),
    Filter_1: str = Form(...),
    Sub_ID: str = Form(...),
    Have_Attorney: str = Form(...),
    Trusted_Form_URL: str = Form(...),
    tc_id: str = Form(...),
):

    # Build PING payload
    ping_payload = {
        "Format": "JSON",
        "Mode": "ping",
        "Key": "a1598e131406605ba08ef7e9b5c0f7d3568b568d532ee38b32c1afe780a92716",
        "API_Action": "custom4llIprSubmitLeadWithComboCheck",
        "Match_With_Partner_ID": "20827",
        "TYPE": "9",
        "SRC": "DurationLKC120Transfer",
        "ZIP": ZIP,
        "Language": Language,
        "Origin_Phone_Country_Code": "1",
        "Origin_Phone_Area_Code": Origin_Phone_Area_Code,
        "Terminating_Phone_Country_Code": "1",
        "Terminating_Phone": "2534870338",
        "Filter_1": Filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": Sub_ID,
        "Have_Attorney": Have_Attorney,
        "Trusted_Form_URL": Trusted_Form_URL,
        "tc_id": tc_id,
    }

    # Send Ping
    ping_response = requests.post(
        "https://leads.4legalleads.com/new_api/api.php", data=ping_payload
    )

    ping_response_json = ping_response.json()

    # If Matched, do POST
    lead_id = ping_response_json.get("response", {}).get("lead_id")
    post_response_json = {}
    if ping_response_json.get("response", {}).get("status") == "Matched" and lead_id:
        post_payload = ping_payload.copy()
        post_payload["Mode"] = "post"
        post_payload["Lead_ID"] = lead_id

        post_response = requests.post(
            "https://leads.4legalleads.com/new_api/api.php", data=post_payload
        )
        post_response_json = post_response.json()

    # Save the transaction for /view page
    record_id = str(uuid.uuid4())
    ping_post_store[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_response_json,
        "post_payload": post_payload if lead_id else {},
        "post_response": post_response_json,
    }

    return RedirectResponse(url=f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}")
def view_record(request: Request, record_id: str):
    record = ping_post_store.get(record_id)
    if not record:
        return templates.TemplateResponse(
            "view.html",
            {
                "request": request,
                "ping_payload": {},
                "ping_response": {},
                "post_payload": {},
                "post_response": {},
                "record_id": record_id,
            },
        )

    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "ping_payload": record["ping_payload"],
            "ping_response": record["ping_response"],
            "post_payload": record["post_payload"],
            "post_response": record["post_response"],
            "record_id": record_id,
        },
    )
