from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class LogParser:
    """
    A class for parsing chronological logs and extracting information.
    Handles both assignment info and question-level details.
    """

    log_lines: List[str]
    week_tag: Optional[str] = None
    student_info: Dict[str, str] = field(default_factory=dict)
    assignments: Dict[str, Dict] = field(default_factory=dict)

    def parse_logs(self):
        """
        Main method to parse logs and populate student_info and assignments.
        """
        unique_students = set()

        self._find_all_questions()

        for line in reversed(
            self.log_lines
        ):  # Process in reverse to get the most recent entries first
            if self._is_student_info(line):
                self._process_student_info(line, unique_students)
            elif (
                any(item in line for item in self.all_questions)
                and "total-points" not in line
            ):
                self._process_assignment_entry(line)

    def _find_all_questions(self):
        """
        Finds all questions in the log_lines and returns a list of them.
        """
        questions = []
        for line in self.log_lines:
            if self.week_tag in line:
                parts = line.split(", ")
                question_tag = parts[3]
                if question_tag not in questions:
                    questions.append(question_tag)
        self.all_questions = questions

    def _is_student_info(self, line: str) -> bool:
        """
        Checks if the line contains student information.
        """
        return line.startswith("Student Info")

    def _process_student_info(self, line: str, unique_students: set):
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

    def _process_assignment_entry(self, line: str):
        """
        Processes a line containing an assignment entry.
        Adds it to the assignments dictionary.
        """
        parts = line.split(", ")
        assignment_tag = parts[0]

        if assignment_tag.startswith("total-points"):
            # Handle total-points lines as assignment info
            total_points_value = self._extract_total_points(parts)
            timestamp = parts[-1].strip()
            notebook_name = assignment_tag.split(",")[3].strip()

            if notebook_name not in self.assignments:
                self.assignments[notebook_name] = {
                    "max_points": total_points_value,
                    "notebook": notebook_name,
                    "assignment": self.week_tag,
                    "total_score": 0.0,
                    "latest_timestamp": timestamp,
                }
            else:
                self.assignments[notebook_name]["latest_timestamp"] = max(
                    self.assignments[notebook_name]["latest_timestamp"], timestamp
                )
                self.assignments[notebook_name]["max_points"] = total_points_value

        else:
            # Normal question line
            question_tag = parts[1].strip()
            score_earned = float(parts[2].strip()) if len(parts) > 2 else 0.0
            score_possible = float(parts[3].strip()) if len(parts) > 3 else 0.0
            timestamp = parts[-1].strip()

            if assignment_tag not in self.assignments:
                self.assignments[assignment_tag] = {
                    "max_points": None,  # Will be computed if missing
                    "questions": {},
                    "total_score": 0.0,
                    "latest_timestamp": timestamp,
                }

            # Add or update the question with the most recent timestamp
            if (
                question_tag not in self.assignments[assignment_tag]["questions"]
                or timestamp
                > self.assignments[assignment_tag]["questions"][question_tag][
                    "timestamp"
                ]
            ):
                self.assignments[assignment_tag]["questions"][question_tag] = {
                    "score_earned": score_earned,
                    "score_possible": score_possible,
                    "timestamp": timestamp,
                }

            # Update the latest timestamp if this one is more recent
            if timestamp > self.assignments[assignment_tag]["latest_timestamp"]:
                self.assignments[assignment_tag]["latest_timestamp"] = timestamp

    def _extract_total_points(self, parts: List[str]) -> Optional[float]:
        """
        Extracts the total-points value from the parts array of a total-points line.
        """
        try:
            return float(parts[1].strip())
        except (ValueError, IndexError):
            return None

    def calculate_total_scores(self):
        """
        Calculates total scores for each assignment by summing the 'score_earned'
        of its questions, and sets 'total_points' if it was not specified.
        """
        for assignment, data in self.assignments.items():
            # Sum of all question score_earned
            total_score = sum(q["score_earned"] for q in data["questions"].values())
            data["total_score"] = total_score

            # If total_points wasn't provided by a total-points line,
            # we set it as the sum of the 'score_possible' values of the questions.
            if data["max_points"] is None:
                data["max_points"] = sum(
                    q["score_possible"] for q in data["questions"].values()
                )

    def get_results(self) -> Dict[str, Dict]:
        """
        Returns the parsed results as a hierarchical dictionary with three sections:
        """
        return {
            "student_information": self.student_info,
            "assignment_information": {
                assignment: {
                    "latest_timestamp": data["latest_timestamp"],
                    "max_points": data["max_points"],
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
