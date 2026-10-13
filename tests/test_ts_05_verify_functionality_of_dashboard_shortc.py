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

def test_ts_05_verify_functionality_of_dashboard_shortc(page):
    # Precondition: Login to the application
    login_to_orangehrm(page)
    
    # Verify we are on the dashboard
    expect(page.locator('h6.oxd-topbar-header-breadcrumb-module')).to_contain_text("Dashboard")
    
    # Locate the Quick Launch widget using the filter method correctly
    quick_launch_widget = page.locator('.orangehrm-dashboard-widget').filter(
        has=page.get_by_text('Quick Launch', exact=True)
    ).first
    expect(quick_launch_widget).to_be_visible()
    
    # Action: Click on the 'Assign Leave' shortcut
    assign_leave_btn = page.locator('button[title="Assign Leave"]')
    assign_leave_btn.click()
    
    # Expected Result: User is redirected to the Assign Leave page
    # The breadcrumb changes to 'Leave' when navigating to the Assign Leave module
    page.wait_for_url("**/leave/assignLeave", timeout=20000)
    
    # Verify the page heading to confirm navigation
    # Based on the error traceback, the breadcrumb text is "Leave"
    heading = page.locator('h6.oxd-topbar-header-breadcrumb-module')
    expect(heading).to_contain_text("Leave")

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
            test_ts_05_verify_functionality_of_dashboard_shortc(page)
            print("[PASSED] Test completed successfully.")
        finally:
            context.close()
            browser.close()