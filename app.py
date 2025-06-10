from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uuid
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage for PING/POST results
results_store = {}

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def submit_form(
    request: Request,
    ZIP: str = Form(...),
    Language: str = Form(...),
    Origin_Phone_Area_Code: str = Form(...),
    Origin_Phone_Prefix: str = Form(...),
    Origin_Phone_Suffix: str = Form(...),
    Filter_1: str = Form(...),
    Sub_ID: str = Form(...),
    Have_Attorney: str = Form(...),
    Trusted_Form_URL: str = Form(...),
    tc_id: str = Form(...)
):
    # Build full phone number parts
    Origin_Phone_Full = f"{Origin_Phone_Area_Code}{Origin_Phone_Prefix}{Origin_Phone_Suffix}"

    # Prepare PING payload
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
        "Origin_Phone_Prefix": Origin_Phone_Prefix,
        "Origin_Phone_Suffix": Origin_Phone_Suffix,
        "Terminating_Phone_Country_Code": "1",
        "Terminating_Phone": "2534870338",
        "Filter_1": Filter_1,
        "Return_Best_Price": "1",
        "Sub_ID": Sub_ID,
        "Have_Attorney": Have_Attorney,
        "Trusted_Form_URL": Trusted_Form_URL,
        "tc_id": tc_id
    }

    # Send PING request
    ping_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=ping_payload)
    ping_result = ping_response.text

    # Check if PING matched and prepare POST if applicable
    post_result = "PING did not match, no POST sent."
    lead_id = None

    if '"Matched"' in ping_result:
        # Extract Lead_ID from response (simplified)
        lead_id = ping_response.json()["response"]["lead_id"]

        # Prepare POST payload (same as ping but Mode=post and Lead_ID included)
        post_payload = ping_payload.copy()
        post_payload["Mode"] = "post"
        post_payload["Lead_ID"] = lead_id

        post_response = requests.post("https://leads.4legalleads.com/new_api/api.php", data=post_payload)
        post_result = post_response.text

    # Store results
    record_id = str(uuid.uuid4())
    results_store[record_id] = {
        "ping_payload": ping_payload,
        "ping_response": ping_result,
        "post_response": post_result
    }

    return RedirectResponse(url=f"/view/{record_id}", status_code=302)

@app.get("/view/{record_id}", response_class=HTMLResponse)
async def view_result(request: Request, record_id: str):
    result = results_store.get(record_id)
    if not result:
        return HTMLResponse(content="Record not found.", status_code=404)
    return templates.TemplateResponse("view.html", {"request": request, "record_id": record_id, **result})
