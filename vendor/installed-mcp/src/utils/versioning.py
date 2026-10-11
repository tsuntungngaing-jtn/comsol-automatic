"""Version naming utilities for model version management."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4
import re

# Base directory for all COMSOL models
MODELS_BASE_DIR = Path(__file__).parent.parent.parent / "comsol_models"


def safe_model_name(model_name: str) -> str:
    name = str(model_name)
    if name.lower().endswith('.mph'):
        name = name[:-4]
    if (not name or name in {'.', '..'} or name != name.strip()
            or name.endswith('.') or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', name)):
        raise ValueError('Model name must be a plain, non-reserved file name, not a path.')
    return name


def confined(path: Path) -> Path:
    root = MODELS_BASE_DIR.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('Version path escapes the configured versions directory.')
    return resolved


def get_model_directory(model_name: str) -> Path:
    return confined(MODELS_BASE_DIR / safe_model_name(model_name))


def generate_version_name(base_name: str) -> str:
    """
    Generate a versioned name with timestamp suffix.
    
    Args:
        base_name: Original model name (with or without .mph extension)
        
    Returns:
        Versioned name with timestamp, e.g., "model_20260215_143022.mph"
    """
    path = Path(base_name)
    stem = path.stem
    extension = path.suffix or ".mph"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_{timestamp}{extension}"


def generate_version_path(model_name: str, base_path: str = None) -> str:
    if base_path is not None:
        raise ValueError('Custom version base paths are not supported.')
    name = safe_model_name(model_name)
    directory = get_model_directory(name)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for _ in range(10):
        path = confined(directory / f'{name}_{stamp}_{uuid4().hex}.mph')
        try:
            # Reserve the unique path atomically before COMSOL writes it.
            with path.open('xb'):
                pass
            return str(path)
        except FileExistsError:
            continue
    raise FileExistsError('Could not reserve a unique model version.')


def generate_latest_path(model_name: str) -> str:
    name = safe_model_name(model_name)
    path = confined(get_model_directory(name) / f'{name}_latest.mph')
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def list_model_versions(model_name: str) -> list:
    """
    List all versions of a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        List of version file paths, sorted by modification time (newest first)
    """
    model_dir = get_model_directory(model_name)
    if not model_dir.exists():
        return []
    
    versions = []
    for f in model_dir.glob("*.mph"):
        if "_latest" not in f.name:
            versions.append(str(f))
    
    # Sort by modification time, newest first
    versions.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    return versions


def parse_version_info(name: str) -> dict | None:
    """
    Parse version information from a model name.
    
    Args:
        name: Model name to parse
        
    Returns:
        Dict with 'base_name', 'timestamp', 'datetime' or None if not versioned
    """
    path = Path(name)
    stem = path.stem
    
    import re
    match = re.match(r"^(.+)_(\d{8}_\d{6})(?:_[0-9a-f]{32})?$", stem)
    if match:
        base_name = match.group(1)
        timestamp_str = match.group(2)
        try:
            dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            return {
                "base_name": base_name,
                "timestamp": timestamp_str,
                "datetime": dt,
            }
        except ValueError:
            pass
    return None
