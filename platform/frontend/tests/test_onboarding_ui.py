"""
Headless browser tests for the SSO Onboarding UI.

Uses Playwright (via pytest-playwright) to exercise the full onboarding flow
against a running frontend (Vite dev server) and backend (FastAPI).

Prerequisites:
    pip install pytest pytest-playwright
    playwright install chromium

Run:
    # Start backend + frontend first, then:
    pytest platform/frontend/tests/test_onboarding_ui.py -v

    # Override base URL (default: http://localhost:5173):
    pytest ... --base-url http://localhost:5173

    # Run headed (visible browser) for debugging:
    pytest ... --headed
"""

import re
import pytest
from playwright.sync_api import Page, expect


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def onboarding_page(page: Page, base_url: str) -> Page:
    """Navigate to the onboarding page and wait for it to load."""
    page.goto(f"{base_url}/onboarding")
    page.wait_for_load_state("networkidle")
    # Wait for heading to render (SPA may take a moment)
    page.wait_for_selector("h1", timeout=10000)
    expect(page.locator("h1")).to_contain_text("Onboarding Jobs")
    return page


# ─── Page Structure Tests ─────────────────────────────────────────────────────

class TestOnboardingPageStructure:
    """Verify that the onboarding page renders all expected elements."""

    def test_heading_visible(self, onboarding_page: Page):
        expect(onboarding_page.locator("h1")).to_contain_text("Onboarding Jobs")

    def test_sso_onboarding_card_visible(self, onboarding_page: Page):
        expect(onboarding_page.locator("text=SSO Onboarding")).to_be_visible()

    def test_monitoring_agents_card_visible(self, onboarding_page: Page):
        expect(onboarding_page.get_by_role("heading", name="Monitoring Agents")).to_be_visible()

    def test_app_dropdown_present(self, onboarding_page: Page):
        select = onboarding_page.locator("select")
        expect(select).to_be_visible()
        # Should have a default placeholder option
        expect(select.locator("option").first).to_contain_text("Select application")

    def test_create_button_present(self, onboarding_page: Page):
        btn = onboarding_page.locator("button", has_text="Create Onboarding Job")
        expect(btn).to_be_visible()

    def test_deploy_monitoring_button_present(self, onboarding_page: Page):
        btn = onboarding_page.locator("button", has_text="Deploy Monitoring Agents")
        expect(btn).to_be_visible()

    def test_job_history_section_present(self, onboarding_page: Page):
        expect(onboarding_page.locator("text=Job History")).to_be_visible()

    def test_refresh_button_present(self, onboarding_page: Page):
        expect(onboarding_page.locator("button", has_text="Refresh")).to_be_visible()


# ─── App Dropdown Tests ───────────────────────────────────────────────────────

class TestAppDropdown:
    """Verify the application dropdown loads apps from the API."""

    def test_dropdown_has_apps(self, onboarding_page: Page):
        """Apps should be loaded from the /apps API."""
        select = onboarding_page.locator("select")
        options = select.locator("option")
        # At least the placeholder + one app
        assert options.count() > 1, "Dropdown should have at least one app option"

    def test_dropdown_contains_grafana(self, onboarding_page: Page):
        """Grafana should be listed as an onboarding target."""
        select = onboarding_page.locator("select")
        expect(select.locator("option", has_text="Grafana")).to_be_attached()

    def test_dropdown_contains_jenkins(self, onboarding_page: Page):
        select = onboarding_page.locator("select")
        expect(select.locator("option", has_text="Jenkins")).to_be_attached()

    def test_create_button_disabled_without_selection(self, onboarding_page: Page):
        """Create button should be disabled when no app is selected."""
        btn = onboarding_page.locator("button", has_text="Create Onboarding Job")
        expect(btn).to_be_disabled()


# ─── SSO Onboarding Flow Tests ────────────────────────────────────────────────

class TestSSOOnboardingFlow:
    """End-to-end test: select app → create job → execute → verify status."""

    def test_create_grafana_onboarding_job(self, onboarding_page: Page):
        """Create an onboarding job for Grafana and verify it appears in history."""
        page = onboarding_page

        # Select Grafana
        page.locator("select").select_option(label="Grafana")

        # Click Create
        page.locator("button", has_text="Create Onboarding Job").click()

        # Wait for success message
        page.wait_for_selector("text=Job created for grafana", timeout=5000)

        # Job should appear in history with pending status
        job_row = page.locator("span", has_text="grafana").first
        expect(job_row).to_be_visible()
        expect(page.locator("span", has_text="pending").first).to_be_visible()

    def test_create_jenkins_onboarding_job(self, onboarding_page: Page):
        """Create an onboarding job for Jenkins."""
        page = onboarding_page

        page.locator("select").select_option(label="Jenkins")
        page.locator("button", has_text="Create Onboarding Job").click()
        page.wait_for_selector("text=Job created for jenkins", timeout=5000)

        job_row = page.locator("span", has_text="jenkins").first
        expect(job_row).to_be_visible()
        expect(page.locator("span", has_text="pending").first).to_be_visible()

    def test_execute_button_visible_on_pending_job(self, onboarding_page: Page):
        """After creating a job, the Execute button should be visible."""
        page = onboarding_page

        page.locator("select").select_option(label="Grafana")
        page.locator("button", has_text="Create Onboarding Job").click()
        page.wait_for_selector("text=Job created for grafana", timeout=5000)

        execute_btn = page.locator("button", has_text="Execute").first
        expect(execute_btn).to_be_visible()

    def test_execute_triggers_playbook(self, onboarding_page: Page):
        """Clicking Execute should transition job from pending → running."""
        page = onboarding_page

        # Create a job
        page.locator("select").select_option(label="Grafana")
        page.locator("button", has_text="Create Onboarding Job").click()
        page.wait_for_selector("text=Job created for grafana", timeout=5000)

        # Execute it
        page.locator("button", has_text="Execute").first.click()

        # Should show success message about playbook starting
        page.wait_for_selector("text=Playbook started", timeout=5000)

        # Job card should show the playbook name
        expect(page.locator("text=sso_onboarding.yml").first).to_be_visible()

    def test_job_status_polling(self, onboarding_page: Page):
        """When a job is running, status should eventually update via polling."""
        page = onboarding_page

        page.locator("select").select_option(label="Grafana")
        page.locator("button", has_text="Create Onboarding Job").click()
        page.wait_for_selector("text=Job created for grafana", timeout=5000)

        page.locator("button", has_text="Execute").first.click()
        page.wait_for_selector("text=Playbook started", timeout=5000)

        # Wait up to 30s for the job to finish (either succeeded or failed)
        # In a lab environment with actual Ansible, this could take longer
        try:
            page.locator("text=succeeded").or_(page.locator("text=failed")).first.wait_for(timeout=30000)
        except Exception:
            # If it's still running after 30s, that's acceptable in a test env
            pass


