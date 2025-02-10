from pykubegrader.telemetry import get_assignments_submissions
from dateutil import parser
from pykubegrader.graders.late_assignments import calculate_late_submission

import pandas as pd
from datetime import datetime

import numpy as np


# from pykubegrader.assignments import assignment_type

##### assignment.py #####


class assignment_type:

    def __init__(self, name, weekly, weight):
        self.name = name
        self.weekly = weekly
        self.weight = weight


class Assignment(assignment_type):

    def __init__(
        self, name, weekly, weight, score, grade_adjustment_func=None, **kwargs
    ):
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
        self.students_exempted.extend(students)

    def update_score(self, submission):

        if self.exempted:
            self.score = np.nan
            return self.score
        else:
            score_ = self.grade_adjustment(submission)

            # Update the score if the new score is higher
            if score_ > self.score:
                self.score = score_

            return self.score

    def grade_adjustment(self, submission):
        """Apply the adjustment function if provided."""

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
    assignment_type("midterm", False, 0.015),
    assignment_type("practicefinal", False, 0.02),
    assignment_type("final", False, 0.015),
]

# Dictionary to store custom grading functions for specific assignments
# custom_grade_adjustments = {
#     ("quiz", 3): lambda score: score * 1.10,  # Example: Boost Quiz in Week 3 by 10%
#     ("homework", 5): lambda score: min(score + 5, 100),  # Example: Add 5 points to Homework in Week 5
# }
custom_grade_adjustments = {("quiz", 3): lambda score: "Exempt"}

globally_exempted_assignments = [("quiz", 2)]

# Common Assignment Aliases
aliases = {
    "practicequiz": "practice quiz",
    "practice-quiz": "practice quiz",
    "attend": "attendance",
    "attendance": "attendance",
}

skipped_assignments = {}

##### END CONFIGURATION #####


class GradeReport:

    def __init__(self, start_date="2025-01-06", verbose=True):
        self.start_date = start_date
        self.verbose = verbose
        self.assignment_type_list = assignment_type_list
        self.aliases = aliases
        self.globally_exempted_assignments = globally_exempted_assignments

        self.assignments, self.student_subs = get_assignments_submissions()

        self.setup_grades_df()
        self.build_assignments()
        self.update_global_exempted_assignments()
        self.calculate_grades()
        self.update_weekly_table()
        # self.new_weekly_grades = fill_grades_df(
        #     self.new_grades_df, self.assignments, self.student_subs
        # )
        # self.current_week = get_current_week(self.start_date)
        # self.avg_grades_dict = get_average_weighted_grade(
        #     self.assignments, self.current_week, self.new_weekly_grades, self.weights
        # )

    def update_weekly_table(self):
        for assignment in self.graded_assignments:
            if assignment.weekly:
                self.weekly_grades_df.loc[
                    f"week{assignment.week}", assignment.name
                ] = assignment.score

    def update_global_exempted_assignments(self):

        for assignment_type, week in self.globally_exempted_assignments:

            self.get_graded_assignment(week, assignment_type)[0].exempted = True

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

    def graded_assignment_constructor(self, assignment_type, **kwargs):
        custom_func = custom_grade_adjustments.get((assignment_type.name, None), None)

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

        for assignment in self.graded_assignments:

            filtered_submission = self.filter_submissions(
                assignment.week, assignment.name
            )

            for submission in filtered_submission:
                assignment.update_score(submission)

    def filter_submissions(self, week_number, assignment_type):
        # Normalize the assignment type using aliases
        normalized_type = self.aliases.get(
            assignment_type.lower(), assignment_type.lower()
        )

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
            if assignment["week_number"] == week_number
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
                and a.week == week_number,
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
