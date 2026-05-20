# AI Agents

Two AI agents extend `sso-cli` with local LLM capabilities via Ollama.
No cloud dependency — all inference runs on-device.

## Requirements

- [Ollama](https://ollama.com) running locally (`ollama serve`)
- Model pulled: `ollama pull gemma3:270m`
- Package installed: `pip install -e ansible/sso`

---

## 1. Troubleshoot Agent

**"Why is \<app\> SAML failing?"**

Collects context from the Ansible run log and Keycloak admin events, then asks the LLM for a root cause, specific fix, and verification steps.

### Usage

```bash
# Generic diagnosis
sso-cli diagnose jenkins

# Specific question
sso-cli diagnose wazuh -q "Users authenticate but land on a blank page"

# Direct
python sso_cli/ai/troubleshoot_agent.py nessus "SAML assertion rejected"
```

### Context collected

| Source | What |
|---|---|
| `sso-cli.log` | Last 60 lines of Ansible output |
| Keycloak events API | Last 20 `LOGIN_ERROR` events for the app's client |
| Static config | Client ID, realm, Keycloak base URL |

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `KEYCLOAK_ADMIN_PASSWORD` | *(empty)* | Required for Keycloak event fetching |
| `KEYCLOAK_BASE_URL` | `https://keycloak.local` | Keycloak base URL |
| `KEYCLOAK_REALM` | `master` | Realm name |
| `OLLAMA_MODEL` | `gemma3:270m` | Ollama model to use |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama API endpoint |

### Supported apps

`jenkins`, `sonar`, `jira`, `confluence`, `bitbucket`, `nessus`, `artifactory`, `wazuh`

---

## 2. Onboarding Agent

Generates a complete Ansible role and playbook for a new SAML service provider,
using the existing `jenkins_saml_config` and `sonarqube_saml_config` roles as
few-shot examples.

### Usage

```bash
# Onboard a new app (host group and service name default to app name)
sso-cli ai-onboard gitlab

# With explicit host group and systemd service name
sso-cli ai-onboard grafana --host-group monitoring --service grafana-server

# Direct
python sso_cli/ai/onboarding_agent.py gitlab
```

### What gets generated

```
roles/<app>_saml_config/
  tasks/main.yml
  tasks/detect_home.yml
  tasks/retrieve_metadata.yml
  tasks/configure_saml.yml
  tasks/validate.yml
  defaults/main.yml
  handlers/main.yml

playbooks/<app>_saml.yml
```

The generated role follows the same structure as all existing SP roles:
`detect_home → retrieve_metadata → configure_saml → validate`.
All Keycloak URLs are referenced from `group_vars/all/main.yml` — nothing is hardcoded.

### After generation

1. Review the generated files and adjust app-specific config (API paths, config file locations, restart command)
2. Add the app to `group_vars/all/main.yml` → `keycloak_saml_clients` list
3. Add the host to `inventory`
4. Run: `sso-cli onboard-app <app>`

---

## Source

```
ansible/sso/sso_cli/ai/
  troubleshoot_agent.py
  onboarding_agent.py
```
