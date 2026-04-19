# Manual Setup Guide: FreeIPA → Keycloak → SonarQube SAML SSO

This document describes every step required to configure single sign-on between
FreeIPA (user directory), Keycloak (SAML IdP), and SonarQube (SAML SP) without
using any automation. Follow the sections in order.

---

## Architecture Overview

```
Browser
  │
  ▼
SonarQube (SAML Service Provider)
  │  SAML AuthnRequest / Response
  ▼
Keycloak (SAML Identity Provider)   ←──LDAP──►  FreeIPA (User Directory)
```

- **FreeIPA** stores users and groups. Keycloak reads them via LDAP.
- **Keycloak** authenticates users and issues SAML assertions to SonarQube.
- **SonarQube** trusts Keycloak assertions and grants access based on the mapped attributes.

### Reference values used in this guide

| Component  | Hostname        | Port |
|------------|-----------------|------|
| FreeIPA    | freeipa.local   | 389 (LDAP) / 636 (LDAPS) |
| Keycloak   | keycloak.local  | 443 (HTTPS) / 8080 (internal) |
| SonarQube  | sonar.local     | 443 (HTTPS) / 9000 (internal) |

- Keycloak realm: `ipa`
- FreeIPA base DN: `dc=freeipa,dc=local`
- LDAP bind account: `uid=keycloak-bind,cn=sysaccounts,cn=etc,dc=freeipa,dc=local`

---

## Part 1 — FreeIPA: Create the LDAP Bind Account

Keycloak needs a read-only system account to query FreeIPA's LDAP directory.
FreeIPA system accounts live under `cn=sysaccounts,cn=etc` and are not normal IPA
users (they bypass password-policy enforcement).

### 1.1 SSH into the FreeIPA server

```bash
ssh root@freeipa.local
```

### 1.2 Authenticate as an IPA admin

```bash
kinit admin
```

Enter the IPA admin password when prompted.

### 1.3 Create the bind account using ldapmodify
> **Ansible:** `roles/freeipa_keycloak_prep/tasks/bind_account.yml`, template: `roles/freeipa_keycloak_prep/templates/keycloak-bind.update.j2`

Create a file `/root/keycloak-bind.ldif` with the following content:

```ldif
dn: uid=keycloak-bind,cn=sysaccounts,cn=etc,dc=freeipa,dc=local
changetype: add
objectClass: account
objectClass: simplesecurityobject
uid: keycloak-bind
userPassword: <choose-a-strong-password>
passwordExpirationTime: 20380119031407Z
nsIdleTimeout: 0
```

Apply it:

```bash
ldapadd -x -D "cn=Directory Manager" -W -f /root/keycloak-bind.ldif
```

Alternatively, using `ipa-ldap-updater` (preferred on IPA servers):

```bash
# Save the file as /root/keycloak-bind.update then run:
ipa-ldap-updater /root/keycloak-bind.update
```

### 1.4 Export the FreeIPA CA certificate
> **Ansible:** `roles/freeipa_keycloak_prep/tasks/export_ca.yml`

Keycloak needs the FreeIPA CA to trust LDAP connections. The cert is at:

```bash
cat /etc/ipa/ca.crt
```

Copy this file to the Keycloak server (it will be needed in Part 2):

```bash
scp /etc/ipa/ca.crt root@keycloak.local:/tmp/freeipa-ca.crt
```

---

## Part 2 — Keycloak: Initial Setup

Log in to the Keycloak Admin Console at `https://keycloak.local` with the admin
credentials.

### 2.1 Create a new realm
> **Ansible:** `roles/keycloak_saml_federation/tasks/realm.yml`

1. Click the realm drop-down at the top-left (shows **master** by default).
2. Click **Create Realm**.
3. Set **Realm name** to `ipa`.
4. Ensure **Enabled** is toggled on.
5. Click **Create**.

---

## Part 3 — Keycloak: Connect to FreeIPA via LDAP

All steps in this part are performed inside the `ipa` realm.

### 3.1 Add a User Federation provider

1. In the left menu go to **User Federation**.
2. Click **Add provider → ldap**.

### 3.2 Fill in the LDAP settings
> **Ansible:** `roles/keycloak_saml_federation/tasks/ldap_provider.yml`, template: `roles/keycloak_saml_federation/templates/ldap-provider.json.j2`

