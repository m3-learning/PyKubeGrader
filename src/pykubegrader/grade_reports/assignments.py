import numpy as np
from dateutil import parser
from datetime import datetime
from pykubegrader.graders.late_assignments import calculate_late_submission


class assignment_type:
    """
    Base class for assignment types.

    Attributes:
        weight (float): The weight of the assignment in the overall grade.

    Methods:
        __init__(name: str, weekly: bool, weight: float):
            Initializes an instance of the assignment_type class.
    """

    def __init__(self, name: str, weekly: bool, weight: float):
        """Initializes an instance of the assignment_type class.
        Args:
            name (str): The name of the assignment.
            weekly (bool): Indicates if the assignment is weekly.
            weight (float): The weight of the assignment in the overall grade."""
        self.name = name
        self.weekly = weekly
        self.weight = weight


class Assignment(assignment_type):
    """
    Class for storing and updating assignment scores.

    Attributes:
        week (int, optional): The week number of the assignment.
        exempted (bool): Indicates if the assignment is exempted.
        graded (bool): Indicates if the assignment has been graded.
        late_adjustment (bool): Indicates if late submissions are allowed.
        students_exempted (list): List of student IDs exempted from the assignment.
        due_date (datetime, optional): The due date of the assignment.
        max_score (float, optional): The maximum score possible for the assignment.
        grade_adjustment_func (callable, optional): Function to adjust the grade for late or exempted submissions.

    Methods:
        add_exempted_students(students):
            Add students to the exempted list.

        update_score(submission=None):
            Update the score of the assignment based on the submission.

        grade_adjustment(submission):
            Apply the adjustment function if provided.
    """

    def __init__(
        self,
        name: str,
        weekly: bool,
        weight: float,
        score: float,
        grade_adjustment_func=None,
        **kwargs,
    ):
        """
        Initializes an instance of the Assignment class.

        weekly (bool): Indicates if the assignment is weekly.
        grade_adjustment_func (callable, optional): Used to calculate the grade in the case of late or exempted submissions. Defaults to None.
        **kwargs: Additional keyword arguments.
            week (int, optional): The week number of the assignment. Defaults to None.
            exempted (bool, optional): Indicates if the assignment is exempted. Defaults to False.
            graded (bool, optional): Indicates if the assignment is graded. Defaults to False.
            late_adjustment (bool, optional): Indicates if late adjustment is applied. Defaults to True.
            students_exempted (list, optional): List of students exempted from the assignment. Defaults to an empty list.
            due_date (datetime, optional): The due date of the assignment. Defaults to None.
            max_score (float, optional): The maximum score possible for the assignment. Defaults to None.
        """
        super().__init__(name, weekly, weight)
        self.score = score
        self._score = score
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
        """
        Add students to the exempted list.
        Args:
            students (list): List of student IDs to exempt from the assignment.
        """
        self.students_exempted.extend(students)

    def update_score(self, submission=None):
        """Updates the assignment score based on the given submission.

        This method adjusts the score using the `grade_adjustment` function if a submission
        is provided. If the submission results in a higher score than the current score,
        the assignment score is updated. If no submission is provided and the student is
        not exempted, the score is set to zero. If the student is exempted, the score
        is set to NaN.

        Args:
            submission (dict, optional): The submission data, expected to contain relevant
                details for grading. Defaults to None.

        Returns:
            float: The updated assignment score. If exempted, returns NaN. If no submission
                is provided, returns 0.
        """
        if self.exempted:
            self.score = np.nan
            
            # If the score is "---", return the score as is, this is an assignment that does not exist.
            if self._score == "---":
                return self.score

            # Saves a table with the score of the exempted assignment still recorded.
            try: 
                # Adjust the score based on submission
                score_ = self.grade_adjustment(submission)
                if score_ > self._score:
                    self._score = score_
            except:
                pass
            return self.score
        
        elif submission is not None:
            # Adjust the score based on submission
            score_ = self.grade_adjustment(submission)

            # Update the score only if the new score is higher
            if score_ > self.score:
                self.score = score_
                self._score = score_

            return self.score
        else:
            # Set the score to zero if not exempted and no submission
            self.score = 0
            self._score = 0
            return self.score

    def grade_adjustment(self, submission):
        """Applies adjustments to the submission score based on grading policies.

        This method applies any provided grade adjustment function to the raw score.
        If no custom function is given, it determines the final score by considering
        lateness penalties based on the submission timestamp and due date.

        Args:
            submission (dict): A dictionary containing:
                - `"raw_score"` (float): The initial unadjusted score.
                - `"timestamp"` (str): The submission timestamp in a parsable format.

        Returns:
            float: The adjusted score, incorporating lateness penalties if applicable.
                Returns 0 for late submissions if no late adjustment policy is defined.
        """
        score = submission["raw_score"]
        entry_date = parser.parse(submission["timestamp"])

        if self.grade_adjustment_func:
            return self.grade_adjustment_func(score)
        else:
            if self.late_adjustment:
                # Convert due date to datetime object
                due_date = datetime.fromisoformat(self.due_date.replace("Z", "+00:00"))

                late_modifier = calculate_late_submission(
                    due_date.strftime("%Y-%m-%d %H:%M:%S"),
                    entry_date.strftime("%Y-%m-%d %H:%M:%S"),
                )

                # Apply late modifier and normalize score
                return (score / self.max_score) * late_modifier
            else:
                # Return normalized score if on time
                if entry_date < self.due_date:
                    return score / self.max_score
                # Assign zero score for late submissions without a late adjustment policy
                else:
                    return 0
