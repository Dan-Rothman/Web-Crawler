import logging
from pathlib import Path
from typing import Any
import yaml

logger = logging.getLogger(__name__)

class config:

    config_obj: dict[str, Any]
    exluded_extentions: frozenset[str]
    search_words: frozenset[str]
    other_homes: frozenset[str]
    home: str
    depth: int
    

    def __init__(self):
        self.config_obj = self.load_config("config.yml")
        logger.debug("Config loaded: %s", self.config_obj)
        self.excluded_extentions = self.get_excluded_extensions(self.config_obj)
        logger.debug("Extentions excluded: %s", self.excluded_extentions)
        self.search_words = self.get_search_words(self.config_obj)
        logger.debug("Search words: %s", self.search_words)
        self.home = self.config_obj["Home_URL"]
        logger.debug("Home URL: %s", self.home)
        self.otherHomes = self.get_other_homes(self.config_obj)
        logger.debug("Other homes: %s", self.otherHomes)
        self.depth = self.config_obj["Maximum_Depth"]
        logger.debug("Maxmimum Depth: %s", self.depth)

    def load_config(self, config_path : str | Path) -> dict[str, Any]:
        path = Path(config_path)

        if not path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with path.open("r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)

        if not isinstance(config, dict):
            raise ValueError("The configuration file must contain a YAML mapping.")

        return config

    def get_other_homes(self, config: dict[str, Any]) -> frozenset[str]:
        try:
            other_homes = config["Other_Homes"]
        except:
            return None

        if not isinstance(other_homes, list):
            raise ValueError(
                "Other_Homes must be a YAML list."
            )

        return frozenset(other_homes)

    def get_search_words(self, config: dict[str, Any]) -> frozenset[str]:
        try:
            configured_words = config["Search_Words"]
        except:
            return None

        if not isinstance(configured_words, list):
            raise ValueError(
                "Search_Words must be a YAML list."
            )
        normalized_words = set()

        for word in configured_words:
            if not isinstance(word, str):
                raise ValueError(
                    "Every word must be a string."
                )

            word = word.strip().lower()

            normalized_words.add(word)

        return frozenset(normalized_words)

    def get_excluded_extensions(self, config: dict[str, Any]) -> frozenset[str]:
        try:
            configured_extensions = config["Excluded_Extensions"]
        except:
            return None

        if not isinstance(configured_extensions, list):
            raise ValueError(
                "Excluded_Extensions must be a YAML list."
            )
        normalized_extensions = set()

        for extension in configured_extensions:
            if not isinstance(extension, str):
                raise ValueError(
                    "Every excluded extension must be a string."
                )

            extension = extension.strip().lower()

            if not extension.startswith("."):
                extension = f".{extension}"

            normalized_extensions.add(extension)

        return frozenset(normalized_extensions)