from pykubegrader.build.widget_questions.utils import process_widget_questions
import os
from pykubegrader.utils.logging import Logger
from pykubegrader.build.build_folder import NotebookProcessor, check_for_heading
from pykubegrader.build.widget_questions.utils import extract_raw_cells, generate_mcq_file, replace_cells_between_markers
from dataclasses import dataclass
from abc import abstractmethod
import json
@dataclass
class QuestionProcessorBaseClass:
    ipynb_file: str
    temp_notebook_path: str = None
    
    def __post_init__(self, **kwargs):
        if self.temp_notebook_path is None:
            self.temp_notebook_path = self.ipynb_file.replace(".ipynb", "_temp.ipynb")
            
        self.logger = Logger(**kwargs)

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
    
    def extract_raw_cells(self, **kwargs):
        """
        Extracts all metadata from value cells in a Jupyter Notebook file for a specified heading.

        Args:
            ipynb_file (str): Path to the .ipynb file.
            heading (str): The heading to search for in value cells.

        Returns:
            list of dict: A list of dictionaries containing extracted metadata for each heading occurrence.
        """
        try:
            with open(self.ipynb_file, "r", encoding="utf-8") as f:
                notebook_data = json.load(f)

            # Extract value cell content
            raw_cells = [
                "".join(
                    cell.get("source", [])
                )  # Join multiline sources into a single string
                for cell in notebook_data.get("cells", [])
                if cell.get("cell_type") == "raw"
            ]

            # Process each value cell to extract metadata
            metadata_list = []
            for raw_cell in raw_cells:
                metadata_list.extend(self._extract_metadata_from_heading(raw_cell, **kwargs))

            return metadata_list

        except FileNotFoundError:
            print(f"File {self.ipynb_file} not found.")
            return []
        except json.JSONDecodeError:
            print("2 Invalid JSON in notebook file.")
            return []
        
    def _extract_metadata_from_heading(self, raw_cell, **kwargs):
        """
        Extracts metadata from a single raw cell string based on the presence of a specified heading.

        Args:
            raw_cell (str): The content of a raw cell as a string.
            **kwargs: Additional keyword arguments.
                - metadata_indicator (str): The prefix used to identify metadata lines. Defaults to "##".

        Returns:
            list of dict: A list of dictionaries, each containing key-value pairs extracted from the metadata lines.
        """
        
        metadata_indicator = kwargs.get("metadata_indicator", "##")
        
        metadata_list = []
        lines = raw_cell.split("\n")
        current_metadata = None

        for line in lines:
            if line.startswith(self.start_tag):
                if current_metadata:
                    metadata_list.append(current_metadata)  # Save previous metadata
                current_metadata = {}  # Start new metadata block
            elif line.startswith(metadata_indicator) and current_metadata is not None:
                # Extract key and value from lines
                key, value = line[3:].split(":", 1)
                current_metadata[key.strip()] = value.strip()

        if current_metadata:  # Append the last metadata block
            metadata_list.append(current_metadata)

        return metadata_list

    
    def run(self, **kwargs):
        
        if self.has_assignment():
            
            # prints/logs the message
            self.logger.print_and_log(
                f"Notebook {self.temp_notebook_path} has {self.question_type} questions"
            )
            
            # Extract all the questions
            data = self.extract()
            
            # determine the output file path
            solution_path = f"{os.path.splitext(self.ipynb_file)[0]}_solutions.py"
            question_path = f"{os.path.splitext(self.ipynb_file)[0]}_questions.py"
            
            # Extract the first value cells
            value = self.extract_raw_cells(self.temp_notebook_path, **kwargs)
            
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
    
    