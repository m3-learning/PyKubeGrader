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

        self.assignments, self.student_subs = get_assignments_submissions()
        self.new_grades_df = self.setup_grades_df()
        # self.new_weekly_grades = fill_grades_df(
        #     self.new_grades_df, self.assignments, self.student_subs
        # )
        # self.current_week = get_current_week(self.start_date)
        # self.avg_grades_dict = get_average_weighted_grade(
        #     self.assignments, self.current_week, self.new_weekly_grades, self.weights
        # )

    def get_weekly_assignments(self):
        """Get all weekly assignments from the assignment list configuration"""
        weekly_assignments = [
            assignment for assignment in self.assignment_list if assignment.weekly
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
        restruct_grades = {k.name: [0 for i in range(len(inds))] for k in weekly_assignments}
        new_weekly_grades = pd.DataFrame(restruct_grades, dtype=float)
        new_weekly_grades["inds"] = inds
        new_weekly_grades.set_index("inds", inplace=True)
        self.week_grades_df = new_weekly_grades
