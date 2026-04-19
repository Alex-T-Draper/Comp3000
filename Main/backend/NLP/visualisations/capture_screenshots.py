"""Capture full-page screenshots of each ToS condition for use as
visualisation backgrounds.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    1. Start the Angular frontend:  cd frontend && ng serve
    2. Start the NLP backend:       cd backend/NLP && python app.py
    3. Run:  python capture_screenshots.py [base_url]
       base_url defaults to http://localhost:4200

Screenshots are saved to output/screenshots/ as screenshot_{condition}.png,
matching the naming convention expected by the visualisation generators.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gaze_utils import SCREENSHOTS_DIR, SCREEN_W, SCREEN_H

# Route → condition_group label (must match session.condition_group in DB)
CONDITIONS = [
    ("tos-plain", "control"),
    ("tos-scroll-required", "scroll-gate"),
    ("tos-formatted", "formatted"),
    ("tos-ai-summary", "ai-summary"),
    ("tos-ai-enhanced", "ai-enhanced"),
    ("tos-ai-hover", "ai-hover"),
]


async def capture_all(base_url):
    from playwright.async_api import async_playwright

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": SCREEN_W, "height": SCREEN_H}
        )

        # Load the Angular SPA once so the router is available.
        # SSR prerender can fail for some routes, but client-side
        # routing always works once the app is bootstrapped.
        print("Loading Angular app...")
        await page.goto(base_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        for route, condition in CONDITIONS:
            print(f"Capturing {condition} (/{route})...")

            # Navigate by updating the URL bar and dispatching a popstate
            # event so Angular's router picks it up — avoids SSR prerender
            # failures (e.g. "Cannot GET /tos-scroll-required").
            await page.evaluate(f"""() => {{
                window.history.pushState({{}}, '', '/{route}');
                window.dispatchEvent(new PopStateEvent('popstate'));
            }}""")
            await page.wait_for_timeout(1500)

            # Wait for ToS text to load from the backend API.
            # The .tos-text div is always in the DOM but empty until the API
            # responds, so poll until it has real text content.
            try:
                await page.wait_for_function(
                    "() => (document.querySelector('.tos-text')?.textContent?.trim().length ?? 0) > 50",
                    timeout=15000,
                )
            except Exception as e:
                print(f"  Warning: ToS text did not load ({e.__class__.__name__}). "
                      "Is the backend (python app.py) running?")
            await page.wait_for_timeout(1000)

            # For AI conditions, click the generate button if present
            generate_btn = page.locator("button.btn-generate")
            if await generate_btn.count() > 0:
                await generate_btn.click()
                print("  Waiting for NLP analysis...")
                # Wait for the summary panel to appear
                await page.wait_for_selector(".summary-panel",
                                             timeout=60000)
                await page.wait_for_timeout(2000)

            # Clean up layout for screenshot:
            # 1. Hide the fixed action bar (Continue button) so it doesn't
            #    float in the middle of a full-page capture.
            # 2. Remove max-height/overflow on .summary-column so the full
            #    AI analysis panel is visible in the screenshot.
            await page.evaluate("""() => {
                const actions = document.querySelector('.actions');
                if (actions) actions.style.display = 'none';
                const sc = document.querySelector('.summary-column');
                if (sc) { sc.style.maxHeight = 'none'; sc.style.overflow = 'visible'; }
            }""")
            await page.wait_for_timeout(300)

            output_path = SCREENSHOTS_DIR / f"screenshot_{condition}.png"
            await page.screenshot(path=str(output_path), full_page=True)
            print(f"  Saved: {output_path}")

        await browser.close()

    print(f"\nAll screenshots saved to: {SCREENSHOTS_DIR.resolve()}")
    print("\nRe-run your visualisation generators to overlay gaze data on these screenshots.")


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4200"
    print(f"Base URL: {base_url}")
    print(f"Viewport: {SCREEN_W}x{SCREEN_H}")
    print(f"Output:   {SCREENSHOTS_DIR.resolve()}\n")
    asyncio.run(capture_all(base_url))


if __name__ == "__main__":
    main()
