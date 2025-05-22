import yaml
from pathlib import Path
import os

def load_config():
    CONFIG_PATH = Path(os.getcwd()) / "config.yaml"
    if "QUORRA_CONFIG" in os.environ:
        CONFIG_PATH = Path(os.environ["QUORRA_CONFIG"])

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                config = yaml.safe_load(config_file)
        except yaml.YAMLError as exc:
            print("Configuration error: {}".format(exc))
            exit(1)
        else:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                config = yaml.safe_load(config_file)
    else:
        print("Config file not found!")
        print("Using defaults")
        config = {"server": {"address": "http://localhost:8080"}, "oidc": {"clients": []}}

    # Default path is None
    if "path" not in config["server"]:
        config["server"]["path"] = None
    return config

config = load_config()
server_url = config["server"]["address"]
