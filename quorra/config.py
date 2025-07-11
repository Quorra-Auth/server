import yaml
from pathlib import Path
import os
from deepmerge import always_merger

def load_config():
    default_config: dict = {}
    loaded_config: dict = {}
    CONFIG_PATH: Path = Path(os.getcwd()) / "config.yaml"
    if "QUORRA_CONFIG" in os.environ:
        CONFIG_PATH = Path(os.environ["QUORRA_CONFIG"])

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                yaml.safe_load(config_file)
        except yaml.YAMLError as exc:
            print("Configuration error: {}".format(exc))
            exit(1)
        else:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                loaded_config = yaml.safe_load(config_file)
    else:
        print("Config file not found!")
        print("Using defaults")
    default_config["server"] = {"address": "http://localhost:8080", "registrations": False}
    default_config["oidc"] = {"clients": []}
    default_config["database"] = {}
    default_config["database"]["sql"] = {"string": "sqlite:///database.db"}
    default_config["database"]["valkey"] = {"host": "localhost", "port": 6379, "db": 0}
    always_merger.merge(default_config, loaded_config)

    # Default path is None
    if "path" not in default_config["server"]:
        default_config["server"]["path"] = None
    return default_config


def determine_server_url(config: dict) -> str:
    server_url = config["server"]["address"]
    if config["server"]["path"] is not None:
        server_url = server_url + config["server"]["path"]
    return server_url


config: dict = load_config()
server_url: str = determine_server_url(config)
oidc_clients: list = config["oidc"]["clients"]
