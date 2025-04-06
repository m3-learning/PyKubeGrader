from pykubegrader.build.widget_questions.utils import process_widget_questions
import os
from pykubegrader.build.build_folder import NotebookProcessor, check_for_heading
from pykubegrader.build.widget_questions.utils import extract_raw_cells, generate_mcq_file, replace_cells_between_markers
from dataclasses import dataclass
from abc import abstractmethod

@dataclass
class QuestionProcessorBaseClass:
    ipynb_file: str
    temp_notebook_path: str = None
    
    def __post_init__(self):
        if self.temp_notebook_path is None:
            self.temp_notebook_path = self.ipynb_file.replace(".ipynb", "_temp.ipynb")

    # Abstract properties to be implemented by subclasses
    @property
    @abstractmethod
    def start_tag(self):
        pass

    @property
    @abstractmethod
    def end_tag(self):
        pass

    @property
    @abstractmethod
    def question_type(self):
        pass
            
    @abstractmethod
    def extract(self):
        pass
    
    def has_assignment(self):
        """
        Determines if the Jupyter notebook contains specific configuration tags.

        This method checks the notebook for the presence of predefined start and end tags
        to verify if it includes the necessary configuration for assignments.

        Returns:
            bool: True if the notebook contains any of the specified start or end tags, False otherwise.
        """
        
        tags = [self.start_tag, self.end_tag]

        # Use the helper function to check for the presence of any specified tag
        return check_for_heading(self.temp_notebook_path, tags)
    
    def run(self):
        
        if self.has_assignment():
            
            # prints/logs the message
            self._print_and_log(
                f"Notebook {self.temp_notebook_path} has {self.question_type} questions"
            )
            
            # Extract all the multiple choice questions
            data = self.extract()
            
            # determine the output file path
            solution_path = f"{os.path.splitext(self.ipynb_file)[0]}_solutions.py"
            question_path = f"{os.path.splitext(self.ipynb_file)[0]}_questions.py"
            
            # Extract the first value cells
            value = extract_raw_cells(self.temp_notebook_path)
            
            data = NotebookProcessor.merge_metadata(value, data)

            self.mcq_total_points = NotebookProcessor.generate_widget_solutions(
                data, output_file=solution_path
            )            

            generate_mcq_file(data, output_file=question_path)
            
            markers = (self.start_tag, self.end_tag)

            replace_cells_between_markers(
                data, markers, self.temp_notebook_path, self.temp_notebook_path
            )

            return solution_path, question_path
    
        else:
            
            return None, None


@dataclass
class MultipleChoice(QuestionProcessorBaseClass):
    start_tag: str = "# BEGIN MULTIPLE CHOICE"
    end_tag: str = "# END MULTIPLE CHOICE"
    question_type: str = "multiple choice"

    def __post_init__(self):
        if self.temp_notebook_path is None:
            self.temp_notebook_path = self.ipynb_file.replace(".ipynb", "_temp.ipynb")

    def extract(self):
        return process_widget_questions(self.ipynb_file, self.start_tag, self.end_tag)
    
    