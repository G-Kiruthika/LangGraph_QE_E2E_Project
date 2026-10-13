import os
import time
from playwright.sync_api import sync_playwright, expect

def navigate_to(page, url, retries=3):
    for i in range(retries):
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=45000)
            return
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2)

def login_to_orangehrm(page):
    page.context.clear_cookies()
    navigate_to(page, "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
    page.locator('input[name="username"]').fill("Admin")
    page.locator('input[name="password"]').fill("admin123")
    page.locator('button[type="submit"]').click()
    page.wait_for_url("**/dashboard/index", timeout=30000)

def test_ts_04_verify_dashboard_accessibility_and_error(page):
    # Capture console errors
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exception: console_errors.append(str(exception)))

    # Perform login
    login_to_orangehrm(page)

    # Verify Dashboard accessibility
    expect(page.locator('h6.oxd-topbar-header-breadcrumb-module')).to_contain_text("Dashboard")
    expect(page.locator('.orangehrm-dashboard-widget').first).to_be_visible()

    # Check for console errors
    assert len(console_errors) == 0, f"Console errors detected: {console_errors}"

if __name__ == "__main__":
    with sync_playwright() as p:
        videos_dir = os.path.join(os.getcwd(), "outputs", "reports", "videos")
        os.makedirs(videos_dir, exist_ok=True)
        browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors', '--no-sandbox'])
        context = browser.new_context(
            ignore_https_errors=True,
            record_video_dir=videos_dir,
            record_video_size={"width": 1280, "height": 720}
        )
        page = context.new_page()
        page.set_default_timeout(20000)
        try:
            test_ts_04_verify_dashboard_accessibility_and_error(page)
            print("[PASSED] Test completed successfully: Dashboard loaded without errors.")
        except Exception as e:
            print(f"[FAILED] Test failed: {e}")
            raise
        finally:
            context.close()
            browser.close()