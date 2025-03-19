from datetime import datetime
import numpy as np
from dateutil import parser
from ..graders.late_assignments import calculate_late_submission

class assignment_type:
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


class Assignment(assignment_type):
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
        self.max_score = kwargs.get("max_score", None)
        self.bonus_points = kwargs.get("bonus_points", 0)
        # TODO: this is not implemented yet
        self.student_with_extension = kwargs.get("student_with_extension", (None, None))

        # Stores the grade adjustment function which is used to calculate the grade in the case of late or exempted submissions.
        self.grade_adjustment_func = grade_adjustment_func

    @property
    def bonus_points(self):
        return self._bonus_points
    
    @bonus_points.setter
    def bonus_points(self, bonus_points):
        if not isinstance(bonus_points, float) and not isinstance(bonus_points, int) or bonus_points is None:
            raise ValueError("bonus_points must be a float or an integer")
        self._bonus_points = bonus_points

    @property
    def max_score(self):
        return self._max_score
    
    @max_score.setter
    def max_score(self, max_score):
        if not isinstance(max_score, float) and not isinstance(max_score, int) or max_score is None:
            raise ValueError("max_score must be a float or an integer")
        self._max_score = max_score
        
    #TODO: add setter for due_date with error handling

    @property
    def late_adjustment(self):
        return self._late_adjustment
    
    @late_adjustment.setter
    def late_adjustment(self, late_adjustment):
        if not isinstance(late_adjustment, bool):
            raise ValueError("late_adjustment must be a boolean")
        self._late_adjustment = late_adjustment

    @property
    def exempted(self):
        return self._exempted
    
    @exempted.setter
    def exempted(self, exempted):
        if not isinstance(exempted, bool):
            raise ValueError("exempted must be a boolean")
        self._exempted = exempted

    @property
    def week(self):
        return self._week
    
    @week.setter
    def week(self, week):
        if not isinstance(week, int):
            raise ValueError("week must be an integer")
        self._week = week

    # visible score
    @property
    def score_(self):
        return self._score_
    
    @score_.setter
    def score_(self, score):
        self._score_ = score

    # TODO: Come back to this for error handling
    # hidden score
    @property
    def _score(self):
        return self.__score
    
    @_score.setter
    def _score(self, score):
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

    def update_score(self, submission=None, **kwargs):
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

        elif submission is not None:
            # Adjust the score based on submission
            score_ = self.grade_adjustment(submission, **kwargs)

            # Update the score only if the new score is higher
            if score_ > self.score_:
                self.score_ = score_
                self._score = score_

            return self.score_
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

        if self.grade_adjustment_func:
            score = self.grade_adjustment_func(score)
            score = self.check_cheater(score, **kwargs)
            return score
        else:
            if self.late_adjustment:
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
            else:
                # Return normalized score if on time
                if entry_date < self.due_date:
                    score = score / self.max_score
                    score = self.check_cheater(score, **kwargs)
                    return score
                # Assign zero score for late submissions without a late adjustment policy
                else:
                    return 0

    def check_cheater(self, score, **kwargs):
        # TODO: fix once we record bonus points this is the mns fix.
        if score > 161:
            print(
                f"A Cheater has been detected with a score of {score} for {self.name}. {kwargs.get('student_name', 'You')} have been reported to the instructor."
            )
            return 0
        else:
            return score
