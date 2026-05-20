"""
Onboarding Agent — generates a new SAML SP Ansible role + playbook using local Ollama.

Given an app name and its base URL, the agent:
  1. Reads two reference roles (jenkins, sonarqube) as few-shot examples
  2. Asks Ollama to generate the new role files following the same structure
  3. Writes the files to roles/<app>_saml_config/ and playbooks/<app>_saml.yml
  4. Prints a summary of what was created
"""

import os
import re
import json
import requests

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:270m")

BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "platform", "identity", "ansible"))
ROLES_DIR    = os.path.join(BASE_DIR, "..", "..", "integrations")   # platform/integrations/<role>
PLAYBOOK_DIR = os.path.join(BASE_DIR, "playbooks")

# ── Reference role loader ─────────────────────────────────────────────────────

def _read_role(role_name):
    """Return a dict of filename → content for a reference role."""
    role_path = os.path.join(ROLES_DIR, role_name)
    files = {}
    for root, _, fnames in os.walk(role_path):
        for fname in fnames:
            fpath = os.path.join(root, fname)
            rel   = os.path.relpath(fpath, role_path)
            with open(fpath) as f:
                files[rel] = f.read()
    return files


def _format_role(name, files):
    parts = [f"### Role: {name}"]
    for path, content in files.items():
        parts.append(f"## {path}\n```\n{content}\n```")
    return "\n\n".join(parts)

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = """\
You are an Ansible expert. Generate a new SAML SP role for "{app_name}" following \
the exact structure of the two reference roles below.

Rules:
- Role name: {role_name}
- App host group: {host_group}
- App base URL variable: {app_name}_base_url  (already defined in group_vars/all/main.yml)
- App service name (systemd): {service_name}
- Validate certs variable: {app_name}_validate_certs (default: false)
- All Keycloak URLs come from group_vars/all/main.yml — never hardcode them
- Follow the same task file split: main.yml, detect_home.yml, retrieve_metadata.yml, \
configure_saml.yml, validate.yml
- Follow the same handlers/main.yml and defaults/main.yml patterns
- Output ONLY a JSON object mapping relative file paths to file contents, like:
  {{"tasks/main.yml": "...", "tasks/detect_home.yml": "...", ...}}
- No explanation, no markdown fences around the JSON — raw JSON only

{reference_roles}
"""

# ── Ollama call ───────────────────────────────────────────────────────────────

def _ask_ollama(prompt):
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"]

# ── JSON extractor ────────────────────────────────────────────────────────────

def _extract_json(text):
    """Extract the first JSON object from LLM output (handles markdown fences)."""
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    # Find first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output:\n{text[:500]}")
    return json.loads(match.group())

# ── File writer ───────────────────────────────────────────────────────────────

def _write_role(role_name, files):
    role_path = os.path.join(ROLES_DIR, role_name)
    written = []
    for rel_path, content in files.items():
        full_path = os.path.join(role_path, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        written.append(full_path)
    return written


def _write_playbook(app_name, role_name, host_group):
    content = f"""---
# Configures {app_name} SAML authentication.
# Prerequisite: run keycloak_config.yml first.

- name: Configure {app_name} SAML settings
  hosts: {host_group}
  become: true
  gather_facts: false
  roles:
    - {role_name}
"""
    path = os.path.join(PLAYBOOK_DIR, f"{app_name}_saml.yml")
    with open(path, "w") as f:
        f.write(content)
    return path

# ── Public API ────────────────────────────────────────────────────────────────

def onboard(app_name, host_group=None, service_name=None):
    """
    Generate and write a new SAML SP role + playbook for app_name.

    Args:
        app_name:     short name, e.g. "gitlab", "grafana"
        host_group:   Ansible inventory group (defaults to app_name)
        service_name: systemd service name (defaults to app_name)

    Returns:
        list of written file paths
    """
    host_group   = host_group   or app_name
    service_name = service_name or app_name
    role_name    = f"{app_name}_saml_config"

    # Load reference roles
    jenkins_files  = _read_role("jenkins_saml_config")
    sonarqube_files = _read_role("sonarqube_saml_config")
    reference = (
        _format_role("jenkins_saml_config",  jenkins_files) + "\n\n" +
        _format_role("sonarqube_saml_config", sonarqube_files)
    )

    prompt = PROMPT.format(
        app_name=app_name,
        role_name=role_name,
        host_group=host_group,
        service_name=service_name,
        reference_roles=reference,
    )

    print(f"[AI] Generating role '{role_name}' via {OLLAMA_MODEL}...")
    raw = _ask_ollama(prompt)

    role_files = _extract_json(raw)
    written    = _write_role(role_name, role_files)
    pb_path    = _write_playbook(app_name, role_name, host_group)
    written.append(pb_path)

    return written

# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python onboarding_agent.py <app_name> [host_group] [service_name]")
        sys.exit(1)
    app      = sys.argv[1]
    group    = sys.argv[2] if len(sys.argv) > 2 else None
    service  = sys.argv[3] if len(sys.argv) > 3 else None
    paths    = onboard(app, group, service)
    print("\n[AI] Files written:")
    for p in paths:
        print(f"  {p}")