| Field | Value |
|---|---|
| **UI display name** | `freeipa-ldap` |
| **Vendor** | `Other` |
| **Connection URL** | `ldap://freeipa.local:389` |
| **Enable StartTLS** | Off (use plain LDAP on 389) |
| **Bind type** | `simple` |
| **Bind DN** | `uid=keycloak-bind,cn=sysaccounts,cn=etc,dc=freeipa,dc=local` |
| **Bind credentials** | (the password you set in 1.3) |
| **Edit mode** | `READ_ONLY` |
| **Users DN** | `cn=users,cn=accounts,dc=freeipa,dc=local` |
| **Username LDAP attribute** | `uid` |
| **RDN LDAP attribute** | `uid` |
| **UUID LDAP attribute** | `ipaUniqueID` |
| **User object classes** | `top,person,organizationalPerson,inetOrgPerson` |
| **Search scope** | `Subtree` |
| **Trust email** | On |
| **Import users** | On |
| **Sync registrations** | Off |
| **Batch size for sync** | `1000` |

Click **Test connection**, then **Test authentication** to verify. Click **Save**.

### 3.3 Add LDAP attribute mappers
> **Ansible:** `roles/keycloak_saml_federation/tasks/ldap_mappers.yml`, templates: `roles/keycloak_saml_federation/templates/user-attribute-mapper.json.j2`, `group-ldap-mapper.json.j2`, `full-name-mapper.json.j2`

After saving the provider, go to the **Mappers** tab and add the following mappers
(click **Add mapper** for each). These map LDAP attributes to Keycloak user fields.

**Username mapper**

| Field | Value |
|---|---|
| Name | `username` |
| Mapper type | `user-attribute-ldap-mapper` |
| User model attribute | `username` |
| LDAP attribute | `uid` |
| Always read value from LDAP | Off |
| Read only | On |

**Email mapper**

| Field | Value |
|---|---|
| Name | `email` |
| Mapper type | `user-attribute-ldap-mapper` |
| User model attribute | `email` |
| LDAP attribute | `mail` |
| Read only | On |

**First name mapper**

| Field | Value |
|---|---|
| Name | `firstName` |
| Mapper type | `user-attribute-ldap-mapper` |
| User model attribute | `firstName` |
| LDAP attribute | `givenName` |
| Read only | On |

**Last name mapper**

| Field | Value |
|---|---|
| Name | `lastName` |
| Mapper type | `user-attribute-ldap-mapper` |
| User model attribute | `lastName` |
| LDAP attribute | `sn` |
| Read only | On |

**Groups mapper**

| Field | Value |
|---|---|
| Name | `groups` |
| Mapper type | `group-ldap-mapper` |
| LDAP groups DN | `cn=groups,cn=accounts,dc=freeipa,dc=local` |
| Group name LDAP attribute | `cn` |
| Membership LDAP attribute | `member` |
| Membership attribute type | `DN` |
| Mode | `READ_ONLY` |
| User groups retrieve strategy | `LOAD_GROUPS_BY_MEMBER_ATTRIBUTE` |
| Drop non-existing groups during sync | Off |

### 3.4 Trigger an initial user sync
> **Ansible:** `roles/keycloak_saml_federation/tasks/sync.yml`

On the provider detail page, scroll to the bottom and click **Synchronize all users**.
Confirm that FreeIPA users (e.g. `jemal`) appear under **Users** in the left menu.

---

## Part 4 — Keycloak: Create the SonarQube SAML Client

### 4.1 Create the client
> **Ansible:** `roles/keycloak_saml_federation/tasks/saml_clients.yml`, template: `roles/keycloak_saml_federation/templates/saml-client.json.j2`

1. Go to **Clients → Create client**.
2. Set:
   - **Client type**: `SAML`
   - **Client ID**: `sonarqube`
3. Click **Next**, then **Save**.

### 4.2 Configure client settings

On the **Settings** tab:

| Field | Value |
|---|---|
| **Name** | `sonarqube-saml` |
| **Root URL** | `https://sonar.local` |
| **Home URL** | `https://sonar.local` |
| **Valid redirect URIs** | `https://sonar.local/*` |
| **Master SAML Processing URL** | `https://sonar.local` |
| **IDP-Initiated SSO URL Name** | (leave blank) |

