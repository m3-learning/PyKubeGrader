from pykubegrader.build.widget_questions.QuestionProcessBaseClass import QuestionProcessorBaseClass
from dataclasses import dataclass
@dataclass
class MultipleChoice(QuestionProcessorBaseClass):
    start_tag: str = "# BEGIN MULTIPLE CHOICE"
    end_tag: str = "# END MULTIPLE CHOICE"
    question_type: str = "multiple choice"
    class_name: str = "MCQuestion"
    
    def make_question_file(self, data_dict, **kwargs):
        
        # Define the additional header lines for the MCQuestion class imports
        self.additional_header_lines = ["from pykubegrader.widgets.multiple_choice import MCQuestion, MCQ\n",]
        
        # Make the question file
        self.make_question_py_file(data_dict, output_file = self.question_path)
        
@dataclass
class TrueFalse(QuestionProcessorBaseClass):
    start_tag: str = "# BEGIN TF"
    end_tag: str = "# END TF"
    question_type: str = "true false"
    class_name: str = "TFQuestion"
    
    def make_question_file(self, data_dict, **kwargs):
        
        self.additional_header_lines = ["from pykubegrader.widgets.true_false import TFQuestion, TFStyle\n",]
        
        # Make the question file
        self.make_question_py_file(data_dict, output_file = self.question_path)
        
@dataclass
class SelectMany(QuestionProcessorBaseClass):
    start_tag: str = "# BEGIN SELECT MANY"
    end_tag: str = "# END SELECT MANY"
    question_type: str = "select many"
    class_name: str = "SelectMany"
    
    def make_question_file(self, data_dict, **kwargs):
        
        # Define the additional header lines for the SelectManyQuestion class imports
        self.additional_header_lines = ["from pykubegrader.widgets.select_many import MultiSelect, SelectMany\n",]
        
        # Make the question file
        self.make_question_py_file(data_dict, output_file = self.question_path)
        