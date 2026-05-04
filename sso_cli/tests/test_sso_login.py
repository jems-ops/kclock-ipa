from playwright.sync_api import sync_playwright

JENKINS_URL = "http://jenkins.local:8080/jenkins"
USERNAME = "testuser"
PASSWORD = "Password123!"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set True for CI
        page = browser.new_page()

        print("[INFO] Opening Jenkins...")
        page.goto(JENKINS_URL)

        # Click SSO login (adjust if label differs)
        print("[INFO] Clicking SSO login...")
        page.click("text=Login")

        # Wait for redirect to Keycloak
        page.wait_for_url("**keycloak**")

        print("[INFO] On Keycloak login page")

        # Fill credentials
        page.fill('input[name="username"]', USERNAME)
        page.fill('input[name="password"]', PASSWORD)

        # Submit login
        page.click('input[type="submit"]')

        # Wait for redirect back to Jenkins
        page.wait_for_url("**jenkins**")

        print("[INFO] Redirected back to Jenkins")

        # Validate login success
        if page.locator("text=Dashboard").is_visible():
            print("[SUCCESS] SSO Login Successful ✅")
        else:
            print("[ERROR] Login may have failed ❌")

        browser.close()


if __name__ == "__main__":
    run()
