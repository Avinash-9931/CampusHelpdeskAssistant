"""
Automated Playwright script to capture visual screenshots of all 5 Streamlit application pages.
Saves high-resolution screenshots to docs/screenshots/:
- 01_home_page.png
- 02_chatbot_with_sources.png
- 03_knowledge_base.png
- 04_evaluation.png
- 05_about_project.png
"""

import time
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def run_capture():
    print(f"Starting Playwright screenshot capture...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use desktop high-dpi viewport for crisp editorial UI capture
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        print("Navigating to http://localhost:8501...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(3)

        # 1. Capture Home Page
        print("Capturing 01_home_page.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_home_page.png"), full_page=True)

        # 2. Navigate to AI Chatbot Page & Ask Question
        print("Navigating to AI Chatbot...")
        page.click("button:has-text('AI Chatbot')")
        time.sleep(2)

        # Click attendance quick question chip
        print("Triggering quick question chip...")
        chip = page.locator("button:has-text('Attendance Requirement')").first
        if chip.count() > 0:
            chip.click()
        else:
            page.fill("textarea", "What is the minimum attendance requirement?")
            page.keyboard.press("Enter")
        
        time.sleep(4)
        print("Capturing 02_chatbot_with_sources.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "02_chatbot_with_sources.png"), full_page=True)

        # 3. Navigate to Knowledge Base Page
        print("Navigating to Knowledge Base...")
        page.click("button:has-text('Knowledge Base')")
        time.sleep(2)
        print("Capturing 03_knowledge_base.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "03_knowledge_base.png"), full_page=True)

        # 4. Navigate to Test / Evaluation Page
        print("Navigating to Test / Evaluation...")
        page.click("button:has-text('Test / Evaluation')")
        time.sleep(2)
        print("Capturing 04_evaluation.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "04_evaluation.png"), full_page=True)

        # 5. Navigate to About Project Page
        print("Navigating to About Project...")
        page.click("button:has-text('About Project')")
        time.sleep(2)
        print("Capturing 05_about_project.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "05_about_project.png"), full_page=True)

        browser.close()
        print(f"All 5 screenshots captured successfully in {SCREENSHOTS_DIR}!")


if __name__ == "__main__":
    run_capture()
