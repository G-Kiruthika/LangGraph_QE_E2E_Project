import os
import time
import re
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

def test_ts_01_verify_login_page_elements_are_displayed(page):
    """
    TS-01: Verify login page elements are displayed correctly.
    """
    # Clear cookies to ensure we are on the fresh login page
    page.context.clear_cookies()
    
    # Navigate to the login URL
    navigate_to(page, "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
    
    # Verify URL using a regex pattern as required by Playwright assertions
    expect(page).to_have_url(re.compile(r".*/auth/login"))
    
    # Verify UI elements are visible
    username_field = page.locator('input[name="username"]')
    password_field = page.locator('input[name="password"]')
    login_button = page.locator('button[type="submit"]')
    
    expect(username_field).to_be_visible()
    expect(password_field).to_be_visible()
    expect(login_button).to_be_visible()
    
    # Verify Login heading
    expect(page.get_by_role('heading', name='Login')).to_be_visible()

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
            test_ts_01_verify_login_page_elements_are_displayed(page)
            print("[PASSED] Test completed successfully: Login page elements are displayed.")
        except Exception as e:
            print(f"[FAILED] Test failed with error: {e}")
            raise
        finally:
            context.close()
            browser.close()