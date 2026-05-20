import os

ENVIRONMENTS = {
    "dev": "inventory/dev",
    "prod": "inventory/prod",
    "lab": "inventory"
}

def get_inventory(env):
    return ENVIRONMENTS.get(env, "inventory")
