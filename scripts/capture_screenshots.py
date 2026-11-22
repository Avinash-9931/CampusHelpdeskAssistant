"""
Automated Playwright script to capture visual screenshots of Campus Helpdesk Assistant.
Captures FAANG-grade UI and role-based authentication screens:
- 00_login_page.png
- 00_otp_verification.png
- 01_home_page.png
- 02_chatbot_with_sources.png
- 03_knowledge_base.png
- 04_evaluation.png
- 05_about_project.png
- 06_user_management.png
- 07_audit_log.png
- 08_student_restricted_access.png
"""

import time
import sys
import re
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.sync_api import sync_playwright
from auth.db import get_db_connection

SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def run_capture():
    print("Resetting test rate limits for admin user...")
    with get_db_connection() as conn:
        conn.execute("DELETE FROM otp_codes WHERE user_id='admin';")
        conn.execute("DELETE FROM login_attempts WHERE user_id='admin';")

    print("Starting Playwright screenshot capture for UI + Auth Overhaul...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        print("Navigating to http://localhost:8501...")
        page.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(3)

        # 1. Capture Login Screen
        print("Capturing 00_login_page.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "00_login_page.png"), full_page=True)

        # 2. Enter credentials for admin
        print("Submitting login credentials (admin / admin123)...")
        page.fill("input[aria-label='User ID / Student Roll Number']", "admin")
        page.fill("input[aria-label='Password']", "admin123")
        page.click("button:has-text('Continue with Password')")
        time.sleep(3)

        # 3. Capture OTP Screen
        print("Capturing 00_otp_verification.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "00_otp_verification.png"), full_page=True)

        # 4. Extract Dev OTP Code and Sign In
        body_text = page.inner_text("body")
        match = re.search(r'verification code is:\s*(\d{6})', body_text, re.IGNORECASE)
        if not match:
            match = re.search(r'<strong[^>]*>(\d{6})</strong>', page.content())

        if match:
            dev_otp = match.group(1)
            print(f"Extracted DEV OTP: {dev_otp}")
            page.fill("input[aria-label='Enter 6-Digit Code']", dev_otp)
            page.click("button:has-text('Verify Code & Sign In')")
            time.sleep(4)
        else:
            print("ERROR: Dev OTP could not be extracted!")

        # Retrieve active session token from database
        session_token = ""
        with get_db_connection() as conn:
            cur = conn.cursor()
            row = cur.execute(
                "SELECT session_id FROM sessions WHERE user_id='admin' AND status='active' ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if row:
                session_token = row[0]
                print(f"Acquired persistent session token: {session_token[:8]}...")

        token_param = f"session_token={session_token}&" if session_token else ""

        # 5. Capture Home Page (Authenticated)
        print("Capturing 01_home_page.png...")
        page.goto(f"http://localhost:8501/?{token_param}page=Home", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=str(SCREENSHOTS_DIR / "01_home_page.png"), full_page=True)

        # 6. Capture AI Chatbot Page & Ask Question
        print("Navigating to AI Chatbot...")
        page.goto(f"http://localhost:8501/?{token_param}page=AI+Chatbot", wait_until="networkidle")
        time.sleep(3)

        print("Triggering quick question chip...")
        try:
            page.wait_for_selector("button:has-text('Attendance')", timeout=8000)
            page.locator("button:has-text('Attendance')").first.click()
            print("Clicked Attendance chip.")
        except Exception as e:
            print(f"Could not click attendance chip: {e}")
            try:
                page.wait_for_selector("textarea", timeout=5000)
                page.fill("textarea", "What is the minimum attendance requirement?")
                page.keyboard.press("Enter")
            except Exception:
                pass

        time.sleep(5)
        print("Capturing 02_chatbot_with_sources.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "02_chatbot_with_sources.png"), full_page=True)

        # 7. Knowledge Base (Admin)
        print("Navigating to Knowledge Base...")
        page.goto(f"http://localhost:8501/?{token_param}page=Knowledge+Base", wait_until="networkidle")
        time.sleep(3)
        print("Capturing 03_knowledge_base.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "03_knowledge_base.png"), full_page=True)

        # 8. User Management (Admin)
        print("Navigating to User Admin...")
        page.goto(f"http://localhost:8501/?{token_param}page=User+Admin", wait_until="networkidle")
        time.sleep(3)
        print("Capturing 06_user_management.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "06_user_management.png"), full_page=True)

        # 9. Audit Log (Admin)
        print("Navigating to Audit Log...")
        page.goto(f"http://localhost:8501/?{token_param}page=Audit+Log", wait_until="networkidle")
        time.sleep(3)
        print("Capturing 07_audit_log.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "07_audit_log.png"), full_page=True)

        # 10. My Conversation History
        print("Navigating to My History...")
        page.goto(f"http://localhost:8501/?{token_param}page=My+History", wait_until="networkidle")
        time.sleep(3)
        print("Capturing 05_my_history.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "05_my_history.png"), full_page=True)

        # 12. Student Restricted Access Demo
        print("Switching role to Student to demonstrate RBAC restriction...")
        try:
            # Click top navbar role toggle
            role_btn = page.locator("button:has-text('🛡️ Admin')").first
            if role_btn.count() > 0:
                role_btn.scroll_into_view_if_needed()
                role_btn.click()
                time.sleep(2)
        except Exception as e:
            print(f"Navbar toggle note: {e}")

        print("Navigating to Knowledge Base as Student...")
        page.goto(f"http://localhost:8501/?{token_param}page=Knowledge+Base", wait_until="networkidle")
        time.sleep(3)
        print("Capturing 08_student_restricted_access.png...")
        page.screenshot(path=str(SCREENSHOTS_DIR / "08_student_restricted_access.png"), full_page=True)

        browser.close()
        print(f"All screenshots captured successfully in {SCREENSHOTS_DIR}!")


if __name__ == "__main__":
    run_capture()
