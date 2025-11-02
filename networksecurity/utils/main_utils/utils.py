"""
YAML helpers that always resolve paths relative to the project root
(the folder that contains main.py), so you never get
  FileNotFoundError: [Errno 2] No such file or directory: data_schema\\schema.yaml
again.
"""
import os
import sys
from pathlib import Path
import yaml
from networksecurity.exception.exception import NetworkSecurityException

# ------------------------------------------------------------------
# private helper – project root (where main.py lives)
# ------------------------------------------------------------------
def _project_root() -> Path:
    """
    This file is assumed to live in
      <root>/networksecurity/utils/main_utils/utils.py
    -> 3 parents up gives the project root.
    """
    return Path(__file__).resolve().parents[3]        # <-- absolute Path object

# ------------------------------------------------------------------
# read any YAML file (schema or anything else)
# ------------------------------------------------------------------
def read_yaml_file(file_path: str | os.PathLike) -> dict:
    try:
        file_path = Path(file_path)
        if not file_path.is_absolute():               # make it absolute
            file_path = _project_root() / file_path

        if not file_path.exists():
            raise FileNotFoundError(
                f"YAML file not found at: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as yf:
            return yaml.safe_load(yf) or {}
    except Exception as e:
        raise NetworkSecurityException(str(e), sys) from e

# ------------------------------------------------------------------
# write any YAML file (creates folders automatically)
# ------------------------------------------------------------------
def write_yaml_file(file_path: str | os.PathLike,
                    content: dict,
                    replace: bool = False) -> None:
    try:
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = _project_root() / file_path

        if replace and file_path.exists():
            file_path.unlink()

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as yf:
            yaml.dump(content, yf, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise NetworkSecurityException(str(e), sys) from e