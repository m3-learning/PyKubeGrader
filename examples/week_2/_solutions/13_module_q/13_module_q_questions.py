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
            keys=['q1-1-What-is-a-Python-Module'],
            options=[['A built-in function in Python.', 'A package that must always be installed separately.', 'A Python file containing reusable code.', 'A set of Python standards for formatting code.']],
            descriptions=['What is a Python module?'],
            points=[1.0],
        )
class Question2(TFQuestion):
    def __init__(self):
        super().__init__(
            title=f"Select if the statement is True or False",
            style=TFStyle,
            question_number=2,
            keys=['q2-1-Python-built-in-modules'],
            descriptions=["Python's built-in modules require installation using `pip`."],
            points=[1.0],
        )
class Question3(SelectMany):
    def __init__(self):
        super().__init__(
            title=f"Select All That Apply",
            style=MultiSelect,
            question_number=3,
            keys=['q3-1-Examples-of-Python-Built-in-Modules', 'q3-2-Statements-about-Python-Modules'],
            descriptions=["Which of the following are examples of Python's built-in modules?** (Select all that apply)", 'Which of the following statements about Python modules is true?** (Select all that apply)'],
            options=[['`os`', '`sys`', '`requests`', '`math`'], ['Modules promote code reuse.', 'Modules can only contain functions.', 'You can import a specific function from a module.', 'Python packages are a collection of modules.']],
            points=[2.0, 2.0],
            grade=['parts'],
        )
