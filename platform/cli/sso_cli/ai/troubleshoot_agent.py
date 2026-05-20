"""
Troubleshoot Agent — answers "Why is <app> SAML failing?" using local Ollama.

Collects context from:
  - sso-cli.log (last Ansible run output)
  - Keycloak admin events API
  - Known SAML config for the app (base URL, client ID)

Then sends structured context to Ollama and returns a diagnosis.
"""

import os
import json
import requests

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:270m")

KEYCLOAK_BASE   = os.getenv("KEYCLOAK_BASE_URL",       "https://keycloak.local")
KEYCLOAK_REALM  = os.getenv("KEYCLOAK_REALM",          "master")
KEYCLOAK_USER   = os.getenv("KEYCLOAK_ADMIN_USER",     "admin")
KEYCLOAK_PASS   = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "sso-cli.log")

APP_CLIENT_IDS = {
    "jenkins":     "jenkins",
    "sonar":       "sonarqube",
    "jira":        "https://jira.local",
    "confluence":  "https://confluence.local",
    "bitbucket":   "https://bitbucket.local",
    "nessus":      "https://tenable.sc",
    "artifactory": "https://artifactory.local",
    "grafana":     "grafana",
    "prometheus":  "prometheus",
}

# ── Context collectors ────────────────────────────────────────────────────────

def _tail_log(n=60):
    """Return last n lines of sso-cli.log."""
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
        return "".join(lines[-n:]).strip() or "(log empty)"
    except FileNotFoundError:
        return "(sso-cli.log not found)"


def _keycloak_token():
    """Obtain a short-lived Keycloak admin token."""
    resp = requests.post(
        f"{KEYCLOAK_BASE}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "grant_type": "password",
            "username": KEYCLOAK_USER,
            "password": KEYCLOAK_PASS,
        },
        verify=False,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _keycloak_events(app):
    """Fetch last 20 Keycloak ERROR events for the app's client."""
    client_id = APP_CLIENT_IDS.get(app, app)
    try:
        token = _keycloak_token()
        resp = requests.get(
            f"{KEYCLOAK_BASE}/admin/realms/{KEYCLOAK_REALM}/events",
            params={"type": "LOGIN_ERROR", "client": client_id, "max": 20},
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
            timeout=10,
        )
        resp.raise_for_status()
        events = resp.json()
        if not events:
            return "(no recent LOGIN_ERROR events)"
        return json.dumps(events, indent=2)
    except Exception as e:
        return f"(could not fetch Keycloak events: {e})"


# ── Prompt builder ────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """\
You are an expert in Keycloak SAML SSO, FreeIPA LDAP, and DevOps tooling.

A user reports: "{question}"

## Ansible log (last 60 lines)
{log}

## Keycloak LOGIN_ERROR events for {app}
{events}

## Known config
- App: {app}
- Keycloak client ID: {client_id}
- Keycloak realm: {realm}
- Keycloak base URL: {keycloak_base}

Diagnose the root cause and provide:
1. Root cause (1-2 sentences)
2. Specific fix (commands or config changes)
3. How to verify the fix worked
"""


def build_prompt(app, question):
    return PROMPT_TEMPLATE.format(
        question=question,
        app=app,
        log=_tail_log(),
        events=_keycloak_events(app),
        client_id=APP_CLIENT_IDS.get(app, app),
        realm=KEYCLOAK_REALM,
        keycloak_base=KEYCLOAK_BASE,
    )


# ── Ollama call ───────────────────────────────────────────────────────────────

def ask_ollama(prompt):
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]


# ── Public API ────────────────────────────────────────────────────────────────

def diagnose(app, question=None):
    """
    Diagnose a SAML failure for the given app.

    Args:
        app:      app name (jenkins, sonar, jira, confluence, bitbucket,
                  nessus, artifactory, wazuh)
        question: optional free-text question; defaults to generic failure query

    Returns:
        str: AI diagnosis
    """
    if app not in APP_CLIENT_IDS:
        return f"Unknown app '{app}'. Valid apps: {', '.join(APP_CLIENT_IDS)}"

    if not question:
        question = f"Why is {app} SAML authentication failing?"

    prompt = build_prompt(app, question)
    return ask_ollama(prompt)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    app  = sys.argv[1] if len(sys.argv) > 1 else "jenkins"
    q    = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
    print(diagnose(app, q))
