from pykubegrader.build.widget_questions.question_base import QuestionProcessorBaseClass
from dataclasses import dataclass
@dataclass
class MultipleChoice(QuestionProcessorBaseClass):
    """
    A class to process multiple choice questions in a Jupyter notebook.

    Attributes:
        start_tag (str): The start tag to identify the beginning of multiple choice questions.
        end_tag (str): The end tag to identify the end of multiple choice questions.
        question_type (str): The type of question being processed.
        class_name (str): The name of the class being processed.
    """
    start_tag: str = "# BEGIN MULTIPLE CHOICE"
    end_tag: str = "# END MULTIPLE CHOICE"
    question_type: str = "multiple choice"
    class_name: str = "MCQuestion"
    
    def make_question_file(self, data_dict, **kwargs):
        """
        Generates a Python file defining multiple choice question classes from a dictionary.

        This method creates a Python file containing the necessary class definitions
        for the multiple choice questions provided in the data dictionary. It ensures
        that the required header lines are present and writes the class definitions
        and their attributes.

        Args:
            data_dict (dict): A nested dictionary containing question metadata.
            **kwargs: Additional keyword arguments.
        """
        # Define the additional header lines for the MCQuestion class imports
        self.additional_header_lines = ["from pykubegrader.widgets.multiple_choice import MCQuestion, MCQ\n",]
        
        # Make the question file
        self.make_question_py_file(data_dict, output_file = self.question_path)
        
@dataclass
class TrueFalse(QuestionProcessorBaseClass):
    """
    A class to process true/false questions in a Jupyter notebook.

    Attributes:
        start_tag (str): The start tag to identify the beginning of true/false questions.
        end_tag (str): The end tag to identify the end of true/false questions.
        question_type (str): The type of question being processed.
        class_name (str): The name of the class being processed.
    """
    start_tag: str = "# BEGIN TF"
    end_tag: str = "# END TF"
    question_type: str = "true false"
    class_name: str = "TFQuestion"
    
    def make_question_file(self, data_dict, **kwargs):
        """
        Generates a Python file defining true/false question classes from a dictionary.

        This method creates a Python file containing the necessary class definitions
        for the true/false questions provided in the data dictionary. It ensures
        that the required header lines are present and writes the class definitions
        and their attributes.

        Args:
            data_dict (dict): A nested dictionary containing question metadata.
            **kwargs: Additional keyword arguments.
        """
        self.additional_header_lines = ["from pykubegrader.widgets.true_false import TFQuestion, TFStyle\n",]
        
        # Make the question file
        self.make_question_py_file(data_dict, output_file = self.question_path)
@dataclass
class SelectMany(QuestionProcessorBaseClass):
    """
    A class to process select many questions in a Jupyter notebook.

    Attributes:
        start_tag (str): The start tag to identify the beginning of select many questions.
        end_tag (str): The end tag to identify the end of select many questions.
        question_type (str): The type of question being processed.
        class_name (str): The name of the class being processed.
    """
    start_tag: str = "# BEGIN SELECT MANY"
    end_tag: str = "# END SELECT MANY"
    question_type: str = "select many"
    class_name: str = "SelectMany"
    
    def make_question_file(self, data_dict, **kwargs):
        """
        Generates a Python file defining select many question classes from a dictionary.

        This method creates a Python file containing the necessary class definitions
        for the select many questions provided in the data dictionary. It ensures
        that the required header lines are present and writes the class definitions
        and their attributes.

        Args:
            data_dict (dict): A nested dictionary containing question metadata.
            **kwargs: Additional keyword arguments.
        """
        # Define the additional header lines for the SelectManyQuestion class imports
        self.additional_header_lines = ["from pykubegrader.widgets.select_many import MultiSelect, SelectMany\n",]
        
        # Make the question file
        self.make_question_py_file(data_dict, output_file = self.question_path)
        