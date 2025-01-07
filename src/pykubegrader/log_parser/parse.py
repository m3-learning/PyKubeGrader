from dataclasses import dataclass, field
from typing import Any, Optional, TypedDict


class LogParserResults(TypedDict):
    student_information: dict[str, str]
    week: Optional[str]
    week_num: Optional[int]
    assignment_type: Optional[str]
    assignment_information: dict[str, Any]
    assignment_scores: dict[str, Any]


@dataclass
class LogParser:
    """
    A class for parsing chronological logs and extracting information.
    Handles both assignment info and question-level details.
    """

    log_lines: list[str]
    week_tag: Optional[str] = None
    student_info: dict[str, str] = field(default_factory=dict)
    assignments: dict[str, dict] = field(default_factory=dict)

    def parse_logs(self) -> None:
        """
        Main method to parse logs and populate student_info and assignments.
        """
        unique_students: set[str] = set()

        self._find_all_questions()

        for line in reversed(
            self.log_lines
        ):  # Process in reverse to get the most recent entries first
            if self._is_student_info(line):
                self._process_student_info(line, unique_students)
            elif (
                any(item in line for item in self.all_questions)
                and "total-points" in line
            ):
                self._process_assignment_header(line)

        # process assignment entries after all headers have been processed
        for line in reversed(self.log_lines):
            if (
                any(item in line for item in self.all_questions)
                and "total-points" not in line
            ):
                self._process_assignment_entry(line)

    def _find_all_questions(self) -> None:
        """
        Finds all questions in the log_lines and returns a list of them.
        """
        questions = []
        for line in self.log_lines:
            if self.week_tag and self.week_tag in line:
                parts = line.split(",")
                question_tag = parts[3].strip()
                if question_tag not in questions:
                    questions.append(question_tag)
        self.all_questions = questions

    def _is_student_info(self, line: str) -> bool:
        """
        Checks if the line contains student information.
        """
        return line.startswith("Student Info")

    def _process_student_info(self, line: str, unique_students: set) -> None:
        """
        Processes a line containing student information.
        Raises an error if multiple unique students are found.
        """
        parts = line.split(", ")
        # Example: "Student Info, 790, jovyan, 2024-12-27 19:40:10"
        student_name = parts[2].strip()
        unique_students.add(student_name)

        if len(unique_students) > 1:
            raise ValueError(
                f"Error: Multiple unique student names found: {unique_students}"
            )

        # Only set student_info once
        if not self.student_info:
            self.student_info = {
                "student_id": parts[1].strip(),
                "username": student_name,
                "timestamp": parts[3].strip(),
            }

    def _process_assignment_header(self, line: str) -> None:
        parts = line.split(",")
        assignment_tag = parts[0].strip()
        if assignment_tag.startswith("total-points"):
            # Handle total-points lines as assignment info
            total_points_value = self._extract_total_points(parts)
            timestamp = parts[-1].strip()
            notebook_name = parts[3].strip()

            if notebook_name not in self.assignments:
                self.assignments[notebook_name] = {
                    "max_points": total_points_value,
                    "notebook": notebook_name,
                    "assignment": self.week_tag,
                    "total_score": 0.0,
                    "latest_timestamp": timestamp,
                    "questions": {},  # Ensure 'questions' key is initialized
                }
            elif self.assignments[notebook_name]["latest_timestamp"] < timestamp:
                self.assignments[notebook_name]["max_points"] = total_points_value
                self.assignments[notebook_name]["latest_timestamp"] = timestamp

    def _process_assignment_entry(self, line: str) -> None:
        """
        Processes a line containing an assignment entry.
        Adds it to the assignments dictionary.
        """
        parts = line.split(",")
        assignment_tag = parts[0].strip()
        question_tag = parts[1].strip()
        score_earned = float(parts[2].strip()) if len(parts) > 2 else 0.0
        score_possible = float(parts[3].strip()) if len(parts) > 3 else 0.0
        timestamp = parts[-1].strip()

        # Ensure assignment entry exists
        if assignment_tag not in self.assignments:
            self.assignments[assignment_tag] = {
                "questions": {},
                "total_score": 0.0,
                "latest_timestamp": timestamp,
            }

        # Add or update the question with the most recent timestamp
        questions = self.assignments[assignment_tag]["questions"]
        if (
            question_tag not in questions
            or timestamp > questions[question_tag]["timestamp"]
        ):
            questions[question_tag] = {
                "score_earned": score_earned,
                "score_possible": score_possible,
                "timestamp": timestamp,
            }

        # Update the latest timestamp if this one is more recent
        if timestamp > self.assignments[assignment_tag]["latest_timestamp"]:
            self.assignments[assignment_tag]["latest_timestamp"] = timestamp

    def _extract_total_points(self, parts: list[str]) -> Optional[float]:
        """
        Extracts the total-points value from the parts array of a total-points line.
        """
        try:
            return float(parts[1].strip())
        except (ValueError, IndexError):
            return None

    def calculate_total_scores(self) -> None:
        """
        Calculates total scores for each assignment by summing the 'score_earned'
        of its questions, and sets 'total_points' if it was not specified.
        """
        for data in self.assignments.values():
            # Sum of all question score_earned
            total_score = sum(q["score_earned"] for q in data["questions"].values())
            data["total_score"] = total_score

    def get_results(self) -> LogParserResults:
        """
        Returns the parsed results as a hierarchical dictionary with three sections:
        """
        return {
            "student_information": self.student_info,
            "week": self.week_tag,
            "week_num": (
                int(self.week_tag.split("-")[0].strip().replace("week", ""))
                if self.week_tag
                else None
            ),
            "assignment_type": (
                self.week_tag.split("-")[1].strip() if self.week_tag else None
            ),
            "assignment_information": {
                assignment: {
                    "latest_timestamp": data["latest_timestamp"],
                    "total_score": data["total_score"],
                    "max_points": data.get("max_points", 0.0),
                }
                for assignment, data in self.assignments.items()
            },
            "assignment_scores": {
                assignment: {
                    "questions": data["questions"],
                    "total_score": data["total_score"],
                }
                for assignment, data in self.assignments.items()
            },
        }
