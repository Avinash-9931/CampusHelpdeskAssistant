import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path("/Users/avinashsingh/.gemini/antigravity/brain/c90471c5-1fbc-4a18-97fc-55f100fc8782/screenshots")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        page = context.new_page()

        # 1. Clear session and open login
        print("Navigating to login...")
        page.goto("http://localhost:8501/?logout=true", wait_until="networkidle")
        time.sleep(3)

        # Capture Login Page with Faculty Fast Access
        print("Capturing 00_calley_login.png...")
        page.screenshot(path=str(ARTIFACT_DIR / "00_calley_login.png"), full_page=True)

        # 2. Click 1-Click Faculty Login
        print("Clicking 1-Click Faculty Examiner Login button...")
        fac_btn = page.locator("button:has-text('1-Click Faculty Examiner Login')")
        if fac_btn.count() > 0:
            fac_btn.first.click()
            time.sleep(3)
        else:
            print("1-Click button not found, clicking Student / Staff ID tab...")
            page.locator("button[data-testid='stTab']:has-text('Student / Staff ID')").click()
            time.sleep(1)
            page.fill("input[aria-label='User ID / Student Roll Number']", "faculty")
            page.fill("input[aria-label='Password']", "faculty123")
            page.click("button:has-text('Continue with Password')")
            time.sleep(3)

        # Capture AI Chatbot page
        print("Capturing 01_calley_chatbot_empty.png...")
        page.screenshot(path=str(ARTIFACT_DIR / "01_calley_chatbot_empty.png"), full_page=True)

        # 3. Click Attendance Question Chip
        print("Clicking Attendance Requirement quick chip...")
        chip = page.locator("button:has-text('Attendance Requirement')")
        if chip.count() > 0:
            chip.first.click()
        else:
            chat_input = page.locator("textarea[placeholder='Type your message here...']")
            if chat_input.count() > 0:
                chat_input.fill("What is the minimum attendance requirement?")
                page.keyboard.press("Enter")

        print("Waiting for bot response bubble...")
        try:
            page.wait_for_selector(".calley-msg-bubble-bot", timeout=25000)
            time.sleep(3)
        except Exception as e:
            print(f"Wait timed out: {e}")
            time.sleep(5)

        # Capture Chatbot with conversation
        print("Capturing 02_calley_chatbot_conversation.png...")
        page.screenshot(path=str(ARTIFACT_DIR / "02_calley_chatbot_conversation.png"), full_page=True)

        # 4. Navigate to Home page
        print("Navigating to Home page...")
        home_btn = page.locator("button:has-text('Home')")
        if home_btn.count() > 0:
            home_btn.first.click()
            time.sleep(3)
            print("Capturing 03_calley_home.png...")
            page.screenshot(path=str(ARTIFACT_DIR / "03_calley_home.png"), full_page=True)

        browser.close()
        print("Screenshots captured successfully!")


if __name__ == "__main__":
    main()
