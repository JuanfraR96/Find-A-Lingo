import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any

from scraper import run_scraper

app = FastAPI()

# Make sure static dir exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

from scraper_cmi import run_scraper_cmi

@app.get("/api/filters")
async def get_filters(registry: str = "rid"):
    if registry == "cmi":
        with open("filters_cmi.json", "r") as f:
            return json.load(f)
    else:
        with open("filters.json", "r") as f:
            return json.load(f)

@app.post("/api/scrape")
async def scrape_endpoint(request: Request):
    filters = await request.json()
    registry = filters.pop("registry", "rid")
    
    # Run scraper
    if registry == "cmi":
        excel_data = await run_scraper_cmi(filters)
    else:
        excel_data = await run_scraper(filters)
    
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=find_a_lingo_results.xlsx"}
    )