On the **Keys** tab:

| Field | Value |
|---|---|
| **Client signature required** | Off |

On the **Advanced** tab (SAML settings section):

| Field | Value |
|---|---|
| **Sign assertions** | On |
| **Sign documents** | Off |
| **Force POST binding** | On |
| **Include AuthnStatement** | On |
| **Name ID format** | `email` (`urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`) |
| **Assertion Consumer Service POST Binding URL** | `https://sonar.local/oauth2/callback/saml` |

Click **Save**.

### 4.3 Remove default client scopes
> **Ansible:** `roles/keycloak_saml_federation/templates/saml-client.json.j2` — `defaultClientScopes: []` and `optionalClientScopes: []`

SonarQube does not use OpenID Connect scopes. Leaving them attached can inject
extra attributes and cause duplicate-name validation errors.

1. Go to the **Client scopes** tab of the `sonarqube` client.
2. Remove **all** assigned default and optional scopes (select each, click **Remove**).

---

## Part 5 — Keycloak: Configure SAML Protocol Mappers

Still on the `sonarqube` client, go to the **Mappers** tab. Add the following four
mappers one by one.

> **Important**: each mapper must have a unique `Name` AND a unique
> `SAML Attribute Name`. Duplicate attribute names in the SAML assertion will
> cause SonarQube to reject the login with a `ValidationError`.

### 5.1 NameID mapper (maps NameID to user's email)
> **Ansible:** `roles/keycloak_saml_federation/tasks/saml_mappers.yml`, template: `roles/keycloak_saml_federation/templates/saml-nameid-mapper.json.j2`

1. Click **Add mapper → By configuration → User Attribute NameID Mapper**.

| Field | Value |
|---|---|
| **Name** | `nameid` |
| **User attribute** | `email` |
| **NameID format** | `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress` |

### 5.2 Username attribute mapper
> **Ansible:** `roles/keycloak_saml_federation/tasks/saml_mappers.yml`, template: `roles/keycloak_saml_federation/templates/saml-user-property-mapper.json.j2`

1. Click **Add mapper → By configuration → User Property**.

| Field | Value |
|---|---|
| **Name** | `username` |
| **Property** | `username` |
| **SAML Attribute Name** | `username` |
| **Friendly Name** | `username` |
| **SAML Attribute NameFormat** | `Basic` |

### 5.3 Email attribute mapper
> **Ansible:** `roles/keycloak_saml_federation/tasks/saml_mappers.yml`, template: `roles/keycloak_saml_federation/templates/saml-user-property-mapper.json.j2`

1. Click **Add mapper → By configuration → User Property**.

| Field | Value |
|---|---|
| **Name** | `email` |
| **Property** | `email` |
| **SAML Attribute Name** | `email` |
| **Friendly Name** | `email` |
| **SAML Attribute NameFormat** | `Basic` |

### 5.4 Groups mapper
> **Ansible:** `roles/keycloak_saml_federation/tasks/saml_mappers.yml`, template: `roles/keycloak_saml_federation/templates/saml-group-mapper.json.j2`

1. Click **Add mapper → By configuration → Group list**.

| Field | Value |
|---|---|
| **Name** | `groups` |
| **SAML Attribute Name** | `groups` |
| **Friendly Name** | `groups` |
| **SAML Attribute NameFormat** | `Basic` |
| **Single Group Attribute** | On |
| **Full group path** | Off |

---

## Part 6 — Keycloak: Retrieve the Signing Certificate

SonarQube needs Keycloak's signing certificate to verify SAML assertions.

### 6.1 Get the certificate from the IdP metadata URL
> **Ansible:** `roles/sonarqube_saml_config/tasks/retrieve_cert.yml`

Open in a browser (or curl):

```
https://keycloak.local/realms/ipa/protocol/saml/descriptor
```

Find the `<ds:X509Certificate>` element and copy the base64 content (a long single
line, everything between the tags — no line breaks).

### 6.2 Alternative: export via Admin Console

1. Go to **Realm Settings → Keys**.
2. Find the `RS256` key entry.
3. Click **Certificate** to see the PEM. Strip the `-----BEGIN/END CERTIFICATE-----`
   headers and join all lines into one continuous base64 string.

