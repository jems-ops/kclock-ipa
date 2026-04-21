.PHONY: help lint freeipa-prep keycloak-config sonarqube-saml jenkins-saml site \
        vault-encrypt vault-edit vault-view check

INVENTORY   := inventory
VAULT_FILE  := group_vars/all/vault.yml

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Playbook targets:"
	@echo "  site            Run the full site playbook (all three steps)"
	@echo "  freeipa-prep    Prepare FreeIPA bind account and export CA"
	@echo "  keycloak-config Configure Keycloak realm, LDAP federation, SAML clients"
	@echo "  sonarqube-saml  Push SAML config to SonarQube via API"
	@echo "  jenkins-saml    Push SAML config to Jenkins (config.xml template + restart)"
	@echo ""
	@echo "Check / lint:"
	@echo "  check           Dry-run the full site playbook"
	@echo "  lint            Run ansible-lint"
	@echo ""
	@echo "Vault:"
	@echo "  vault-encrypt   Encrypt the vault file"
	@echo "  vault-edit      Edit the encrypted vault file"
	@echo "  vault-view      View the encrypted vault file"

site:
	ansible-playbook -i $(INVENTORY) playbooks/site.yml

freeipa-prep:
	ansible-playbook -i $(INVENTORY) playbooks/freeipa_prep.yml

keycloak-config:
	ansible-playbook -i $(INVENTORY) playbooks/keycloak_config.yml

sonarqube-saml:
	ansible-playbook -i $(INVENTORY) playbooks/sonarqube_saml.yml

jenkins-saml:
	ansible-playbook -i $(INVENTORY) playbooks/jenkins_saml.yml

check:
	ansible-playbook -i $(INVENTORY) playbooks/site.yml --check

lint:
	ansible-lint

vault-encrypt:
	ansible-vault encrypt $(VAULT_FILE)

vault-edit:
	ansible-vault edit $(VAULT_FILE)

vault-view:
	ansible-vault view $(VAULT_FILE)
