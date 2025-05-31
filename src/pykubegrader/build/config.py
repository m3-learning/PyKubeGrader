from dataclasses import dataclass
import os
from pathlib import Path
from abc import abstractmethod
from abc import ABC
import nbformat
from pykubegrader.build.notebooks.writers import AddKeyRequirementImportBaseClass
from pykubegrader.build.util import EncryptionKeyBaseClass
from textwrap import dedent

@dataclass
class DisplayQuestionCode:
    
    @property
    def build_code(self, file_name_ipynb, dict_):
        return [
                "# Run this block of code by pressing Shift + Enter to display the question\n",
                f"from questions.{file_name_ipynb} import Question{dict_['question number']}\n",
                f"Question{dict_['question number']}().show()\n",
            ]

@dataclass
class QuestionClassType:
    class_type: str
    style: str

question_class_type = {
    "MCQuestion": QuestionClassType(class_type="MCQuestion", style="MCQ"),
    "SelectMany": QuestionClassType(class_type="SelectMany", style="MultiSelect"),
    "TFQuestion": QuestionClassType(class_type="TFQuestion", style="TFStyle"),
}


@dataclass
class SubmissionCodeBaseClass:

    @property
    def submission_markdown_code(self):
        string = [ "## Submitting Final Assignment\n\n"
            "Please run this cell with the provided token to identify your submission as final. Once your submission is final, you will not be able to make any changes to your assignment. "
        ]
        return string

    @property
    def submission_code(self):
        string = [ "from pykubegrader.submit.final_submission import final_submission\n\n"
            f"final_submission(assignment='{self.assignment_tag}', assignment_type='{self.assignment_type}', token='replace your token here', week_number = {self.week_num})"
        ]
        return string
    

@dataclass
class EncryptionKeyTransfer(EncryptionKeyBaseClass):
    client_private_key_path: str = "./keys/.client_private_key.bin"
    server_public_key_path: str = "./keys/.server_public_key.bin"
    
    #TODO: Fix and refactor for simplicity  
@dataclass
class AddKeyRequirementImport(AddKeyRequirementImportBaseClass):
    @property
    def validate_token_line(self):
        # Add an additional line for validate_token()
        validate_token_line = (
            f"from pykubegrader.tokens.validate_token import validate_token\n"
            f"validate_token(assignment = '{self.assignment_tag}')\n"
        )
        return validate_token_line
    
    @property
    def code_cell(self):
        
        # Prepare the lines of code to include
        lines = []

        # Optionally include the validate_token_line
        if self.require_key:
            lines.append(self.validate_token_line)
            lines.append("")  # blank line for readability

        # Always include import and submission call
        lines += [
            "from pykubegrader.submit.submit_assignment import submit_assignment",
            f'submit_assignment("{self.assignment_tag}", "{Path(notebook_path).stem}")'
        ]

        # Create the code cell with joined lines
        code_cell = nbformat.v4.new_code_cell("\n".join(lines))
        
        return code_cell
        
@dataclass
class EnvironmentVariables:
    jhub_user: str = "jca92"
    token: str = "token"
    api_url: str = "https://engr-131-api.eastus.cloudapp.azure.com/"
    keys_student: str = "capture"
    user_name_student: str = "student"


@dataclass
class OtterConfigSettings(ABC):
    _test_required_imports: str = dedent("""
        from pykubegrader.telemetry import (
            ensure_responses,
            log_variable,
            score_question,
            submit_question,
            telemetry,
            update_responses,
        )
        import os
        import base64
        import matplotlib
        matplotlib.use('Agg')
    """)
    end_test_config_line = "# END TEST CONFIG"
    
    def get_key_validation_line(self, assignment_tag: str) -> str:
        """
        Generates a line of code for validating an assignment key.

        This method constructs a string that includes the necessary import statement
        and function call to validate an assignment key using the provided assignment tag.

        Args:
            assignment_tag (str): The tag associated with the assignment to be validated.

        Returns:
            str: A string containing the import statement and the function call to validate
                 the assignment key.
        """
        return (
            "from pykubegrader.tokens.validate_token import validate_token\n"
            f"validate_token(assignment='{assignment_tag}')\n"
        )
    def first_test_header(self, cell_dict: dict, max_question_points: float, filename: str) -> list[str]:
        """
        Constructs the header for the first test cell in a notebook.

        This method generates a list of strings that form the header for the first test cell.
        It initializes environment variables for tracking earned and total points, and logs
        the total points for the assignment.

        Args:
            cell_dict (dict): A dictionary containing information about the test cell.
            max_question_points (float): The maximum points available for the question.
            filename (str): The name of the file where the test is located.

        Returns:
            list[str]: A list of strings representing the header lines for the test cell.
        """
        return dedent(f"""
            max_question_points = str({max_question_points})
            earned_points = 0
            os.environ['EARNED_POINTS'] = str(earned_points)
            os.environ['TOTAL_POINTS_FREE_RESPONSE'] = str({self.total_points})
            log_variable("total-points",f"{self.assignment_tag}, {filename}", {self.total_points})
        """).strip().split("\n")
        
    def question_information(self, cell_dict: dict) -> str:
        """
        Generates a string containing information about a question.

        This method constructs a formatted string that includes the question ID,
        maximum score, and initializes the score for a given test cell. The question
        ID is a combination of the question identifier and the test number.

        Args:
            cell_dict (dict): A dictionary containing details about the test cell,
                              including the question identifier, test number, and points.

        Returns:
            str: A formatted string with the question ID, maximum score, and initialized score.
        """
        question_info = dedent(f"""
            question_id = {cell_dict["question"]} + "-" + {str(cell_dict["test_number"])}   
            max_score = {cell_dict['points']}
            score = 0
        """).strip().split("\n")
        return question_info
        
    @property
    def test_required_imports(self) -> str:
        return self.format_imports(self._test_required_imports)
    
    @staticmethod
    def format_imports(imports: list[str]) -> str:
        return imports.strip() + "\n"

    @abstractmethod
    @property
    def total_points(self) -> float:
        pass

@dataclass
class InitializationCell:
    """
    A data class representing the initialization cell for a Jupyter notebook.

    This class holds the necessary information to construct the initialization
    code for a Jupyter notebook, which includes the path to the notebook, the
    week identifier, and the type of assignment.

    Attributes:
        notebook_path (str): The file path to the Jupyter notebook.
        week (str): The week identifier for the assignment.
        assignment_type (str): The type of the assignment.
    """
    notebook_path: str
    week: str
    assignment_type: str

    @property
    def initialization_cell(self) -> str:
        """
        Constructs the initialization code for the Jupyter notebook.

        This property generates a string containing the necessary import statements
        and initialization function call required to set up the assignment environment
        in the notebook. It ensures that users are reminded to execute all cells in
        sequence to avoid errors.

        Returns:
            str: A formatted string with import statements and initialization code.
        """
        notebook_name = os.path.splitext(os.path.basename(self.notebook_path))[0]
        import_statements = (
            "# You must make sure to run all cells in sequence using shift + enter or you might encounter errors\n"
            "from pykubegrader.initialize import initialize_assignment\n"
        )
        initialization_code = f'responses = initialize_assignment("{notebook_name}", "{self.week}", "{self.assignment_type}")\n'
        return import_statements + initialization_code