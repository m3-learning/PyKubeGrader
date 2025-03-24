# TODO: if not due yet and score is 0, make NAN, fix the rendering

import os
from datetime import datetime, timedelta
from itertools import product

import numpy as np
import pandas as pd
from IPython.display import display

from pykubegrader.grade_reports.assignments import (
    Assignment,
)
from pykubegrader.grade_reports.assignments import (
    assignment_type as AssignmentType,
)
from pykubegrader.grade_reports.grading_config import (
    aliases,
    assignment_type_list,
    custom_grade_adjustments,
    dropped_assignments,
    duplicated_scores,
    exclude_from_running_avg,
    globally_exempted_assignments,
    grade_ranges,
    max_week,
    optional_drop_assignments,
    optional_drop_week,
    global_extensions_AVL,
)
from pykubegrader.telemetry import get_assignments_submissions


class GradeReport:
    """Class to generate a grade report for a course and perform grade calculations for each student.

    Methods:
        __init__(start_date="2025-01-06", verbose=True, params=None, display_=True, **kwargs):
            Initializes an instance of the GradeReport class.

        load_assignments():
            Loads assignments for the course.

        load_student_submissions():
            Loads student submissions for the assignments.

        calculate_grades():
            Calculates grades for each student based on their submissions.

        generate_report():
            Generates a grade report for the course.

        display_report():
            Displays the grade report.

        save_report(filename):
            Saves the grade report to a file.

        update_grades(student):
            Updates the grades for a specific student.

        drop_lowest_scores(n):
            Drops the lowest `n` scores for each student.

        duplicate_scores():
            Duplicates scores from one assignment to another based on configuration.

        apply_global_exemptions():
            Applies global exemptions to assignments.

        apply_optional_drops():
            Applies optional drops to assignments.

        calculate_statistics():
            Calculates statistics for the class grades.

        export_to_excel(out_name='output.xlsx'):
            Exports the grade report to an Excel file.
    """

    def __init__(
        self,
        start_date="2025-01-06",
        verbose=True,
        params=None,
        display_=True,
        **kwargs,
    ):
        """Initializes an instance of the GradeReport class.

        This constructor sets up the initial state of the GradeReport object, including
        loading assignments and student submissions, setting course parameters, and
        performing initial grade calculations.

        Args:
            start_date (str, optional): The start date of the course. Defaults to "2025-01-06".
            verbose (bool, optional): Indicates if verbose output should be displayed. Defaults to True.
            params (dict, optional): A dictionary of parameters that may include user-specific
                information such as 'username'. Defaults to None.
            display_ (bool, optional): Determines if the grade report should be displayed
                immediately upon initialization. Defaults to True.
            **kwargs: Additional keyword arguments that can be used to extend the functionality
                or configuration of the GradeReport class.
                start_week (int): The week number to start creating assignments from. Defaults to 1.
                max_week (int): The maximum week number to create assignments for. Defaults to None.

        Attributes:
            assignments (list): A list of assignments for the course.
            student_subs (list): A list of student submissions.
            student_name (str): The name of the student, extracted from params or environment.
            max_week (int): The maximum number of weeks in the course.
            start_date (str): The start date of the course.
            verbose (bool): Flag to control verbose output.
            assignment_type_list (list): List of assignment types.
            aliases (dict): Dictionary of aliases for assignment names.
            globally_exempted_assignments (list): List of assignments globally exempted from grading.
            dropped_assignments (list): List of assignments that have been dropped.
            optional_drop_week (int): The week number where optional drops are allowed.
            optional_drop_assignments (list): List of assignments that can be optionally dropped.
            excluded_from_running_avg (list): List of assignments excluded from the running average.
            student_assignments_dropped (list): List of assignments dropped for a specific student.

        """

        # Get the username from the params
        self.set_username(params)

        self.assignments, self.student_subs = get_assignments_submissions(
            params={"username": self.student_name}
        )

        # Get the max week from kwargs
        max_week = kwargs.get("max_week", None)

        # Get the number of weeks
        self.max_week = max_week if max_week else self.num_weeks

        self.start_date = start_date
        self.verbose = verbose
        self.assignment_type_list = assignment_type_list
        self.aliases = aliases

        # Assignments that are globally exempted from grading.
        self.globally_exempted_assignments = globally_exempted_assignments

        # Assignments that have been dropped from the grade calculation.
        self.dropped_assignments = dropped_assignments

        # The week number where optional drops are allowed.
        self.optional_drop_week = optional_drop_week

        # Assignments that can be optionally dropped.
        self.optional_drop_assignments = optional_drop_assignments

        # Assignments that are excluded from the running average.
        self.excluded_from_running_avg = exclude_from_running_avg

        # assignments that have been dropped for a given students.
        self.student_assignments_dropped = []

        # Initialize the weekly grades DataFrame.
        self.setup_grades_df()

        # Build the list of assignments.
        self.build_assignments(**kwargs)

        # Update the global exempted assignments.
        self.update_global_exempted_assignments()

        self.calculate_grades()
        self.update_assignments_not_due_yet()
        self.calculate_grades()
        self.duplicate_scores()
        self.drop_lowest_n_for_types(1)
        self.calculate_grades()
        self.duplicate_scores()
        self.update_weekly_table()
        self._build_running_avg()
        self.check_optional_drop_assignments()
        self.calculate_grades()
        self.duplicate_scores()
        self.update_weekly_table()
        self._build_running_avg()
        self._calculate_final_average()
        df = self.highlight_nans(self.weekly_grades_df, self.weekly_grades_df_display)
        if display_:
            try:
                display(df)
                display(self.weighted_average_grades)
            except:  # noqa: E722
                pass
    
    ### Properties ###
    
    @property
    def student_assignments_dropped(self):
        """
        Gets the assignments which have been dropped for a given student.
        """
        return self._student_assignments_dropped
    
    @student_assignments_dropped.setter
    def student_assignments_dropped(self, value):
        """
        Sets the assignments which have been dropped for a given student.
        """
        if not isinstance(value, list):
            raise ValueError("student_assignments_dropped must be a list")
        #TODO improved error 
        self._student_assignments_dropped = value
    
    @property
    def excluded_from_running_avg(self):
        """
        Gets the assignments which are excluded from the running average.
        """
        return self._excluded_from_running_avg
    
    @excluded_from_running_avg.setter
    def excluded_from_running_avg(self, value):
        """
        Sets the assignments which are excluded from the running average.
        """
        if not isinstance(value, list):
            raise ValueError("excluded_from_running_avg must be a list")
        if not all(isinstance(item, str) for item in value):
            raise ValueError("excluded_from_running_avg must be a list of strings")
        self._excluded_from_running_avg = value
    
    @property
    def optional_drop_assignments(self):
        """
        Gest the assignments which are dropped if they do not improve the running average.
        
        Returns:
            list: The optional drop assignments.
        """
        return self._optional_drop_assignments
    
    @optional_drop_assignments.setter
    def optional_drop_assignments(self, value):
        """
        Sets the optional drop assignments. The optional drop assignments are the assignments which are dropped if they do not improve the running average.

        Args:
            value (list): A list of tuples, where each tuple contains a string and an integer or None.

        Raises:
            ValueError: If the provided value is not a list.
            ValueError: If any item in the list is not a tuple of a string and an integer or None.
        """
        if not isinstance(value, list):
            raise ValueError("optional_drop_assignments must be a list")
        if not all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) and (isinstance(item[1], int) or item[1] is None) for item in value):
            raise ValueError("optional_drop_assignments must be a list of tuples, where each tuple contains a string and an integer or None")
        self._optional_drop_assignments = value
    

    @property
    def optional_drop_week(self):
        """
        Gets the optional drop week. These are the weeks which can be dropped if they do not improve the running average.
        """
        return self._optional_drop_week 
    
    @optional_drop_week.setter
    def optional_drop_week(self, value):
        """
        Sets the optional drop week. These are the weeks which can be dropped if they do not improve the running average.

        Args:
            value (list): A list of integers representing the weeks which can be dropped.

        Raises:
            ValueError: If the provided value is not a list.
            ValueError: If any item in the list is not an integer.
        """
        if not isinstance(value, list):
            raise ValueError("optional_drop_week must be a list")
        if not all(isinstance(item, int) for item in value):
            raise ValueError("optional_drop_week must be a list of integers")
        self._optional_drop_week = value
    
    @property
    def dropped_assignments(self):
        """
        Gets the dropped assignments.
        """
        return self._dropped_assignments
    
    @dropped_assignments.setter
    def dropped_assignments(self, value):
        """
        Sets the dropped assignments.

        Args:
            value (list): A list of strings representing the dropped assignments.

        Raises:
            ValueError: If the provided value is not a list.
            ValueError: If any item in the list is not a string.
        """
        if not isinstance(value, list):
            raise ValueError("dropped_assignments must be a list")
        if not all(isinstance(item, str) for item in value):
            raise ValueError("dropped_assignments must be a list of strings")
        self._dropped_assignments = value

    @property
    def globally_exempted_assignments(self):
        """
        Gets the globally exempted assignments.
        """
        return self._globally_exempted_assignments
    
    @globally_exempted_assignments.setter
    def globally_exempted_assignments(self, value):
        """
        Sets the globally exempted assignments.

        Args:
            value (list): A list of tuples, where each tuple contains:
                - A string representing the assignment type.
                - An integer or None representing the week number.

        Raises:
            ValueError: If the provided value is not a list of tuples.
            ValueError: If any tuple does not contain exactly two elements.
            ValueError: If the first element of any tuple is not a string.
            ValueError: If the second element of any tuple is not an integer or None.
        """
        if not isinstance(value, list):
            raise ValueError("globally_exempted_assignments must be a list of tuples")
        if not all(isinstance(item, tuple) for item in value):
            raise ValueError("globally_exempted_assignments must be a list of tuples")
        if not all(len(item) == 2 for item in value):
            raise ValueError("globally_exempted_assignments must be a list of tuples with two elements")
        if not all(isinstance(item[0], str) for item in value):
            raise ValueError("globally_exempted_assignments must be a list of tuples with a string as the first element")
        if not all(isinstance(item[1], (int, type(None))) for item in value):
            raise ValueError("globally_exempted_assignments must be a list of tuples with an integer or None as the second element")
        self._globally_exempted_assignments = value
    
    @property
    def student_name(self):
        """
        Gets the student name.
        """
        return self._student_name
    @property
    def aliases(self):
        """
        Gets the aliases for the course.
        """
        return self._aliases
    
    @aliases.setter
    def aliases(self, value):
        """
        Sets the aliases for the course.

        Args:
            value (dict): A dictionary of aliases for the course.

        Raises:
            ValueError: If the provided value is not a dictionary.
        """
        if not isinstance(value, dict):
            raise ValueError("aliases must be a dictionary")
        self._aliases = value
    
    
    @property
    def assignment_type_list(self):
        """
        Gets the assignment type list.
        """
        return self._assignment_type_list
    
    @assignment_type_list.setter
    def assignment_type_list(self, value):
        """
        Sets the assignment type list.

        Args:
            value (list): A list of AssignmentType objects to set as the assignment type list.

        Raises:
            ValueError: If the provided value is not a list.
            ValueError: If the list contains items that are not AssignmentType objects.
        """
        if not isinstance(value, list):
            raise ValueError("assignment_type_list must be a list")
        if not all(isinstance(item, AssignmentType) for item in value):
            raise ValueError("assignment_type_list must contain only AssignmentType objects")
        self._assignment_type_list = value
    
    @property
    def student_name(self):
    @property
    def verbose(self):
        """
        Gets the verbose flag.
        """
        return self._verbose
    
    @verbose.setter
    def verbose(self, value):
        """
        Sets the verbose flag.
        """
        if not isinstance(value, bool):
            raise ValueError("verbose must be a boolean")
        self._verbose = value
    
    @property
    def start_date(self):
        """
        Gets the start date for the course.
        """
        return self._start_date
    
    @start_date.setter
    def start_date(self, value):
        """
        Sets the start date for the course.
        """
        if not isinstance(value, datetime):
            raise ValueError("start_date must be a datetime object")
        self._start_date = value
    
    @property
    def num_weeks(self):
        """
        Gets the number of weeks in the course.
        """
        return self._num_weeks
    @property
    def max_week(self):
        """
        Gets the maximum week number for the course.

        Returns:
            int: The maximum week number.
        """
        return self._max_week
    
    @max_week.setter
    def max_week(self, value):
        """
        Sets the maximum week number for the course.

        This method sets the maximum week number for the course. The value must be an integer.
        If the provided value is not an integer, a ValueError is raised.

        Args:
            value (int): The maximum week number to set.

        Raises:
            ValueError: If the provided value is not an integer.

        Example:
            >>> grade_report = GradeReport()
            >>> grade_report.max_week = 15
            >>> print(grade_report.max_week)
            15
        """
        if not isinstance(value, int):
            raise ValueError("max_week must be an integer")
        
        self._max_week = value

    def set_username(self, params):
        """
        Sets the username for the student.

        This method attempts to set the student's username from the provided parameters.
        If the username is not found in the parameters, it falls back to using the
        JUPYTERHUB_USER environment variable.

        Args:
            params (dict): A dictionary containing the parameters, expected to have a key "username".

        Example:
            >>> grade_report = GradeReport()
            >>> grade_report.set_username({"username": "student123"})
            >>> print(grade_report.student_name)
            student123
        """
        try:
            self.student_name = params.get("username", None)
        except Exception:
            self.student_name = os.environ.get("JUPYTERHUB_USER", None)

    def check_optional_drop_assignments(self):
        """
        Checks if optional assignments should be dropped based on running average.

        For each assignment that is marked as optionally droppable, compares the student's
        running average at that point to their score on the assignment. If the running
        average is higher than their assignment score, the assignment is exempted from
        grade calculations.

        This allows students to drop assignments that would lower their overall grade,
        up to the maximum number of optional drops allowed.

        The optional drops are specified in self.optional_drop_assignments as tuples of
        (assignment_name, week_number).
        """
        # Iterate through all assignments in the course
        for assignment in self.graded_assignments:
            # Check if the assignment is in the list of optional drop assignments
            if (assignment.name, assignment.week) in self.optional_drop_assignments:
                # Compare the running average to the assignment score
                if (
                    self.weekly_grades_df_display.loc["Running Avg", assignment.name]
                    > assignment.score_
                ):
                    # If the running average is higher, exempt the assignment
                    assignment.exempted = True

    @staticmethod
    def highlight_nans(nan_df, display_df, color="red"):
        """
        Highlights NaN values from one DataFrame on another DataFrame by applying background colors.

        This static method takes two DataFrames - one containing NaN values to highlight and another
        to apply the highlighting to. It creates a styled version of the display DataFrame where cells
        corresponding to NaN values in the first DataFrame are highlighted with the specified color.

        Args:
            nan_df (pd.DataFrame): The DataFrame containing NaN values that should be highlighted.
                This DataFrame's NaN locations will determine which cells get colored.
            display_df (pd.DataFrame): The DataFrame that will have the highlighting applied to it.
                This DataFrame's values will be displayed with the highlighting.
            color (str, optional): The background color to use for highlighting NaN cells.
                Can be any valid CSS color value. Defaults to "red".

        Returns:
            pd.io.formats.style.Styler: A styled version of display_df with NaN cells highlighted
                according to nan_df's NaN locations.

        Example:
            >>> grades_df = pd.DataFrame({'A': [1, np.nan], 'B': [np.nan, 2]})
            >>> display_df = pd.DataFrame({'A': [1, '---'], 'B': ['---', 2]})
            >>> styled = GradeReport.highlight_nans(grades_df, display_df, color='yellow')
            >>> styled  # Will show display_df with yellow highlighting where grades_df has NaNs
        """
        # Ensure both DataFrames have the same index and columns
        nan_mask = nan_df.isna().reindex_like(display_df)

        # Function to apply the highlight conditionally
        def apply_highlight(row):
            """
            Applies background color to NaN values in the row.

            Args:
                row (pd.Series): A row from the DataFrame.

            Returns:
                list: A list of CSS styles for each cell in the row, with background-color
                    set for cells corresponding to NaN values.
            """
            return [
                f"background-color: {color}" if nan_mask.loc[row.name, col] else ""
                for col in row.index
            ]

        # Apply the highlighting row-wise
        styled_df = display_df.style.apply(apply_highlight, axis=1)

        return styled_df

    def update_assignments_not_due_yet(self):
        """
        Updates the score of assignments that are not due yet to NaN.

        This method iterates through all graded assignments and checks their due dates.
        For assignments that are not yet due and have a score of 0, it:
        - Sets the numeric score to NaN
        - Sets the display score to "---"
        - Marks the assignment as exempted

        The assignment must:
        - Have a due date set
        - Not be in the excluded_from_running_avg list
        - Have a due date in the future
        - Currently have a score of 0

        This prevents assignments that aren't due yet from negatively impacting grades.
        """
        # Iterate through all graded assignments
        for assignment in self.graded_assignments:
            # Check if the assignment has a due date and is not excluded from running avg
            if (
                assignment.due_date
                and assignment.name not in self.excluded_from_running_avg
            ):
                # Convert due date to datetime object
                due_date = datetime.fromisoformat(
                    assignment.due_date.replace("Z", "+00:00")
                )
                # Check if the due date is in the future and the score is 0
                if due_date > datetime.now(due_date.tzinfo) and assignment.score == 0:
                    assignment.score_ = np.nan
                    assignment._score = "---"
                    assignment.exempted = True

    def color_cells(self, styler, week_list, assignment_list):
        """Recursively colors cells in a pandas styler object based on week and assignment lists.

        This method takes a pandas styler object and recursively applies yellow background
        coloring to cells specified by corresponding week and assignment pairs. It processes
        the lists from right to left using pop().

        Args:
            styler (pandas.io.formats.style.Styler): The pandas styler object to modify
            week_list (list): List of week identifiers corresponding to row indices
            assignment_list (list): List of assignment names corresponding to column names

        Returns:
            pandas.io.formats.style.Styler: The modified styler object with colored cells

        Note:
            The week_list and assignment_list must be of equal length.
            The method modifies the input lists by popping elements.
        """

        # Base case: if either list is empty, return the styler unchanged
        if week_list:
            week = week_list.pop()
            assignment = assignment_list.pop()

            # Apply the style to the current cell
            styler = styler.set_properties(
                subset=pd.IndexSlice[[week], [assignment]],
                **{"background-color": "yellow"},
            )
            # Recursive call
            return self.color_cells(styler, week_list, assignment_list)
        else:
            return styler

    def _calculate_final_average(self):
        """Calculates final grade averages considering optional weighted assignments.

        This method computes both a regular weighted average grade and a final weighted average
        that accounts for optional assignment weights. It handles assignments that can have
        variable weights (specified as tuples) by calculating all possible weight combinations
        and selecting the most favorable outcome for the student.

        The method performs the following steps:
        1. Separates assignments into regular and optional weighted categories
        2. Calculates base score from regular weighted assignments
        3. Computes all possible combinations of optional assignment weights
        4. Determines the maximum possible final grade
        5. Updates the grade report with running averages and letter grade

        Attributes modified:
            final_grade (float): Regular weighted average without optional weights
            final_grade_final (float): Maximum weighted average considering optional weights
            weighted_average_grades (pd.DataFrame): DataFrame containing all grade calculations

        Note:
            Assignment weights specified as tuples indicate optional weighting schemes.
            The final grade uses the weight combination that maximizes the student's grade.
        """

        # percentage of the total score -- this is 100%
        total_percentage = 1
        df_ = self.compute_final_average()
        score_earned = 0
        optional_weighted_assignments = []
        final_weights = {}

        # Iterate through all assignments to identify optional weighted assignments, this is when multiple weights are specified
        for assignment_type in self.assignment_type_list:
            if isinstance(assignment_type.weight, tuple):
                # subtract the weight from the total percentage
                total_percentage -= assignment_type.weight[0]
                # add the assignment to the list of optional weighted assignments
                optional_weighted_assignments.append(assignment_type)
                # add the weights to the final weights dictionary
                final_weights[assignment_type.name] = list(assignment_type.weight)
            else:
                # add the score earned to the score earned variable
                score_earned += assignment_type.weight * df_[assignment_type.name]

        # calculate the non optional score
        non_optional_score = score_earned / total_percentage
        # calculate all possible combinations of optional assignment weights
        combinations = list(product(*final_weights.values()))
        final_scores_list = []
        for weight_combo in combinations:
            score = 0

            for i, assignment_type in enumerate(optional_weighted_assignments):
                score += weight_combo[i] * df_[assignment_type.name]

            # calculate the final score
            final_scores_list.append(
                non_optional_score * (1 - sum(weight_combo)) + score
            )

        # update the final grade and final grade final
        self.final_grade = score_earned / total_percentage
        self.final_grade_final = max(*final_scores_list)

        # update the weighted average grades
        self.weighted_average_grades = pd.concat(
            [
                pd.DataFrame(self.final_grades),
                pd.DataFrame(
                    {"Running Avg": [self.final_grade]},
                    index=["Weighted Average Grade"],
                ),
                pd.DataFrame(
                    {"Running Avg": [self.final_grade_final]},
                    index=["Weighted Average Grade w Final"],
                ),
                pd.DataFrame(
                    {"Running Avg": [self._get_letter_grade(self.final_grade_final)]},
                    index=["Letter Grade"],
                ),
            ]
        )

    def update_weekly_table(self):
        """Updates both the display and internal weekly grades tables.

        This method updates two tables:
        1. The internal weekly grades table with calculated scores via _update_weekly_table_nan()
        2. The display weekly grades table with formatted scores via _update_weekly_table_scores()
        """
        self._update_weekly_table_nan()
        self._update_weekly_table_scores()

    @staticmethod
    def _get_letter_grade(score: float) -> str:
        """Gets the letter grade corresponding to a numeric score.

        Args:
            score (float): The numeric score to convert to a letter grade.

        Returns:
            str: The letter grade (e.g. 'A', 'B', etc.) corresponding to the score based on
                the grade ranges defined in the grading config. Returns 'Invalid Score' if
                the score does not fall within any defined range.
        """
        for low, high, grade in grade_ranges:
            if low <= score <= high:
                return grade
        return "Invalid Score"

    def _update_weekly_table_scores(self):
        """Updates the display weekly grades table with formatted scores.

        Iterates through all graded assignments and updates the display table
        (weekly_grades_df_display) with the formatted scores (_score) for weekly
        assignments. The scores are indexed by week number and assignment name.
        """
        for assignment in self.graded_assignments:
            if assignment.weekly:
                self.weekly_grades_df_display.loc[
                    f"week{assignment.week}", assignment.name
                ] = assignment._score

    def _update_weekly_table_nan(self):
        """Updates the weekly grades table with the calculated scores.

        This method iterates through all graded assignments and updates the internal
        weekly grades table (weekly_grades_df) with the calculated scores (score_)
        for weekly assignments. The scores are indexed by week number and assignment name.

        The method only processes weekly assignments, skipping any non-weekly ones.
        The scores are stored in their raw numerical form, not formatted for display.
        """

        for assignment in self.graded_assignments:
            if assignment.weekly:
                self.weekly_grades_df.loc[f"week{assignment.week}", assignment.name] = (
                    assignment.score_
                )

    def update_global_exempted_assignments(self):
        """Updates the graded assignments with globally exempted assignments.

        This method iterates through the globally exempted assignments list and marks
        matching assignments as exempted. For each exempted assignment, it:
        1. Sets the exempted flag to True
        2. Updates the display score to "---"

        The method silently skips any assignments that don't exist in the graded
        assignments list.

        Note:
            The globally_exempted_assignments list contains tuples of
            (assignment_type, week) pairs.
        """
        for assignment_type, week in self.globally_exempted_assignments:
            try:
                self.get_graded_assignment(week, assignment_type)[0].exempted = True
                self.get_graded_assignment(week, assignment_type)[0]._score = "---"
            except:  # noqa: E722
                pass

    def build_assignments(self, **kwargs):
        """Builds the list of graded assignments for the course.

        This method initializes and populates the graded_assignments list with Assignment
        objects for both weekly and non-weekly assignments.

        Args:
            **kwargs: Keyword arguments
                start_week (int): The week number to start creating assignments from. Defaults to 1.

        The method works in two steps:
        1. Creates Assignment objects for weekly assignments (e.g. labs, quizzes) for each week
           from start_week up to max_week
        2. Creates Assignment objects for non-weekly assignments (e.g. midterm, final)

        Each Assignment object is constructed using graded_assignment_constructor() which handles:
        - Setting the assignment name, type and weight
        - Applying any custom grade adjustments from the grading config
        - Setting the due date based on filtered submissions
        - Setting the max score from filtered assignments
        - For weekly assignments, also sets the week number

        The constructed Assignment objects are stored in self.graded_assignments for later
        grade calculations.

        Note:
            Weekly assignments are created for each week in the range [start_week, max_week].
            Non-weekly assignments like midterms and finals are created once per type.
        """
        start_week = kwargs.get("start_week", 1)

        # Initialize the list of graded assignments
        self.graded_assignments = []
        # Get the weekly assignments
        weekly_assignments = self.get_weekly_assignments()

        # Create Assignment objects for weekly assignments
        for assignment_type in weekly_assignments:
            for week in range(start_week, self.max_week + 1):  # Weeks start at 1
                self.graded_assignment_constructor(assignment_type, week=week)

        non_weekly_assignments = self.get_non_weekly_assignments()

        for assignment_type in non_weekly_assignments:
            self.graded_assignment_constructor(assignment_type)

    def graded_assignment_constructor(self, assignment_type: AssignmentType, **kwargs):
        """Constructs a graded assignment object and appends it to the graded_assignments list.

        This method creates a new Assignment object with the specified type and parameters,
        and adds it to the list of graded assignments for the course.

        Args:
            assignment_type (AssignmentType): The type of assignment to create. Contains:
                - name (str): Name of the assignment type (e.g. readings, quiz, lab)
                - weekly (bool): Whether this is a weekly assignment
                - weight (float): Weight of this assignment type in grade calculations
            **kwargs: Additional keyword arguments:
                week (int, optional): Week number for weekly assignments

        The method:
        1. Looks up any custom grade adjustment function for this assignment type/week
        2. Gets filtered assignments matching the type/week
        3. Creates new Assignment with:
            - Basic properties (name, weekly status, weight) from assignment_type
            - Score initialized to 0
            - Custom grade adjustment function if specified
            - Due date determined from filtered assignments
            - Max score determined from filtered assignments
            - Any additional kwargs passed through
        4. Adds the new Assignment to self.graded_assignments list
        """
        custom_func = custom_grade_adjustments.get(
            (assignment_type.name, kwargs.get("week", None)), None
        )

        filtered_assignments = self.get_assignment(
            kwargs.get("week", None), assignment_type.name
        )

        new_assignment = Assignment(
            name=assignment_type.name,
            weekly=assignment_type.weekly,
            weight=assignment_type.weight,
            score=0,
            grade_adjustment_func=custom_func,
            due_date=self.determine_due_date(filtered_assignments),
            max_score=self.get_max_score(filtered_assignments),
            **kwargs,
        )
        self.graded_assignments.append(new_assignment)

    def calculate_grades(self):
        """Calculates the grades for each student based on the graded assignments.

        This method iterates through all graded assignments and updates their scores based on
        student submissions. For each assignment:

        1. Gets any matching submissions for that assignment week/type
        2. If submissions exist:
           - Updates the assignment score using each submission
        3. If no submissions exist:
           - Updates the assignment score with default values

        The score updates take into account:
        - Raw submission scores
        - Any grade adjustment functions defined for that assignment
        - Student-specific exemptions or adjustments
        - Maximum possible points

        Args:
            None

        Returns:
            None

        Side Effects:
            - Updates the score attributes of all Assignment objects in self.graded_assignments
        """
        for assignment in self.graded_assignments:
            filtered_submission = self.filter_submissions(
                assignment.week, assignment.name
            )

            if filtered_submission:
                for submission in filtered_submission:
                    assignment.update_score(submission, student_name=self.student_name)

            # runs if there are no filtered submissions
            else:
                assignment.update_score(student_name=self.student_name)

    def compute_final_average(self):
        """Computes the final average by combining running average and non-weekly scores.

        This method calculates the final grade by:
        1. Taking the running average from weekly assignments stored in weekly_grades_df
        2. Adding scores from non-weekly assignments like midterms/finals

        The running average comes from the "Running Avg" row of weekly_grades_df.
        Non-weekly assignment scores are taken directly from their Assignment objects.

        Returns:
            pandas.Series: A series containing the final grades, including both the
                running average from weekly assignments and individual scores from
                non-weekly assignments like exams.

        Side Effects:
            - Sets self.final_grades to the computed final grade series
        """
        # Extract running average from the weekly table
        self.final_grades = self.weekly_grades_df.loc["Running Avg"]

        for assignment in self.graded_assignments:
            if not assignment.weekly:
                self.final_grades[f"{assignment.name}"] = assignment.score_

        return self.final_grades

    def filter_submissions(self, week_number, assignment_type):
        """Filters student submissions based on week number and assignment type.

        This method filters the list of student submissions (self.student_subs) to find
        submissions matching the specified week number and assignment type. The assignment
        type is normalized using aliases to handle different naming variations.

        Args:
            week_number (int): The week number to filter by. If None, only filters by
                assignment type.
            assignment_type (str): The type of assignment to filter for. Will be normalized
                using the aliases dictionary.

        Returns:
            list: A filtered list of submission dictionaries that match the specified
                week number (if provided) and normalized assignment type.

        Example:
            >>> grade_report.filter_submissions(1, "lab")
            [{'week_number': 1, 'assignment_type': 'lab', ...}, ...]
        """
        # Normalize the assignment type using aliases
        normalized_type = self.aliases.get(
            assignment_type.lower(), [assignment_type.lower()]
        )

        if week_number:
            # Filter the assignments based on the week number and normalized assignment type
            filtered = [
                assignment
                for assignment in self.student_subs
                if assignment["week_number"] == week_number
                and assignment["assignment_type"].lower() in normalized_type
            ]

        # If week_number is None, filter based on the normalized assignment type only
        else:
            # Filter the assignments based on the normalized assignment type
            filtered = [
                assignment
                for assignment in self.student_subs
                if assignment["assignment_type"].lower() in normalized_type
            ]

        return filtered

    def get_assignment(self, week_number, assignment_type):
        """Retrieves assignments matching the specified week number and assignment type.

        This method filters the list of assignments (self.assignments) to find those that match
        the specified week number and assignment type. The assignment type is normalized using
        aliases to handle different naming variations.

        Args:
            week_number (int, optional): The week number to filter by. If None, only filters by
                assignment type.
            assignment_type (str): The type of assignment to filter for. Will be normalized
                using the aliases dictionary.

        Returns:
            list: A filtered list of assignment dictionaries that match the specified
                week number (if provided) and normalized assignment type.

        Example:
            >>> grade_report.get_assignment(1, "lab")
            [{'week_number': 1, 'assignment_type': 'lab', ...}, ...]
        """
        # Normalize the assignment type using aliases
        normalized_type = self.aliases.get(
            assignment_type.lower(), [assignment_type.lower()]
        )

        # Filter the assignments based on the week number and normalized assignment type
        filtered = [
            assignment
            for assignment in self.assignments
            if (assignment["week_number"] == week_number or week_number is None)
            and assignment["assignment_type"].lower() in normalized_type
        ]

        return filtered

    def get_graded_assignment(self, week_number, assignment_type):
        """Retrieves graded assignments matching the specified week number and assignment type.

        This method filters the list of graded assignments (self.graded_assignments) to find those
        that match the specified week number and assignment type.

        Args:
            week_number (int, optional): The week number to filter by. If None, only filters by
                assignment type.
            assignment_type (str): The type of assignment to filter for.

        Returns:
            list: A filtered list of Assignment objects that match the specified week number
                (if provided) and assignment type.

        Example:
            >>> grade_report.get_graded_assignment(1, "lab")
            [<Assignment week=1 name='lab' ...>, ...]
        """
        return list(
            filter(
                lambda a: isinstance(a, Assignment)
                and a.name == assignment_type
                and (week_number is None or a.week == week_number),
                self.graded_assignments,
            )
        )

    def get_max_score(self, filtered_assignments):
        """Gets the maximum score possible for a set of filtered assignments.

        This method determines the maximum score possible by finding the assignment
        with the highest ID in the filtered assignments list and returning its max_score.

        Args:
            filtered_assignments (list): A list of assignment dictionaries containing
                at least 'id' and 'max_score' keys.

        Returns:
            int: The maximum score possible. Returns 0 if the filtered_assignments list
                is empty.

        Example:
            >>> assignments = [{'id': 1, 'max_score': 10}, {'id': 2, 'max_score': 20}]
            >>> grade_report.get_max_score(assignments)
            20
        """
        if not filtered_assignments:
            return 0

        return max(filtered_assignments, key=lambda x: x["id"])["max_score"]

    def determine_due_date(self, filtered_assignments):
        """Determines the latest due date for a set of filtered assignments.

        This method finds the assignment with the latest due date from the filtered assignments
        and applies any global extensions the student may have.

        Args:
            filtered_assignments (list): A list of assignment dictionaries containing at least
                a 'due_date' key with an ISO format datetime string.

        Returns:
            str or None: The latest due date as an ISO format string, with any applicable
                extensions added. Returns None if filtered_assignments is empty.

        Example:
            >>> assignments = [
            ...     {'due_date': '2024-01-01T23:59:59Z'},
            ...     {'due_date': '2024-01-02T23:59:59Z'}
            ... ]
            >>> grade_report.determine_due_date(assignments)
            '2024-01-02T23:59:59+00:00'
        """
        if not filtered_assignments:
            return None  # Return None if the list is empty

        # Convert due_date strings to datetime objects and find the max
        max_due = max(
            filtered_assignments,
            key=lambda x: datetime.fromisoformat(x["due_date"].replace("Z", "+00:00")),
        )

        extension_minutes = self.check_global_extensions()
        if extension_minutes:
            max_due["due_date"] = (
                datetime.fromisoformat(max_due["due_date"].replace("Z", "+00:00"))
                + timedelta(minutes=extension_minutes)
            ).isoformat()

        return max_due["due_date"]  # Return the max due date as a string

    def check_global_extensions(self):
        """Check if the student has a global extension available.

        This method checks if the current student has been granted a global extension
        by looking up their name in the global_extensions_AVL dictionary.

        Returns:
            int or None: The number of minutes of extension if the student has one available,
                otherwise None.

        Example:
            >>> grade_report = GradeReport(params={'username': 'student1'})
            >>> grade_report.check_global_extensions()
            60  # Returns 60 if student1 has a 60 minute extension
            >>> grade_report = GradeReport(params={'username': 'student2'})
            >>> grade_report.check_global_extensions()
            None  # Returns None if student2 has no extension
        """
        if self.student_name in global_extensions_AVL:
            return global_extensions_AVL[self.student_name]
        else:
            return None

    def get_non_weekly_assignments(self):
        """Get all non-weekly assignments from the assignment list configuration.

        This method filters the assignment_type_list to extract assignments that are not marked as weekly.

        Returns:
            list: A list of non-weekly assignments.

        Example:
            >>> grade_report = GradeReport()
            >>> non_weekly = grade_report.get_non_weekly_assignments()
            >>> len(non_weekly)
            2  # Returns number of non-weekly assignments found
        """
        non_weekly_assignments = [
            assignment
            for assignment in self.assignment_type_list
            if not assignment.weekly
        ]
        return non_weekly_assignments

    @property
    def weekly_assignments(self):
        """
        A list of weekly assignments from the assignment list configuration.

        This property filters the assignment_type_list to extract assignments that are marked as weekly.

        Returns:
            list: A list of weekly assignments.

        Example:
            >>> grade_report = GradeReport()
            >>> weekly = grade_report.weekly_assignments
            >>> len(weekly)
            3  # Returns number of weekly assignments found
        """
        return [
            assignment for assignment in self.assignment_type_list if assignment.weekly
        ]

    @property
    def num_weeks(self):
        """
        Gets the total number of weeks in the course based on assignment data.

        Returns:
            int: The maximum week number found in the course assignments.

        Example:
            >>> grade_report = GradeReport()
            >>> grade_report.num_weeks
            15  # Returns total number of weeks in the course
        """
        max_week_number = max(item["week_number"] for item in self.assignments)
        return max_week_number

    def setup_grades_df(self):
        """
        Sets up the DataFrame for weekly grades and initializes it with zeros.

        This method creates two DataFrames:
        - weekly_grades_df: For storing and calculating weekly grades
        - weekly_grades_df_display: A string copy for display purposes

        The DataFrames have:
        - Rows for each week ("week1", "week2", etc) plus a "Running Avg" row
        - Columns for each weekly assignment type
        - All values initialized to 0

        Example:
            >>> grade_report = GradeReport()
            >>> grade_report.setup_grades_df()
            >>> grade_report.weekly_grades_df.shape
            (16, 3)  # 15 weeks + Running Avg row, 3 assignment types
            >>> grade_report.weekly_grades_df.index[0]
            'week1'
            >>> grade_report.weekly_grades_df_display.dtypes[0]
            dtype('O')  # String type for display

        Returns:
            None
        """
        weekly_assignments = self.get_weekly_assignments()
        inds = [f"week{i + 1}" for i in range(self.max_week)] + ["Running Avg"]
        restruct_grades = {
            k.name: [0 for i in range(len(inds))] for k in weekly_assignments
        }
        new_weekly_grades = pd.DataFrame(restruct_grades, dtype=float)
        new_weekly_grades["inds"] = inds
        new_weekly_grades.set_index("inds", inplace=True)

        # This is the dataframe that will be used for calculations
        self.weekly_grades_df = new_weekly_grades
        # this is the dataframe that will be displayed in the notebook
        self.weekly_grades_df_display = new_weekly_grades.copy().astype(str)

    def _build_running_avg(self):
        """
        Computes and updates the running average row in the grade DataFrames.

        This method calculates the mean score for each assignment type, excluding the
        "Running Avg" row itself, and updates both the calculation DataFrame
        (weekly_grades_df) and display DataFrame (weekly_grades_df_display) with these
        averages.

        The calculation:
        - Drops the "Running Avg" row to avoid including it in the mean
        - Computes mean along axis=0 (down columns)
        - Skips NaN values using skipna=True
        - Updates both DataFrames with the calculated averages

        Example:
            >>> grade_report = GradeReport()
            >>> grade_report._build_running_avg()
            >>> grade_report.weekly_grades_df.loc["Running Avg", "Lab"]
            85.5  # Average of all Lab scores, excluding NaNs

        Returns:
            None
        """
        self.weekly_grades_df.loc["Running Avg"] = self.weekly_grades_df.drop(
            "Running Avg", errors="ignore"
        ).mean(axis=0, skipna=True)
        self.weekly_grades_df_display.loc["Running Avg"] = self.weekly_grades_df.drop(
            "Running Avg", errors="ignore"
        ).mean(axis=0, skipna=True)

    def drop_lowest_n_for_types(self, n, assignments_=None):
        """
        Exempts the lowest n assignments for each specified assignment type, with special handling for optional drops.

        This method processes assignments and drops the lowest scoring ones based on certain rules:
        1. For each assignment type, finds the n lowest scoring assignments
        2. Skips assignments that are in optional_drop_week
        3. Skips assignments that are in optional_drop_assignments
        4. Marks dropped assignments as exempted and tracks them in student_assignments_dropped

        Args:
            n (int): Number of lowest scores to exempt per assignment type
            assignments_ (list, optional): List of assignment types (names) to process.
                If None, processes assignments in self.dropped_assignments. Defaults to None.

        Example:
            >>> grade_report = GradeReport()
            >>> grade_report.drop_lowest_n_for_types(1) # Drop lowest score for each type
            >>> grade_report.drop_lowest_n_for_types(2, ['Lab']) # Drop 2 lowest Lab scores
        """
        from collections import defaultdict

        import numpy as np

        # Group assignments by name
        assignment_groups = defaultdict(list)
        for assignment in self.graded_assignments:
            if assignments_ is None:
                if (
                    assignment.name in self.dropped_assignments
                    and not assignment.exempted
                ):
                    assignment_groups[assignment.name].append(assignment)
            else:
                if assignment.name in assignments_ and not assignment.exempted:
                    assignment_groups[assignment.name].append(assignment)

        # Iterate over each specified assignment type and drop the lowest n scores
        for name, assignments in assignment_groups.items():
            # Filter assignments that are not already exempted (NaN scores should not count)
            valid_assignments = [a for a in assignments if not np.isnan(a.score_)]

            # Sort assignments by score in ascending order
            valid_assignments.sort(key=lambda a: a.score_)

            # Exempt the lowest `n` assignments
            dropped = []
            index = 0
            num_dropped = 0
            while index < n:
                valid_assignments[index + num_dropped].exempted = True
                if (
                    valid_assignments[index + num_dropped].week
                    in self.optional_drop_week
                ):
                    num_dropped += 1
                    continue

                if (
                    name,
                    valid_assignments[index + num_dropped].week,
                ) in self.optional_drop_assignments:
                    num_dropped += 1
                    continue

                dropped.append(valid_assignments[index + num_dropped])
                self.student_assignments_dropped.append(
                    valid_assignments[index + num_dropped]
                )
                index += 1

    def duplicate_scores(self):
        """Duplicate scores from one assignment to another.

        This method copies scores between assignments based on the duplicated_scores configuration.
        For each pair of assignments specified in duplicated_scores, it:
        - Gets the source assignment based on week and assignment type
        - Gets the target assignment to duplicate to
        - Copies the score, raw score, and exemption status from source to target

        The duplicated_scores configuration should be a list of tuples, where each tuple contains:
        - Source assignment: (week number, assignment type)
        - Target assignment: (week number, assignment type)

        This is useful for cases where the same work is counted for multiple assignments
        or when scores need to be propagated between related assignments.
        """

        for (week, assignment_type), (
            duplicate_week,
            duplicate_assignment_type,
        ) in duplicated_scores:
            assignment = self.get_graded_assignment(week, assignment_type)[0]
            duplicate_assignment = self.get_graded_assignment(
                duplicate_week, duplicate_assignment_type
            )[0]
            duplicate_assignment.score_ = assignment.score_
            duplicate_assignment._score = assignment._score
            duplicate_assignment.exempted = assignment.exempted
