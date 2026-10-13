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

def test_ts_02_verify_successful_login_with_valid_crede(page):
    # Precondition: User is on the login page
    page.context.clear_cookies()
    navigate_to(page, "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
    
    # Step 1: Enter valid username and password
    username_input = page.locator('input[name="username"]')
    password_input = page.locator('input[name="password"]')
    login_button = page.locator('button[type="submit"]')
    
    username_input.fill("Admin")
    password_input.fill("admin123")
    
    # Step 2: Click Login button
    login_button.click()
    
    # Postcondition: User is authenticated and redirected to the dashboard
    page.wait_for_url("**/dashboard/index", timeout=30000)
    
    # Verify Dashboard access
    expect(page.locator('h6.oxd-topbar-header-breadcrumb-module')).to_contain_text("Dashboard")
    expect(page.locator('.orangehrm-dashboard-widget').first).to_be_visible()

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
            test_ts_02_verify_successful_login_with_valid_crede(page)
            print("[PASSED] Test completed successfully.")
        except Exception as e:
            print(f"[FAILED] Test failed with error: {e}")
            raise
        finally:
            context.close()
            browser.close()