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

# Replacements for normalization
# This is a dictionary that maps the original assignment type to the normalized assignment type.
replacements = {
    "practicequiz": "practice quiz",
    "practice-quiz": "practice quiz",
    "attend": "attendance",
    "attendance": "attendance",
}
