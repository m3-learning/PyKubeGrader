# TODO: if not due yet and score is 0, make NAN, fix the rendering

from pykubegrader.telemetry import get_assignments_submissions
from pykubegrader.grade_reports.assignments import Assignment
from pykubegrader.grade_reports.grading_config import (
    assignment_type_list,
    aliases,
    globally_exempted_assignments,
    dropped_assignments,
    optional_drop_week,
    exclude_from_running_avg,
    custom_grade_adjustments,
    duplicated_scores,
)

import pandas as pd
from datetime import datetime
from IPython.display import display
import numpy as np

from ..telemetry import get_assignments_submissions


class GradeReport:
    """Class to generate a grade report for a course and perform grade calculations for each student."""

    def __init__(self, start_date="2025-01-06", verbose=True, params=None, display_ = True):
        """Initializes an instance of the GradeReport class.
        Args:
            start_date (str, optional): The start date of the course. Defaults to "2025-01-06".
            verbose (bool, optional): Indicates if verbose output should be displayed. Defaults to True.
        """
        self.assignments, self.student_subs = get_assignments_submissions(params=params) 

        self.start_date = start_date
        self.verbose = verbose
        self.assignment_type_list = assignment_type_list
        self.aliases = aliases
        self.globally_exempted_assignments = globally_exempted_assignments
        self.dropped_assignments = dropped_assignments
        self.optional_drop_week = optional_drop_week

        # assignments that have been dropped for a given students.
        self.student_assignments_dropped = []

        self.setup_grades_df()
        self.build_assignments()
        self.update_global_exempted_assignments()
        self.calculate_grades()
        self.update_assignments_not_due_yet()
        self.calculate_grades()
        self.duplicate_scores()
        self.drop_lowest_n_for_types(1)
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

    @staticmethod
    def highlight_nans(nan_df, display_df, color='red'):
        """
        Highlights NaN values from nan_df on display_df.
        
        Parameters:
        nan_df (pd.DataFrame): DataFrame containing NaNs to be highlighted.
        display_df (pd.DataFrame): DataFrame to be recolored.
        color (str): Background color for NaNs. Default is 'red'.
        
        Returns:
        pd.io.formats.style.Styler: Styled DataFrame with NaNs highlighted.
        """
        # Ensure both DataFrames have the same index and columns
        nan_mask = nan_df.isna().reindex_like(display_df)
        
        # Function to apply the highlight conditionally
        def apply_highlight(row):
            return [
                f'background-color: {color}' if nan_mask.loc[row.name, col] else ''
                for col in row.index
            ]

        # Apply the highlighting row-wise
        styled_df = display_df.style.apply(apply_highlight, axis=1)
        
        return styled_df

    def update_assignments_not_due_yet(self):
        """
        Updates the score of assignments that are not due yet to NaN.
        """
        for assignment in self.graded_assignments:
            if assignment.due_date:
                # Convert due date to datetime object
                due_date = datetime.fromisoformat(assignment.due_date.replace("Z", "+00:00"))
                if due_date > datetime.now(due_date.tzinfo) and assignment.score == 0:
                    assignment.score = np.nan
                    assignment._score = "---"
                    assignment.exempted = True
                    
                    
    def color_cells(self, styler, week_list, assignment_list):
        if week_list:
            week = week_list.pop()
            assignment = assignment_list.pop()

            # Apply the style to the current cell
            styler = styler.set_properties(
                subset=pd.IndexSlice[[week], [assignment]],
                **{'background-color': 'yellow'}
            )
            # Recursive call
            return self.color_cells(styler, week_list, assignment_list)
        else:
            return styler

    def _calculate_final_average(self):
        total_percentage = 1
        df_ = self.compute_final_average()
        score_earned = 0

        for assignment_type in self.assignment_type_list:
            if assignment_type.name in exclude_from_running_avg:
                total_percentage -= assignment_type.weight

            score_earned += assignment_type.weight * df_[assignment_type.name]

        self.final_grade = score_earned / total_percentage
        self.weighted_average_grades = pd.concat(
            [
                pd.DataFrame(self.final_grades),
                pd.DataFrame(
                    {"Running Avg": [self.final_grade]},
                    index=["Weighted Average Grade"],
                ),
            ]
        )

    # def grade_report(self):
    #     """Generates a grade report for the course.
    #     Returns:
    #         pd.DataFrame: A DataFrame containing the grade report or weekly grades only.
    #     """
    #     self._update_running_avg()
    #     return self.weekly_grades_df
    
    def update_weekly_table(self):
        self._update_weekly_table_nan()
        self._update_weekly_table_scores()
    
    # TODO: populate with average scores calculated from the exempted 
    def _update_weekly_table_scores(self):
        for assignment in self.graded_assignments:
            if assignment.weekly:
                self.weekly_grades_df_display.loc[f"week{assignment.week}", assignment.name] = (
                    assignment._score
                )

    def _update_weekly_table_nan(self):
        """Updates the weekly grades table with the calculated scores."""
        for assignment in self.graded_assignments:
            if assignment.weekly:
                self.weekly_grades_df.loc[f"week{assignment.week}", assignment.name] = (
                    assignment.score
                )

    def update_global_exempted_assignments(self):
        """Updates the graded assignments with the globally exempted assignments. If assignment doesn't exist, pass."""
        for assignment_type, week in self.globally_exempted_assignments:
            try:
                self.get_graded_assignment(week, assignment_type)[0].exempted = True
                self.get_graded_assignment(week, assignment_type)[0]._score = "---"
            except:  # noqa: E722
                pass

    def build_assignments(self):
        """Generates a list of Assignment objects for each week, applying custom adjustments where needed."""
        self.graded_assignments = []
        weekly_assignments = self.get_weekly_assignments()

        for assignment_type in weekly_assignments:
            for week in range(1, self.get_num_weeks() + 1):  # Weeks start at 1
                self.graded_assignment_constructor(assignment_type, week=week)

        non_weekly_assignments = self.get_non_weekly_assignments()

        for assignment_type in non_weekly_assignments:
            self.graded_assignment_constructor(assignment_type)

    def graded_assignment_constructor(self, assignment_type: str, **kwargs):
        """Constructs a graded assignment object and appends it to the graded_assignments list.

        Args:
            assignment_type (str): Type of assignment. Options: readings, lecture, practicequiz, quiz, homework, lab, labattendance, practicemidterm, midterm, practicefinal, final.
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
            # filters the submissions for an assignment and gets the last due date
            due_date=self.determine_due_date(filtered_assignments),
            max_score=self.get_max_score(filtered_assignments),
            **kwargs,
        )
        self.graded_assignments.append(new_assignment)

    def calculate_grades(self):
        """Calculates the grades for each student based on the graded assignments.
        If there are filtered assignments, the score is updated based on the submission.
        Otherwise,
        """
        for assignment in self.graded_assignments:
            filtered_submission = self.filter_submissions(
                assignment.week, assignment.name
            )

            if filtered_submission:
                for submission in filtered_submission:
                    assignment.update_score(submission)

            # runs if there are no filtered submissions
            else:
                assignment.update_score()

    def compute_final_average(self):
        """
        Computes the final average by combining the running average from weekly assignments
        and the midterm/final exam scores.
        """

        # Extract running average from the weekly table
        self.final_grades = self.weekly_grades_df.loc["Running Avg"]

        for assignment in self.graded_assignments:
            if not assignment.weekly:
                self.final_grades[f"{assignment.name}"] = assignment.score

        return self.final_grades

    def filter_submissions(self, week_number, assignment_type):
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
        return list(
            filter(
                lambda a: isinstance(a, Assignment)
                and a.name == assignment_type
                and (week_number is None or a.week == week_number),
                self.graded_assignments,
            )
        )

    def get_max_score(self, filtered_assignments):
        if not filtered_assignments:
            return None

        return max(filtered_assignments, key=lambda x: x["id"])["max_score"]

    def determine_due_date(self, filtered_assignments):
        if not filtered_assignments:
            return None  # Return None if the list is empty

        # Convert due_date strings to datetime objects and find the max
        max_due = max(
            filtered_assignments,
            key=lambda x: datetime.fromisoformat(x["due_date"].replace("Z", "+00:00")),
        )

        return max_due["due_date"]  # Return the max due date as a string

    def get_non_weekly_assignments(self):
        """Get all weekly assignments from the assignment list configuration"""
        non_weekly_assignments = [
            assignment
            for assignment in self.assignment_type_list
            if not assignment.weekly
        ]
        return non_weekly_assignments

    def get_weekly_assignments(self):
        """Get all weekly assignments from the assignment list configuration"""
        weekly_assignments = [
            assignment for assignment in self.assignment_type_list if assignment.weekly
        ]
        return weekly_assignments

    def get_num_weeks(self):
        """Get the number of weeks in the course"""
        max_week_number = max(item["week_number"] for item in self.assignments)
        return max_week_number

    def setup_grades_df(self):
        weekly_assignments = self.get_weekly_assignments()
        max_week_number = self.get_num_weeks()
        inds = [f"week{i + 1}" for i in range(max_week_number)] + ["Running Avg"]
        restruct_grades = {
            k.name: [0 for i in range(len(inds))] for k in weekly_assignments
        }
        new_weekly_grades = pd.DataFrame(restruct_grades, dtype=float)
        new_weekly_grades["inds"] = inds
        new_weekly_grades.set_index("inds", inplace=True)
        self.weekly_grades_df = new_weekly_grades
        self.weekly_grades_df_display = new_weekly_grades.copy().astype(str) 
        
    def _build_running_avg(self):
        """
        Subfunction to compute and update the Running Avg row, handling NaNs.
        """
        
        self.weekly_grades_df.loc["Running Avg"] = self.weekly_grades_df.drop(
            "Running Avg", errors="ignore"
        ).mean(axis=0, skipna=True)
        self.weekly_grades_df_display.loc["Running Avg"] = self.weekly_grades_df.drop(
            "Running Avg", errors="ignore"
        ).mean(axis=0, skipna=True)

    def drop_lowest_n_for_types(self, n, assignments_=None):
        """
        Exempts the lowest n assignments for each specified assignment type.
        If the lowest dropped score is from week 1, an additional lowest score is dropped.

        :param assignments_: List of assignment types (names) to process.
        :param n: Number of lowest scores to exempt per type.
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
            valid_assignments = [a for a in assignments if not np.isnan(a.score)]

            # Sort assignments by score in ascending order
            valid_assignments.sort(key=lambda a: a.score)

            # Exempt the lowest `n` assignments
            dropped = []
            i = 0
            j = 0
            while i < n:
                valid_assignments[i+j].exempted = True
                if valid_assignments[i+j].week in self.optional_drop_week:
                    j += 1
                    continue
                dropped.append(valid_assignments[i+j])
                self.student_assignments_dropped.append(valid_assignments[i+j])
                i += 1
                
        self.calculate_grades()

    def duplicate_scores(self):
        """Duplicate scores from one assignment to another"""
        
        for (week, assignment_type), (duplicate_week, duplicate_assignment_type) in duplicated_scores:
            assignment = self.get_graded_assignment(week, assignment_type)[0]
            duplicate_assignment = self.get_graded_assignment(duplicate_week, duplicate_assignment_type)[0]
            duplicate_assignment.score = assignment.score
            duplicate_assignment._score = assignment._score
            duplicate_assignment.exempted = assignment.exempted
            