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

@app.get("/api/filters")
async def get_filters():
    with open("filters.json", "r") as f:
        return json.load(f)

@app.post("/api/scrape")
async def scrape_endpoint(request: Request):
    filters = await request.json()
    
    # Run scraper
    csv_data = await run_scraper(filters)
    
    return Response(
        content=csv_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=find_a_lingo_results.xlsx"}
    )
