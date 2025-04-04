from pykubegrader.widgets.select_many import MultiSelect, SelectMany
from pykubegrader.widgets.true_false import TFQuestion, TFStyle
from pykubegrader.widgets.multiple_choice import MCQuestion, MCQ
import pykubegrader.initialize
import panel as pn

pn.extension()

class Question1(MCQuestion):
    def __init__(self):
        super().__init__(
            title=f"Select the Best Answer",
            style=MCQ,
            question_number=1,
            keys=['q1-1-Python-Operators', 'q1-2-Addition-Operator'],
            options=[['Store data in variables', 'Perform operations on one or more operands', 'Define functions', 'Loop through data'], ['`-`', '`*`', '`+`', '`/`']],
            descriptions=['What is the primary purpose of Python operators?', 'Which operator is used for addition in Python?'],
            points=[2.0, 2.0],
        )
class Question3(TFQuestion):
    def __init__(self):
        super().__init__(
            title=f"Select if the statement is True or False",
            style=TFStyle,
            question_number=3,
            keys=['q3-1-multiplication-operator', 'q3-2-Logical-Operators'],
            descriptions=['The `/` operator in Python is used for multiplication.', 'Logical operators in Python include `and`, `or`, and `not`.'],
            points=[1.0, 1.0],
        )
class Question2(SelectMany):
    def __init__(self):
        super().__init__(
            title=f"Select All That Apply",
            style=MultiSelect,
            question_number=2,
            keys=['q2-1-Categories-of-Python-Operators', 'q2-2-Arithmetic-Operators'],
            descriptions=['Select all categories of Python operators:** (Select all that apply)', 'Which of the following are arithmetic operators in Python?** (Select all that apply)'],
            options=[['Logical', 'Arithmetic', 'String Formatting', 'Membership'], ['`%`', '`**`', '`!=`', '`+`']],
            points=[4.0, 4.0],
            grade=['parts'],
        )
