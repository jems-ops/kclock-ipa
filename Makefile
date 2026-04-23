.PHONY: help lint check site freeipa-prep keycloak-config sonarqube-saml jenkins-saml saml-apps \
        vault-encrypt vault-edit vault-view

INVENTORY  := inventory
PLAYBOOK   := playbooks/site.yml
VAULT_FILE := group_vars/all/vault.yml

ANSIBLE    := ansible-playbook -i $(INVENTORY) $(PLAYBOOK)

# Optional knobs:
#   make <target> LIMIT=jenkins.local     narrow the run to a single host
#   make site     TAGS=keycloak_config    pass tags directly to site
LIMIT ?=
TAGS  ?=
LIMIT_ARG := $(if $(LIMIT),--limit $(LIMIT),)
TAGS_ARG  := $(if $(TAGS),--tags $(TAGS),)

help:
	@echo "Usage: make <target> [LIMIT=host] [TAGS=tag,tag]"
	@echo ""
	@echo "Playbook targets (all drive playbooks/site.yml with tags):"
	@echo "  site             Run every play                            (no tag filter)"
	@echo "  freeipa-prep     Tag: freeipa_prep    FreeIPA bind account + CA export"
	@echo "  keycloak-config  Tag: keycloak_config Keycloak realm, LDAP fed, SAML clients"
	@echo "  sonarqube-saml   Tag: sonarqube_saml  SonarQube SAML settings"
	@echo "  jenkins-saml     Tag: jenkins_saml    Jenkins SAML config.xml"
	@echo "  saml-apps        Tag: saml_sp         All SAML SPs (SonarQube + Jenkins)"
	@echo ""
	@echo "Check / lint:"
	@echo "  check            Dry-run site.yml"
	@echo "  lint             Run ansible-lint"
	@echo ""
	@echo "Vault:"
	@echo "  vault-encrypt    Encrypt the vault file"
	@echo "  vault-edit       Edit the encrypted vault file"
	@echo "  vault-view       View the encrypted vault file"
	@echo ""
	@echo "Examples:"
	@echo "  make site"
	@echo "  make keycloak-config"
	@echo "  make saml-apps LIMIT=sonar.local"
	@echo "  make site TAGS=keycloak_config,sonarqube_saml LIMIT=keycloak.local"

site:
	$(ANSIBLE) $(TAGS_ARG) $(LIMIT_ARG)

freeipa-prep:
	$(ANSIBLE) --tags freeipa_prep $(LIMIT_ARG)

keycloak-config:
	$(ANSIBLE) --tags keycloak_config $(LIMIT_ARG)

sonarqube-saml:
	$(ANSIBLE) --tags sonarqube_saml $(LIMIT_ARG)

jenkins-saml:
	$(ANSIBLE) --tags jenkins_saml $(LIMIT_ARG)

saml-apps:
	$(ANSIBLE) --tags saml_sp $(LIMIT_ARG)

check:
	$(ANSIBLE) --check $(TAGS_ARG) $(LIMIT_ARG)

lint:
	ansible-lint

vault-encrypt:
	ansible-vault encrypt $(VAULT_FILE)

vault-edit:
	ansible-vault edit $(VAULT_FILE)

vault-view:
	ansible-vault view $(VAULT_FILE)
