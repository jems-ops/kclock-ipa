# freeipa_keycloak_prep
Ansible role that prepares **FreeIPA** for Keycloak LDAP federation and
configures the **Keycloak** side of that federation. It's the IdP-backend
half of the stack — the per-application SSO client side lives in the sister
role [`keycloak_saml_integration`](../keycloak_saml_integration/).
## What it does
1. **On the FreeIPA host** (`bind_account` / `admin_groups` / `export_ca` /
   `validate`):
   - Creates two dedicated IPA service users — `svc.ldap` (LDAP bind
     account for federation sync) and `svc.keycloak` (Keycloak service
     user for connecting to downstream apps) — with non-expiring passwords.
   - Ensures the canonical per-app admin groups exist
     (`jenkins-administrators`, `sonar-administrators`, …).
   - Auto-detects and exports the FreeIPA CA cert to a known path
     (`/tmp/freeipa-ca.crt`).
   - Validates the bind account by running `ldapsearch` against the IPA
     directory.
2. **On the Keycloak host** (`tasks/ldap_federation.yml` orchestrator + the
   `tasks/ldap/*` workers):
   - Slurps the FreeIPA CA cert and imports it into Keycloak's JKS
     truststore, wires the SPI truststore options into `keycloak.conf`,
     restarts Keycloak.
   - Obtains an admin token, creates / updates the `freeipa-ldap`
     UserStorageProvider, attaches the username / email / firstName /
     lastName / full-name / group LDAP mappers, and triggers a full
     user sync.
## Layout
```
roles/freeipa_keycloak_prep/
├── defaults/main.yml
├── handlers/main.yml                    # restart keycloak
├── tasks/
│   ├── main.yml                         # IPA-side entry point
│   ├── bind_account.yml                 # svc.ldap + svc.keycloak IPA users
│   ├── admin_groups.yml                 # canonical app admin groups
│   ├── export_ca.yml                    # IPA CA → /tmp/freeipa-ca.crt
│   ├── validate.yml                     # ldapsearch sanity check
│   ├── ldap_federation.yml              # Keycloak-side entry point
│   └── ldap/
│       ├── ldap_truststore.yml          # IPA CA → JKS, keycloak.conf wiring
│       ├── get_keycloak_token.yml       # admin-cli token (post-restart)
│       ├── ldap_provider.yml            # UserStorageProvider component
│       ├── ldap_mappers.yml             # username / email / fullName / groups
│       └── ldap_sync.yml                # POST .../sync?action=triggerFullSync
└── templates/
    ├── ldap-provider.json.j2
    ├── ldap-user-attribute-mapper.json.j2
    ├── ldap-full-name-mapper.json.j2
    └── ldap-group-mapper.json.j2
```
## Prerequisites
Vault keys (encrypted in `group_vars/all/vault.yml`; full reference in
`group_vars/all/vault.yml.example`):
- `vault_freeipa_admin_password`        — IPA admin password used for `kinit`
- `vault_freeipa_ldap_bind_password`    — password set on `svc.ldap`
- `vault_freeipa_keycloak_svc_password` — password set on `svc.keycloak`
- `vault_keycloak_admin_password`       — Keycloak admin user password
- `vault_keycloak_truststore_password`  — JKS truststore passphrase
Inventory groups in `inventory`:
- `[freeipa]`   — the IPA master
- `[keycloak]`  — the Keycloak host
The non-secret federation variables live in `group_vars/all/freeipa.yml`
(base DN, users DN, groups DN, bind UID, LDAP scheme/port, CA candidates,
truststore paths, LDAP attribute names, the `keycloak_ldap_*` knobs).
## How to run
The role isn't invoked directly with `roles:` — it ships with two entry
points exposed through `playbooks/configure-keycloak-ldap-federation.yml`:
- IPA-side play uses the role's default `tasks/main.yml`.
- Keycloak-side play imports `tasks_from: ldap_federation`.
End-to-end (IPA prep + Keycloak federation + full user sync):
```bash
ansible-playbook -i inventory playbooks/configure-keycloak-ldap-federation.yml
```
Tag-scoped variants:
```bash
# IPA-side only: svc.ldap + svc.keycloak users, admin groups, CA export, bind validation
ansible-playbook -i inventory playbooks/configure-keycloak-ldap-federation.yml --tags freeipa_prep
# Keycloak-side only: truststore, provider, mappers, sync
ansible-playbook -i inventory playbooks/configure-keycloak-ldap-federation.yml --tags ldap
```
The Keycloak-side play targets `http://localhost:8080` from the Keycloak
host, so it's resilient to the public HTTPS reverse proxy being unavailable.
## Verifying
```bash
ansible-playbook -i inventory --syntax-check playbooks/configure-keycloak-ldap-federation.yml
# Confirm the freeipa-ldap UserStorageProvider exists and was synced:
./scripts/trigger-freeipa-ldap-sync.sh    # prints the sync result JSON
```
A successful run prints something like:
```
LDAP provider 'freeipa-ldap' (ID: <uuid>) status: updated
FreeIPA full sync result:
  {'ignored': False, 'added': 0, 'updated': 7, 'removed': 0, 'failed': 0,
   'status': '0 imported users, 7 updated users'}
```
## Further reading
- Sister role for SP-side onboarding: [`../keycloak_saml_integration/`](../keycloak_saml_integration/)
- Short federation + SSO summary: [`docs/Freeipa-keycloak-sso-summary.md`](../../docs/Freeipa-keycloak-sso-summary.md)
- Implementation note: [`docs/FREEIPA_KEYCLOAK_FEDERATION_NOTE.md`](../../docs/FREEIPA_KEYCLOAK_FEDERATION_NOTE.md)
