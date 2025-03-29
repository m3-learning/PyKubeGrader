from datetime import datetime
import numpy as np
from dateutil import parser
from ..graders.late_assignments import calculate_late_submission


class AssignmentType:
    """
    Base class for assignment types.

    Attributes:
        name (str): The name of the assignment.
        weekly (bool): Indicates if the assignment is weekly.
        weight (float | tuple[float, float]): The weight of the assignment in the overall grade.
            If a tuple is provided, it represents a range of possible weights.

    Methods:
        __init__(name: str, weekly: bool, weight: float | tuple[float, float]):
            Initializes an instance of the assignment_type class.
    """

    def __init__(self, name: str, weekly: bool, weight: float | tuple[float, float]):
        """
        Initializes an instance of the assignment_type class.

        Args:
            name (str): The name of the assignment.
            weekly (bool): Indicates if the assignment is weekly.
            weight (float | tuple[float, float]): The weight of the assignment in the overall grade.
                If a tuple is provided, it represents a range of possible weights.
        """
        self.name = name
        self.weekly = weekly
        self.weight = weight


class Assignment(AssignmentType):
    """
    Represents an assignment with functionality to store and update scores.

    Attributes:
        week (int, optional): The week number associated with the assignment.
        exempted (bool): Flag indicating if the assignment is exempted for a student.
        graded (bool): Flag indicating if the assignment has been graded.
        late_adjustment (bool): Flag indicating if late submissions are subject to adjustment.
        students_exempted (list): A list of student IDs who are exempted from the assignment.
        due_date (datetime, optional): The due date for the assignment submission.
        max_score (float, optional): The maximum achievable score for the assignment.
        grade_adjustment_func (callable, optional): A function to adjust grades for late or exempted submissions.

    Methods:
        add_exempted_students(students):
            Adds a list of students to the exempted list.

        update_score(submission=None):
            Updates the assignment score based on the provided submission.

        grade_adjustment(submission):
            Applies the grade adjustment function if it is provided.
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

        Args:
            name (str): The name of the assignment.
            weekly (bool): Indicates if the assignment is weekly.
            weight (float): The weight of the assignment in the overall grade.
            score (float): The initial score of the assignment.
            grade_adjustment_func (callable, optional): A function to adjust grades for late or exempted submissions. Defaults to None.
            **kwargs: Additional keyword arguments.
                week (int, optional): The week number of the assignment. Defaults to None.
                exempted (bool, optional): Indicates if the assignment is exempted. Defaults to False.
                graded (bool, optional): Indicates if the assignment is graded. Defaults to False.
                late_adjustment (bool, optional): Indicates if late adjustment is applied. Defaults to True.
                students_exempted (list, optional): List of students exempted from the assignment. Defaults to an empty list.
                due_date (datetime, optional): The due date of the assignment. Defaults to None.
                max_score (float, optional): The maximum score possible for the assignment. Defaults to None.
                bonus_points (float, optional): The bonus points for the assignment. Defaults to 0.
                student_with_extension (tuple, optional): A tuple containing the student ID and the extension time as a timedelta object. Defaults to (None, None).
        """
        super().__init__(name, weekly, weight)
        # visible score
        self.score_ = score
        # hidden score
        self._score = score

        self.week = kwargs.get("week", None)
        self.exempted = kwargs.get("exempted", False)
        self.graded = kwargs.get("graded", False)
        self.late_adjustment = kwargs.get("late_adjustment", True)
        self.students_exempted = kwargs.get("students_exempted", [])
        self.due_date = kwargs.get("due_date", None)
        self.max_score = kwargs.get("max_score", 0)
        self.bonus_points = kwargs.get("bonus_points", 0)
        # TODO: this is not implemented yet
        self.student_with_extension = kwargs.get("student_with_extension", (None, None))

        # Stores the grade adjustment function which is used to calculate the grade in the case of late or exempted submissions.
        self.grade_adjustment_func = grade_adjustment_func

    @property
    def bonus_points(self):
        """
        Gets the bonus points for the assignment.

        Returns:
            float: The bonus points for the assignment.
        """
        return self._bonus_points

    @bonus_points.setter
    def bonus_points(self, bonus_points):
        """
        Sets the bonus points for the assignment.

        Args:
            bonus_points (float | int): The bonus points to be set for the assignment.

        Raises:
            ValueError: If bonus_points is not a float or an integer.
        """
        if (
            not isinstance(bonus_points, float)
            and not isinstance(bonus_points, int)
            or bonus_points is None
        ):
            raise ValueError("bonus_points must be a float or an integer")
        self._bonus_points = bonus_points

    @property
    def max_score(self):
        """
        Gets the maximum score for the assignment.

        Returns:
            float: The maximum score for the assignment.
        """
        return self._max_score

    @max_score.setter
    def max_score(self, max_score):
        """
        Sets the maximum score for the assignment.

        Args:
            max_score (float | int): The maximum score to be set for the assignment.

        Raises:
            ValueError: If max_score is not a float or an integer.
        """
        if (
            not isinstance(max_score, float)
            and not isinstance(max_score, int)
            or max_score is None
        ):
            raise ValueError("max_score must be a float or an integer")
        self._max_score = max_score

    @property
    def due_date(self):
        """
        Gets the due date for the assignment.

        Returns:
            datetime: The due date for the assignment.
        """
        return self._due_date

    @due_date.setter
    def due_date(self, due_date):
        """
        Sets the due date for the assignment.

        Args:
            due_date (datetime): The due date to be set for the assignment.
        """
        if not isinstance(due_date, datetime) and due_date is not None:
            raise ValueError("due_date must be a datetime object")
        self._due_date = due_date

    @property
    def late_adjustment(self):
        """
        Gets the late adjustment flag for the assignment.

        Returns:
            bool: The late adjustment flag for the assignment.
        """
        return self._late_adjustment

    @late_adjustment.setter
    def late_adjustment(self, late_adjustment):
        """
        Sets the late adjustment flag for the assignment.

        Args:
            late_adjustment (bool): The late adjustment flag to be set for the assignment.

        Raises:
            ValueError: If late_adjustment is not a boolean.
        """
        self._late_adjustment = late_adjustment

    @property
    def exempted(self):
        """
        Gets the exempted flag for the assignment.

        Returns:
            bool: The exempted flag for the assignment.
        """
        return self._exempted

    @exempted.setter
    def exempted(self, exempted):
        """
        Sets the exempted flag for the assignment.

        Args:
            exempted (bool): The exempted flag to be set for the assignment.
        """
        if not isinstance(exempted, bool):
            raise ValueError("exempted must be a boolean")
        self._exempted = exempted

    @property
    def week(self):
        """
        Gets the week number for the assignment.

        Returns:
            int: The week number for the assignment.
        """
        return self._week

    @week.setter
    def week(self, week):
        """
        Sets the week number for the assignment.

        Args:
            week (int): The week number to be set for the assignment.
        """
        if not isinstance(week, int) and self.weekly:
            raise ValueError("week must be an integer")
        self._week = week

    # visible score
    @property
    def score_(self):
        """
        Gets the visible score for the assignment.

        Returns:
            float: The visible score for the assignment.
        """
        return self._score_

    @score_.setter
    def score_(self, score):
        """
        Sets the visible score for the assignment.

        Args:
            score (float): The visible score to be set for the assignment.
        """
        if not isinstance(score, (float, int)) or score is None:
            raise ValueError("score must be a float or an integer and cannot be None")
        self._score_ = score

    # TODO: Come back to this for error handling
    # hidden score
    @property
    def _score(self):
        """
        Gets the hidden score for the assignment.

        Returns:
            float: The hidden score for the assignment.
        """
        return self.__score

    @_score.setter
    def _score(self, score):
        """
        Sets the hidden score for the assignment.

        Args:
            score (float): The hidden score to be set for the assignment.
        """
        if not isinstance(score, (float, int)) and score != "---":
            raise ValueError("score must be a float, an integer, or '---'")
        self.__score = score

    @property
    def students_exempted(self):
        """
        Gets the list of students exempted from the assignment.

        Returns:
            list: A list of student IDs who are exempted from the assignment.
        """
        return self._students_exempted

    @students_exempted.setter
    def students_exempted(self, students):
        """
        Sets the exempted students list for the assignment.

        Args:
            students (list): A list of student IDs to exempt from the assignment.
        """
        if isinstance(students, str):
            self._students_exempted = [students]
        elif isinstance(students, list):
            self._students_exempted = students
        else:
            raise ValueError("students must be a list or a string")

    def mark_exempted(self, submission=None, **kwargs):
        """
        Marks the assignment as exempted and adjusts the score if necessary.

        This method sets the assignment score to NaN to indicate exemption. If the
        assignment score is "---", it returns NaN as the assignment does not exist.
        Otherwise, it attempts to adjust the score based on the provided submission
        and updates the score if the adjusted score is higher.

        Args:
            submission (dict, optional): The submission data, expected to contain relevant
                details for grading. Defaults to None.
            **kwargs: Additional keyword arguments for grade adjustment.

        Returns:
            float: The score of the exempted assignment, NaN if exempted, or the adjusted
            score if applicable.
        """

        self.score_ = np.nan

        # If the score is "---", return the score as is, this is an assignment that does not exist.
        if self._score == "---":
            return self.score_

        # Saves a table with the score of the exempted assignment still recorded.
        try:
            # Adjust the score based on submission
            score_ = self.grade_adjustment(submission, **kwargs)
            if score_ > self._score:
                self._score = score_
        except Exception:
            pass
        return self.score_

    def write_score(self, submission=None, **kwargs):
        """
        Writes the score for the assignment.

        This method adjusts the score using the `grade_adjustment` function if a submission
        is provided. If the adjusted score is higher than the current score, the assignment
        score is updated.

        Args:
            submission (dict, optional): The submission data, expected to contain relevant
                details for grading. Defaults to None.
            **kwargs: Additional keyword arguments for grade adjustment.

        Returns:
            float: The updated assignment score.
        """
        # Adjust the score based on submission
        score_ = self.grade_adjustment(submission, **kwargs)

        # Update the score only if the new score is higher
        if score_ > self.score_:
            self.score_ = score_
            self._score = score_

        return self.score_

    def update_score(self, submission=None, **kwargs):
        """Updates the assignment score based on the given submission.

        This method adjusts the score using the `grade_adjustment` function if a submission
        is provided. If the submission results in a higher score than the current score,
        the assignment score is updated. If no submission is provided and the assignment
        is not exempted, the score is set to zero. If the assignment is exempted, the score
        is set to NaN.

        Args:
            submission (dict, optional): The submission data, expected to contain relevant
                details for grading. Defaults to None.

        Returns:
            float: The updated assignment score. If exempted, returns NaN. If no submission
                is provided, returns 0.
        """
        if self.exempted:
            return self.mark_exempted(submission, **kwargs)

        elif submission is not None:
            return self.write_score(submission, **kwargs)
        else:
            # Set the score to zero if not exempted and no submission
            self.score_ = 0
            self._score = 0
            return self.score_

    def grade_adjustment(self, submission, **kwargs):
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

        # If a custom grade adjustment function is provided, use it
        if self.grade_adjustment_func:
            score = self.grade_adjustment_func(score)
            score = self.check_cheater(score, **kwargs)
            return score
        else:
            # If no custom grade adjustment function is provided, apply the late adjustment
            if self._late_adjustment:
                return self._calculate_late_adjustment(score, entry_date, **kwargs)
            else:
                # Return normalized score if on time
                if entry_date < self.due_date:
                    score = self._calculate_score(score, **kwargs)
                    return score
                else:
                    return 0.0

    def _late_adjustment(self, score, entry_date, **kwargs):
        """
        Adjusts the score for late submissions based on the due date and entry date.

        This method calculates a late modifier based on the difference between the due date
        and the submission date. It then applies this modifier to the score and normalizes it.

        Args:
            score (float): The initial unadjusted score.
            entry_date (datetime): The submission timestamp as a datetime object.
            **kwargs: Additional keyword arguments.

        Returns:
            float: The adjusted score after applying the late modifier and normalization.
        """
        # Convert due date to datetime object
        due_date = datetime.fromisoformat(self.due_date.replace("Z", "+00:00"))

        late_modifier = calculate_late_submission(
            due_date.strftime("%Y-%m-%d %H:%M:%S"),
            entry_date.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Apply late modifier and normalize score
        score = (score / self.max_score) * late_modifier
        score = self.check_cheater(score, **kwargs)
        return score

    def check_cheater(self, score, **kwargs):
        # TODO: fix once we record bonus points this is the mns fix.
        if score > 161:
            print(
                f"A Cheater has been detected with a score of {score} for {self.name}. {kwargs.get('student_name', 'You')} have been reported to the instructor."
            )
            return 0.0
        else:
            return score
