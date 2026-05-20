"""
Async Ansible playbook runner.

Executes playbooks in background threads and updates OnboardingJob status
via the DB. Called by the onboarding API router.
"""
import os
import subprocess
import threading
import logging
from pathlib import Path

from db.base import SessionLocal
from models.onboarding_job import JobStatus
import services

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
# Resolve paths relative to the repository root (three levels up from backend/).
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent.parent
IDENTITY_ANSIBLE_DIR = _REPO_ROOT / "platform" / "identity" / "ansible"
IDENTITY_PLAYBOOKS_DIR = IDENTITY_ANSIBLE_DIR / "playbooks"
IDENTITY_INVENTORY = _REPO_ROOT / "platform" / "identity" / "inventory"
IDENTITY_CFG = IDENTITY_ANSIBLE_DIR / "ansible.cfg"
DEPLOY_DIR = _REPO_ROOT / "deploy"
DEPLOY_INVENTORY = DEPLOY_DIR / "inventory"
DEPLOY_CFG = DEPLOY_DIR / "ansible.cfg"

# Map app IDs to the Ansible tag used in sso_onboarding.yml
APP_TAG_MAP = {
    "jenkins":     "jenkins",
    "sonar":       "sonarqube",
    "jira":        "jira",
    "confluence":  "confluence",
    "bitbucket":   "bitbucket",
    "nessus":      "nessus",
    "artifactory": "artifactory",
    "grafana":     "grafana",
    "wazuh":       "wazuh",
}

# Map app IDs directly to their individual playbook files
APP_PLAYBOOK_MAP = {
    "jenkins":     "jenkins_saml.yml",
    "sonar":       "sonarqube_saml.yml",
    "jira":        "jira_saml.yml",
    "confluence":  "confluence_saml.yml",
    "bitbucket":   "bitbucket_saml.yml",
    "nessus":      "nessus_saml.yml",
    "artifactory": "artifactory_saml.yml",
    "grafana":     "grafana_oidc.yml",
    "prometheus":  "prometheus_oidc.yml",
}


def _run_playbook(playbook: str, inventory: str, tags: list[str] | None = None,
                  extra_vars: dict | None = None, timeout: int = 600) -> tuple[int, str]:
    """
    Run an ansible-playbook command and return (returncode, combined stdout+stderr).
    """
    cmd = [
        "ansible-playbook",
        "-i", str(inventory),
        str(playbook),
    ]
    if tags:
        cmd += ["--tags", ",".join(tags)]
    if extra_vars:
        import json
        cmd += ["--extra-vars", json.dumps(extra_vars)]

    env = os.environ.copy()
    env["ANSIBLE_FORCE_COLOR"] = "false"
    env["ANSIBLE_NOCOLOR"] = "true"

    # Point Ansible at the correct config file for this playbook
    playbook_path = Path(playbook).resolve()
    if str(IDENTITY_PLAYBOOKS_DIR) in str(playbook_path):
        env["ANSIBLE_CONFIG"] = str(IDENTITY_CFG)
    elif str(DEPLOY_DIR) in str(playbook_path):
        env["ANSIBLE_CONFIG"] = str(DEPLOY_CFG)

    # Run from the playbook's parent directory so Ansible picks up ansible.cfg
    cwd = str(Path(playbook).resolve().parent)
    logger.info("Running: %s (cwd=%s)", " ".join(cmd), cwd)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=cwd,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return 1, f"Playbook timed out after {timeout}s"
    except Exception as e:
        return 1, f"Failed to execute playbook: {e}"


def run_sso_onboarding(job_id: str, app_id: str, include_prep: bool = False):
    """
    Run the individual app SSO playbook in a background thread.
    Uses the app-specific playbook directly to avoid running unrelated plays.
    """
    def _worker():
        db = SessionLocal()
        try:
            services.update_onboarding_job(db, job_id, JobStatus.running)

            playbook_name = APP_PLAYBOOK_MAP.get(app_id)
            if not playbook_name:
                services.update_onboarding_job(
                    db, job_id, JobStatus.failed,
                    error=f"No playbook mapped for app '{app_id}'")
                return

            playbook = IDENTITY_PLAYBOOKS_DIR / playbook_name
            rc, output = _run_playbook(
                playbook=playbook,
                inventory=IDENTITY_INVENTORY,
            )

            if rc == 0:
                services.update_onboarding_job(
                    db, job_id, JobStatus.succeeded, log_output=output)
            else:
                services.update_onboarding_job(
                    db, job_id, JobStatus.failed, log_output=output,
                    error=f"Playbook exited with code {rc}")
        except Exception as e:
            logger.exception("Onboarding job %s failed", job_id)
            services.update_onboarding_job(db, job_id, JobStatus.failed, error=str(e))
        finally:
            db.close()

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def run_monitoring_agents(job_id: str):
    """
    Run the monitoring-agents playbook in a background thread.
    """
    def _worker():
        db = SessionLocal()
        try:
            services.update_onboarding_job(db, job_id, JobStatus.running)

            rc, output = _run_playbook(
                playbook=DEPLOY_DIR / "monitoring-agents.yml",
                inventory=DEPLOY_INVENTORY,
            )

            status = JobStatus.succeeded if rc == 0 else JobStatus.failed
            error = f"Playbook exited with code {rc}" if rc != 0 else None
            services.update_onboarding_job(
                db, job_id, status, log_output=output, error=error)
        except Exception as e:
            logger.exception("Monitoring agents job %s failed", job_id)
            services.update_onboarding_job(
                db, job_id, JobStatus.failed, error=str(e))
        finally:
            db.close()

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


# Tag map for federation job types
_FED_TAG_MAP = {
    "full_federation": ["freeipa_prep", "ldap"],
    "freeipa_prep":    ["freeipa_prep"],
    "ldap_only":       ["ldap"],
    "user_sync":       ["ldap"],
}


def run_federation(job_id: str, job_type):
    """Run the LDAP federation playbook in a background thread."""
    from models.ldap_federation_job import LdapFederationJob, FedJobStatus

    def _worker():
        db = SessionLocal()
        try:
            job = db.get(LdapFederationJob, job_id)
            if not job:
                return
            job.status = FedJobStatus.running
            from datetime import datetime, timezone
            job.started_at = datetime.now(timezone.utc)
            db.commit()

            tags = _FED_TAG_MAP.get(str(job_type).split(".")[-1], ["ldap"])
            playbook = IDENTITY_PLAYBOOKS_DIR / "configure-keycloak-ldap-federation.yml"

            rc, output = _run_playbook(
                playbook=playbook,
                inventory=IDENTITY_INVENTORY,
                tags=tags,
            )

            job.status = FedJobStatus.succeeded if rc == 0 else FedJobStatus.failed
            job.log_output = output
            job.error = f"Playbook exited with code {rc}" if rc != 0 else None
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as e:
            logger.exception("Federation job %s failed", job_id)
            job = db.get(LdapFederationJob, job_id)
            if job:
                job.status = FedJobStatus.failed
                job.error = str(e)
                db.commit()
        finally:
            db.close()

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
