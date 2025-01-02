import datetime

import numpy as np


def calculate_late_submission(
    due: str,
    submitted: str,
    Q0: int = 100,
    Q_min: int = 40,
    k: float = 6.88e-5,
) -> float:
    """
    Calculate the percentage value based on an exponential decay model
    with respect to a due date, using datetime string inputs.

    Parameters:
    - due_date_str (str): The due date as a string in the format "%Y-%m-%d %H:%M:%S".
    - submission_date (str): The comparison date as a string in the format "%Y-%m-%d %H:%M:%S".
    - Q0 (float): Initial value (default is 100).
    - Q_min (float): Minimum value (default is 40).
    - k (float): Decay constant per minute (default is 6.88e-5).

    Returns:
    - float: The percentage value after decay, bounded between Q_min and Q0.
    """

    # Convert datetime strings to UNIX timestamps
    due_date = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
    submitted_date = datetime.datetime.strptime(submitted, "%Y-%m-%d %H:%M:%S")

    # Calculate time difference in seconds
    time_difference = (submitted_date - due_date).total_seconds()

    # Convert time difference from seconds to minutes
    time_in_minutes = time_difference / 60.0

    # Calculate the exponential decay
    Q: float = Q0 * np.exp(-k * time_in_minutes)

    # Apply floor and ceiling conditions
    Q = np.maximum(Q, Q_min)
    Q = np.minimum(Q, Q0)

    return Q
