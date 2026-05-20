"""
Playwright test configuration.

Provides shared fixtures for the headless browser tests.
--base-url is provided by pytest-base-url (installed with pytest-playwright).
"""

import pytest


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Merge custom context args with pytest-playwright defaults."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {"width": 1280, "height": 800},
    }
