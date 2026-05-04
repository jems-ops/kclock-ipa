.PHONY: help deploy prep keycloak validate jenkins sonar artifactory nessus wazuh atlassian-rollback logs clean

help:
	@echo "SSO CLI Makefile"
	@echo "-------------------------"
	@echo "make deploy      - Full deployment"
	@echo "make prep        - Prepare FreeIPA"
	@echo "make keycloak    - Configure Keycloak"
	@echo "make validate    - Run validation"
	@echo "make jenkins     - Onboard Jenkins"
	@echo "make sonar       - Onboard SonarQube"
	@echo "make artifactory - Onboard Artifactory"
	@echo "make nessus      - Onboard Nessus"
	@echo "make wazuh       - Onboard Wazuh"
	@echo "make atlassian-rollback - Rollback Atlassian SAML"
	@echo "make logs        - Tail CLI logs"
	@echo "make clean       - Cleanup temp/logs"

deploy:
	sso-cli deploy

prep:
	sso-cli prep

keycloak:
	sso-cli keycloak

validate:
	sso-cli validate

jenkins:
	sso-cli onboard-app jenkins

sonar:
	sso-cli onboard-app sonar

artifactory:
	sso-cli onboard-app artifactory

nessus:
	sso-cli onboard-app nessus

wazuh:
	sso-cli onboard-app wazuh

atlassian-rollback:
	sso-cli atlassian-rollback

validate-local:
	sso-cli validate-local

validate-dns:
	sso-cli validate-dns

validate-sso:
	sso-cli validate-sso

test-login:
	sso-cli test-login

logs:
	tail -f sso-cli.log

clean:
	rm -f sso-cli.log
