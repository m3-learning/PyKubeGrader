from pykubegrader.telemetry import get_assignments_submissions, get_all_students
from dateutil import parser
from pykubegrader.graders.late_assignments import calculate_late_submission

import pandas as pd
from datetime import datetime

import numpy as np


# from pykubegrader.assignments import assignment_type

##### assignment.py #####


class assignment_type:
    """ Base class for assignment types."""
    def __init__(self, name:str, weekly:bool, weight:float):
        """Initializes an instance of the assignment_type class.
        Args:
            name (str): The name of the assignment.
            weekly (bool): Indicates if the assignment is weekly.
            weight (float): The weight of the assignment in the overall grade."""
        self.name = name
        self.weekly = weekly
        self.weight = weight


class Assignment(assignment_type):
    """ Class for storing and updating assignment scores."""
    def __init__(
        self, name:str, weekly:bool, weight:float, score:float, grade_adjustment_func=None, **kwargs
    ):
        """Initializes an instance of the Assignment class.

        Args:
            name (str): The name of the assignment.
            weekly (bool):  Indicates if the assignment is weekly.
            weight (float): The weight of the assignment in the overall grade.
            score (float): The current score of the assignment.
            grade_adjustment_func (optional): Used to calculate the grade in the case of late or exempted submissions. Defaults to None.
        """
        super().__init__(name, weekly, weight)
        self.score = score
        self.week = kwargs.get("week", None)
        self.exempted = kwargs.get("exempted", False)
        self.graded = kwargs.get("graded", False)
        self.late_adjustment = kwargs.get("late_adjustment", True)
        self.students_exempted = kwargs.get("students_exempted", [])
        self.due_date = kwargs.get("due_date", None)
        self.max_score = kwargs.get("max_score", None)

        # Store the function for later use
        self.grade_adjustment_func = grade_adjustment_func

    def add_exempted_students(self, students):
        """Add students to the exempted list.
        Args:
            students (list): List of student IDs to exempt from the assignment.
        """
        self.students_exempted.extend(students)

    def update_score(self, submission=None):
        """Update the score of the assignment based on the submission.

        Args:
            submission (dict, optional): Defaults to None.

        Returns:
            float: Adjusted submission score
        """
        if self.exempted:
            self.score = np.nan
            return self.score
        elif submission is not None:
            
            # deal with incomplete submissions
            score_ = self.grade_adjustment(submission)

                
            # Update the score if the new score is higher
            if score_ > self.score:
                self.score = score_

            return self.score
        # sets the score to zero if not exempted and no submission
        else:
            self.score = 0
            return self.score

    def grade_adjustment(self, submission):
        """Apply the adjustment function if provided.
        Args:
            submission (dict): Submission data.
        Returns:
            float: Score adjusted for lateness or exemptions. If none are present, returns 0.
        """

        score = submission["raw_score"]
        entry_date = parser.parse(submission["timestamp"])

        if self.grade_adjustment_func:
            return self.grade_adjustment_func(score)
        else:
            if self.late_adjustment:

                # Convert to datetime object
                due_date = datetime.fromisoformat(self.due_date.replace("Z", "+00:00"))

                late_modifier = calculate_late_submission(
                    due_date.strftime("%Y-%m-%d %H:%M:%S"),
                    entry_date.strftime("%Y-%m-%d %H:%M:%S"),
                )

                # return score for on-time submissions
                return (score / self.max_score) * late_modifier

            else:

                # return score for on-time submissions
                if entry_date < self.due_date:
                    return score / self.max_score

                # zero score for late submissions w/o late adjustment
                else:
                    return 0


#### BEGIN CONFIGURATION ####

assignment_type_list = [
    assignment_type("readings", True, 0.15),
    assignment_type("lecture", True, 0.15),
    assignment_type("practicequiz", True, 0.015),
    assignment_type("quiz", True, 0.15),
    assignment_type("homework", True, 0.15),
    assignment_type("lab", True, 0.15),
    assignment_type("labattendance", True, 0.05),
    assignment_type("practicemidterm", False, 0.015),
    assignment_type("midterm", False, 0.15),
    assignment_type("practicefinal", False, 0.02),
    assignment_type("final", False, 0.2),
]

# Dictionary to store custom grading functions for specific assignments
# custom_grade_adjustments = {
#     ("quiz", 3): lambda score: score * 1.10,  # Example: Boost Quiz in Week 3 by 10%
#     ("homework", 5): lambda score: min(score + 5, 100),  # Example: Add 5 points to Homework in Week 5
# }

