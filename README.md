# keycloak-ipa-integration

Ansible automation to configure **Keycloak + FreeIPA LDAP federation** with **SonarQube** as a SAML SSO test client.

## Architecture

```
User → SonarQube (SAML SP) → Keycloak (SAML IdP) → FreeIPA (LDAP identity source)
```

## Servers

| Role      | DNS              | IP               |
|-----------|------------------|------------------|
| FreeIPA   | freeipa.local    | 192.168.56.14    |
| Keycloak  | keycloak.local   | 192.168.201.12   |
| SonarQube | sonar.local      | 192.168.201.16   |

## Quick Start

### 1. Set your FreeIPA domain

Edit `group_vars/all/main.yml` and update these values to match your FreeIPA installation:

```yaml
freeipa_domain:  "ipa.local"      # your actual IPA domain
freeipa_realm:   "IPA.LOCAL"      # uppercase Kerberos realm
freeipa_base_dn: "dc=ipa,dc=local"
```

### 2. Create and populate the vault

```bash
cp group_vars/all/vault.yml.example group_vars/all/vault.yml
# edit vault.yml and fill in all passwords/tokens
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass
ansible-vault encrypt group_vars/all/vault.yml
```

### 3. Run in order

```bash
# Step 1 — FreeIPA: create LDAP bind account, export CA cert
make freeipa-prep

# Step 2 — Keycloak: create realm, configure LDAP federation, create SonarQube SAML client
make keycloak-config

# Step 3 — SonarQube: push SAML settings via API
make sonarqube-saml

# Or run all three in one go:
make site
```

## Roles

| Role                     | Target Host     | What it does                                          |
|--------------------------|-----------------|-------------------------------------------------------|
| `freeipa_keycloak_prep`  | freeipa.local   | Creates LDAP bind account, exports CA cert            |
| `keycloak_saml_federation` | keycloak.local| Creates realm, LDAP federation, SonarQube SAML client |
| `sonarqube_saml_config`  | localhost (API) | Configures SonarQube SAML settings via REST API       |

## Vault variables

See `group_vars/all/vault.yml.example` for the full list. Required secrets:

| Variable                        | Description                              |
|---------------------------------|------------------------------------------|
| `vault_ansible_user`            | SSH user for all hosts                   |
| `vault_ansible_password`        | SSH password                             |
| `vault_ansible_become_password` | sudo password                            |
| `vault_freeipa_bind_password`   | Password for the Keycloak LDAP bind acct |
| `vault_keycloak_admin_password` | Keycloak admin password                  |
| `vault_keycloak_truststore_password` | JKS truststore password (default: changeit) |
| `vault_sonarqube_admin_token`   | SonarQube admin user token               |

## Validate after run

1. Open `https://keycloak.local/realms/ipa/protocol/saml/descriptor` — should return SAML metadata XML
2. Open `https://sonar.local` → Login with SSO → redirected to Keycloak → log in with a FreeIPA user
3. Check Keycloak Admin UI: Realm `ipa` → User Federation → should show `freeipa-ldap` provider with synced users