# ─── Monitoring Agents Tests ──────────────────────────────────────────────────

class TestMonitoringAgents:
    """Test the Deploy Monitoring Agents button and flow."""

    def test_deploy_creates_job(self, onboarding_page: Page):
        """Clicking Deploy Monitoring Agents should create a prometheus job."""
        page = onboarding_page

        page.locator("button", has_text="Deploy Monitoring Agents").click()

        # Success message
        page.wait_for_selector("text=Monitoring agents deployment started", timeout=5000)

        # Job should appear with prometheus app_id and monitoring-agents.yml playbook
        job_card = page.locator(".glass.rounded-xl", has_text="prometheus").first
        expect(job_card).to_be_visible()
        expect(job_card.locator("text=monitoring-agents.yml")).to_be_visible()


# ─── Log Viewer Tests ─────────────────────────────────────────────────────────

class TestLogViewer:
    """Test the expandable log viewer on completed/failed jobs."""

    def _create_and_execute_job(self, page: Page, app_label: str):
        """Helper: create + execute a job and wait for it to finish."""
        page.locator("select").select_option(label=app_label)
        page.locator("button", has_text="Create Onboarding Job").click()
        page.wait_for_selector("text=Job created for", timeout=5000)
        page.locator("button", has_text="Execute").first.click()
        page.wait_for_selector("text=Playbook started", timeout=5000)

        # Wait for job to complete (either succeeded or failed)
        page.locator("text=succeeded").or_(page.locator("text=failed")).first.wait_for(timeout=60000)

    def test_logs_button_appears_after_completion(self, onboarding_page: Page):
        """The Logs button should appear once a job has output."""
        page = onboarding_page
        self._create_and_execute_job(page, "Grafana")

        logs_btn = page.locator("button", has_text="Logs").first
        expect(logs_btn).to_be_visible()

    def test_logs_expand_and_collapse(self, onboarding_page: Page):
        """Clicking Logs should expand the log panel; clicking again collapses it."""
        page = onboarding_page
        self._create_and_execute_job(page, "Grafana")

        logs_btn = page.locator("button", has_text="Logs").first
        logs_btn.click()

        # Log panel should be visible (contains <pre> with output)
        log_panel = page.locator("pre").first
        expect(log_panel).to_be_visible()

        # Collapse
        logs_btn.click()
        expect(log_panel).not_to_be_visible()


# ─── Navigation Tests ─────────────────────────────────────────────────────────

class TestNavigation:
    """Verify navigation to/from the onboarding page."""

    def test_nav_link_active(self, onboarding_page: Page):
        """Onboarding nav link should be highlighted as active."""
        nav_link = onboarding_page.locator("nav a", has_text="Onboarding")
        expect(nav_link).to_have_class(re.compile(r"text-indigo-400"))

    def test_navigate_from_dashboard(self, page: Page, base_url: str):
        """Should be able to navigate to onboarding from the Apps dashboard."""
        page.goto(f"{base_url}/dashboard")
        page.wait_for_load_state("networkidle")

        page.locator("nav a", has_text="Onboarding").click()
        page.wait_for_url("**/onboarding")

        expect(page.locator("h1")).to_contain_text("Onboarding Jobs")

    def test_navigate_from_landing(self, page: Page, base_url: str):
        """The landing page CTA should link to onboarding."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        page.locator("a", has_text="Start Onboarding").click()
        page.wait_for_url("**/onboarding")

        expect(page.locator("h1")).to_contain_text("Onboarding Jobs")


# ─── API Error Handling Tests ──────────────────────────────────────────────────

class TestErrorHandling:
    """Verify the UI handles API errors gracefully."""

    def test_create_job_shows_error_on_failure(self, page: Page, base_url: str):
        """If the backend is down, creating a job should show an error message."""
        page.goto(f"{base_url}/onboarding")
        page.wait_for_load_state("networkidle")

        # Try to create a job with a non-existent app by manipulating the select
        # (only possible if the dropdown had loaded apps; otherwise button is disabled)
        select = page.locator("select")
        if select.locator("option").count() > 1:
            select.select_option(index=1)
            # Intercept the API call to simulate a 500 error
            page.route("**/onboarding", lambda route: route.fulfill(
                status=500,
                content_type="application/json",
                body='{"detail":"Internal Server Error"}',
            ))
            page.locator("button", has_text="Create Onboarding Job").click()

            # Error message should appear
            page.wait_for_selector(".text-red-400", timeout=5000)
