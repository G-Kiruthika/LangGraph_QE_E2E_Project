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

def test_ts_07_verify_login_failure_with_empty_credentials(page):
    """
    TS-07: Verify login failure with empty credentials
    """
    # Clear cookies to ensure we are on a fresh login state
    page.context.clear_cookies()
    
    # Navigate to login page
    login_url = "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login"
    navigate_to(page, login_url)
    
    # Ensure we are on the login page
    expect(page.locator('input[name="username"]')).to_be_visible()
    
    # Leave fields empty and click login
    page.locator('button[type="submit"]').click()
    
    # Verify validation messages appear for both fields
    # The application displays "Required" under each input field
    error_messages = page.locator('.oxd-input-field-error-message')
    
    # Expect at least two "Required" messages (one for username, one for password)
    # We use count to ensure both fields triggered the validation
    expect(error_messages).to_have_count(2)
    expect(error_messages.first).to_contain_text("Required")
    expect(error_messages.nth(1)).to_contain_text("Required")
    
    # Verify user remains on the login page
    # Using regex to match the end of the URL to avoid issues with query parameters or trailing slashes
    expect(page).to_have_url(re.compile(r".*/auth/login$"))

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
            test_ts_07_verify_login_failure_with_empty_credentials(page)
            print("[PASSED] Test TS-07 completed successfully.")
        except Exception as e:
            print(f"[FAILED] Test TS-07 failed with error: {e}")
            raise
        finally:
            context.close()
            browser.close()