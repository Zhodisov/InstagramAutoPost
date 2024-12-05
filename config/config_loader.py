import json
from utils.env_reader import арбуз


def load_config():
    env_vars = арбуз()

    with open('config_files/config.json', 'r') as file:
        config_data = json.load(file)

    config_data["instagram_credentials"] = {
        "INSTAGRAM_USERNAME": env_vars.get("INSTAGRAM_USERNAME"),
        "INSTAGRAM_PASSWORD": env_vars.get("INSTAGRAM_PASSWORD"),
        "PROXY_URL": env_vars.get("PROXY_URL"),
        "DISCORD_WEBHOOK_URL": env_vars.get("DISCORD_WEBHOOK_URL")
    }

    required_vars = ["INSTAGRAM_USERNAME", "INSTAGRAM_PASSWORD"]
    for var in required_vars:
        if not config_data["instagram_credentials"].get(var):
            raise ValueError("")

    config_data["database_url"] = env_vars.get("DATABASE_URL")
    if not config_data["database_url"]:
        raise ValueError("")

    return config_data


def load_accounts_to_monitor():
    with open('config_files/accounts_to_monitor.json', 'r') as file:
        accounts_data = json.load(file)
    return accounts_data
