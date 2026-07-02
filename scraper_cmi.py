import asyncio
import io
import re
from playwright.async_api import async_playwright
from openpyxl import Workbook

async def run_scraper_cmi(filters: dict):
    print("Running CMI scraper with filters:", filters)
    
    # We will store scraped people here
    people = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to the CMI registry
        await page.goto("https://www.imiaweb.org/0_nbcmi_registry_3/mc_registry.asp?mode=3&view=table")
        
        # We need to switch back to form if mode=3 skips it? No, mode=3&view=table directly shows all records!
        # Wait, if we use ?mode=3&view=table we skip the search form.
        # Let's go to the main page first.
        await page.goto("https://www.imiaweb.org/0_nbcmi_registry_3/mc_registry.asp")
        await page.wait_for_selector("#SearchForm")
        
        row_idx = 0
        if filters.get("cmi_language"):
            if row_idx > 0:
                await page.click("#add-row")
                await page.wait_for_timeout(500)
            await page.locator("select[name='Attribute']").nth(row_idx).select_option("CertifiedLanguage")
            await page.wait_for_timeout(500)
            await page.locator("select[name='Criteria']").nth(row_idx).select_option(filters["cmi_language"])
            row_idx += 1

        if filters.get("cmi_state"):
            if row_idx > 0:
                await page.click("#add-row")
                await page.wait_for_timeout(500)
            await page.locator("select[name='Attribute']").nth(row_idx).select_option("WorkState")
            await page.wait_for_timeout(500)
            await page.locator("select[name='Criteria']").nth(row_idx).select_option(filters["cmi_state"])
            row_idx += 1
            
        # Submit the form
        if row_idx > 0:
            async with page.expect_navigation():
                await page.click("button[type='submit']")
        else:
            # If no filters, click View All
            async with page.expect_navigation():
                await page.click("#ViewAll")

        # Now we are on the results page.
        # Check if there are pages
        page_options = await page.locator("select#PageNumber option").all()
        total_pages = len(page_options) if page_options else 1
        print(f"Total pages detected: {total_pages}")
        
        for p_idx in range(total_pages):
            print(f"Scraping page {p_idx + 1} of {total_pages}")
            if p_idx > 0:
                # change the select option and wait for navigation
                async with page.expect_navigation():
                    await page.select_option("select#PageNumber", value=str(p_idx + 1))
            
            # wait for table to be visible
            await page.wait_for_selector("table[style*='margin-top: 30px']")
            
            # extract rows
            rows = await page.locator("table[style*='margin-top: 30px'] tr").all()
            
            # row[0] is headers, skip it
            for row in rows[1:]:
                cells = await row.locator("td").all_inner_texts()
                if len(cells) >= 7:
                    # Extract email from the <a> tag in the second cell
                    email = ""
                    a_tag = row.locator("td").nth(1).locator("a")
                    if await a_tag.count() > 0:
                        email = await a_tag.first.get_attribute("data-email") or ""
                        
                    person = {
                        "Name": cells[2].strip(),
                        "Email": email.strip(),
                        "Type": cells[3].strip(),
                        "Expires": cells[4].strip(),
                        "Language": cells[5].strip(),
                        "City/State/Country": cells[6].strip(),
                    }
                    people.append(person)
        
        await browser.close()
    
    # Generate Excel file
    wb = Workbook()
    ws = wb.active
    ws.title = "CMI Registry Results"
    
    headers = ["Name", "Email", "Type", "Expires", "Language", "Location"]
    ws.append(headers)
    
    for p in people:
        ws.append([
            p.get("Name", ""),
            p.get("Email", ""),
            p.get("Type", ""),
            p.get("Expires", ""),
            p.get("Language", ""),
            p.get("City/State/Country", "")
        ])
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output.read()

# Optional manual test
if __name__ == "__main__":
    async def main():
        filters = {"cmi_state": "WA"}
        data = await run_scraper_cmi(filters)
        with open("test_cmi_output.xlsx", "wb") as f:
            f.write(data)
        print("Done! Saved to test_cmi_output.xlsx")
    
    asyncio.run(main())
