from pykubegrader.telemetry import get_assignments_submissions

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
        self.students_exempted = kwargs.get("students_exempted", [])

        # Store the function for later use
        self.grade_adjustment_func = grade_adjustment_func

    def add_exempted_students(self, students):
        self.students_exempted.extend(students)
        
    def get_grade(self):
        """Get the grade of the assignment."""
        return self.grade_adjustment()

    def grade_adjustment(self):
        """Apply the adjustment function if provided."""
        if self.grade_adjustment_func:
            return self.grade_adjustment_func(self.score)
        else:
            return self.score


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
custom_grade_adjustments = {}

# Replacements for normalization
replacements = {
        "practicequiz": "practice quiz",
        "practice-quiz": "practice quiz",
        "attend": "attendance",
        "attendance": "attendance",
    }

##### END CONFIGURATION #####


class GradeReport:

    def __init__(self, start_date="2025-01-06", verbose=True):
        self.start_date = start_date
        self.verbose = verbose
        self.assignment_type_list = assignment_type_list

        self.assignments, self.student_subs = get_assignments_submissions()
        self.setup_grades_df()
        self.build_assignments() 
        # self.new_weekly_grades = fill_grades_df(
        #     self.new_grades_df, self.assignments, self.student_subs
        # )
        # self.current_week = get_current_week(self.start_date)
        # self.avg_grades_dict = get_average_weighted_grade(
        #     self.assignments, self.current_week, self.new_weekly_grades, self.weights
        # )
        
    def build_assignments(self):
        """Generates a list of Assignment objects for each week, applying custom adjustments where needed."""
        self.graded_assignments = []
        weekly_assignments = self.get_weekly_assignments()

        for assignment_type in weekly_assignments:
            for week in range(1, self.get_num_weeks() + 1):  # Weeks start at 1
                
                self.graded_assignment_constructor(assignment_type)
                
        non_weekly_assignments = self.get_non_weekly_assignments()
        
        for assignment_type in non_weekly_assignments:
            
            self.graded_assignment_constructor(assignment_type)

    def graded_assignment_constructor(self, assignment_type):
        custom_func = custom_grade_adjustments.get((assignment_type.name, None), None)
        new_assignment = Assignment(
                name=assignment_type.name,
                weekly=assignment_type.weekly,
                weight=assignment_type.weight,
                score=0,
                grade_adjustment_func=custom_func,
            )
        self.graded_assignments.append(new_assignment)          
                
    def get_non_weekly_assignments(self):
        """Get all weekly assignments from the assignment list configuration"""
        non_weekly_assignments = [
            assignment for assignment in self.assignment_type_list if not assignment.weekly
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
        restruct_grades = {k.name: [0 for i in range(len(inds))] for k in weekly_assignments}
        new_weekly_grades = pd.DataFrame(restruct_grades, dtype=float)
        new_weekly_grades["inds"] = inds
        new_weekly_grades.set_index("inds", inplace=True)
        self.weekly_grades_df = new_weekly_grades
        
    #def fill_grades_df(self, student_subs):
        
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
