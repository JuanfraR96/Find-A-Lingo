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
        
        # change size
        print("Changing page size...")
        try:
            async with page.expect_response(lambda r: "Member.aspx" in r.url and r.request.method == "POST", timeout=10000):
                await page.select_option("select[name$='$ctl10']", value="50")
            print("Page size changed successfully")
        except Exception as e:
            print("Page size change failed:", e)
        
        await page.wait_for_timeout(2000) # give JS time to apply DOM changes
        
        # go to page 2
        print("Navigating to page 2...")
        try:
            async with page.expect_response(lambda r: "Member.aspx" in r.url and r.request.method == "POST", timeout=10000):
                await page.evaluate("__doPostBack('ctl00$FormContentPlaceHolder$Panel$resultsGrid','Page$2')")
            print("Navigation succeeded")
        except Exception as e:
            print("Navigation failed:", e)

        await page.wait_for_timeout(2000)
        html = await page.inner_html("#FormContentPlaceHolder_Panel_resultsGrid")
        if "Page$3" in html:
            print("Successfully reached page 2 (Page 3 link exists)")
        else:
            print("Did not reach page 2")
            
        await browser.close()

asyncio.run(main())
