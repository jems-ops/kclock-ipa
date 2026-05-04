import click
import subprocess
import os
import logging

# -------------------------
# Setup paths
# -------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLAYBOOK_DIR = os.path.join(BASE_DIR, "playbooks")

ENVIRONMENTS = {
    "dev": "inventory/dev",
    "prod": "inventory/prod",
    "lab": "inventory"
}

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    filename="sso-cli.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------
# Helpers
# -------------------------
def get_inventory(env):
    return ENVIRONMENTS.get(env, "inventory")


def run_playbook(playbook, env="lab", extra_vars=None):
    inventory = get_inventory(env)

    cmd = [
        "ansible-playbook",
        "-i", inventory,
        os.path.join(PLAYBOOK_DIR, playbook)
    ]

    if extra_vars:
        cmd.extend(["-e", extra_vars])

    logging.info(f"Running command: {' '.join(cmd)}")
    click.echo(f"\n[INFO] Running: {' '.join(cmd)}\n")

    subprocess.run(cmd, check=True)


# -------------------------
# CLI ROOT
# -------------------------
@click.group()
def cli():
    """SSO CLI - Keycloak + FreeIPA Automation"""
    pass


# -------------------------
# DEPLOY
# -------------------------
@cli.command()
@click.option("--env", default="lab", help="Environment (dev/prod/lab)")
def deploy(env):
    """Full deployment"""
    run_playbook("site.yml", env)


# -------------------------
# PREP
# -------------------------
@cli.command()
@click.option("--env", default="lab")
def prep(env):
    """Prepare FreeIPA"""
    run_playbook("freeipa_prep.yml", env)


# -------------------------
# KEYCLOAK
# -------------------------
@cli.command()
@click.option("--env", default="lab")
def keycloak(env):
    """Configure Keycloak"""
    run_playbook("keycloak_config.yml", env)


# -------------------------
# VALIDATION
# -------------------------
@cli.command()
@click.option("--env", default="lab")
def validate(env):
    """Run validation checks"""
    run_playbook("validation.yml", env)

@cli.command(name="validate-local")
@click.option("--env", default="lab")
def validate_local(env):
    """Local service validation"""
    run_playbook("validation_local.yml", env)


@cli.command(name="validate-dns")
@click.option("--env", default="lab")
def validate_dns(env):
    """DNS / SSO path validation"""
    run_playbook("validation_dns.yml", env)

@cli.command(name="validate-sso")
@click.option("--env", default="lab")
def validate_sso(env):
    """Validate SSO login flow (Keycloak → Jenkins)"""
    run_playbook("validation_sso.yml", env)


@cli.command(name="test-login")
def test_login():
    """Run Playwright SSO login test"""
    subprocess.run(["python", "sso_cli/tests/test_sso_login.py"])


# -------------------------
# ONBOARD APP
# -------------------------
@cli.command()
@click.argument("app")
@click.option("--env", default="lab")
def onboard_app(app, env):
    """Onboard SAML apps dynamically"""

    playbook_map = {
        "jenkins":    "jenkins_saml.yml",
        "sonar":      "sonarqube_saml.yml",
        "jira":       "jira_saml.yml",
        "confluence": "confluence_saml.yml",
        "bitbucket":  "bitbucket_saml.yml",
        "nessus":     "nessus_saml.yml",
        "artifactory": "artifactory_saml.yml",
        "wazuh":      "wazuh_saml.yml",
    }

    playbook = playbook_map.get(app)

    if not playbook:
        click.echo(f"[ERROR] No playbook mapped for app: {app}")
        return

    run_playbook(playbook, env)


# -------------------------
# DEBUG
# -------------------------
@cli.command()
@click.argument("service")
def debug(service):
    """Debug services logs"""

    logs = {
        "keycloak": "journalctl -u keycloak -n 50",
        "nginx": "journalctl -u nginx -n 50",
        "sonar": "journalctl -u sonarqube -n 50",
        "freeipa": "journalctl -u ipa -n 50"
    }

    cmd = logs.get(service)

    if not cmd:
        click.echo("[ERROR] Unknown service")
        return

    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    cli()
