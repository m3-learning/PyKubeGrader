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
        """Update the score of the assignment based on the submission.

        Args:
            submission (dict, optional): Defaults to None.

        Returns:
            float: Adjusted submission score
        """
        if self.exempted:
            self.score = np.nan
            return self.score
        elif submission is not None:

            # deal with incomplete submissions
            score_ = self.grade_adjustment(submission)

            # Update the score if the new score is higher
            if score_ > self.score:
                self.score = score_

            return self.score
        # sets the score to zero if not exempted and no submission
        else:
            self.score = 0
            return self.score

    def grade_adjustment(self, submission):
        """Apply the adjustment function if provided.
        Args:
            submission (dict): Submission data.
        Returns:
            float: Score adjusted for lateness or exemptions. If none are present, returns 0.
        """

        score = submission["raw_score"]
        entry_date = parser.parse(submission["timestamp"])

        if self.grade_adjustment_func:
            return self.grade_adjustment_func(score)
        else:
            if self.late_adjustment:

                # Convert to datetime object
                due_date = datetime.fromisoformat(self.due_date.replace("Z", "+00:00"))

                late_modifier = calculate_late_submission(
                    due_date.strftime("%Y-%m-%d %H:%M:%S"),
                    entry_date.strftime("%Y-%m-%d %H:%M:%S"),
                )

                # return score for on-time submissions
                return (score / self.max_score) * late_modifier

            else:

                # return score for on-time submissions
                if entry_date < self.due_date:
                    return score / self.max_score

                # zero score for late submissions w/o late adjustment
                else:
                    return 0
