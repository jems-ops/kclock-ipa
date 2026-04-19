# keycloak-ipa-integration

Ansible automation to configure **Keycloak + FreeIPA LDAP federation** with **SonarQube** as a SAML SSO test client.

## Architecture

```
User → SonarQube (SAML SP) → Keycloak (SAML IdP) → FreeIPA (LDAP identity source)
```

## Servers

| Role      | DNS             | IP (set in `inventory`) |
|-----------|-----------------|-----------------------------------|
| FreeIPA   | freeipa.local   | see inventory                     |
| Keycloak  | keycloak.local  | see inventory                     |
| SonarQube | sonar.local     | see inventory                     |

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
# edit vault.yml and fill in all passwords/tokens — see vault.yml.example for required keys
echo "your-vault-password" > .vault_pass   # never commit this file
chmod 600 .vault_pass
ansible-vault encrypt group_vars/all/vault.yml
```

### 3. Run in order

```bash
# Step 1 — FreeIPA: create LDAP bind account, export CA cert
make freeipa-prep

# Step 2 — Keycloak: create realm, configure LDAP federation, create SonarQube SAML client
make keycloak-config

# Step 3 — SonarQube: write SAML settings to `sonar.properties`
make sonarqube-saml

# Or run all three in one go:
make site
```

## Roles

| Role                     | Target Host     | What it does                                          |
|--------------------------|-----------------|-------------------------------------------------------|
| `freeipa_keycloak_prep`  | freeipa.local   | Creates LDAP bind account, exports CA cert            |
| `keycloak_saml_federation` | keycloak.local| Creates realm, LDAP federation, SonarQube SAML client |
| `sonarqube_saml_config`  | sonar.local      | Writes SAML settings into `sonar.properties` and restarts SonarQube |

## Vault variables

See `group_vars/all/vault.yml.example` for the full list of required keys.
All secrets are stored encrypted via `ansible-vault`. **Never commit `.vault_pass`.**

## Validate after run

1. Open the Keycloak realm SAML descriptor URL for your configured host — it should return SAML metadata XML
2. Open the configured SonarQube URL → Login with SSO → redirected to Keycloak → log in with a FreeIPA user
3. Check Keycloak Admin UI: Realm `ipa` → User Federation → should show `freeipa-ldap` provider with synced users
