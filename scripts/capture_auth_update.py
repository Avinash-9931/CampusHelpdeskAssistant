"""
Capture screenshots of all login tabs including Forgot Password.
"""

import time
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright
from auth.db import get_db_connection

SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACTS_SCREENSHOTS = Path("/Users/avinashsingh/.gemini/antigravity/brain/c90471c5-1fbc-4a18-97fc-55f100fc8782/screenshots")
ARTIFACTS_SCREENSHOTS.mkdir(parents=True, exist_ok=True)


def run():
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET status='revoked';")
        conn.execute("DELETE FROM otp_codes;")
        conn.execute("DELETE FROM login_attempts;")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 920}, device_scale_factor=2)
        page = context.new_page()

        print("1. Opening Login page via logout reset...")
        page.goto("http://localhost:8501/?logout=1", wait_until="networkidle")
        time.sleep(3)

        st_tabs = page.locator("div[data-testid='stTab']")
        print(f"Detected {st_tabs.count()} tabs: {[t.inner_text() for t in st_tabs.all()]}")

        # Tab 0: Google / Email OTP
        print("Capturing 00_login_page_google.png...")
        st_tabs.nth(0).click()
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_page_google.png"), full_page=True)

        # Tab 1: Student / Staff ID
        print("Capturing 00_login_page_id.png...")
        st_tabs.nth(1).click()
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_page_id.png"), full_page=True)

        # Tab 2: Create Account
        print("Capturing 00_login_page_create.png...")
        st_tabs.nth(2).click()
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_page_create.png"), full_page=True)

        # Tab 3: Forgot Password
        print("Capturing 00_login_page_forgot.png...")
        st_tabs.nth(3).click()
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_page_forgot.png"), full_page=True)

        browser.close()

    # Sync screenshots to artifact dir
    for f in SCREENSHOTS_DIR.glob("*.png"):
        shutil.copy2(f, ARTIFACTS_SCREENSHOTS / f.name)
    print("Copied all screenshots to artifacts directory.")


if __name__ == "__main__":
    run()
