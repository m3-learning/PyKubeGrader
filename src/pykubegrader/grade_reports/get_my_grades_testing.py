

# ##### CONFIGURATION #####

# weights = {
#     "homework": 0.15,
#     "lab": 0.15,
#     "lecture": 0.15,
#     "quiz": 0.15,
#     "readings": 0.15,
#     "labattendance": 0.05,
#     "practicequiz": 0.015,
#     "practicemidterm": 0.015,
#     "midterm": 0.15,
#     "practicefinal": 0.02,
#     "final": 0.2,
# }

# ##### END CONFIGURATION #####


# class GradeReport:
    
#     def __init__(self, start_date="2025-01-06", verbose=True):
#         self.start_date = start_date
#         self.verbose = verbose
#         self.weights = weights
       
#         self.assignments, self.student_subs = get_assignments_submissions()
#         self.new_grades_df = setup_grades_df(self.assignments)
#         self.new_weekly_grades = fill_grades_df(
#             self.new_grades_df, self.assignments, self.student_subs
#         )
#         self.current_week = get_current_week(self.start_date)
#         self.avg_grades_dict = get_average_weighted_grade(
#             self.assignments, self.current_week, self.new_weekly_grades, self.weights
#         )
    
#     @property
#     def weights(self):
#         return self.weights


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
