import asyncio
from app.scraper import run_scraper

async def main():
    filters = {"ctl00$FormContentPlaceHolder$Panel$stateDropDownList": "48fdccc5-cf2f-e511-80c5-00155d631510"} # Washington
    # I will temporarily modify run_scraper in the test to print how many links it extracts per page
    # Since I can't easily modify the module for printing without editing the real file,
    # I will just edit scraper.py directly to add debug prints.
    pass

asyncio.run(main())
