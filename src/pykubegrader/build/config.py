from dataclasses import dataclass
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
