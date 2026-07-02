import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.imiaweb.org/0_nbcmi_registry_3/mc_registry.asp")
        
        # Add Language filter
        await page.locator("select[name='Attribute']").nth(0).select_option("CertifiedLanguage")
        await page.wait_for_timeout(500) # Wait for JS to populate Criteria
        await page.locator("select[name='Criteria']").nth(0).select_option("Spanish")
        
        # Click search
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")
        
        html = await page.content()
        with open("cmi_results.html", "w") as f:
            f.write(html)
        
        await browser.close()

asyncio.run(main())
