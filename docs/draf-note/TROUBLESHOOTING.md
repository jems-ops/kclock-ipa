# Keycloak + FreeIPA + SonarQube SSO — Troubleshooting Guide

This document captures every issue encountered during the initial deployment of the
FreeIPA → Keycloak → SonarQube SAML SSO integration, including root causes and resolutions.

---

## Environment

| Component  | Host            | IP              | Version       |
|------------|-----------------|-----------------|---------------|
| FreeIPA    | freeipa.local   | 192.168.56.14   | FreeIPA 4.x   |
| Keycloak   | keycloak.local  | 192.168.56.12   | 22.0.5        |
| SonarQube  | sonar.local     | 192.168.56.18   | 10.3.0.82913  |
| Nginx proxy| (sonar.local)   | 192.168.56.15   | —             |

---

## Issue 1 — `invalid requester` on SAML redirect

### Symptom
Keycloak returned `invalid requester` immediately after SonarQube redirected to it.
The browser URL contained a `SAMLRequest` parameter.

### Diagnosis
Decoded the SAMLRequest (base64 + zlib inflate):
```python
import base64, zlib, urllib.parse
xml = zlib.decompress(base64.b64decode(urllib.parse.unquote(saml_param)), -15).decode()
```
The `<saml:Issuer>` matched the registered client ID (`sonarqube`) and the
`AssertionConsumerServiceURL` matched the configured ACS URL. The problem was not
the request content — it was Keycloak requiring the SP to **sign** the request.

### Root Cause
When Keycloak creates a SAML client via the REST API, it defaults
`saml.client.signature = true`. This requires every AuthnRequest from SonarQube to be
cryptographically signed. SonarQube does not sign AuthnRequests by default.

### Resolution
Set `saml.client.signature = false` on the Keycloak SAML client:
```bash
kcadm.sh update clients/<ID> -r ipa \
  -s 'attributes."saml.client.signature"="false"'
```
In the Ansible template (`saml-client.json.j2`) add:
```json
"saml.client.signature": "false"
```

---

## Issue 2 — Keycloak LDAP sync returns `UnknownError`

### Symptom
Running `kcadm.sh create user-storage/<LDAP_ID>/sync?action=triggerFullSync -r ipa`
returned `UnknownError`. No users appeared in the realm. The Keycloak LDAP connection
test (`testLDAPConnection`) returned HTTP 204 (success), confirming the bind credentials
and network path were correct.

### Diagnosis
- Port 389 reachable from Keycloak VM ✓
- Bind credentials valid (tested with ldapsearch) ✓
- LDAP search returned users including `ipaUniqueID` attribute ✓
- Checking the LDAP provider component via `kcadm.sh get components/<ID> -r ipa` showed
  `"parentId": "ipa"` (realm name, not UUID).

### Root Cause
Keycloak's user storage sync engine uses the `parentId` of the LDAP component to look up
the realm internally. When `parentId` is the realm **name** (`ipa`), the sync fails
silently with `UnknownError`. It must be the realm **UUID**.

The Ansible role passed `"parentId": "{{ keycloak_realm }}"` (the name) in the
`ldap-provider.json.j2` template, which Keycloak accepted for creation but internally
stored incorrectly for sync operations.

### Resolution
Fetch the realm UUID before creating the LDAP provider and use it as `parentId`:
```yaml
- name: Get realm UUID
  ansible.builtin.shell: >
    {{ keycloak_kcadm }} get realms/{{ keycloak_realm }}
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])'
  register: keycloak_realm_uuid_cmd
```

Then in `ldap-provider.json.j2`:
```json
"parentId": "{{ keycloak_realm_uuid }}"
```

To fix an existing broken provider:
```bash
REALM_UUID=$(kcadm.sh get realms/ipa | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
kcadm.sh update components/<LDAP_ID> -r ipa -s "parentId=$REALM_UUID"
```

---

## Issue 3 — `Found an Attribute element with duplicated Name` (Role attributes)

### Symptom
SonarQube showed `https://sonar.local/sessions/unauthorized`.
SonarQube `web.log` showed:
```
com.onelogin.saml2.exception.ValidationError: Found an Attribute element with duplicated Name
```

### Diagnosis
Enabled SonarQube SAML debug logging:
```
POST /api/system/change_log_level
level=DEBUG&packageName=org.sonar.auth.saml
```
The debug log revealed the SAML assertion contained multiple
`<saml:Attribute Name="Role">` elements — one per Keycloak role:
`uma_authorization`, `view-profile`, `manage-account`, `default-roles-ipa`, etc.

The SonarQube SAML library (onelogin) rejects any SAML assertion that contains
two or more `<saml:Attribute>` elements sharing the same `Name` attribute.

### Root Cause
The Keycloak `role_list` **default client scope** was automatically attached to the
SonarQube SAML client. Its `role-list` mapper creates a separate
`<saml:Attribute Name="Role">` element for every Keycloak role the user has —
instead of grouping them into one element with multiple values.

SonarQube doesn't use Keycloak roles at all; they were redundant.

### Resolution
Remove the `role_list` scope from the SAML client:
```bash
kcadm.sh delete clients/<ID>/default-client-scopes/<ROLE_LIST_SCOPE_ID> -r ipa
```
In `saml-client.json.j2` add to prevent it being added automatically:
```json
"defaultClientScopes": [],
"optionalClientScopes": []
```

---

## Issue 4 — `Found an Attribute element with duplicated Name` (groups attribute)

### Symptom
Same `ValidationError: Found an Attribute element with duplicated Name` in SonarQube
`web.log`, persisting after Issue 3 was fixed.

