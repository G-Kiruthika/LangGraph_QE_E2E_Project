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

def test_ts_06_verify_login_failure_with_invalid_creden(page):
    # Precondition: Clear cookies to ensure clean state
    page.context.clear_cookies()
    
    # Navigate to login page
    navigate_to(page, "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
    
    # Verify we are on the login page
    expect(page.get_by_role('heading', name='Login')).to_be_visible()
    
    # Step 1: Enter invalid username and password
    page.locator('input[name="username"]').fill("InvalidUser")
    page.locator('input[name="password"]').fill("WrongPassword")
    
    # Step 2: Click Login button
    page.locator('button[type="submit"]').click()
    
    # Expected Result: System displays an error message
    # Verify error message appears
    expect(page.locator('p.oxd-alert-content-text')).to_contain_text("Invalid credentials")
    
    # Verify URL remains on the login page (using regex for URL validation)
    expect(page).to_have_url(re.compile(r".*/auth/login"))
    
    # Verify user is still on the login page by checking for login elements
    expect(page.locator('input[name="username"]')).to_be_visible()

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
            test_ts_06_verify_login_failure_with_invalid_creden(page)
            print("[PASSED] Test completed successfully.")
        except Exception as e:
            print(f"[FAILED] Test failed with error: {e}")
            raise
        finally:
            context.close()
            browser.close()