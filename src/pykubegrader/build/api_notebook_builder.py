from dataclasses import dataclass
from pathlib import Path
import json
import nbformat
import json
import re


@dataclass
class FastAPINotebookBuilder:
    notebook_path: str

    def __post_init__(self):
        self.root_path, self.filename = FastAPINotebookBuilder.get_filename_and_root(
            self.notebook_path
        )

        self.import_cell = self.extract_first_cell()
        self.import_cell = self.add_imports()

        self.assertion_tests_dict = self.question_dict()

        self.add_api_code()

    def add_api_code(self):

        for i, (cell_index, cell_dict) in enumerate(self.assertion_tests_dict.items()):
            cell = self.get_cell(cell_index)
            cell_source = FastAPINotebookBuilder.add_import_statements_to_tests(
                cell["source"]
            )

            last_import_line_ind = FastAPINotebookBuilder.find_last_import_line(
                cell_source
            )

            top_cell_source = []

            if cell_dict["is_first"]:
                top_cell_source.append(
                    self.construct_first_cell_question_header(cell_dict)
                )

            top_cell_source.append(
                FastAPINotebookBuilder.construct_question_info(cell_dict)
            )

            cell_source = FastAPINotebookBuilder.insert_list_at_index(
                cell_source, top_cell_source, last_import_line_ind + 1
            )

    def construct_first_cell_question_header(self, cell_dict):
        max_question_points = sum(
            cell["points"]
            for cell in self.assertion_tests_dict.values()
            if cell["question"] == cell_dict["question"]
        )

        first_cell_header = ["max_question_points = " + str(max_question_points)]
        first_cell_header.append("earned_points = 0")

        return first_cell_header

    @staticmethod
    def construct_update_responses(cell_dict):
        update_responses = []
        question_id = cell_dict["question"] + "-" + str(cell_dict["test_number"])

        logging_variables = cell_dict["logging_variables"]

        for logging_variable in logging_variables:
            update_responses.append(
                f"responses = update_responses({question_id}, {logging_variable})"
            )

        return update_responses

    @staticmethod
    def construct_graders(cell_dict):

        # Generate Python code
        added_code = [
            "if " + " and ".join(f"({test})" for test in cell_dict["assertions"]) + ":"
        ]
        added_code.append(f"    score = {cell_dict['points']}")

        return added_code

    @staticmethod
    def construct_question_info(cell_dict):
        question_info = []

        question_id = cell_dict["question"] + "-" + str(cell_dict["test_number"])

        question_info.append(f'question_id = "{question_id}"')
        question_info.append(f'max_score = {cell_dict["points"]}')
        question_info.append(f"score = 0")

        return question_info

    @staticmethod
    def insert_list_at_index(
        original_list, insert_list, index, line_break=True, inplace_line_break=True
    ):
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

    @staticmethod
    def add_import_statements_to_tests(cell_source):
        """
        Adds the necessary import statements to the first cell of the notebook.
        """

        end_test_config_line = "# END TEST CONFIG"

        # Imports to add
        imports = [
            "from pygrader_utils.telemetry import (\n",
            "    ensure_responses,\n",
            "    log_variable,\n",
            "    score_question,\n",
            "    submit_question_new,\n",
            "    telemetry,\n",
            "    update_responses,\n",
            ")",
        ]

        for i, line in enumerate(cell_source):
            if end_test_config_line in line:
                # Insert the imports immediately after the current line
                cell_source[i + 1 : i + 1] = [
                    "\n"
                ] + imports  # Add a blank line for readability
                return cell_source  # Exit the loop once the imports are inserted

    def add_imports(
        self, import_text="from pykubegrader.initialize import initialize_assignment"
    ):
        """
        Adds the necessary imports to the first cell of the notebook.
        """

        lines = self.import_cell["source"]
        last_import_index = -1

        # Find the index of the last 'import' line
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("import") or stripped_line.startswith("from"):
                last_import_index = i

        # Insert the new import line after the last import
        if last_import_index != -1:
            lines.insert(last_import_index + 1, import_text)
        else:
            # If no import is found, add the new import line at the top
            lines.insert(0, import_text)

        # adds the initialize assignment line
        lines.append(f'responses = initialize_assignment("{self.filename}")')
        lines = [line.replace("\n", "") for line in lines]

        return "\n".join(lines)

    def extract_first_cell(self):
        with open(self.notebook_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)
        if "cells" in notebook and len(notebook["cells"]) > 0:
            return notebook["cells"][0]
        else:
            return None

    @staticmethod
    def get_filename_and_root(path):
        path_obj = Path(path).resolve()  # Resolve the path to get an absolute path
        root_path = path_obj.parent  # Get the parent directory
        filename = path_obj.name  # Get the filename
        return root_path, filename

    def get_cell(self, cell_index):
        with open(self.notebook_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)
        if "cells" in notebook and len(notebook["cells"]) > cell_index:
            return notebook["cells"][cell_index]
        else:
            return None

    def replace_cell_source(self, cell_index, new_source, output_path=None):
        """
        Replace the source code of a specific Jupyter notebook cell.

        Args:
            cell_index (int): Index of the cell to be modified (0-based).
            new_source (str): New source code to replace the cell's content.
            output_path (str): Path to save the modified notebook (default is to overwrite the original).
        """
        # Load the notebook
        with open(self.notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Check if the cell index is valid
        if cell_index >= len(notebook.cells) or cell_index < 0:
            raise IndexError(
                f"Cell index {cell_index} is out of range for this notebook."
            )

        # Replace the source code of the specified cell
        notebook.cells[cell_index]["source"] = new_source

        # Save the notebook
        output_path = (
            output_path or self.notebook_path
        )  # Overwrite original if no output path is provided
        with open(output_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        print(f"Updated notebook saved to {output_path}")

    @staticmethod
    def find_last_import_line(cell_source):
        """
        Finds the index of the last line with an import statement in a list of code lines.

        Args:
            cell_source (list): List of strings representing the code lines.

        Returns:
            int: The index of the last line with an import statement, or -1 if no import is found.
        """
        last_import_index = -1

        for i, line in enumerate(cell_source):
            # Check if the line starts with "import" or "from ... import"
            if line.strip().startswith("import") or line.strip().startswith("from"):
                last_import_index = i

        return last_import_index

    @staticmethod
    def extract_log_variables(cell):
        """Extracts log variables from the first cell."""
        if "source" in cell:
            for line in cell["source"]:
                # Look for the log_variables pattern
                match = re.search(r"log_variables:\s*\[(.*?)\]", line)
                if match:
                    # Split the variables by comma and strip whitespace
                    log_variables = [var.strip() for var in match.group(1).split(",")]
                    return log_variables
        return []

    def tag_questions(cells_dict):
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
        question_groups = {}
        for key, cell in cells_dict.items():
            question = cell.get(
                "question"
            )  # Use .get() to avoid errors if key is missing
            if question not in question_groups:
                question_groups[question] = []
            question_groups[question].append(key)

        # Add 'is_first' and 'is_last' flags to all cells
        for question, keys in question_groups.items():
            test_number = 1
            for i, key in enumerate(keys):
                cells_dict[key]["is_first"] = i == 0
                cells_dict[key]["is_last"] = i == len(keys) - 1
                cells_dict[key]["test_number"] = test_number
                test_number += 1

        return cells_dict

    def question_dict(self):
        """
        Extracts all logical conditions from `assert` statements in Jupyter notebook cells
        that start with ''''# BEGIN TEST CONFIG'. Also extracts the first line containing `points:`
        and adds the points value to the dictionary.

        Returns:
            dict: A dictionary where keys are cell indices and values are dictionaries containing:
                - "assertions": A list of logical conditions extracted from assert statements.
                - "points": The points value extracted from the first `points:` line.
        """

        # Read the notebook file
        notebook_path = Path(self.notebook_path)
        if not notebook_path.exists():
            raise FileNotFoundError(f"The file {notebook_path} does not exist.")

        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        # Initialize the dictionary to store conditions and points
        results_dict = {}

        # Iterate through the cells in the notebook
        for cell_index, cell in enumerate(notebook.get("cells", [])):
            if cell.get("cell_type") == "raw":
                source = "".join(
                    cell.get("source", "")
                )  # Join the cell source as a string
                if source.strip().startswith("# BEGIN QUESTION"):
                    question_name = re.search(r"name:\s*(.*)", source)
                    question_name = (
                        question_name.group(1).strip() if question_name else None
                    )
            elif cell.get("cell_type") == "code":
                source = "".join(
                    cell.get("source", "")
                )  # Join the cell source as a string

                # Check if the cell starts with """ # BEGIN TEST CONFIG
                if source.strip().startswith('""" # BEGIN TEST CONFIG'):

                    logging_variables = FastAPINotebookBuilder.extract_log_variables(
                        cell
                    )

                    # Extract all assert statements (multiline enabled)
                    matches = re.findall(r"assert\s+(.+?)(?:\n|$)", source, re.DOTALL)

                    # Log matches for debugging
                    print("Matches:", matches)  # Debugging step, remove in production

                    # Process assertions
                    cleaned_matches = []
                    for match in matches:
                        # Clean and preserve formatting
                        cleaned_condition = " ".join(match.splitlines()).strip()
                        cleaned_matches.append(cleaned_condition)

                    # Extract the first line containing `points:`
                    points_line = next(
                        (line for line in source.split("\n") if "points:" in line), None
                    )
                    points_value = None
                    if points_line:
                        try:
                            points_value = float(points_line.split(":")[-1].strip())
                        except ValueError:
                            points_value = None  # Handle cases where the points value is not a valid number

                    # Add assertions and points to the dictionary
                    results_dict[cell_index] = {
                        "assertions": cleaned_matches,
                        "question": question_name,
                        "points": points_value,
                        "logging_variables": logging_variables,
                    }

                    results_dict = FastAPINotebookBuilder.tag_questions(results_dict)

        return results_dict
