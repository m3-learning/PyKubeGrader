# # import the password and user from the build folder
# try:
#     from pykubegrader.build.passwords import password, user
# except:  # noqa: E722
#     print("Passwords not found, cannot access database")

from pykubegrader.grade_reports.grading_config import assignment_type_list, skipped_users
from pykubegrader.grade_reports.grade_report import GradeReport
# from ..build.passwords import password, user
from pykubegrader.telemetry import get_all_students


import os
import requests
from requests.auth import HTTPBasicAuth
import socket
import pandas as pd
import numpy as np
import tqdm

# user = user()
# password = password()

# Set the environment variables for the database
# os.environ["JUPYTERHUB_USER"] = "jca92"
# os.environ["TOKEN"] = "token"
# os.environ["DB_URL"] = "https://engr-131-api.eastus.cloudapp.azure.com/"
# os.environ["keys_student"] = "capture"
# os.environ["user_name_student"] = "student"

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

    def __init__(self, user, password):
        """Initializes the class grade report.

        Retrieves the student list using authentication, sorts it, and sets up
        the class-wide grade report by initializing and populating a DataFrame.
        """
        self.user = user
        self.password = password
        
        self.student_list = get_all_students(self.user, self.password)
        self.student_list = list( set(self.student_list)-set(skipped_users) )
        self.student_list.sort()

        self.setup_class_grades()
        self.fill_class_grades()
        self.get_class_stats()
        

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
        report = GradeReport(params={"username": student}, display_=False)
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

    def get_class_stats(self):
        """Calculates and stores descriptive statistics for the class-wide grade report.
        Requires filling class grades first
        """
        # Calculate descriptive statistics
        self.stats_df = self.all_student_grades_df.describe(include='all')

    def write_excel_spreadsheet(self, out_name='output.xlsx'):
        """Exports the class-wide grade report to an Excel spreadsheet.

        Args:
            out_name (str, optional): Name of output file. Defaults to 'output.xlsx'.
        """
        # Export to Excel with different sheets
        with pd.ExcelWriter('output.xlsx') as writer:
            self.all_student_grades_df.to_excel(writer, sheet_name='all_student_grades')
            self.stats_df.to_excel(writer, sheet_name='performance_statistics')


def main():
    class_grades = ClassGradeReport()
    print(class_grades.all_student_grades_df)

if __name__ == "__main__":
    main()