---

## Part 7 — SonarQube: Configure SAML Authentication

SAML settings are written into `sonar.properties`. The file is located at:

```
<sonarqube-home>/conf/sonar.properties
```

(e.g. `/opt/sonarqube-10.3.0.82913/conf/sonar.properties`)

### 7.1 SSH into the SonarQube server

```bash
ssh root@sonar.local
```

### 7.2 Back up sonar.properties

```bash
cp /opt/sonarqube-10.3.0.82913/conf/sonar.properties \
   /opt/sonarqube-10.3.0.82913/conf/sonar.properties.bak
```

### 7.3 Set the server base URL

Ensure this line is present (required so the ACS URL in SAMLRequests is correct):

```properties
sonar.core.serverBaseURL=https://sonar.local
```

### 7.4 Add the SAML configuration block
> **Ansible:** `roles/sonarqube_saml_config/tasks/configure_saml.yml`

Append the following lines to `sonar.properties`:

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
sonar.auth.saml.certificate.secured=<paste single-line base64 cert from Part 6>
```

> `sonar.auth.saml.certificate.secured` must be a single continuous base64 string
> with no spaces or newlines.

### 7.5 Restart SonarQube

```bash
systemctl restart sonarqube
# or if running as a service user:
sudo -u sonarqube /opt/sonarqube-10.3.0.82913/bin/linux-x86-64/sonar.sh restart
```

Wait until SonarQube is fully started (check `logs/sonarqube.log`).

---

## Part 8 — Verify the Integration

### 8.1 Confirm SonarQube shows the SSO button

Open `https://sonar.local` in a browser. The login page should show a button
labelled **Log in with FreeIPA via Keycloak** in addition to the local login form.

### 8.2 Test login with a FreeIPA user

1. Click the SSO button.
2. You are redirected to `https://keycloak.local`.
3. Enter FreeIPA credentials (e.g. `jemal` / password).
4. Keycloak verifies credentials against FreeIPA LDAP and redirects back to SonarQube.
5. SonarQube creates the user on first login and grants access.

### 8.3 Check SonarQube logs if login fails

```bash
tail -f /opt/sonarqube-10.3.0.82913/logs/web.log
```

Common errors and their causes:

| Error message | Cause | Fix |
|---|---|---|
| `username is missing` | `username` SAML attribute not sent | Check mapper in Part 5.2; ensure `Property=username` and `SAML Attribute Name=username` |
| `Found an Attribute element with duplicated Name` | Two mappers share the same SAML attribute name | Remove duplicate mappers; ensure every mapper has a unique `SAML Attribute Name` |
| `already associated with another authentication method` | User was created locally in SonarQube before first SAML login | Anonymize the user via Admin → Users → anonymize, then log in again via SSO |
| `You're not authorized to access this page` | Usually caused by one of the above errors being caught upstream | Check `web.log` for the underlying `ValidationError` or `NullPointerException` |

---

## Key Attribute Mapping Summary

```
FreeIPA LDAP          Keycloak user model       SAML assertion         SonarQube property
──────────────────────────────────────────────────────────────────────────────────────────
uid              →    username            →     username          →    sonar.auth.saml.user.login
uid              →    username            →     username          →    sonar.auth.saml.user.name
mail             →    email               →     email             →    sonar.auth.saml.user.email
mail             →    email               →     NameID (emailAddr)→    (used for SAML session)
cn (group)       →    Keycloak group      →     groups            →    sonar.auth.saml.group.name
```

---

## Notes

- Use plain LDAP (`ldap://` port 389) unless you have a trusted CA for LDAPS.
  If you enable LDAPS, import the FreeIPA CA into Keycloak's JKS truststore using
  `keytool -importcert` and configure `spi-truststore-file-*` in `keycloak.conf`.
- Do **not** pre-create SonarQube users that will log in via SAML. If a user exists
  locally without `externalIdentityProvider=saml`, the SAML login will fail with
  an identity conflict.
- The Keycloak `role_list` default scope must not be assigned to the SonarQube
  SAML client. It injects a `Role` attribute that conflicts with the `groups` mapper.
- SonarQube requires the signing certificate as a single-line base64 string — not
  PEM-formatted with line breaks.
