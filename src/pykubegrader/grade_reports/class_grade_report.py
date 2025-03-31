# # import the password and user from the build folder
# try:
#     from pykubegrader.build.passwords import password, user
# except:  # noqa: E722
#     print("Passwords not found, cannot access database")

import os

import pandas as pd
import tqdm

from pykubegrader.grade_reports.grade_report import GradeReport
from pykubegrader.grade_reports.grading_config import (
    assignment_type_list,
    skipped_users,
    students_to_include,
)
from pykubegrader._telemetry import get_all_students

api_base_url = os.getenv("DB_URL")
student_user = os.getenv("user_name_student")
student_pw = os.getenv("keys_student")


class ClassGradeReport:
    """Generates and manages a class-wide grade report.

    This class retrieves a list of students, initializes a structured grade report,
    and populates it with individual student grade data. The final report includes
    both assignment-specific grades and weighted average grades.

    Attributes:
        student_list (list): A sorted list of all students in the class, excluding skipped users
            and filtered to only include specified students.
        all_student_grades_df (pd.DataFrame): A DataFrame storing grades for each student,
            including assignment scores and weighted averages.
        user (str): Username for authentication.
        password (str): Password for authentication.

    Methods:
        setup_class_grades():
            Initializes an empty DataFrame with assignment names and weighted average columns.
        update_student_grade(student):
            Fetches and updates an individual student's weighted average grades in the DataFrame.
        fill_class_grades():
            Iterates through all students to populate the class-wide grade report.
        get_class_stats():
            Calculates class-wide statistics from the grade data.
        make_report(**kwargs):
            Generates an HTML report with grade statistics and visualizations using ydata-profiling.
            Args:
                title (str, optional): Title for the report. Defaults to "Grade Report".
                filename (str, optional): Output filename. Defaults to "Grade_report.html".
    """

    def __init__(self, user, password, **kwargs):
        """Initializes the class grade report.

        Retrieves the student list using authentication, filters it based on inclusion/exclusion
        rules, and sets up the class-wide grade report by initializing and populating a DataFrame.

        Args:
            user (str): Username for authentication to access student data
            password (str): Password for authentication to access student data
            **kwargs: Additional keyword arguments passed to make_report()
                title (str, optional): Title for the grade report. Defaults to "Grade Report"
                filename (str, optional): Output filename. Defaults to "Grade_report.html"

        The initialization process:
        1. Authenticates and retrieves full student list
        2. Filters out students in skipped_users list
        3. Filters to only include students in students_to_include list
        4. Sorts the filtered student list
        5. Sets up empty grade DataFrame
        6. Populates grades for all students
        7. Calculates class statistics
        8. Generates HTML report
        """
        self.user = user
        self.password = password

        self.student_list = get_all_students(self.user, self.password)

        # Remove skipped users
        self.student_list = list(set(self.student_list) - set(skipped_users))

        # Only include students in the students_to_include list
        self.student_list = [s for s in students_to_include if s in self.student_list]

        # Sort the student list
        self.student_list.sort()

        self.setup_class_grades()
        self.fill_class_grades()
        self.get_class_stats()
        self.make_report(**kwargs)

    def make_report(self, **kwargs):
        """Makes the class grade report using ydata-profiling.

        Generates an HTML report containing statistical analysis and visualizations of the class grades.
        The report includes distributions, correlations, and other descriptive statistics.

        Args:
            **kwargs: Additional keyword arguments
                title (str, optional): Title for the report. Defaults to "Grade Report"
                filename (str, optional): Output filename. Defaults to "Grade_report.html"

        Raises:
            Warning: If ydata-profiling package is not installed
        """
        try:
            title = kwargs.get("title", "Grade Report")
            filename = kwargs.get("filename", "Grade_report.html")
            from ydata_profiling import ProfileReport

            profile = ProfileReport(self.all_student_grades_df, title=title)
            profile.to_file(filename)
        except Exception:
            Warning("ydata_profiling not installed, cannot make report")

    def setup_class_grades(self):
        """Creates an empty DataFrame to store grades for all students.

        This method initializes a pandas DataFrame to store grades for all students in the class.
        The DataFrame has students as row indices and columns for each assignment type plus
        weighted average grades.

        The DataFrame structure is:
        - Index: Student usernames from self.student_list
        - Columns:
            - One column per assignment type from assignment_type_list (e.g. readings, labs)
            - "Weighted Average Grade w Final": Final weighted average including final exam
            - "Weighted Average Grade": Running weighted average without final exam
        - Values: All cells initialized to 0.0 with float dtype

        The empty DataFrame will be populated later by fill_class_grades().
        """
        self.all_student_grades_df = pd.DataFrame(
            0.0,
            dtype=float,
            index=self.student_list,
            columns=[a.name for a in assignment_type_list]
            + ["Weighted Average Grade w Final", "Weighted Average Grade"],
        )

    def update_student_grade(self, student):
        """Fetches and updates the grade report for an individual student.

        This method creates a GradeReport instance for the specified student, extracts their
        weighted average grades, and updates their row in the class-wide grade DataFrame.

        Args:
            student (str): The username or identifier of the student to update grades for.

        Updates:
            The student's row in `all_student_grades_df` with their weighted average grades,
            including:
            - Individual assignment type averages (e.g. readings, labs, etc.)
            - Weighted average grade without final
            - Weighted average grade with final

        Note:
            The GradeReport is created with display_=False to prevent printing output.
            The weighted averages are transposed and reindexed to match the columns of
            all_student_grades_df before updating.
        """
        report = GradeReport(params={"username": student}, display_=False)
        row_series = report.weighted_average_grades.transpose().iloc[
            0
        ]  # Example transformation
        row_series = row_series.reindex(self.all_student_grades_df.columns)
        self.all_student_grades_df.loc[student] = row_series

    def fill_class_grades(self):
        """Populates the class-wide grade report with data from all students.

        This method iterates through all students in the class and updates the grade report
        DataFrame with each student's weighted average grades. It uses a progress bar to
        show the status of grade collection.

        The method:
        1. Iterates through self.student_list with a progress bar
        2. For each student, calls update_student_grade() to:
            - Create their individual GradeReport
            - Extract their weighted averages
            - Update their row in all_student_grades_df

        Note:
            This method must be called after setup_class_grades() to ensure the DataFrame
            exists and is properly structured.

        Updates:
            self.all_student_grades_df: Populates all cells with actual grade data,
            replacing the initial 0.0 values.
        """
        for student in tqdm.tqdm(self.student_list):
            self.update_student_grade(student)

    def get_class_stats(self):
        """Calculates and stores descriptive statistics for the class-wide grade report.

        This method computes summary statistics for all columns in the class-wide grade report,
        including:
        - count: Number of non-null values
        - mean: Average grade
        - std: Standard deviation
        - min: Minimum grade
        - 25%: First quartile
        - 50%: Median
        - 75%: Third quartile
        - max: Maximum grade

        The statistics are stored in self.stats_df for later access and export.

        Note:
            This method must be called after fill_class_grades() to ensure grade data exists.

        Updates:
            self.stats_df (pd.DataFrame): DataFrame containing descriptive statistics for all
                grade columns in all_student_grades_df.
        """
        # Calculate descriptive statistics
        self.stats_df = self.all_student_grades_df.describe(include="all")

    def write_excel_spreadsheet(self, out_name="output.xlsx"):
        """Exports the class-wide grade report to an Excel spreadsheet.

        This method writes the grade report data to an Excel file with multiple sheets:
        - 'all_student_grades': Contains the full grade report DataFrame with individual
          student grades for all assignments and weighted averages
        - 'performance_statistics': Contains summary statistics like mean, median, std dev
          for each graded component

        Args:
            out_name (str, optional): Name/path of the output Excel file. Defaults to 'output.xlsx'.

        Note:
            This method requires that fill_class_grades() and get_class_stats() have been called
            first to populate the grade data and statistics.

        Updates:
            Creates or overwrites the specified Excel file with the grade report data.
        """
        # Export to Excel with different sheets
        with pd.ExcelWriter("output.xlsx") as writer:
            self.all_student_grades_df.to_excel(writer, sheet_name="all_student_grades")
            self.stats_df.to_excel(writer, sheet_name="performance_statistics")


def main():
    """Example usage of the ClassGradeReport class.

    This function demonstrates how to:
    1. Create a ClassGradeReport instance to generate a class-wide grade report
    2. Display the resulting grade DataFrame containing all student grades

    The grade report includes individual assignment scores and weighted averages
    for all students in the class.

    Example:
        >>> main()
        # Displays DataFrame with student grades
    """
    class_grades = ClassGradeReport()
    print(class_grades.all_student_grades_df)


if __name__ == "__main__":
    """Script entry point.
    
    When this module is run directly (rather than imported), executes the main() 
    function to demonstrate example usage of the ClassGradeReport class.
    
    Example:
        $ python class_grade_report.py
        # Displays DataFrame with student grades
    """
    main()
