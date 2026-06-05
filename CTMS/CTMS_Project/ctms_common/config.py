from configparser import ConfigParser
from pathlib import Path


def load_config(config_path: str | None = None) -> ConfigParser:
    parser = ConfigParser()
    parser.read(Path(config_path or "config/services.ini"), encoding="utf-8")
    return parser
