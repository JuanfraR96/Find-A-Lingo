import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://myaccount.rid.org/Public/Search/Member.aspx")
        
        await page.select_option("select[name='ctl00$FormContentPlaceHolder$Panel$stateDropDownList']", label="Washington")
        await page.click("#FormContentPlaceHolder_Panel_searchButtonStrip_searchButton")
        
        await page.wait_for_selector("#FormContentPlaceHolder_Panel_resultsGrid", timeout=15000)
        await page.select_option("select[name='ctl00$FormContentPlaceHolder$Panel$resultsGrid$ctl13$ctl10']", value="50")
        await page.wait_for_timeout(3000)
        
        html = await page.inner_html("#FormContentPlaceHolder_Panel_resultsGrid")
        
        # Save it to check
        with open("grid.html", "w") as f:
            f.write(html)
            
        print("Done")
        await browser.close()

asyncio.run(main())
