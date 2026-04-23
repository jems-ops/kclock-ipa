# keycloak-ipa-integration

Ansible automation for a complete **FreeIPA → Keycloak → multiple SAML SPs** single-sign-on stack.
One FreeIPA username and password. One Keycloak realm session. Any number of SAML-capable apps.

Today the repo provisions **SonarQube** and **Jenkins** as SPs sharing the `master` realm. Adding more apps (Artifactory, Nexus, Grafana, …) is a vars-only change plus — if the app needs its own configuration — a small role modelled on the existing ones.

## Table of contents

- [Architecture](#architecture)
- [Hosts](#hosts)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Running — one playbook, tag-driven](#running--one-playbook-tag-driven)
- [Roles](#roles)
- [Extending: add Artifactory (worked example)](#extending-add-artifactory-worked-example)
- [Vault variables](#vault-variables)
- [Validation](#validation)
- [Project layout](#project-layout)
- [Contributing](#contributing)
- [Further docs](#further-docs)

## Architecture

```
              ┌── SonarQube (SAML SP)
User ────────┤
              └── Jenkins   (SAML SP)
                        │
                        ▼
                Keycloak (SAML IdP, single realm)
                        │
                        ▼
                FreeIPA (LDAP identity source)
```

All SPs share the same Keycloak realm, so signing in once unlocks every app in the same browser session.

## Hosts

Defined in `inventory`. Update the IPs for your environment.

| Role      | DNS             | IP (reference)  |
|-----------|-----------------|-----------------|
| FreeIPA   | `freeipa.local` | 192.168.56.14   |
| Keycloak  | `keycloak.local`| 192.168.56.12   |
| SonarQube | `sonar.local`   | 192.168.56.18   |
| Jenkins   | `jenkins.local` | 192.168.56.13   |

## Prerequisites

- Control host: Python 3.9+, Ansible 2.15+, `ansible-vault`, `make`
- Each target host reachable over SSH with the credentials stored in the vault
- Keycloak 22.x installed at `/opt/keycloak-22.0.5` (override `keycloak_home` in `group_vars/all/main.yml` if different)
- SonarQube 10.x installed (the role auto-detects `/opt/sonarqube-*`)
- Jenkins 2.x with the **SAML** plugin installed (the role writes `$JENKINS_HOME/config.xml` and restarts)
- FreeIPA server reachable on LDAP (389) with `admin` Kerberos credentials available if you need to troubleshoot

No hostnames or URLs are hardcoded in any role — every `<service>_base_url` and SAML endpoint is derived from `inventory` + `group_vars/all/main.yml`, so retargeting to a new environment is a config-only change.

## Quick start

### 1. Set inventory and domain

```bash
# Edit inventory to point at your four hosts
$EDITOR inventory

# Confirm / override FreeIPA domain if it isn't the hostname
$EDITOR group_vars/all/main.yml
```

### 2. Create and populate the vault

```bash
cp group_vars/all/vault.yml.example group_vars/all/vault.yml
$EDITOR group_vars/all/vault.yml
echo "your-vault-password" > .vault_pass   # git-ignored — never commit
chmod 600 .vault_pass
ansible-vault encrypt group_vars/all/vault.yml
```

### 3. Run everything

```bash
make site
```

That runs the four plays in order: FreeIPA prep → Keycloak config → SonarQube SAML → Jenkins SAML.

## Running — one playbook, tag-driven

The entire project is a **single** playbook, `playbooks/site.yml`, with four tagged plays. Every `make` target translates to running `site.yml` with a `--tags` filter, optionally narrowed with `--limit`.

### Makefile shortcuts

```bash
make site              # everything
make freeipa-prep      # tag: freeipa_prep
make keycloak-config   # tag: keycloak_config
make sonarqube-saml    # tag: sonarqube_saml
make jenkins-saml      # tag: jenkins_saml
make saml-apps         # tag: saml_sp   (SonarQube + Jenkins in one go)
make check             # --check (dry run) against site.yml
make lint              # ansible-lint
```

### Tags cheat-sheet

| Tag               | Runs                                                           |
|-------------------|----------------------------------------------------------------|
| `freeipa_prep`    | FreeIPA bind account + CA cert export                          |
| `prep`            | Same as `freeipa_prep`                                         |
| `keycloak_config` | Keycloak realm / LDAP federation / all SAML clients + mappers  |
| `idp`             | Same as `keycloak_config`                                      |
| `sonarqube_saml`  | SonarQube SP configuration                                     |
| `jenkins_saml`    | Jenkins SP configuration                                       |
| `saml_sp`         | Both `sonarqube_saml` and `jenkins_saml`                       |

### Narrowing by host with `--limit`

Every play has its own `hosts:` stanza, so `--limit` just filters which plays actually execute tasks. Example use cases:

```bash
# Only reconfigure SonarQube
ansible-playbook -i inventory playbooks/site.yml --tags sonarqube_saml --limit sonar.local

# Same, via make
make sonarqube-saml LIMIT=sonar.local

# Run Keycloak + both SPs but only hit one Keycloak node
make site TAGS=keycloak_config,saml_sp LIMIT=keycloak.local,sonar.local,jenkins.local
```

## Roles

| Role                        | Target host      | What it does                                                                                                                  |
|-----------------------------|------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `freeipa_keycloak_prep`     | `freeipa.local`  | Creates the `keycloak-bind` LDAP sysaccount via `ipa-ldap-updater`; auto-detects and exports the FreeIPA CA certificate       |
| `keycloak_saml_federation`  | `keycloak.local` | Verifies the realm, imports the FreeIPA CA into the JKS truststore, provisions LDAP federation, loops over `keycloak_saml_clients` to create/update **every** SAML client + its NameID / user-property / group mappers, triggers a user sync |
| `sonarqube_saml_config`     | `sonar.local`    | Auto-detects SonarQube home, fetches Keycloak IdP metadata from the controller, rewrites the SAML block in `sonar.properties`, restarts SonarQube |
| `jenkins_saml_config`       | `jenkins.local`  | Auto-detects `$JENKINS_HOME`, fetches Keycloak IdP metadata on the controller, renders `config.xml` from a Jinja template with the XML embedded inline, restarts Jenkins |

Two design invariants make multi-app SSO easy:

1. **`keycloak_saml_clients` is a list.** The `keycloak_saml_federation` role loops over it to create / update every SAML client, its NameID mapper, the user-property mappers, and the groups mapper.
2. **All URLs are centralized.** `freeipa_base_url`, `keycloak_base_url`, `sonarqube_base_url`, `jenkins_base_url`, and the Keycloak SAML endpoint URLs (`keycloak_realm_base_url`, `keycloak_saml_metadata_url`, `keycloak_saml_login_url`, `keycloak_logout_url`) live in `group_vars/all/main.yml`. No role references a hostname literal.

## Extending: add Artifactory (worked example)

Artifactory is a good demo because it's a typical SAML SP with its own ACS endpoint, and it exercises both sides of the pipeline: a new Keycloak client plus a new app-side config step.

**End-to-end it's five stages — all but the last are a few lines of YAML.**

### 1. Inventory — add the host

`inventory`:

```ini
[artifactory]
artifactory.local ansible_host=192.168.56.17
```

### 2. `group_vars/all/main.yml` — add vars + register the SAML client

```yaml
# Hostname + base URL (follow the existing pattern for every service)
artifactory_hostname: "{{ groups['artifactory'][0] }}"
artifactory_base_url: "https://{{ artifactory_hostname }}"

# ACS path is an app-side property, not a hosting choice
artifactory_saml_acs_path: "/webapp/saml/loginResponse"

# Append to keycloak_saml_clients (same schema as SonarQube / Jenkins)
keycloak_saml_clients:
  # ... existing sonarqube-saml, jenkins-saml entries ...

  - name:       artifactory-saml
    client_id:  artifactory
    acs_url:    "{{ artifactory_base_url }}{{ artifactory_saml_acs_path }}"
    admin_url:  "{{ artifactory_base_url }}"
    base_url:   "{{ artifactory_base_url }}"
    redirect_uris:
      - "{{ artifactory_base_url }}/*"
    nameid_format:           email
    nameid_user_attribute:   email
    sign_documents:          "false"
    sign_assertions:         "true"
    force_post_binding:      "true"
    include_authnstatement:  "true"
    attributes:
      - { property: username, saml_name: username, friendly_name: username }
      - { property: email,    saml_name: email,    friendly_name: email    }
```

### 3. Apply Keycloak-side changes

```bash
make keycloak-config
```

The existing role loops over `keycloak_saml_clients` and creates / updates the new `artifactory` SAML client and all its mappers. No code changes needed in the role.

### 4. New role for the Artifactory side

Copy `roles/sonarqube_saml_config` (or `roles/jenkins_saml_config`) as a starting point:

```bash
cp -r roles/sonarqube_saml_config roles/artifactory_saml_config
```

Adapt `tasks/configure_saml.yml` to write Artifactory's SAML settings. Artifactory exposes a REST API (`/artifactory/api/saml/config`) and also accepts a `saml.yaml` config on disk — pick the path that fits your install. Keep the same three-step shape as SonarQube: **retrieve IdP metadata on the controller** → **write config** → **restart service via handler**.

### 5. New play in `site.yml`

```yaml
- name: Configure Artifactory SAML settings
  hosts: artifactory
  become: true
  gather_facts: false
  tags:
    - artifactory_saml
    - saml_sp
  roles:
    - artifactory_saml_config
```

And a matching Makefile target:

```make
artifactory-saml:
	$(ANSIBLE) --tags artifactory_saml $(LIMIT_ARG)
```

Run it:

```bash
make artifactory-saml                           # just Artifactory
make saml-apps                                  # all SPs in one run
make site TAGS=artifactory_saml LIMIT=artifactory.local
```

## Vault variables

Required keys (see `group_vars/all/vault.yml.example`):

```yaml
vault_ansible_user:                 # SSH user for all hosts
vault_ansible_password:             # SSH password
vault_ansible_become_password:      # sudo password
vault_freeipa_bind_password:        # chosen by you — set during freeipa_prep
vault_keycloak_admin_password:      # Keycloak admin user password
vault_keycloak_truststore_password: # JKS store password
vault_sonarqube_admin_token:        # squ_... token generated in SonarQube
```

`.vault_pass` is in `.gitignore` — never commit it.

## Validation

After `make site`:

1. `curl -sk $(ansible -i inventory keycloak -m debug -a 'var=keycloak_saml_metadata_url' --vault-password-file .vault_pass | awk '/=>/{print $NF}')` should return valid SAML metadata XML.
2. Open `https://sonar.local` in a private browser — click **Log in with FreeIPA via Keycloak** → Keycloak login → enter a FreeIPA user → land in SonarQube.
3. In the same window open `https://jenkins.local` → click **Login with SAML SSO** → no second password prompt, you're in.
4. Keycloak admin console → realm `master` → **User federation** → `freeipa-ldap` → confirm synced users and group counts.
5. Keycloak admin console → realm `master` → **Clients** → confirm `sonarqube` and `jenkins` both present.

## Project layout

```
.
├── ansible.cfg
├── inventory
├── Makefile
├── README.md
├── docs/
│   ├── MANUAL-SETUP.md         # step-by-step manual equivalent
│   └── TROUBLESHOOTING.md      # issues we've hit, with RCAs
├── group_vars/
│   └── all/
│       ├── main.yml            # every non-secret var (all URLs, DNs, mapper configs)
│       └── vault.yml           # encrypted secrets
├── playbooks/
│   └── site.yml                # single tag-driven playbook
└── roles/
    ├── freeipa_keycloak_prep/
    ├── keycloak_saml_federation/
    ├── sonarqube_saml_config/
    └── jenkins_saml_config/
```

## Contributing

- Run `make lint` before committing. The repo currently passes the `production` profile.
- No hardcoded hostnames or URLs in roles — always reference `<service>_base_url` / `keycloak_saml_*_url` from `group_vars/all/main.yml`. A `grep` check is part of the unwritten contract.
- Every new play in `site.yml` gets its own primary tag (snake_case) plus at least one umbrella tag (`saml_sp`, `prep`, …).
- Add a matching Makefile shortcut for discoverability.
- Mirror the SonarQube / Jenkins role structure when adding a new SAML SP: `defaults/main.yml`, `tasks/{main,detect_home,retrieve_*,configure_*,validate}.yml`, `handlers/main.yml`, a single Jinja template where reasonable.
- Commits should include the co-author line:

  ```
  Co-Authored-By: <your-name> <your-email>
  ```

## Further docs

- `docs/MANUAL-SETUP.md` — the same integration done by hand, step by step, with `ldapmodify` / `kcadm.sh` / `sonar.properties` / Jenkins admin UI walkthroughs. Useful when you want to audit what Ansible is doing.
- `docs/TROUBLESHOOTING.md` — every issue we hit during the initial build (SAML duplicate-attribute errors, LDAP sync `UnknownError`, signature rejection, identity conflicts) with root-cause analysis and fixes.
