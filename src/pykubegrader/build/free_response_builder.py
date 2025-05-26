import ast
import base64
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from pykubegrader.build.io import get_filename_and_root
from pykubegrader.build.notebooks.io import modify_notebook_cell
from pykubegrader.build.notebooks.search import find_first_cell_with
from pykubegrader.build.notebooks.search import find_last_import_line
from pykubegrader.build.notebooks.writers import insert_into_source
from pykubegrader.build.notebooks.writers import add_text_after_octothorpe
from pykubegrader.utils.logging import Logger  # For robust datetime parsing
from pykubegrader.build.notebooks.io import get_cell_source
from pykubegrader.build.config import OtterConfigSettings

import nbformat


@dataclass
class OtterNotebookBuilder(Logger, OtterConfigSettings):
    """
    A class for building and processing Otter notebooks.

    This class extends Logger and OtterConfigSettings to provide functionality for
    managing and processing Jupyter notebooks specifically for Otter assignments.

    Attributes:
        notebook_path (str): The file path to the original Jupyter notebook.
        temp_notebook (Optional[str]): The file path to a temporary notebook used for processing.
        assignment_tag (str): A tag identifying the assignment.
        require_key (bool): A flag indicating whether a key is required for processing.
        verbose (bool): A flag indicating whether verbose output is enabled.
    """
    notebook_path: str
    temp_notebook: Optional[str] = None
    assignment_tag: str = ""
    require_key: bool = False
    verbose: bool = False

    def __post_init__(self, **kwargs) -> None:
        """
        Post-initialization method for configuring the OtterNotebookBuilder instance.

        This method is automatically invoked after the instance is created. It performs
        several key setup tasks essential for the functionality of the OtterNotebookBuilder:

        1. **Initialization of Base Classes**: 
           - Calls the `__init__` methods of the `Logger` and `OtterConfigSettings` base classes.
           - Passes any additional keyword arguments (`**kwargs`) to these initializers to ensure
             that any configuration settings or logging parameters are properly set up.

        2. **Path Extraction**:
           - Utilizes the `get_filename_and_root` function to derive the root directory and filename
             from the provided `notebook_path`.
           - This is crucial for managing file operations and ensuring that the notebook is accessed
             correctly within its directory structure.

        3. **Points Initialization**:
           - Sets `total_points` to `0.0`, establishing a baseline for accumulating the total score
             across all questions in the notebook.
           - Initializes `max_question_points` as an empty dictionary (`dict[str, float]`), which will
             be used to store the maximum possible points for each question, identified by a string key.

        4. **Main Processing Routine**:
           - Invokes the `run` method, passing any additional keyword arguments (`**kwargs`).
           - The `run` method orchestrates the main processing tasks, such as parsing the notebook,
             extracting questions, and calculating points.

        Args:
            **kwargs: Additional keyword arguments that may be used for initialization, allowing
                      for flexible configuration and extension of the base class functionalities.
        """
        super(Logger, OtterConfigSettings, self).__init__(**kwargs)
        self.root_path, self.filename = get_filename_and_root(self.notebook_path)
        self.total_points = 0.0
        self.max_question_points: dict[str, float] = {}
        self.run(**kwargs)

    def run(self, **kwargs) -> None:
        # here for easy debugging
        self.make_temp_notebook()

        self.assertion_tests_dict = self.question_dict()
        self.question_points_by_part = self.construct_question_points_by_part(
            self.assertion_tests_dict
        )

        self.add_points_to_notebook()
        self.add_api_code(**kwargs)

    def make_temp_notebook(self):
        """
        Generate a temporary version of the notebook for further processing.

        This method creates a duplicate of the original notebook file, appending '_temp'
        to its name, if a temporary notebook path is specified. If no temporary path is
        specified, the original notebook path is used as the temporary path.

        Raises:
            IOError: Raised if there is an error during the file copy operation.
        """
        if self.temp_notebook is not None:
            shutil.copy(
                self.notebook_path, self.notebook_path.replace(".ipynb", "_temp.ipynb")
            )
            self.temp_notebook = self.notebook_path.replace(".ipynb", "_temp.ipynb")
        else:
            self.temp_notebook = self.notebook_path

    def add_points_to_notebook(self) -> None:
        """
        Adds point information to the notebook.

        This method updates the notebook with the total points for each question
        and each question part. It modifies the notebook cells to include point
        details in the question descriptions.
        """
        self.add_question_points_to_notebook()
        self.add_question_part_points_to_notebook()

    def add_question_points_to_notebook(self) -> None:
        """
        Updates the notebook with total points for each question.

        This method iterates over each question in the notebook, finds the corresponding
        markdown cell, and appends the total points information to the question description.

        The method uses the `question_points_by_part` attribute to retrieve the points
        information and modifies the notebook cells accordingly.

        Raises:
            ValueError: If the notebook cell cannot be found or modified.
        """
        for question, points in self.question_points_by_part["question_sums"].items():
            index, source = find_first_cell_with(
                self.temp_notebook,
                points["current_key"],
                points["previous_key"],
                "markdown",
                "## ",
            )

            if index is None:
                continue

            source = get_cell_source(self.temp_notebook, index)
            modified_source = add_text_after_octothorpe(
                source,
                f"Question {points['question_number']} (Points: {points['total_points']:.2f}):",
            )
            self.replace_cell_source(index, modified_source)

    def add_question_part_points_to_notebook(self) -> None:
        """
        Updates the notebook with total points for each question part.

        This method iterates over each question part in the notebook, finds the corresponding
        markdown cell, and appends the total points information to the question part description.

        The method uses the `question_points_by_part` attribute to retrieve the points
        information and modifies the notebook cells accordingly.

        Raises:
            ValueError: If the notebook cell cannot be found or modified.
        """
        for question, parts in self.question_points_by_part["part_sums"].items():
            for part, points in parts.items():
                index, source = find_first_cell_with(
                    self.temp_notebook,
                    points["current_key"],
                    points["previous_key"],
                    "markdown",
                    "### ",
                )

                if index is None:
                    continue

                source = get_cell_source(self.temp_notebook, index)
                modified_source = add_text_after_octothorpe(
                    source,
                    f"Question {points['question_number']}-Part {points['question_part_number']} (Points: {points['total_points']:.2f}):",
                    "### ",
                )
                self.replace_cell_source(index, modified_source)

    @staticmethod
    def construct_question_points_by_part(question_dict: dict) -> dict:
        """
        Calculate and return the total points for each question and its parts.

        This function processes a dictionary of question data to compute the total
        points for each question and each part of a question. It utilizes helper
        methods to perform these calculations and combines the results into a
        single dictionary.

        Args:
            question_dict (dict): A dictionary containing question data, where each
                                  key is a unique identifier for a question or part,
                                  and each value is a dictionary with details about
                                  the question or part, including its points.

        Returns:
            dict: A dictionary with two keys:
                  - "question_sums": Contains the total points for each question.
                  - "part_sums": Contains the total points for each part of a question.
        """
        question_sums = OtterNotebookBuilder.question_points(question_dict)
        part_sums = OtterNotebookBuilder.parts_points(question_dict)
        result = {"question_sums": question_sums, "part_sums": part_sums}
        return result

    @staticmethod
    def parts_points(question_dict):
        """
        Calculate the total points for each part of a question.

        This method processes a dictionary of question data to compute the total
        points for each part of a question. It organizes the results in a nested
        dictionary structure, where each question is a key, and its value is another
        dictionary containing parts as keys and their respective total points and
        metadata as values.

        Args:
            question_dict (dict): A dictionary containing question data, where each
                                  key is a unique identifier for a question or part,
                                  and each value is a dictionary with details about
                                  the question or part, including its points.

        Returns:
            dict: A dictionary with questions as keys and dictionaries of parts as values.
                  Each part dictionary contains:
                  - "total_points": The sum of points for the part.
                  - "previous_key": The key of the previous part.
                  - "current_key": The key of the current part.
                  - "question_number": The number of the question.
                  - "question_part_number": The part number of the question.
        """
        part_sums = {}
        prev_part = 0  # Initialize previous cell number as 0

        for key, entry in question_dict.items():
            question = entry["question"]
            part = entry["question_part"]
            if part is None:
                continue
            if question not in part_sums:
                part_sums[question] = {}
            if part not in part_sums[question]:
                part_sums[question][part] = {
                    "total_points": 0,
                    "previous_key": prev_part,
                    "current_key": key,
                    "question_number": entry["question_number"],
                    "question_part_number": entry["question_part"],
                }
                prev_part = key  # Update previous key for the next new question part
            part_sums[question][part]["total_points"] += entry["points"]
        return part_sums

    @staticmethod
    def question_points(question_dict):
        """
        Calculate the total points for each question.

        This method processes a dictionary of question data to compute the total
        points for each question. It organizes the results in a dictionary structure,
        where each question number is a key, and its value is a dictionary containing
        the total points and metadata for that question.

        Args:
            question_dict (dict): A dictionary containing question data, where each
                                  key is a unique identifier for a question or part,
                                  and each value is a dictionary with details about
                                  the question or part, including its points.

        Returns:
            dict: A dictionary with question numbers as keys and dictionaries of metadata as values.
                  Each metadata dictionary contains:
                  - "total_points": The sum of points for the question.
                  - "previous_key": The key of the previous question.
                  - "current_key": The key of the current question.
                  - "question_number": The number of the question.
        """
        question_sums = {}
        prev_question = 0  # Initialize previous cell number as 0

        for key, entry in question_dict.items():
            question_number = entry["question_number"]
            if question_number not in question_sums:
                question_sums[question_number] = {
                    "total_points": 0,
                    "previous_key": prev_question,
                    "current_key": None,
                    "question_number": question_number,
                }
                prev_question = key  # Update previous key for the next new question
            question_sums[question_number]["total_points"] += entry["points"]
            question_sums[question_number]["current_key"] = (
                key  # Update current key to the end of the current question
            )

        return question_sums

    @staticmethod
    def conceal_tests(cell_source: list[str], **kwargs) -> list[str]:
        """
        Conceals code blocks in a cell by encoding them in Base64 and replacing them with exec() statements.

        This method processes a list of code lines, identifying blocks between specified markers,
        encoding them in Base64, and replacing them with an exec() statement that will decode and
        execute the concealed code at runtime.

        Args:
            cell_source (list[str]): A list of strings representing the source code lines.
            **kwargs: Optional keyword arguments:
                - start_hide_line (str): The marker indicating the start of a hidden block. Defaults to "# BEGIN HIDE".
                - end_hide_line (str): The marker indicating the end of a hidden block. Defaults to "# END HIDE".
                - encoder: The encoding function to use. Defaults to base64.b64encode.
                - decoder: The decoding function to use. Defaults to base64.b64decode.

        Returns:
            list[str]: A new list of code lines with concealed blocks replaced by exec() statements.
        """

        start_hide_line = kwargs.get("start_hide_line", "# BEGIN HIDE")
        end_hide_line = kwargs.get("end_hide_line", "# END HIDE")
        encoder = kwargs.get("encoder", base64.b64encode)
        decoder = kwargs.get("decoder", base64.b64decode)

        concealed_lines = []
        hide_mode = False
        hidden_code = []

        for line in cell_source:
            if start_hide_line in line:
                hide_mode = True
                hidden_code = []  # Start a new hidden block
                concealed_lines.append(line)  # Keep the marker for clarity
                continue
            elif end_hide_line in line:
                hide_mode = False
                # Encode the entire block
                encoded_block = encoder("\n".join(hidden_code).encode()).decode()
                concealed_lines.append(
                    f'exec({decoder}("{encoded_block}").decode())  # Obfuscated\n'
                )
                concealed_lines.append(line)  # Keep the marker for clarity
                continue

            if hide_mode:
                hidden_code.append(line.strip())  # Collect hidden code
            else:
                concealed_lines.append(line)

        return concealed_lines

    def add_api_code(self, **kwargs) -> None:
        self.compute_max_points_free_response()

        for i, (cell_index, cell_dict) in enumerate(self.assertion_tests_dict.items()):
            self.print_and_log(
                f"Processing cell {cell_index + 1}, {i} of {len(self.assertion_tests_dict)}"
            )

            cell = get_cell_source(self.temp_notebook, cell_index)
            cell_source = self.add_import_statements_to_tests(
                cell["source"],
            )

            cell_source = self.conceal_tests(cell_source, **kwargs)

            last_import_line_ind = find_last_import_line(cell_source)

            updated_cell_source = []
            updated_cell_source.extend(cell_source[: last_import_line_ind + 1])
            
            if cell_dict["is_first"]:
                updated_cell_source.extend(
                    self.construct_first_cell_question_header(cell_dict)
                )
                
            updated_cell_source.extend(["\n"])
            updated_cell_source.extend(
                self.question_information(cell_dict)
            )

            updated_cell_source.extend(cell_source[last_import_line_ind + 1 :])
            updated_cell_source.extend(["\n"])


            #TODO: Here
            updated_cell_source.extend(
                OtterNotebookBuilder.construct_graders(cell_dict)
            )
            updated_cell_source.extend(["\n"])
            updated_cell_source.extend(
                ["earned_points = float(os.environ.get('EARNED_POINTS', 0))\n"]
            )
            updated_cell_source.extend(["earned_points += score\n"])

            short_filename = self.filename.split(".")[0].replace("_temp", "")
            updated_cell_source.extend(
                [
                    f'log_variable("{short_filename}",f"{{score}}, {{max_score}}", question_id)\n'
                ]
            )
            updated_cell_source.extend(
                ["os.environ['EARNED_POINTS'] = str(earned_points)\n"]
            )

            updated_cell_source.extend(
                OtterNotebookBuilder.construct_update_responses(cell_dict)
            )

            self.replace_cell_source(cell_index, updated_cell_source)

    def find_question_description(self, search_string):
        with open(self.temp_notebook, "r", encoding="utf-8") as f:
            nb_data = json.load(f)

        found_raw = False

        for idx, cell in enumerate(nb_data.get("cells", [])):
            if (
                cell["cell_type"] == "raw"
                and any("# BEGIN QUESTION" in line for line in cell.get("source", []))
                and any(search_string in line for line in cell.get("source", []))
            ):
                found_raw = True
            elif found_raw and cell["cell_type"] == "markdown":
                return idx, cell.get(
                    "source", []
                )  # Return the index of the first matching markdown cell

        return None, None  # Return None if no such markdown cell is found

    def get_max_question_points(self, cell_dict) -> float:
        """
        Calculate the maximum points for a given question.

        This method computes the total points available for a specific question by summing
        the points from all cells in the assertion tests dictionary that belong to the same
        question as the provided cell dictionary.

        Args:
            cell_dict (dict): A dictionary containing information about a specific cell,
                            including the question it belongs to.

        Returns:
            float: The total maximum points available for the question.
        """
        return sum(
            cell["points"]
            for cell in self.assertion_tests_dict.values()
            if cell["question"] == cell_dict["question"]
        )

    def compute_max_points_free_response(self) -> None:
        """
        Computes and stores the maximum points for each free response question.

        This method iterates over the assertion tests dictionary to calculate the
        maximum points for each question. It ensures that points are only counted
        once per question by checking if the cell is marked as the first for that
        question. The computed maximum points are stored in the `max_question_points`
        attribute, and the total points are accumulated in the `total_points` attribute.
        """
        for cell_dict in self.assertion_tests_dict.values():
            if cell_dict["is_first"]:
                max_question_points = self.get_max_question_points(cell_dict)
                self.max_question_points[f"{cell_dict['question']}"] = (
                    max_question_points
                )
                self.total_points += max_question_points

    def construct_first_cell_question_header(self, cell_dict: dict) -> list[str]:
        """
        Constructs the header code for the first cell of a question.

        This method generates the initial code block that sets up the testing environment
        for a question. It includes:
        - Maximum points for the question
        - Total points for the free response section
        - Key validation (if required)
        - Logging setup

        Args:
            cell_dict (dict): A dictionary containing information about the question cell,
                            including the question number and points.

        Returns:
            list[str]: A list of strings representing the lines of code for the question header.
        """
        max_question_points = self.get_max_question_points(cell_dict)
        filename = self.filename.split(".")[0].replace("_temp", "")
        
        first_cell_header = self.first_test_header(cell_dict, max_question_points, filename)

        if self.require_key:
            first_cell_header.append(
                self.get_key_validation_line(assignment_tag=self.assignment_tag)
            )

        return first_cell_header

    @staticmethod
    def construct_update_responses(cell_dict: dict) -> list[str]:
        update_responses = []

        logging_variables = cell_dict["logging_variables"]

        for logging_variable in logging_variables:
            update_responses.append(
                f"responses = update_responses(question_id, str({logging_variable}))\n"
            )

        return update_responses

    @staticmethod
    def split_list_at_marker(
        input_list: list[str], marker: str = """# END TEST CONFIG"""
    ) -> tuple[list[str], list[str]]:
        """
        Splits a list into two parts at the specified marker string.

        Args:
            input_list (list): The list to split.
            marker (str): The string at which to split the list.

        Returns:
            tuple: A tuple containing two lists. The first list contains the elements
                before the marker, and the second list contains the elements after
                the marker (excluding the marker itself).
        """
        if marker in input_list:
            index = input_list.index(marker)
            return input_list[: index + 1], input_list[index + 2 :]
        else:
            return (
                input_list,
                [],
            )  # If the marker is not in the list, return the original list and an empty list

    @staticmethod
    def construct_graders(cell_dict: dict) -> list[str]:
        # Generate Python code
        added_code = [
            "if "
            + " and ".join(f"({test})" for test in cell_dict["assertions"])
            + ":\n"
        ]
        added_code.append(f"    score = {cell_dict['points']}\n")

        return added_code

    @staticmethod
    def insert_list_at_index(
        original_list: list[str],
        insert_list: list[str],
        index: int,
        line_break: bool = True,
        inplace_line_break: bool = True,
    ) -> list[str]:
        """
        Inserts a list into another list at a specific index.

        Args:
            original_list (list): The original list.
            insert_list (list): The list to insert.
            index (int): The position at which to insert the new list.

        Returns:
            list: A single combined list with the second list inserted at the specified index.
        """

        if inplace_line_break:
            insert_list = [s + "\n" for s in insert_list]

        if line_break:
            if inplace_line_break:
                insert_list = ["\n"] + insert_list
            else:
                insert_list = ["\n"] + insert_list + ["\n"]

        return original_list[:index] + insert_list + original_list[index:]

    def add_import_statements_to_tests(
        self,
        cell_source: list[str],
    ) -> list[str]:
        """
        Adds the necessary import statements and optional key validation to the first cell of the notebook.

        This method inserts required import statements and, if specified, a key validation line into the notebook's
        first cell. The imports are inserted before a specified end marker line.

        Args:
            cell_source (list[str]): The source code lines of the cell to modify.
            require_key (bool, optional): Whether to include key validation. Defaults to False.
            assignment_tag (str, optional): The assignment tag to use for key validation. Defaults to None.

        Returns:
            list[str]: The modified cell source with imports and optional key validation inserted.

        Note:
            The imports are inserted before the line containing the end_test_config_line marker.
        """

        lines_to_insert = self.test_required_imports

        if self.require_key:
            lines_to_insert.append(self.get_key_validation_line(self.assignment_tag))

        cell_source = insert_into_source(
            cell_source,
            lines_to_insert=lines_to_insert,
            flag_to_insert=self.end_test_config_line,
        )

        return cell_source

    # TODO: `Any` return not good; would be better to specify return type(s)
    def extract_first_cell(self) -> Any:
        if not self.temp_notebook:
            raise ValueError("No temporary notebook file path provided")
        with open(self.temp_notebook, "r", encoding="utf-8") as f:
            notebook = json.load(f)
        if "cells" in notebook and len(notebook["cells"]) > 0:
            return notebook["cells"][0]
        else:
            return None    

    def replace_cell_source(self, cell_index: int, new_source: str | list[str]) -> None:
        """
        Replace the source code of a specific Jupyter notebook cell.

        Args:
            cell_index (int): Index of the cell to be modified (0-based).
            new_source (str): New source code to replace the cell's content.
        """
        # Load the notebook
        if not self.temp_notebook:
            raise ValueError("No temporary notebook file path provided")
        modify_notebook_cell(self.temp_notebook, cell_index, new_source)

        self.print_and_log(f"Updated notebook saved to {self.temp_notebook}")

    @staticmethod
    def extract_log_variables(cell: dict) -> list[str]:
        """
        Extracts log variables from the first cell.

        Args:
            cell (dict): A dictionary representing a notebook cell.

        Returns:
            list[str]: A list of log variable names extracted from the cell.
        """
        if "source" in cell:
            for line in cell["source"]:
                # Look for the log_variables pattern
                match = re.search(r"log_variables:\s*(\[.*\])", line)
                if match:
                    # Parse the list using ast.literal_eval for safety
                    try:
                        log_variables = ast.literal_eval(match.group(1))
                        if isinstance(log_variables, list):
                            return [var.strip() for var in log_variables]
                    except (SyntaxError, ValueError):
                        pass
        return []

    @staticmethod
    def tag_questions(cells_dict: dict) -> dict:
        """
        Adds 'is_first' and 'is_last' boolean flags to the cells based on their position
        within the group of the same question. All cells will have both flags.

        Args:
            cells_dict (dict): A dictionary where keys are cell IDs and values are cell details.

        Returns:
            dict: The modified dictionary with 'is_first' and 'is_last' flags added.
        """
        if not isinstance(cells_dict, dict):
            raise ValueError("Input must be a dictionary.")

        # Ensure all cells have the expected structure
        for key, cell in cells_dict.items():
            if not isinstance(cell, dict):
                raise ValueError(f"Cell {key} is not a dictionary.")
            if "question" not in cell:
                raise KeyError(f"Cell {key} is missing the 'question' key.")

        # Group the keys by question name
        question_groups = OtterNotebookBuilder.group_keys_by_question_name(cells_dict)

        # Add 'is_first' and 'is_last' flags to all cells
        OtterNotebookBuilder.add_cell_first_last_tag(cells_dict, question_groups)

        return cells_dict

    @staticmethod
    def add_cell_first_last_tag(cells_dict, question_groups):
        """
        Adds 'is_first', 'is_last', and 'test_number' attributes to each cell in the cells_dict.

        This function iterates over groups of cell keys, assigning boolean flags 'is_first' and 'is_last'
        to indicate the position of each cell within its group. It also assigns a sequential 'test_number'
        to each cell.

        Args:
            cells_dict (dict): A dictionary where keys are cell IDs and values are cell details.
            question_groups (dict): A dictionary where keys are question names and values are lists of cell IDs
                                    associated with each question.

        Modifies:
            cells_dict: Updates each cell's dictionary with 'is_first', 'is_last', and 'test_number' attributes.
        """
        for keys in question_groups.values():
            test_number = 1
            for i, key in enumerate(keys):
                cells_dict[key]["is_first"] = i == 0
                cells_dict[key]["is_last"] = i == len(keys) - 1
                cells_dict[key]["test_number"] = test_number
                test_number += 1

    @staticmethod
    def group_keys_by_question_name(cells_dict):
        """
        Groups cell keys by their associated question name.

        This method organizes the keys of a dictionary of cells into groups based on the
        'question' attribute of each cell. It returns a dictionary where each key is a
        question name and the corresponding value is a list of keys from the original
        dictionary that are associated with that question.

        Args:
            cells_dict (dict): A dictionary where keys are cell IDs and values are cell details.

        Returns:
            dict: A dictionary with question names as keys and lists of cell IDs as values.
        """
        question_groups: dict = {}
        for key, cell in cells_dict.items():
            question = cell.get(
                "question"
            )  # Use .get() to avoid errors if key is missing
            if question not in question_groups:
                question_groups[question] = []
            question_groups[question].append(key)
        return question_groups

    @staticmethod
    def extract_question_information(source: str) -> tuple[str, str, str]:
        """
        Extracts question information from the given source string.

        Args:
            source (str): The source string containing question information.

        Returns:
            tuple[str, str, str]: A tuple containing the question name, question number, and question part.
        """
        name_match = re.search(r"name:\s*(.*)", source, re.MULTILINE)
        question_name = name_match.group(1).strip() if name_match else None
        question_number = re.search(r"question:\s*(\d+)", source, re.MULTILINE)
        question_number = question_number.group(1).strip() if question_number else None
        question_part = re.search(r"part:\s*(.*)", source, re.MULTILINE)
        question_part = question_part.group(1).strip() if question_part else None

        return question_name, question_number, question_part

    def question_dict(self) -> dict:
        """
        Builds a dictionary of question information from the notebook.

        Returns:
            dict: A dictionary containing question information.
        """

        # Check if the temporary notebook file path is provided
        if not self.temp_notebook:
            raise ValueError("No temporary notebook file path provided")

        # Check if the file exists
        notebook_path = Path(self.temp_notebook)

        # Check if the file exists
        if not notebook_path.exists():
            raise FileNotFoundError(f"The file {notebook_path} does not exist.")

        # Read the notebook
        notebook = read_notebook(notebook_path)

        # Initialize the results dictionary
        results_dict = {}
        question_name = None  # At least define the variable up front

        for cell_index, cell in enumerate(notebook.get("cells", [])):
            if cell.get("cell_type") == "raw":
                source = "".join(cell.get("source", ""))
                if source.strip().startswith("# BEGIN QUESTION"):
                    question_name, question_number, question_part = (
                        OtterNotebookBuilder.extract_question_information(source)
                    )

            elif cell.get("cell_type") == "code":
                source = "".join(cell.get("source", ""))
                if source.strip().startswith('""" # BEGIN TEST CONFIG'):
                    # Extract the assertion test source
                    logging_variables, assertions, comments, points_value = (
                        self.extract_assertion_test_source(cell, source)
                    )

                    # Add to results dictionary
                    results_dict[cell_index] = {
                        "assertions": assertions,
                        "comments": comments,
                        "question": question_name,
                        "question_number": question_number,
                        "question_part": question_part,
                        "points": points_value,
                        "logging_variables": logging_variables,
                    }

                    results_dict = OtterNotebookBuilder.tag_questions(results_dict)

        return results_dict

    def extract_assertion_test_source(self, cell, source):
        """
        Extracts assertion test information from a given code cell source.

        This method processes the source code of a Jupyter notebook cell to extract
        logging variables, assertions, comments, and point values associated with
        test configurations. It identifies and processes assertion statements,
        ensuring proper handling of multi-line assertions and comments.

        Args:
            cell (dict): A dictionary representing a Jupyter notebook cell.
            source (str): The source code of the cell as a string.

        Returns:
            tuple: A tuple containing:
                - logging_variables (list): A list of variables used for logging.
                - assertions (list): A list of assertion statements extracted from the source.
                - comments (list): A list of comments associated with the assertions.
                - points_value (float or None): The point value extracted from the source, or None if not found.

        Raises:
            ValueError: If the points value cannot be converted to a float.
        """
        logging_variables = OtterNotebookBuilder.extract_log_variables(cell)

        # Extract assert statements using a more robust approach
        assertions = []
        comments = []

        # Split the source into lines for processing
        lines = source.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("assert"):
                # Initialize assertion collection
                assertion_lines = []
                comment = None

                # Handle the first line
                first_line = line[6:].strip()  # Remove 'assert' keyword
                assertion_lines.append(first_line)

                # Stack to track parentheses
                paren_stack = []
                for char in first_line:
                    if char == "(":
                        paren_stack.append(char)
                    elif char == ")":
                        if paren_stack:
                            paren_stack.pop()

                # Continue collecting lines while we have unclosed parentheses
                current_line = i + 1
                while paren_stack and current_line < len(lines):
                    next_line = lines[current_line].strip()
                    assertion_lines.append(next_line)

                    for char in next_line:
                        if char == "(":
                            paren_stack.append(char)
                        elif char == ")":
                            if paren_stack:
                                paren_stack.pop()

                    current_line += 1

                # Join the assertion lines and clean up
                full_assertion = " ".join(assertion_lines)

                # Extract the comment if it exists (handling both f-strings and regular strings)
                comment_match = re.search(
                    r',\s*(?:f?["\'])(.*?)(?:["\'])\s*(?:\)|$)',
                    full_assertion,
                )
                if comment_match:
                    comment = comment_match.group(1).strip()
                    # Remove the comment from the assertion
                    full_assertion = full_assertion[: comment_match.start()].strip()

                # Ensure proper parentheses closure
                open_count = full_assertion.count("(")
                close_count = full_assertion.count(")")
                if open_count > close_count:
                    full_assertion += ")" * (open_count - close_count)

                # Clean up the assertion
                if full_assertion.startswith("(") and not full_assertion.endswith(")"):
                    full_assertion += ")"

                assertions.append(full_assertion)
                comments.append(comment)

                # Update the line counter
                i = current_line
            else:
                i += 1

        # Extract points value
        points_line = next(
            (line for line in source.split("\n") if "points:" in line), None
        )
        points_value = None
        if points_line:
            try:
                points_value = float(points_line.split(":")[-1].strip())
            except ValueError:
                points_value = None
        return logging_variables, assertions, comments, points_value