custom_grade_adjustments = {
    ("lecture", 3): lambda score: 100.0 if score > 0 else 0.0,
    ("lecture", 4): lambda score: 100.0 if score > 0 else 0.0,
    ("lecture", 5): lambda score: 100.0 if score > 0 else 0.0,
}

globally_exempted_assignments = [
    ("readings", 6),
    ("quiz", 6),
    ("practicequiz", 6),
    ("lecture", 6),
    ("homework", 5),
    ("lab", 5),
    ("labattendance", 5),
]

# Common Assignment Aliases
aliases = {
    "practicequiz": "practice quiz",
    "practice-quiz": "practice quiz",
    "attend": "attendance",
    "attendance": "attendance",
}

skipped_assignments = {}

dropped_assignments = [
    "readings",
    "lecture",
    "practicequiz",
    "quiz",
    "homework",
    "lab",
    "labattendance",
]

optional_drop_week = [1]

exclude_from_running_avg = ["final"]

##### END CONFIGURATION #####


class GradeReport:
    """Class to generate a grade report for a course and perform grade calculations for each student.
    """
    def __init__(self, start_date="2025-01-06", verbose=True):
        """Initializes an instance of the GradeReport class.
        Args:
            start_date (str, optional): The start date of the course. Defaults to "2025-01-06".
            verbose (bool, optional): Indicates if verbose output should be displayed. Defaults to True.
        """
        self.start_date = start_date
        self.verbose = verbose
        self.assignment_type_list = assignment_type_list
        self.aliases = aliases
        self.globally_exempted_assignments = globally_exempted_assignments
        self.dropped_assignments = dropped_assignments
        self.optional_drop_week = optional_drop_week

        self.assignments, self.student_subs = get_assignments_submissions()

        self.setup_grades_df()
        self.build_assignments()
        self.update_global_exempted_assignments()
        self.calculate_grades()
        self.drop_lowest_n_for_types(1)
        self.update_weekly_table()
        self._build_running_avg()
        self._calculate_final_average()

    def _calculate_final_average(self):
        """Calculates the final average for the course and creates breakdowns for each assignment type. 
        Sets class attributes `self.final_grade` for final grade and 'self.weighted_average_grades' for weighted average grades dataframe.
        """
        total_percentage = 1
        df_ = self.compute_final_average()
        score_earned = 0

        for assignment_type in self.assignment_type_list:

            if assignment_type.name in exclude_from_running_avg:
                total_percentage -= assignment_type.weight
                
            score_earned += assignment_type.weight * df_[assignment_type.name]
            
        self.final_grade = score_earned / total_percentage
        self.weighted_average_grades = pd.concat(
            [ pd.DataFrame(self.final_grades),
              pd.DataFrame({'Running Avg':[self.final_grade]}, index=['Weighted Average Grade']) ] )

    def grade_report(self):
        """Generates a grade report for the course.
        Returns:
            pd.DataFrame: A DataFrame containing the grade report or weekly grades only.
        """
        self._update_running_avg()
        return self.weekly_grades_df

    def update_weekly_table(self):
        """Updates the weekly grades table with the calculated scores.
        """
        for assignment in self.graded_assignments:
            if assignment.weekly:
                self.weekly_grades_df.loc[f"week{assignment.week}", assignment.name] = (
                    assignment.score
                )

    def update_global_exempted_assignments(self):
        """Updates the graded assignments with the globally exempted assignments. If assignment doesn't exist, pass.
        """
        for assignment_type, week in self.globally_exempted_assignments:
            try:
                self.get_graded_assignment(week, assignment_type)[0].exempted = True
            except:
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

    def graded_assignment_constructor(self, assignment_type:str, **kwargs):
        """Constructs a graded assignment object and appends it to the graded_assignments list.

        Args:
            assignment_type (str): Type of assigment. Options: readings, lecture, practicequiz, quiz, homework, lab, labattendance, practicemidterm, midterm, practicefinal, final.
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
        Otherwise, check other adjustments.
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
            assignment_type.lower(), assignment_type.lower()
        )

        if week_number:
            # Filter the assignments based on the week number and normalized assignment type
            filtered = [
                assignment
                for assignment in self.student_subs
                if assignment["week_number"] == week_number
                and self.aliases.get(
                    assignment["assignment_type"].lower(),
                    assignment["assignment_type"].lower(),
                )
                == normalized_type
            ]

        # If week_number is None, filter based on the normalized assignment type only
        else:
            # Filter the assignments based on the normalized assignment type
            filtered = [
                assignment
                for assignment in self.student_subs
                if self.aliases.get(
                    assignment["assignment_type"].lower(),
                    assignment["assignment_type"].lower(),
                )
                == normalized_type
            ]

        return filtered

    def get_assignment(self, week_number, assignment_type):
        # Normalize the assignment type using aliases
        normalized_type = self.aliases.get(
            assignment_type.lower(), assignment_type.lower()
        )

        # Filter the assignments based on the week number and normalized assignment type
        filtered = [
            assignment
            for assignment in self.assignments
            if (assignment["week_number"] == week_number or week_number is None)
            and self.aliases.get(
                assignment["assignment_type"].lower(),
                assignment["assignment_type"].lower(),
            )
            == normalized_type
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

        max_score = min(
            filtered_assignments,
            key=lambda x: x["max_score"],
        )

        return max_score["max_score"]

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

    def _build_running_avg(self):
        """
        Subfunction to compute and update the Running Avg row, handling NaNs.
        """
        self.weekly_grades_df.loc["Running Avg"] = self.weekly_grades_df.mean(
            axis=0, skipna=True
        )

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
            for i in range(min(n, len(valid_assignments))):
                valid_assignments[i].exempted = True
                dropped.append(valid_assignments[i])

            # Check if the lowest dropped assignment is from week 1
            if dropped and any(a.week in self.optional_drop_week for a in dropped):
                # Find the next lowest non-exempted assignment and drop it
                for a in valid_assignments:
                    if not a.exempted:
                        a.exempted = True
                        break

        self.calculate_grades()


#################################################
# Class Grades
#################################################
from pykubegrader.telemetry import get_all_students
from build.passwords import password, user
import tqdm
class ClassGradeReport():
    
    def __init__(self):
        self.student_list = get_all_students(user,password)
        self.student_list.sort()

        self.setup_class_grades()
        self.fill_class_grades()

    def setup_class_grades(self):
        self.all_student_grades_df = pd.DataFrame(np.nan, 
                  index=self.student_list, 
                  columns=[a.name for a in assignment_type_list]+['Weighted Average Grade'] )

    def fill_class_grades(self):
        for student in tqdm.tqdm(self.student_list):
            report = GradeReport(params={"username": student})
            weighted = report.weighted_average_grades.transpose()     
            self.all_student_grades_df.loc[student] = weighted['Weighted Average Grade']
    
    
    # def fill_grades_df(self, student_subs):

    # for assignment in assignments:

    #     # get the assignment from all submissions
    #     subs = [ sub for sub in student_subs if (sub['assignment_type']==assignment['assignment_type']) and (sub['week_number']==assignment['week_number']) ]
    #     # print(assignment, subs)
    #     # print(assignment)
    #     # print(student_subs[:5])
    #     if assignment["assignment_type"] == "lecture":
    #         if sum([sub["raw_score"] for sub in subs]) > 0: # TODO: good way to check for completion?
    #             new_weekly_grades.loc[f"week{assignment['week_number']}", "lecture"] = 1.0
    #     if assignment["assignment_type"] == "final":
    #         continue
    #     if assignment["assignment_type"] == "midterm":
    #         continue
    #     if len(subs) == 0:
    #         # print(assignment['title'], 0, assignment['max_score'])
    #         continue
    #     elif len(subs) == 1:
    #         grade = subs[0]["raw_score"] / assignment["max_score"]
    #         # print(assignment['title'], sub['raw_score'], assignment['max_score'])
    #     else:
    #         # get due date from assignment
    #         due_date = parser.parse(assignment["due_date"])
    #         grades = []
    #         for sub in subs:
    #             entry_date = parser.parse(sub["timestamp"])
    #             if entry_date <= due_date:
    #                 grades.append(sub["raw_score"])
    #             else:
    #                 grades.append(
    #                     calculate_late_submission(
    #                         due_date.strftime("%Y-%m-%d %H:%M:%S"),
    #                         entry_date.strftime("%Y-%m-%d %H:%M:%S"),
    #                     )
    #                 )
    #         # print(assignment['title'], grades, assignment['max_score'])
    #         grade = max(grades) / assignment["max_score"]

    #     # fill out new df with max
    #     new_weekly_grades.loc[
    #         f"week{assignment['week_number']}", assignment["assignment_type"]
    #     ] = grade

    # # Merge different names
    # new_weekly_grades["attend"] = new_weekly_grades[["attend", "attendance"]].max(axis=1)
    # new_weekly_grades["practicequiz"] = new_weekly_grades[["practicequiz", "practice-quiz"]].max(axis=1)
    # new_weekly_grades["practicemidterm"] = new_weekly_grades[["practicemidterm", "PracticeMidterm"]].max(axis=1)
    # new_weekly_grades.drop(
    #     ["attendance", "practice-quiz", "test", "PracticeMidterm"],
    #     axis=1,
    #     inplace=True,
    #     errors="ignore",
    # )

    # return new_weekly_grades
