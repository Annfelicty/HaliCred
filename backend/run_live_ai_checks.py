# file: scripts/run_live_ai_checks.py
import json
from pathlib import Path

import google.generativeai as genai
from google.oauth2 import service_account
from google.cloud import vision
import requests
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("models/gemini-2.5-flash")
gemini_response = model.generate_content("List two creative eco-initiatives for SMEs.")
print("Gemini:", gemini_response.text[:120], "...")

# Google Vision
base_dir = Path(__file__).resolve().parent

# Google Vision
creds = service_account.Credentials.from_service_account_file(
    base_dir / "keys/google-vision.json"
)
client = vision.ImageAnnotatorClient(credentials=creds)
image_path = base_dir / "sample-data/solar-panel.jpg"
with open(image_path, "rb") as img:
    image = vision.Image(content=img.read())
vision_result = client.label_detection(image=image)
print("Vision labels:", [label.description for label in vision_result.label_annotations[:3]])

# climatiq
headers = {
    "Authorization": f"Bearer {os.environ['CLIMATIQ_API_KEY']}",
    "Content-Type": "application/json",
}

SEARCH_URL = "https://api.climatiq.io/data/v1/search"
ESTIMATE_URL = "https://api.climatiq.io/data/v1/estimate"

def find_emission_factor() -> tuple[str, str]:
    params = {
        "activity_id": "electricity-supply_grid-source_residual_mix",
        "region": "GLO",
        "results_per_page": 1,
        "data_version": "26.26",
    }
    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])

    if not results:
        raise RuntimeError("No emission factors returned from Climatiq search")

    factor = results[0]
    activity_id = factor["activity_id"]
    data_version = params["data_version"]
    return activity_id, data_version




factor_id, data_version = find_emission_factor()
payload = {
    "emission_factor": {
        "activity_id": factor_id,
        "data_version": data_version,
        "region": "GLO",
    },
    "parameters": {
        "energy": 100,
        "energy_unit": "kWh",
    }
}

climatiq_response = requests.post(
    ESTIMATE_URL,
    headers=headers,
    json=payload,
    timeout=30,
)
print("Climatiq:", climatiq_response.status_code, climatiq_response.json())