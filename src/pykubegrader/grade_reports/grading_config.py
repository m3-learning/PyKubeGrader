from typing import Any

from pykubegrader.grade_reports.assignments import assignment_type

# Assignment types, weekly, and weight
# Total of 1st values in tuple should add up to 1.0
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
    assignment_type("final", False, (0.2, 0.4)),
]

# Custom grade adjustments, key is a tuple of assignment type and week, value is a lambda function that takes the score and returns the adjusted score
custom_grade_adjustments = {
    ("lecture", 3): lambda score: 100.0 if score > 0 else 0.0,
    ("lecture", 4): lambda score: 100.0 if score > 0 else 0.0,
    ("lecture", 5): lambda score: 100.0 if score > 0 else 0.0,
    ("lecture", 7): lambda score: 100.0,
    ("lecture", 9): lambda score: 100.0 if score > 0 else 0.0,
    ("quiz", 7): lambda score: min(score / 28 * 100, 100.0),
    ("labattendance", 8): lambda score: 100.0 if score > 0 else 0.0,
    ("labattendance", 2): lambda score: 100.0 if score > 0 else 0.0,
    ("labattendance", 9): lambda score: 100.0 if score > 0 else 0.0,
    ("practicequiz", 9): lambda score: min(score / 20 * 100, 100.0),
}

# Exempted assignments, key is a tuple of assignment type and week
globally_exempted_assignments = [
    ("labattendance", 1),
    ("readings", 6),
    ("quiz", 6),
    ("practicequiz", 6),
    ("lecture", 6),
    ("homework", 5),
    ("lab", 5),
    ("labattendance", 5),
]

# Common Assignment Aliases, these are other names used for the same assignment category
aliases = {
    "practicequiz": [
        "practice quiz",
        "practice-quiz",
        "practice quiz",
        "practice_quiz",
        "practicequiz",
    ],
    "labattendance": ["labattendance", "attendance", "attend"],
}

# Skipped assignments, key is a tuple of assignment type and week
skipped_assignments: dict[tuple, Any] = {}

# Dropped assignments a list of assignments which lowest score will be dropped
dropped_assignments = [
    "readings",
    "lecture",
    "practicequiz",
    "quiz",
    "homework",
    "lab",
    "labattendance",
]

# Duplicated scores, a list of tuples of assignment types and weeks where the scores will be duplicated
duplicated_scores = [[(7, "lab"), (7, "homework")], [(9, "lab"), (9, "homework")]]

# TAs and other users to skip in class grade report
skipped_users = [
    "JCA",
    "jca92",
    "cnp68",
    "dak329",
    "xz498",
    "ag4328",
    "rg897",
    "jce63",
    "qt49",
]

# Optional drop week, a list of weeks where the lowest score will be dropped
optional_drop_week = [1]

# Optional drop assignments, a list of tuples of assignment types and weeks where the lowest score will be dropped
optional_drop_assignments = [("lab", 7), ("homework", 7)]

# Excluded from running average, a list of assignment types that will be excluded from the running average calculation
exclude_from_running_avg = ["final", "practicefinal"]

max_week = 9
