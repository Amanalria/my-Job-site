import asyncio
import os
import glob
from playwright.async_api import async_playwright

STATIC_PAGES = [
    'about-us.html', 'about.html', 'contact.html', 'disclaimer.html',
    'privacy-policy.html', 'terms-and-conditions.html', 'terms.html',
    'index.html', 'admission.html', 'admit-card.html', 'answer-key.html',
    'latest-jobs.html', 'result.html', 'syllabus.html'
]

async def test_post(page, file_path):
    url = f"file://{file_path}"
    await page.goto(url)
    
    filename = os.path.basename(file_path)
    errors = []

    try:
        # Check Important Dates bg color
        dates_hdr = await page.locator("text='Important Dates'").first.evaluate("el => window.getComputedStyle(el).backgroundColor")
        # Could be on the parent td/th. Let's just check if we have any element with that background color
        has_bg_5b032f = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('*')).some(el => {
                let bg = window.getComputedStyle(el).backgroundColor;
                return bg === 'rgb(91, 3, 47)' || bg === '#5b032f' || bg === 'rgba(91, 3, 47, 1)';
            });
        }''')
        if not has_bg_5b032f:
            errors.append("Missing #5b032f background for Important Dates/Application Fee.")

        # Check Age Limits bg
        has_bg_046132 = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('*')).some(el => {
                let bg = window.getComputedStyle(el).backgroundColor;
                return bg === 'rgb(4, 97, 50)' || bg === '#046132' || bg === 'rgba(4, 97, 50, 1)';
            });
        }''')
        if not has_bg_046132:
            errors.append("Missing #046132 background for Age Limits.")
            
        # Check Total Vacancy bg
        has_bg_f53c00 = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('*')).some(el => {
                let bg = window.getComputedStyle(el).backgroundColor;
                return bg === 'rgb(245, 60, 0)' || bg === '#f53c00' || bg === 'rgba(245, 60, 0, 1)';
            });
        }''')
        if not has_bg_f53c00:
            errors.append("Missing #f53c00 background for Total Vacancy.")
            
        # Check Vacancy Matrix bg
        has_bg_000080 = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('*')).some(el => {
                let bg = window.getComputedStyle(el).backgroundColor;
                return bg === 'rgb(0, 0, 128)' || bg === '#000080' || bg === 'rgba(0, 0, 128, 1)';
            });
        }''')
        if not has_bg_000080:
            errors.append("Missing #000080 background for Vacancy Matrix.")

        # Check SOME USEFUL IMPORTANT LINKS
        links_header_exists = await page.locator("text='SOME USEFUL IMPORTANT LINKS'").count() > 0
        if not links_header_exists:
            errors.append("Missing 'SOME USEFUL IMPORTANT LINKS' header.")
            
        # Check FAQs
        q1_exists = await page.locator("text='Q1.'").count() > 0
        q5_exists = await page.locator("text='Q5.'").count() > 0
        if not (q1_exists and q5_exists):
            errors.append("Missing FAQs (Q1 to Q5).")

        if errors:
            print(f"[FAIL] {filename}:")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"[PASS] {filename} is according to reference HTML.")

    except Exception as e:
        print(f"[ERROR] {filename}: {str(e)}")


async def main():
    pages_dir = "/root/sarkari-result-portal/pages"
    files = glob.glob(os.path.join(pages_dir, "*.html"))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        for file in files:
            filename = os.path.basename(file)
            if filename in STATIC_PAGES:
                continue
            await test_post(page, file)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
