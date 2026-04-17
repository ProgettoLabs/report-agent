from pathlib import Path

import yaml


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    return yaml.safe_load(config_path.read_text())


PIPELINE_DIR: Path = (
    Path(__file__).parent.parent / load_config()["use_case_dir"]
).resolve()
