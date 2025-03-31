from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Tuple, Union

from pykubegrader.grade_reports.assignments import AssignmentType


@dataclass
class GradeConfig:
    """
    Configuration class to represent grading scheme and student management.

    Attributes:
        assignment_types (List[AssignmentType]): List of assignment categories.
        global_extensions_AVL (Dict[str, int]): Global extensions available (minutes) keyed by student ID.
        custom_grade_adjustments (Dict[Tuple[str, int], Callable[[float], float]]): Custom grade adjustments per assignment type and week.
        globally_exempted_assignments (List[Tuple[str, int]]): List of globally exempted assignments by type and week.
        aliases (Dict[str, List[str]]): Alternative names for assignment types.
        skipped_assignments (Dict[Tuple[str, int], Any]): Assignments explicitly skipped.
        dropped_assignments (List[str]): List of assignment types where the lowest score is dropped.
        duplicated_scores (List[List[Tuple[int, str]]]): Scores that should be duplicated from one assignment to another.
        skipped_users (List[str]): Users to exclude from reports (e.g., teaching assistants).
        optional_drop_week (List[int]): Weeks eligible for dropping the lowest score.
        optional_drop_assignments (List[Tuple[str, int]]): Assignments eligible for dropping the lowest score.
        exclude_from_running_avg (List[str]): Assignments excluded from running average calculations.
        max_week (int): Maximum number of weeks in the grading period.
        students_to_include (List[str]): List of student IDs to include in the report.
        grade_ranges (List[Tuple[int, int, str]]): Grade thresholds defining letter grades.
    """

    assignment_types: List[AssignmentType]
    global_extensions_AVL: Dict[str, int]
    custom_grade_adjustments: Dict[Tuple[str, int], Callable[[float], float]]
    globally_exempted_assignments: List[Tuple[str, int]]
    aliases: Dict[str, List[str]]
    skipped_assignments: Dict[Tuple[str, int], Any]
    dropped_assignments: List[str]
    duplicated_scores: List[List[Tuple[int, str]]]
    skipped_users: List[str]
    optional_drop_week: List[int]
    optional_drop_assignments: List[Tuple[str, int]]
    exclude_from_running_avg: List[str]
    max_week: int
    students_to_include: List[str]
    grade_ranges: List[Tuple[int, int, str]]


# Example usage
grade_config = GradeConfig(
    assignment_types=[
        AssignmentType("quiz", True, 0.15),
        AssignmentType("final", False, (0.2, 0.4)),
    ],
    global_extensions_AVL={"student123": 2880},  # 48 hours
    custom_grade_adjustments={
        ("quiz", 7): lambda score: min(score / 28 * 100, 100.0),
    },
    globally_exempted_assignments=[("quiz", 6)],
    aliases={"quiz": ["quiz", "test"]},
    skipped_assignments={},
    dropped_assignments=["quiz"],
    duplicated_scores=[[(7, "lab"), (7, "homework")]],
    skipped_users=["TA1", "TA2"],
    optional_drop_week=[1],
    optional_drop_assignments=[("homework", 7)],
    exclude_from_running_avg=["final"],
    max_week=10,
    students_to_include=["student123", "student456"],
    grade_ranges=[(90, 100, "A"), (80, 90, "B"), (0, 80, "F")],
)


