class assignment_type:

    def __init__(self, name, weekly, weight):
        self.name = name
        self.weekly = weekly
        self.weight = weight


class assignment(assignment_type):

    def __init__(self, name, weekly, weight, score, **kwargs):
        super().__init__(name, weekly, weight)
        self.score = score
        self.week = kwargs.get("week", None)
        self.exempted = kwargs.get("exempted", False)
        self.graded = kwargs.get("graded", False)
        self.students_exempted = kwargs.get("students_exempted", [])

    def add_exempted_students(self, students):
        self.students_exempted.extend(students)
