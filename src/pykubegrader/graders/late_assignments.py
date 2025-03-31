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
    Calculate the adjusted percentage value for a late submission using an exponential decay model.

    This function computes the percentage value of a submission based on how late it is compared to the due date.
    The calculation uses an exponential decay formula, which reduces the percentage value over time, bounded by
    specified minimum and maximum values.

    Parameters:
    - due (str): The due date as a string in the format "%Y-%m-%d %H:%M:%S".
    - submitted (str): The submission date as a string in the format "%Y-%m-%d %H:%M:%S".
    - Q0 (int, optional): The initial percentage value before any decay is applied. Defaults to 100.
    - Q_min (int, optional): The minimum percentage value that can be assigned, regardless of how late the submission is. Defaults to 40.
    - k (float, optional): The decay constant that determines the rate of decay per minute. Defaults to 6.88e-5.

    Returns:
    - float: The adjusted percentage value after applying the exponential decay, constrained between Q_min and Q0.
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
