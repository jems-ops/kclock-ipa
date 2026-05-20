# Keycloak + FreeIPA SSO Integration — Architecture

## Overview

A fully automated **FreeIPA → Keycloak → SAML SP** single-sign-on stack.
One FreeIPA identity. One Keycloak realm session. Any number of SAML-capable applications.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          User / Browser                                 │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  HTTPS (SAML AuthnRequest)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Keycloak  (192.168.56.12)                            │
│                    SAML Identity Provider — realm: master               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  SAML Clients (Service Providers)                                │   │
│  │                                                                  │   │
│  │  sonarqube  │  jenkins  │  jira  │  confluence  │  bitbucket    │   │
│  │  nessus     │  artifactory       │  wazuh                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  User Federation  →  LDAP (FreeIPA)                              │   │
│  │  Mappers: NameID, user-property, groups, full-name               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  LDAP / LDAPS (port 389 / 636)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FreeIPA  (192.168.56.14)                             │
│                    LDAP Identity Source + CA                            │
│                                                                         │
│  • Users & Groups (POSIX)                                               │
│  • keycloak-bind sysaccount (read-only LDAP bind)                       │
│  • CA certificate exported → Keycloak JKS truststore                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Service Provider Map

| Application | Host | IP | SAML Client ID |
|---|---|---|---|
| SonarQube | `sonar.local` | 192.168.56.16 | `sonarqube` |
| Jenkins | `jenkins.local` | 192.168.56.13 | `jenkins` |
| Jira | `jira.local` | 192.168.56.20 | `https://jira.local` |
| Confluence | `confluence.local` | 192.168.56.21 | `https://confluence.local` |
| Bitbucket | `bitbucket.local` | 192.168.56.22 | `https://bitbucket.local` |
| Nessus / Tenable.sc | `nessus.local` | 192.168.56.23 | `https://tenable.sc` |
| Artifactory | `artifactory.local` | 192.168.56.17 | `https://artifactory.local` |
| Wazuh | `wazuh.va2.magellan.net` | 192.168.56.24 | `wazuh` |

---

## Automation Architecture

```
Ansible Control Host
│
├── ansible/sso/                        # SSO stack automation
│   ├── playbooks/
│   │   ├── site.yml                    # Full stack: prep → keycloak → all SPs
│   │   ├── freeipa_prep.yml            # FreeIPA bind account + CA export
│   │   ├── keycloak_config.yml         # Keycloak LDAP federation + SAML clients
│   │   ├── sonarqube_saml.yml
│   │   ├── jenkins_saml.yml
│   │   ├── jira_saml.yml
│   │   ├── confluence_saml.yml
│   │   ├── bitbucket_saml.yml
│   │   ├── nessus_saml.yml
│   │   ├── artifactory_saml.yml
│   │   └── wazuh_saml.yml
│   │
│   ├── roles/
│   │   ├── freeipa_keycloak_prep       → freeipa.local
│   │   ├── keycloak_saml_federation    → keycloak.local
│   │   ├── sonarqube_saml_config       → sonar.local
│   │   ├── jenkins_saml_config         → jenkins.local
│   │   ├── atlassian_saml_config       → jira / confluence / bitbucket
│   │   ├── nessus_saml_config          → nessus.local
│   │   ├── artifactory_saml_config     → artifactory.local
│   │   └── wazuh_saml_config           → wazuh host
│   │
│   └── sso_cli/                        # Python CLI wrapper (sso-cli)
│       └── cli.py                      # deploy / prep / keycloak / onboard-app
│
└── ansible/ldap/                       # Standalone LDAP federation automation
    ├── playbooks/
    │   └── configure-keycloak-ldap-federation.yml
    └── roles/
        └── tasks/
            ├── ldap_federation.yml     # Provision LDAP provider in Keycloak
            ├── bind_account.yml        # Create/verify bind account in FreeIPA
            ├── export_ca.yml           # Export FreeIPA CA → Keycloak truststore
            ├── admin_groups.yml        # Sync admin groups
            └── validate.yml            # Post-config validation
```

---

## Authentication Flow

```
1. User navigates to any SP (e.g., Jenkins)
        │
        ▼
2. SP redirects → Keycloak with SAML AuthnRequest
        │
        ▼
3. Keycloak presents login page
        │
        ▼
4. User enters FreeIPA credentials
        │
        ▼
5. Keycloak validates credentials via LDAP federation → FreeIPA
        │
        ▼
6. Keycloak issues SAML Assertion (signed) → SP
        │
        ▼
7. SP validates assertion, creates local session
        │
        ▼
8. Subsequent SP visits in same browser → SSO (no re-authentication)
```

---

## Key Design Decisions

- **Single realm (`master`)** — all SPs share one Keycloak realm; one login unlocks every app.
- **Centralized URLs** — all `<service>_base_url` and SAML endpoint URLs live in `group_vars/all/main.yml`; no hostnames hardcoded in roles.
- **`keycloak_saml_clients` list** — the `keycloak_saml_federation` role loops over this list to create/update every SAML client, enabling zero-code onboarding of new SPs.
- **Vault-encrypted secrets** — all credentials in `vault.yml`, encrypted with `ansible-vault`; `.vault_pass` is git-ignored.
- **Read-only LDAP bind** — Keycloak connects to FreeIPA via a dedicated `keycloak-bind` sysaccount with minimal privileges.
- **CA trust** — FreeIPA CA is exported and imported into Keycloak's JKS truststore to enable LDAPS.

---

## Network Topology

```
192.168.56.0/24  (host-only / private lab network)

  .10  Tenable / Nexus (alt)
  .11  Artifactory (alt) / Nexus
  .12  Keycloak          ← SAML IdP
  .13  Jenkins           ← SAML SP
  .14  FreeIPA           ← LDAP identity source
  .15  Nginx reverse proxy
  .16  SonarQube         ← SAML SP
  .17  Artifactory       ← SAML SP
  .18  SonarQube (alt)
  .19  Wazuh (alt)
  .20  Jira              ← SAML SP
  .21  Confluence        ← SAML SP
  .22  Bitbucket         ← SAML SP
  .23  Nessus            ← SAML SP
  .24  Wazuh             ← SAML SP
```
