# import the password and user from the build folder
try:
    from pykubegrader.build.passwords import password, user
except:  # noqa: E722
    print("Passwords not found, cannot access database")

from pykubegrader.grade_reports.grading_config import assignment_type_list
from pykubegrader.grade_reports.grade_report import GradeReport


import os
import requests
from requests.auth import HTTPBasicAuth
import socket
import pandas as pd
import numpy as np
import tqdm

# Set the environment variables for the database
os.environ["JUPYTERHUB_USER"] = "jca92"
os.environ["TOKEN"] = "token"
os.environ["DB_URL"] = "https://engr-131-api.eastus.cloudapp.azure.com/"
os.environ["keys_student"] = "capture"
os.environ["user_name_student"] = "student"

api_base_url = os.getenv("DB_URL")
student_user = os.getenv("user_name_student")
student_pw = os.getenv("keys_student")


class ClassGradeReport:
    """Generates and manages a class-wide grade report.

    This class retrieves a list of students, initializes a structured grade report,
    and populates it with individual student grade data. The final report includes
    both assignment-specific grades and a weighted average grade.

    Attributes:
        student_list (list): A sorted list of all students in the class.
        all_student_grades_df (pd.DataFrame): A DataFrame storing grades for each student,
            including assignment scores and a weighted average.

    Methods:
        setup_class_grades():
            Initializes an empty DataFrame with assignment names and weighted average columns.
        update_student_grade(student):
            Fetches and updates an individual student’s weighted average grades in the DataFrame.
        fill_class_grades():
            Iterates through all students to populate the class-wide grade report.
    """

    def __init__(self):
        """Initializes the class grade report.

        Retrieves the student list using authentication, sorts it, and sets up
        the class-wide grade report by initializing and populating a DataFrame.
        """
        self.student_list = get_all_students(user, password)
        self.student_list.sort()

        self.setup_class_grades()
        self.fill_class_grades()

    def setup_class_grades(self):
        """Creates an empty DataFrame to store grades for all students.

        The DataFrame contains assignment columns and a "Weighted Average Grade" column,
        with students as index labels.
        """
        self.all_student_grades_df = pd.DataFrame(
            np.nan,
            dtype=float,
            index=self.student_list,
            columns=[a.name for a in assignment_type_list] + ["Weighted Average Grade"],
        )

    def update_student_grade(self, student):
        """Fetches and updates the grade report for an individual student.

        Args:
            student (str): The username or identifier of the student.

        Updates:
            The student's row in `all_student_grades_df` with their weighted average grades.
        """
        report = GradeReport(params={"username": student})
        row_series = report.weighted_average_grades.transpose().iloc[
            0
        ]  # Example transformation
        row_series = row_series.reindex(self.all_student_grades_df.columns)
        self.all_student_grades_df.loc[student] = row_series

    def fill_class_grades(self):
        """Populates the class-wide grade report with data from all students.

        Iterates through the `student_list` and updates the DataFrame by fetching
        and storing each student's weighted average grades.
        """
        for student in tqdm.tqdm(self.student_list):
            self.update_student_grade(student)


def get_all_students(user, password):
    """
    Fetches a list of all students from the API and returns their usernames.

    Args:
        user (str): The username for HTTP basic authentication.
        password (str): The password for HTTP basic authentication.

    Returns:
        list: A list of usernames extracted from the students' email addresses.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
    """
    res = requests.get(
        url=api_base_url.rstrip("/") + "/students",
        auth=HTTPBasicAuth(user, password),
    )
    res.raise_for_status()
    # Input: List of players
    return [student["email"].split("@")[0] for student in res.json()]


def get_assignments_submissions(params=None):
    """
    Fetches assignment submissions for a student from the grading API.
    This function retrieves the assignment submissions for a student by making a GET request to the grading API.
    It requires certain environment variables to be set and validates the JupyterHub username.
    Args:
        params (dict, optional): A dictionary of parameters to be sent in the query string. Defaults to None. If not provided, it will default to {"username": <JUPYTERHUB_USER>}.
    Raises:
        ValueError: If necessary environment variables (student_user, student_pw, api_base_url) are not set.
        ValueError: If there is a mismatch between the JupyterHub username from the hostname and the environment variable.
    Returns:
        dict: A dictionary containing the JSON response from the API with the assignment submissions.
    """

    if not student_user or not student_pw or not api_base_url:
        raise ValueError("Necessary environment variables not set")

    from_hostname = socket.gethostname().removeprefix("jupyter-")
    from_env = os.getenv("JUPYTERHUB_USER")

    if from_hostname != from_env:
        raise ValueError("Problem with JupyterHub username")

    if not params:
        params = {"username": from_env}

    # get submission information
    res = requests.get(
        url=api_base_url.rstrip("/") + "/my-grades-testing",
        params=params,
        auth=HTTPBasicAuth(student_user, student_pw),
    )

    return res.json()
