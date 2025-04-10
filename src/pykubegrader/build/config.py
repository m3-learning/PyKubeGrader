from dataclasses import dataclass
from pathlib import Path

import nbformat
from pykubegrader.build.notebooks.writers import AddKeyRequirementImportBaseClass
from pykubegrader.build.util import EncryptionKeyBaseClass
@dataclass
class DisplayQuestionCode:
    
    @property
    def build_code(self, file_name_ipynb, dict_):
        return [
                "# Run this block of code by pressing Shift + Enter to display the question\n",
                f"from questions.{file_name_ipynb} import Question{dict_['question number']}\n",
                f"Question{dict_['question number']}().show()\n",
            ]



question_class_type = {
    "MCQuestion": {"class_type": "MCQuestion", "style": "MCQ"},
    "SelectMany": {"class_type": "SelectMany", "style": "MultiSelect"},
    "TFQuestion": {"class_type": "TFQuestion", "style": "TFStyle"},
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

