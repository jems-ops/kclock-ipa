# Application Deployment Makefile
# Usage: cd deploy && make <target>
.PHONY: help deploy-all deploy-cicd deploy-monitoring deploy-security deploy-identity \
        jenkins sonarqube keycloak nexus grafana prometheus wazuh tenable freeipa-prep \
        nginx-proxy test-connection validate

CYAN := \\033[36m
GREEN := \\033[32m
YELLOW := \\033[33m
RED := \\033[31m
RESET := \\033[0m

.DEFAULT_GOAL := help
SHELL := /bin/bash

help: ## Show available commands
	@echo "$(CYAN)Application Deployment - Available Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-25s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Full Deployment
deploy-all: ## Deploy all apps + nginx reverse proxy + SSL
	@echo "$(CYAN)Deploying all applications...$(RESET)"
	@ansible-playbook site.yml
	@echo "$(GREEN)All applications deployed!$(RESET)"

##@ Group Deployments
deploy-identity: ## Deploy FreeIPA + Keycloak
	@echo "$(CYAN)Deploying identity stack...$(RESET)"
	@ansible-playbook site.yml --tags identity
	@echo "$(GREEN)Identity stack deployed!$(RESET)"

deploy-cicd: ## Deploy Jenkins + SonarQube + Nexus
	@echo "$(CYAN)Deploying CI/CD stack...$(RESET)"
	@ansible-playbook site.yml --tags cicd
	@echo "$(GREEN)CI/CD stack deployed!$(RESET)"

deploy-monitoring: ## Deploy Grafana + Prometheus
	@echo "$(CYAN)Deploying monitoring stack...$(RESET)"
	@ansible-playbook site.yml --tags monitoring
	@echo "$(GREEN)Monitoring stack deployed!$(RESET)"

deploy-security: ## Deploy Wazuh + Tenable Security Center
	@echo "$(CYAN)Deploying security stack...$(RESET)"
	@ansible-playbook site.yml --tags security
	@echo "$(GREEN)Security stack deployed!$(RESET)"

##@ Individual Applications
jenkins: ## Install Jenkins
	@echo "$(CYAN)Installing Jenkins...$(RESET)"
	@ansible-playbook jenkins.yml
	@echo "$(GREEN)Jenkins installed!$(RESET)"

sonarqube: ## Install SonarQube
	@echo "$(CYAN)Installing SonarQube...$(RESET)"
	@ansible-playbook sonarqube.yml
	@echo "$(GREEN)SonarQube installed!$(RESET)"

keycloak: ## Install Keycloak
	@echo "$(CYAN)Installing Keycloak...$(RESET)"
	@ansible-playbook keycloak.yml
	@echo "$(GREEN)Keycloak installed!$(RESET)"

nexus: ## Install Nexus Repository Manager
	@echo "$(CYAN)Installing Nexus...$(RESET)"
	@ansible-playbook nexus.yml
	@echo "$(GREEN)Nexus installed!$(RESET)"

grafana: ## Install Grafana
	@echo "$(CYAN)Installing Grafana...$(RESET)"
	@ansible-playbook grafana.yml
	@echo "$(GREEN)Grafana installed!$(RESET)"

prometheus: ## Install Prometheus
	@echo "$(CYAN)Installing Prometheus...$(RESET)"
	@ansible-playbook prometheus.yml
	@echo "$(GREEN)Prometheus installed!$(RESET)"

wazuh: ## Install Wazuh
	@echo "$(CYAN)Installing Wazuh...$(RESET)"
	@ansible-playbook wazuh.yml
	@echo "$(GREEN)Wazuh installed!$(RESET)"

tenable: ## Install Tenable Security Center
	@echo "$(CYAN)Installing Tenable Security Center...$(RESET)"
	@ansible-playbook tenable.yml
	@echo "$(GREEN)Tenable Security Center installed!$(RESET)"

freeipa-prep: ## Prepare FreeIPA for Keycloak federation
	@echo "$(CYAN)Preparing FreeIPA...$(RESET)"
	@ansible-playbook freeipa-prep.yml
	@echo "$(GREEN)FreeIPA prepared!$(RESET)"

##@ Nginx Reverse Proxy
nginx-proxy: ## Install nginx + reverse proxy + SSL for all backends
	@echo "$(CYAN)Deploying nginx reverse proxy with SSL...$(RESET)"
	@ansible-playbook nginx-proxy.yml
	@echo "$(GREEN)Nginx reverse proxy configured!$(RESET)"

##@ Monitoring
monitoring-agents: ## Deploy node_exporter to all application servers
	@echo "$(CYAN)Deploying monitoring agents...$(RESET)"
	@ansible-playbook monitoring-agents.yml
	@echo "$(GREEN)Monitoring agents deployed!$(RESET)"

##@ SSO Onboarding
sso-onboard-all: ## Run full SSO onboarding (prep + all apps + validation)
	@echo "$(CYAN)Running SSO onboarding for all apps...$(RESET)"
	@ansible-playbook -i ../platform/identity/inventory ../platform/identity/ansible/playbooks/sso_onboarding.yml
	@echo "$(GREEN)SSO onboarding complete!$(RESET)"

sso-onboard: ## Onboard a single app to SSO (usage: make sso-onboard APP=grafana)
	@echo "$(CYAN)Running SSO onboarding for $(APP)...$(RESET)"
	@ansible-playbook -i ../platform/identity/inventory ../platform/identity/ansible/playbooks/sso_onboarding.yml --tags $(APP)
	@echo "$(GREEN)SSO onboarding for $(APP) complete!$(RESET)"

sso-onboard-full: ## Full onboard: prep + single app (usage: make sso-onboard-full APP=grafana)
	@echo "$(CYAN)Running full SSO onboarding (with prep) for $(APP)...$(RESET)"
	@ansible-playbook -i ../platform/identity/inventory ../platform/identity/ansible/playbooks/sso_onboarding.yml --tags prep,$(APP),validate
	@echo "$(GREEN)Full SSO onboarding for $(APP) complete!$(RESET)"

##@ Testing
test-connection: ## Test connectivity to all servers
	@echo "$(CYAN)Testing connection to all servers...$(RESET)"
	@ansible all -m ping

validate: ## Validate all playbook syntax
	@echo "$(CYAN)Validating playbook syntax...$(RESET)"
	@for f in *.yml; do \
		echo "  Checking $$f..."; \
		ansible-playbook --syntax-check "$$f" || exit $$?; \
	done
	@echo "$(GREEN)All playbooks valid!$(RESET)"
