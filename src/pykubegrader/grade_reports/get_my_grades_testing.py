from pykubegrader.telemetry import get_assignments_submissions

# from pykubegrader.assignments import assignment_type

##### assignment.py #####


class assignment_type:

    def __init__(self, name, weekly, weight):
        self.name = name
        self.weekly = weekly
        self.weight = weight


class assignment(assignment_type):

    def __init__(self, name, weekly, weight, score, **kwargs):
        super().__init__(name, weekly, weight)
        self.score = score
        self.week = kwargs.get("week", None)
        self.exempted = kwargs.get("exempted", False)
        self.graded = kwargs.get("graded", False)
        self.students_exempted = kwargs.get("students_exempted", [])

    def add_exempted_students(self, students):
        self.students_exempted.extend(students)


#### BEGIN CONFIGURATION ####

assignments_list = [
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


##### END CONFIGURATION #####


class GradeReport:

    def __init__(self, start_date="2025-01-06", verbose=True):
        self.start_date = start_date
        self.verbose = verbose
        self.assignment_list = assignments_list

        # self.assignments, self.student_subs = get_assignments_submissions()
        # self.new_grades_df = setup_grades_df(self.assignments)
        # self.new_weekly_grades = fill_grades_df(
        #     self.new_grades_df, self.assignments, self.student_subs
        # )
        # self.current_week = get_current_week(self.start_date)
        # self.avg_grades_dict = get_average_weighted_grade(
        #     self.assignments, self.current_week, self.new_weekly_grades, self.weights
        # )

    @property
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self, new_weights):
        if not isinstance(new_weights, dict):
            raise ValueError("Weights must be a dictionary")
        self._weights = new_weights

    def setup_grades_df(self):

        assignment_types = [
            assignment for assignment in assignments_list if assignment.weekly
        ]

        assignment_types = list(set([a["assignment_type"] for a in self.assignments]))
        inds = [f"week{i + 1}" for i in range(11)] + ["Running Avg"]
        restruct_grades = {k: [0 for i in range(len(inds))] for k in assignment_types}
        new_weekly_grades = pd.DataFrame(restruct_grades, dtype=float)
        new_weekly_grades["inds"] = inds
        new_weekly_grades.set_index("inds", inplace=True)
        self.week_grades_df = new_weekly_grades


# def get_my_grades_testing(start_date="2025-01-06", verbose=True):
#     """takes in json.
#     reshapes columns into reading, lecture, practicequiz, quiz, lab, attendance, homework, exam, final.
#     fills in 0 for missing assignments
#     calculate running average of each category"""

#     # set up new df format
#     weights = {
#         "homework": 0.15,
#         "lab": 0.15,
#         "lecture": 0.15,
#         "quiz": 0.15,
#         "readings": 0.15,
#         # 'midterm':0.15, 'final':0.2
#         "labattendance": 0.05,
#         "practicequiz": 0.05,
#     }

#     assignments, student_subs = get_assignments_submissions()

#     new_grades_df = setup_grades_df(assignments)

#     new_weekly_grades = fill_grades_df(new_grades_df, assignments, student_subs)

#     current_week = get_current_week(start_date)

#     avg_grades_dict = get_average_weighted_grade(
#         assignments, current_week, new_weekly_grades, weights
#     )

#     if verbose:
#         max_key_length = max(len(k) for k in weights.keys())
#         for k, v in avg_grades_dict.items():
#             print(f"{k:<{max_key_length}}:\t {v:.2f}")

#     return new_weekly_grades  # get rid of test and running avg columns
