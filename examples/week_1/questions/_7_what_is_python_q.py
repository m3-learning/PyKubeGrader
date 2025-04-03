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
            keys=['q1-1-High-Level-v-Low-Level', 'q1-2-Python-Advantages', 'q1-3-Python-Interpreter'],
            options=[['High-level languages are written directly in binary, while low-level languages use plain English.', 'Low-level languages are easier to learn and more portable than high-level languages.', 'High-level languages are closer to human language and must be translated for computers to execute.', 'High-level languages are specific to one type of computer, while low-level languages are universal.'], ['Python programs are easy to write and debug.', 'Python is a low-level language, so it runs directly on hardware without translation.', 'Python code is portable and can run on different types of computers.', 'Python’s syntax is simple and close to natural language.'], ['It allows Python to directly control computer hardware.', 'It translates and executes Python code step by step.', 'It converts Python code into plain English for easier understanding.', 'It ensures that Python code is always correct and free of errors.']],
            descriptions=['What is a key difference between high-level and low-level programming languages?', 'Which of the following is NOT an advantage of Python?', 'What is the primary function of the Python Interpreter?'],
            points=[1.0, 1.0, 1.0],
        )
