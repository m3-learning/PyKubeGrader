import logging
import os
import socket
from typing import Optional

import pandas as pd
import requests
from IPython.core.interactiveshell import ExecutionInfo
from requests.auth import HTTPBasicAuth


from pykubegrader.telemetry.responses import log_encrypted
from pykubegrader._utils import api_base_url, student_pw, student_user

#
# Logging setup
#

# Logger for cell execution
logger_code = logging.getLogger("code_logger")
logger_code.setLevel(logging.INFO)

file_handler_code = logging.FileHandler(".output_code.log")
file_handler_code.setLevel(logging.INFO)
logger_code.addHandler(file_handler_code)

# Logger for question scores etc.
logger_reduced = logging.getLogger("reduced_logger")
logger_reduced.setLevel(logging.INFO)

file_handler_reduced = logging.FileHandler(".output_reduced.log")
file_handler_reduced.setLevel(logging.INFO)
logger_reduced.addHandler(file_handler_reduced)


def telemetry(info: ExecutionInfo) -> None:
    cell_content = info.raw_cell
    log_encrypted(logger_code, f"code run: {cell_content}")


#
# API request functions
#


# TODO: Refine
# TODO: This might be deprecate
def verify_server(jhub_user: Optional[str] = None) -> str:
    if not api_base_url:
        raise ValueError("Environment variable for API URL not set")
    params = {"jhub_user": jhub_user} if jhub_user else {}
    res = requests.get(api_base_url, params=params)
    message = f"status code: {res.status_code}"
    return message


# TODO: This might be deprecate
def get_my_grades() -> pd.DataFrame:
    # get all submissions,
    # recalculate late penalty in new columns,
    # take max,
    # divide by total points
    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")
    from_hostname = socket.gethostname().removeprefix("jupyter-")
    from_env = os.getenv("JUPYTERHUB_USER")
    if from_hostname != from_env:
        raise ValueError("Problem with JupyterHub username")

    params = {"username": from_env}
    res = requests.get(
        url=api_base_url.rstrip("/") + "/my-grades",
        params=params,
        auth=HTTPBasicAuth(student_user, student_pw),
    )
    res.raise_for_status()

    grades = res.json()

    # Convert JSON to DataFrame
    df = pd.json_normalize(grades)
    # Transpose the DataFrame to make it vertical
    vertical_df = df.transpose()

    # Sort by row titles (index)
    sorted_vertical_df = vertical_df.sort_index()

    return sorted_vertical_df


#
# Code execution log testing
#
