"""Run once to seed default apps: python seed.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from db.base import Base, engine, SessionLocal
from models import App
import models  # register all models

Base.metadata.create_all(bind=engine)

APPS = [
    dict(id="jenkins",     name="Jenkins",     base_url="https://jenkins.local",     host_group="jenkins_servers",     service_name="jenkins",        saml_client_id="jenkins",                  enabled=True),
    dict(id="sonar",       name="SonarQube",   base_url="https://sonar.local",       host_group="sonarqube_servers",   service_name="sonarqube",      saml_client_id="sonarqube",                enabled=True),
    dict(id="jira",        name="Jira",        base_url="https://jira.local",        host_group="jira",                service_name="jira",           saml_client_id="https://jira.local",       enabled=True),
    dict(id="confluence",  name="Confluence",  base_url="https://confluence.local",  host_group="confluence",          service_name="confluence",     saml_client_id="https://confluence.local", enabled=True),
    dict(id="bitbucket",   name="Bitbucket",   base_url="https://bitbucket.local",   host_group="bitbucket",           service_name="bitbucket",      saml_client_id="https://bitbucket.local",  enabled=True),
    dict(id="nessus",      name="Nessus",      base_url="https://nessus.local",      host_group="nessus",              service_name="nessus",         saml_client_id="https://tenable.sc",       enabled=True),
    dict(id="artifactory", name="Artifactory", base_url="https://artifactory.local", host_group="artifactory_servers", service_name="artifactory",    saml_client_id="https://artifactory.local",enabled=True),
    dict(id="grafana",     name="Grafana",     base_url="https://grafana.local",     host_group="monitoring_servers",  service_name="grafana-server", saml_client_id="grafana",                  enabled=False),
    dict(id="prometheus",  name="Prometheus",  base_url="https://prometheus.local",  host_group="monitoring_servers",  service_name="prometheus",     saml_client_id="prometheus",               enabled=False),
]

db = SessionLocal()
added = 0
for a in APPS:
    if not db.get(App, a["id"]):
        db.add(App(**a))
        added += 1
db.commit()
db.close()
print(f"Seeded {added} apps ({len(APPS) - added} already existed).")
