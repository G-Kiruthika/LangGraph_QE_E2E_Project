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

def test_ts_03_verify_dashboard_page_displays_required(page):
    # Precondition: Login to the application
    login_to_orangehrm(page)
    
    # Verify Dashboard heading
    dashboard_heading = page.locator('h6.oxd-topbar-header-breadcrumb-module')
    expect(dashboard_heading).to_be_visible()
    expect(dashboard_heading).to_contain_text("Dashboard")
    
    # Define widget locators using correct filter syntax
    # Note: In Python Playwright, the filter argument is 'has', not a dictionary key
    time_at_work = page.locator('.orangehrm-dashboard-widget').filter(has=page.get_by_text('Time at Work', exact=True)).first
    my_actions = page.locator('.orangehrm-dashboard-widget').filter(has=page.get_by_text('My Actions', exact=True)).first
    quick_launch = page.locator('.orangehrm-dashboard-widget').filter(has=page.get_by_text('Quick Launch', exact=True)).first
    
    # Verify widgets are loaded and visible
    expect(time_at_work).to_be_visible()
    expect(my_actions).to_be_visible()
    expect(quick_launch).to_be_visible()

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
            test_ts_03_verify_dashboard_page_displays_required(page)
            print("[PASSED] Test completed successfully.")
        finally:
            context.close()
            browser.close()