### Diagnosis
Checked how many groups the test user `jemal` was in:
```bash
kcadm.sh get users/<USER_ID>/groups -r ipa
```
Result: **7 groups** (admins, editors, sonar-admins, ipausers, trust admins,
sonar-developers, sonar-users).

### Root Cause
The Keycloak `saml-group-membership-mapper` with `single = false` (the default)
creates **one separate `<saml:Attribute Name="groups">` element per group**.
With 7 groups, the assertion contained 7 elements all with `Name="groups"`,
which the onelogin library correctly flagged as 6 duplicates.

### Resolution
Set `single = true` on the groups protocol mapper. This produces **one
`<saml:Attribute Name="groups">` element** with a single value containing all
group names:
```bash
kcadm.sh update clients/<ID>/protocol-mappers/models/<GROUPS_MAPPER_ID> \
  -r ipa -s 'config.single="true"'
```
In `saml-group-mapper.json.j2`:
```json
"single": "true"
```

> **Note:** `single=true` sends groups as a comma-separated string in one attribute
> value. SonarQube's group sync reads this correctly.

---

## Issue 5 — `NullPointerException: username is missing`

### Symptom
After fixing the duplicate attribute errors, SonarQube `web.log` showed:
```
java.lang.NullPointerException: username is missing
  at SamlAuthenticator.getNonNullFirstAttribute(SamlAuthenticator.java:186)
  at SamlAuthenticator.getLogin(SamlAuthenticator.java:169)
```

### Diagnosis
Inspected all protocol mappers on the SonarQube SAML client:
```bash
kcadm.sh get clients/<ID>/protocol-mappers/models -r ipa
```
The `username` mapper showed `user.attribute = n/a` (empty/null).

### Root Cause
During an earlier `kcadm.sh update` operation to change the mapper's `name` and
`attribute.name`, the existing `user.attribute = username` config key was silently
dropped. The `saml-user-property-mapper` then had no source property to read,
so the `username` SAML attribute was absent from the assertion.

### Resolution
Explicitly re-set the missing config key:
```bash
kcadm.sh update clients/<ID>/protocol-mappers/models/<MAPPER_ID> \
  -r ipa -s 'config."user.attribute"=username'
```

> **Lesson:** When updating a Keycloak protocol mapper via `kcadm.sh update`,
> always include **all** config keys you want to preserve — partial updates can
> silently drop existing values.

---

## Issue 6 — `This account is already associated with another authentication method`

### Symptom
After all SAML errors were resolved, SonarQube showed:
```
You're not authorized to access this page.
Reason: This account is already associated with another authentication method.
```

### Diagnosis
Checked the pre-created jemal user in SonarQube:
```
externalIdentityProvider: None   ← no SAML provider linked
local: false
```
The user was manually created via the SonarQube API without specifying the
SAML identity provider. When jemal logged in via SAML, SonarQube tried to
match the SAML login to an existing user whose `externalIdentityProvider` was
`null` (not `saml`), causing the conflict.

### Root Cause
Pre-creating a SonarQube user via `POST /api/users/create` without the correct
`externalIdentityProvider` value creates a user that conflicts with SAML auto-provisioning.

### Resolution
Delete (deactivate + anonymize) the conflicting user and let SonarQube auto-create
it correctly on first SAML login (requires `sonar.auth.saml.user.signUpEnabled=true`):
```bash
curl -X POST "https://sonar.local/api/users/deactivate" \
  -u "$TOKEN:" -d "login=jemal&anonymize=true"
```
SonarQube then creates the user on the next successful SAML login with
`externalIdentityProvider = saml` and `externalIdentity = jemal`.

> **Do not pre-create users** when using SAML with `signUpEnabled=true`.
> Let SAML auto-provisioning handle user creation.

---

## Final Working Configuration

### Keycloak SAML Client (`sonarqube`)
| Setting | Value |
|---|---|
| `saml.client.signature` | `false` |
| `saml.assertion.signature` | `true` |
| `saml.server.signature` (sign documents) | `false` |
| `defaultClientScopes` | `[]` (empty — no role_list) |

### Protocol Mappers
| Mapper name | Type | user.attribute | SAML attribute name |
|---|---|---|---|
| `username` | User Property | `username` | `username` |
| `email` | User Property | `email` | `email` |
| `name` | User Property | `username` | `name` |
| `groups` | Group list | — | `groups` (`single=true`) |

### SonarQube `sonar.properties`
```properties
sonar.auth.saml.enabled=true
sonar.auth.saml.applicationId=sonarqube
sonar.auth.saml.providerName=FreeIPA via Keycloak
sonar.auth.saml.providerId=https://keycloak.local/realms/ipa
sonar.auth.saml.loginUrl=https://keycloak.local/realms/ipa/protocol/saml
sonar.auth.saml.user.login=username
sonar.auth.saml.user.name=username
sonar.auth.saml.user.email=email
sonar.auth.saml.group.name=groups
sonar.auth.saml.user.signUpEnabled=true
sonar.auth.saml.certificate.secured=<keycloak-realm-signing-cert>
```

### Keycloak LDAP Federation
| Setting | Value | Notes |
|---|---|---|
| `connectionUrl` | `ldap://freeipa.local:389` | Plain LDAP (no TLS) for lab |
| `usersDn` | `cn=users,cn=accounts,dc=freeipa,dc=local` | FreeIPA users base |
| `uuidLDAPAttribute` | `ipaUniqueID` | FreeIPA unique ID attribute |
| `parentId` | `<realm UUID>` | **Must be UUID, not realm name** |
| `bindCredential` | from vault | Must be explicitly re-set after any kcadm update |
