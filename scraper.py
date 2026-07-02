import asyncio
import csv
from bs4 import BeautifulSoup
import aiohttp
from playwright.async_api import async_playwright
import re
import io

async def fetch_details(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Name
            name_div = soup.find('div', string=re.compile('Member Name:'))
            name = name_div.find_next_sibling('div').text.strip() if name_div and name_div.find_next_sibling('div') else ""
            
            # Home Phone
            hp_div = soup.find('div', string=re.compile('Home Phone:'))
            home_phone = hp_div.find_next_sibling('div').text.strip() if hp_div and hp_div.find_next_sibling('div') else ""
            
            # Mobile Phone
            mp_div = soup.find('div', string=re.compile('Mobile Phone:'))
            mobile_phone = mp_div.find_next_sibling('div').text.strip() if mp_div and mp_div.find_next_sibling('div') else ""
            
            # Work Phone
            wp_div = soup.find('div', string=re.compile('Work Phone:'))
            work_phone = wp_div.find_next_sibling('div').text.strip() if wp_div and wp_div.find_next_sibling('div') else ""
            
            # Email
            email_div = soup.find('div', string=re.compile('Email:'))
            email = ""
            if email_div:
                val_div = email_div.find_next_sibling('div')
                if val_div and val_div.find('a'):
                    email = val_div.find('a').text.strip()
                elif val_div:
                    email = val_div.text.strip()
                    
            return {
                'Name': name,
                'Home Phone': home_phone,
                'Mobile Phone': mobile_phone,
                'Work Phone': work_phone,
                'Email': email
            }
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {
            'Name': "Error",
            'Home Phone': "",
            'Mobile Phone': "",
            'Work Phone': "",
            'Email': ""
        }

async def run_scraper(filters: dict) -> bytes:
    urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://myaccount.rid.org/Public/Search/Member.aspx")
        
        # Apply filters
        for key, value in filters.items():
            if not value: continue
            
            if isinstance(value, list):
                # Checkboxes
                for checkbox_name in value:
                    try:
                        await page.check(f"input[name='{checkbox_name}']")
                    except Exception as e:
                        print(f"Could not check {checkbox_name}: {e}")
            else:
                try:
                    is_input = await page.evaluate(f"document.querySelector('[name=\"{key}\"]').tagName === 'INPUT'")
                    if is_input:
                        await page.fill(f"input[name='{key}']", value)
                    else:
                        await page.select_option(f"select[name='{key}']", value=value)
                except Exception as e:
                    print(f"Could not set {value} for {key}: {e}")
        
        # Click search
        await page.click("#FormContentPlaceHolder_Panel_searchButtonStrip_searchButton")
        
        # Wait for results or no results
        try:
            await page.wait_for_selector("#FormContentPlaceHolder_Panel_resultsGrid", timeout=10000)
            
            try:
                # Change page size to 50 using CSS suffix selector
                async with page.expect_response(lambda r: "Member.aspx" in r.url and r.request.method == "POST", timeout=10000):
                    await page.select_option("select[name$='$ctl10']", value="50", timeout=3000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print("Pagination dropdown not found or failed (maybe only 1 page of results).")
            
            # Get total items/pages
            pages = 1
            try:
                summary = await page.eval_on_selector("div[style='width:100%;text-align:right;'] span", "e => e.innerText", timeout=3000)
                # e.g., "282 items in 6 pages"
                match = re.search(r'in (\d+) pages', summary)
                if match:
                    pages = int(match.group(1))
            except Exception:
                pass
            
            for i in range(1, pages + 1):
                await page.wait_for_selector("#FormContentPlaceHolder_Panel_resultsGrid")
                links = await page.eval_on_selector_all("a.fancybox", "elements => elements.map(e => e.href)")
                for link in links:
                    if link not in urls:
                        urls.append(link)
                
                if i < pages:
                    next_page_num = str(i + 1)
                    try:
                        async with page.expect_response(lambda r: "Member.aspx" in r.url and r.request.method == "POST", timeout=15000):
                            await page.evaluate(f"__doPostBack('ctl00$FormContentPlaceHolder$Panel$resultsGrid','Page${next_page_num}')")
                        await page.wait_for_timeout(2000)
                    except Exception as e:
                        print(f"Error navigating to page {next_page_num}: {e}")
                        await page.wait_for_timeout(3000)
                    
        except Exception as e:
            print("No results found or error:", e)
        finally:
            await browser.close()
            
    # Fetch details
    results = []
    if urls:
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_details(session, url) for url in urls]
            sem = asyncio.Semaphore(15)
            
            async def bounded_fetch(t):
                async with sem:
                    return await t
                    
            bounded_tasks = [bounded_fetch(t) for t in tasks]
            results = await asyncio.gather(*bounded_tasks)
            
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scraped Members"
    ws.append(['Name', 'Home Phone', 'Mobile Phone', 'Work Phone', 'Email'])
    
    for r in results:
        ws.append([r['Name'], r['Home Phone'], r['Mobile Phone'], r['Work Phone'], r['Email']])
        
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
