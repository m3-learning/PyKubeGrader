import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

from IPython.core.getipython import get_ipython


from pykubegrader._telemetry import telemetry

def get_jhub_user():
    jhub_user = os.getenv("JUPYTERHUB_USER")
    if jhub_user is None:
        raise Exception("Setup unsuccessful. Are you on JupyterHub?")
    return jhub_user

def initialize_telemetry():
    ipython = get_ipython()
    if ipython is None:
        raise Exception("Setup unsuccessful. Are you in a Jupyter environment?")

    try:
        move_dotfiles()
        ipython.events.register("pre_run_cell", telemetry)
    except Exception as e:
        raise Exception(f"Failed to register telemetry: {e}")

def build_assignment_tag(week, assignment_type, assignment_tag):
    if assignment_tag is None:
        if week is None:
            raise ValueError("Week is required when assignment_tag is not provided")
        if assignment_type is None:
            raise ValueError("Assignment type is required when assignment_tag is not provided")
        assignment_tag = f"{week}-{assignment_type}"
    return assignment_tag

def move_dotfiles():
    """
    Move essential dotfiles from a fixed source directory to the current working directory.

    Raises:
        FileNotFoundError: If a source file is missing.
        Exception: If copying fails for any other reason.
    """
    source_dir = Path("/opt/dotfiles")
    target_dir = Path.cwd()

    files_to_copy = [".client_private_key.bin", ".server_public_key.bin"]

    for file_name in files_to_copy:
        source_file = source_dir / file_name
        target_file = target_dir / file_name

        if not source_file.exists():
            raise FileNotFoundError(f"Key file not found: {source_file}")

        try:
            shutil.copy2(source_file, target_file)
        except Exception as e:
            raise Exception(f"Failed to copy {source_file} to {target_file}: {e}")


def username_to_seed(username: str, mod: int = 1000) -> int:
    hash_object = hashlib.sha256(username.encode())
    hash_hex = hash_object.hexdigest()
    hash_int = int(hash_hex, 16)
    return hash_int % mod
