from pykubegrader.build.widget_questions.utils import process_widget_questions
import os
from pykubegrader.utils.logging import Logger
from pykubegrader.build.build_folder import NotebookProcessor, check_for_heading
from pykubegrader.build.widget_questions.utils import generate_mcq_file, replace_cells_between_markers
from dataclasses import dataclass
from abc import abstractmethod
import json
import importlib
from pykubegrader.build.build_folder import ensure_imports, write_question_class
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
    
    @staticmethod
    def merge_metadata(raw, data):
        """
        Merges raw metadata with extracted question data.

        This method combines metadata from two sources: raw metadata and question data.
        It ensures that the points associated with each question are appropriately distributed
        and added to the final merged metadata.

        Args:
            raw (list): A list of dictionaries containing raw metadata.
                        Each dictionary must have a 'points' key with a value
                        that can be either a list of points or a string representing a single point value.
            data (list): A list of dictionaries containing extracted question data.
                        Each dictionary represents a set of questions and their details.

        Returns:
            list: A list of dictionaries where each dictionary represents a question
                with merged metadata and associated points.

        Raises:
            KeyError: If 'points' is missing from any raw metadata entry.
            IndexError: If the number of items in `raw` and `data` do not match.

        Example:
            raw = [
                {"points": [1.0, 2.0]},
                {"points": "3.0"}
            ]
            data = [
                {"Q1": {"question_text": "What is 2+2?"}},
                {"Q2": {"question_text": "What is 3+3?"}}
            ]
            merged = merge_metadata(raw, data)
            print(merged)
            # Output:
            # [
            #     {"Q1": {"question_text": "What is 2+2?", "points": 1.0}},
            #     {"Q2": {"question_text": "What is 3+3?", "points": 3.0}}
            # ]
        """
        
        # Loop through each question set in the data
        for i, _data in enumerate(data):
            
            # Handle 'points' from raw metadata: convert single string value to a list if necessary
            points_, grade_ = NotebookProcessor.extract_question_points(raw, i, _data)

            # Merge each question's metadata with corresponding raw metadata
            for j, (key, _) in enumerate(_data.items()):
                
                # Combine raw metadata with question data
                data[i][key] = data[i][key] | raw[i]
                
                # Assign the correct point value to the question
                data[i][key]["points"] = points_[j]

                if "grade" in raw[i]:
                    data[i][key]["grade"] = grade_

        return data
    
    @staticmethod
    def generate_widget_solutions(data_list, **kwargs):
        """
        Generates a Python file with solutions and total points based on the input data.
        If the file already exists, it appends new solutions to the existing solution dictionary.

        Args:
            data_list (list): A list of dictionaries containing question metadata.
            output_file (str): Path to the output Python file.
        """
        
        output_file = kwargs.get("output_file", "output.py")

        solutions = {}
        total_points = []

        # If the output file exists, load the existing solutions and total_points
        QuestionProcessorBaseClass.read_existing_solution(output_file, solutions, total_points)

        question_points = QuestionProcessorBaseClass.build_solutions(data_list, solutions, total_points)

        # Write updated total_points and solutions back to the file
        QuestionProcessorBaseClass.write_solutions(output_file, solutions, total_points)

        return question_points
    
    @staticmethod
    def write_solutions(output_file, solutions, total_points):
        """
        Writes the solutions and total points to a Python file.

        This method creates a Python file that contains the total points and a dictionary
        of solutions. If the file already exists, it will be overwritten.

        Args:
            output_file (str): Path to the output Python file.
            solutions (dict): A dictionary containing question keys and their corresponding solutions.
            total_points (float): The total points for the questions.

        Returns:
            None
        """
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("from typing import Any\n\n")
            f.write(f"total_points: float = {total_points}\n\n")

            f.write("solutions: dict[str, Any] = {\n")
            for key, solution in solutions.items():
                # For safety, we assume solutions are strings, but if not, repr would be safer
                f.write(f'    "{key}": {repr(solution)},\n')
            f.write("}\n")
    
    @staticmethod
    def read_existing_solution(output_file, solutions, total_points):
        """
        Reads existing solutions and total points from a given output file.

        This method dynamically loads a Python module from the specified output file
        and updates the provided solutions dictionary and total_points list with the
        existing data from the module.

        Args:
            output_file (str): Path to the output Python file containing existing solutions and total points.
            solutions (dict): A dictionary to be updated with existing solutions from the output file.
            total_points (list): A list to be extended with existing total points from the output file.

        Returns:
            None
        """
        if os.path.exists(output_file):
            spec = importlib.util.spec_from_file_location(
                "existing_module", output_file
            )
            existing_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(existing_module)  # Load the module dynamically

            # Attempt to read existing solutions and total_points
            if hasattr(existing_module, "solutions"):
                solutions.update(existing_module.solutions)
            if hasattr(existing_module, "total_points"):
                total_points.extend(existing_module.total_points) 
                
    @staticmethod
    def build_solutions(data_list, solutions, total_points):
        """
        Processes new question data and updates solutions and total points.

        This method iterates through the provided data list, extracts question information,
        and updates the solutions dictionary and total points list accordingly.

        Args:
            data_list (list): A list of dictionaries containing question metadata.
            solutions (dict): A dictionary to be updated with question keys and their corresponding solutions.
            total_points (list): A list to be extended with points for each question.

        Returns:
            float: The total points for the questions processed in this method.
        """
        question_points = 0
        
        # Process new question data and update solutions and total_points
        for question_set in data_list:
            for key, question_data in question_set.items():
                solution_key = f"q{question_data['question number']}-{question_data['subquestion_number']}-{key}"
                solutions[solution_key] = question_data["solution"]
                total_points.extend([question_data["points"]])
                question_points += question_data["points"]
        return question_points
    
    @property
    def header_lines(self):
        return [
            "import pykubegrader.initialize\n",
            "import panel as pn\n\n",
            "pn.extension()\n\n",
        ]
    
    def make_question_py_file(self, data_dict, **kwargs):
        
        output_file = kwargs.get("output_file", "questions.py")
        
        header_lines = self.additional_header_lines + self.header_lines
        
        # Ensure header lines are present
        _existing_content = ensure_imports(output_file, header_lines)
        
        for question_dict in data_dict:
            with open(output_file, "a", encoding="utf-8") as f:
                for i, (q_key, q_value) in enumerate(question_dict.items()):
                    if i == 0:
                        # Write the MCQuestion class
                        write_question_class(f, q_value, class_name = "MCQuestion")
                    break

                keys = []
                for i, (q_key, q_value) in enumerate(question_dict.items()):
                    # Write keys
                    keys.append(
                        f"q{q_value['question number']}-{q_value['subquestion_number']}-{q_value['name']}"
                    )

                f.write(f"            keys={keys},\n")

                options = []
                for i, (q_key, q_value) in enumerate(question_dict.items()):
                    # Write options
                    options.append(q_value["OPTIONS"])

                f.write(f"            options={options},\n")

                descriptions = []
                for i, (q_key, q_value) in enumerate(question_dict.items()):
                    # Write descriptions
                    descriptions.append(q_value["question_text"])
                f.write(f"            descriptions={descriptions},\n")

                points = []
                for i, (q_key, q_value) in enumerate(question_dict.items()):
                    # Write points
                    points.append(q_value["points"])

                f.write(f"            points={points},\n")
                f.write("        )\n")
        
        
    
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
            
            data = self.merge_metadata(value, data)

            self.points_subtotal = QuestionProcessorBaseClass.generate_widget_solutions(
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
    
    def make_question_file(self):
        
        self.additional_header_lines = ["from pykubegrader.widgets.multiple_choice import MCQuestion, MCQ\n",]
        
        
        
    
    def generate_mcq_file(data_dict, output_file="mc_questions.py"):
        """
        Generates a Python file defining an MCQuestion class from a dictionary.

        Args:
            data_dict (dict): A nested dictionary containing question metadata.
            output_file (str): The path for the output Python file.

        Returns:
            None
        """

        

        

        
    
    