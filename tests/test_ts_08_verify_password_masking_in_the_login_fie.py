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

def test_ts_08_verify_password_masking_in_the_login_fie(page):
    """
    TS-08: Verify password masking in the login field
    """
    # Ensure no existing session interferes
    page.context.clear_cookies()
    
    # Navigate to login page
    navigate_to(page, "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login")
    
    # Locate password field
    password_field = page.locator('input[name="password"]')
    
    # Verify password field is visible
    expect(password_field).to_be_visible()
    
    # Verify initial type is 'password' (masked)
    expect(password_field).to_have_attribute("type", "password")
    
    # Enter text into the password field
    password_field.fill("testpassword123")
    
    # Verify the type attribute remains 'password' (ensuring masking is active)
    expect(password_field).to_have_attribute("type", "password")
    
    # Verify the value is correctly set despite being masked
    expect(password_field).to_have_value("testpassword123")

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
            test_ts_08_verify_password_masking_in_the_login_fie(page)
            print("[PASSED] Test completed successfully: Password masking verified.")
        except Exception as e:
            print(f"[FAILED] Test failed with error: {e}")
            raise
        finally:
            context.close()
            browser.close()