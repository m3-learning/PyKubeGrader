import ast
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import nbformat


@dataclass
class FastAPINotebookBuilder:
    notebook_path: str
    temp_notebook: Optional[str] = None
    assignment_tag: Optional[str] = ""
    require_key: Optional[bool] = False

    def __post_init__(self):
        self.root_path, self.filename = FastAPINotebookBuilder.get_filename_and_root(
            self.notebook_path
        )
        self.total_points = 0
        self.run()

    def run(self):
        # here for easy debugging
        if self.temp_notebook is not None:
            shutil.copy(
                self.notebook_path, self.notebook_path.replace(".ipynb", "_temp.ipynb")
            )
            self.temp_notebook = self.notebook_path.replace(".ipynb", "_temp.ipynb")
        else:
            self.temp_notebook = self.notebook_path

        self.assertion_tests_dict = self.question_dict()
        self.add_api_code()

    def add_api_code(self):
        self.compute_max_points_free_response()

        for i, (cell_index, cell_dict) in enumerate(self.assertion_tests_dict.items()):
            print(
                f"Processing cell {cell_index + 1}, {i} of {len(self.assertion_tests_dict)}"
            )

            cell = self.get_cell(cell_index)
            cell_source = FastAPINotebookBuilder.add_import_statements_to_tests(
                cell["source"]
            )

            last_import_line_ind = FastAPINotebookBuilder.find_last_import_line(
                cell_source
            )

            # header, body = FastAPINotebookBuilder.split_list_at_marker(cell_source)

            updated_cell_source = []
            updated_cell_source.extend(cell_source[: last_import_line_ind + 1])
            if cell_dict["is_first"]:
                updated_cell_source.extend(
                    self.construct_first_cell_question_header(cell_dict)
                )
            updated_cell_source.extend(["\n"])
            updated_cell_source.extend(
                FastAPINotebookBuilder.construct_question_info(cell_dict)
            )

            updated_cell_source.extend(cell_source[last_import_line_ind + 1 :])
            updated_cell_source.extend(["\n"])

            updated_cell_source.extend(
                FastAPINotebookBuilder.construct_graders(cell_dict)
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
                FastAPINotebookBuilder.construct_update_responses(cell_dict)
            )

            self.replace_cell_source(cell_index, updated_cell_source)

    def compute_max_points_free_response(self):
        for cell_dict in self.assertion_tests_dict.values():
            # gets the question name from the first cell to not double count
            if cell_dict["is_first"]:
                # get the max points for the question
                max_question_points = sum(
                    cell["points"]
                    for cell in self.assertion_tests_dict.values()
                    if cell["question"] == cell_dict["question"]
                )

                self.total_points += max_question_points

    def construct_first_cell_question_header(self, cell_dict):
        max_question_points = sum(
            cell["points"]
            for cell in self.assertion_tests_dict.values()
            if cell["question"] == cell_dict["question"]
        )

        first_cell_header = [f"max_question_points = str({max_question_points})\n"]
        first_cell_header.append("earned_points = 0 \n")
        first_cell_header.append("os.environ['EARNED_POINTS'] = str(earned_points)\n")
        first_cell_header.append(
            f"os.environ['TOTAL_POINTS_FREE_RESPONSE'] = str({self.total_points})\n"
        )

        if self.require_key:
            first_cell_header.append(
                "from pykubegrader.tokens.validate_token import validate_token\nvalidate_token()\n"
            )

        short_filename = self.filename.split(".")[0].replace("_temp", "")
        first_cell_header.extend(
            [
                f'log_variable("total-points",f"{self.assignment_tag}, {short_filename}", {self.total_points})\n'
            ]
        )

        return first_cell_header

    @staticmethod
    def construct_update_responses(cell_dict):
        update_responses = []

        logging_variables = cell_dict["logging_variables"]

        for logging_variable in logging_variables:
            update_responses.append(
                f"responses = update_responses(question_id, str({logging_variable}))\n"
            )

        return update_responses

    @staticmethod
    def split_list_at_marker(input_list, marker="""# END TEST CONFIG"""):
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
    def construct_graders(cell_dict):
        # Generate Python code
        added_code = [
            "if "
            + " and ".join(f"({test})" for test in cell_dict["assertions"])
            + ":\n"
        ]
        added_code.append(f"    score = {cell_dict['points']}\n")

        return added_code

    @staticmethod
    def construct_question_info(cell_dict):
        question_info = []

        question_id = cell_dict["question"] + "-" + str(cell_dict["test_number"])

        question_info.append(f'question_id = "{question_id}"' + "\n")
        question_info.append(f"max_score = {cell_dict['points']}\n")
        question_info.append("score = 0\n")

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
            "from pykubegrader.telemetry import (\n",
            "    ensure_responses,\n",
            "    log_variable,\n",
            "    score_question,\n",
            "    submit_question,\n",
            "    telemetry,\n",
            "    update_responses,\n",
            ")\n",
            "import os\n",
        ]

        for i, line in enumerate(cell_source):
            if end_test_config_line in line:
                # Insert the imports immediately after the current line
                cell_source[i + 1 : i + 1] = [
                    "\n"
                ] + imports  # Add a blank line for readability
                return cell_source  # Exit the loop once the imports are inserted

    def extract_first_cell(self):
        with open(self.temp_notebook, "r", encoding="utf-8") as f:
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
        with open(self.temp_notebook, "r", encoding="utf-8") as f:
            notebook = json.load(f)
        if "cells" in notebook and len(notebook["cells"]) > cell_index:
            return notebook["cells"][cell_index]
        else:
            return None

    def replace_cell_source(self, cell_index, new_source):
        """
        Replace the source code of a specific Jupyter notebook cell.

        Args:
            cell_index (int): Index of the cell to be modified (0-based).
            new_source (str): New source code to replace the cell's content.
        """
        # Load the notebook
        with open(self.temp_notebook, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Check if the cell index is valid
        if cell_index >= len(notebook.cells) or cell_index < 0:
            raise IndexError(
                f"Cell index {cell_index} is out of range for this notebook."
            )

        # Replace the source code of the specified cell
        notebook.cells[cell_index]["source"] = new_source

        # Save the notebook
        with open(self.temp_notebook, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        print(f"Updated notebook saved to {self.temp_notebook}")

    @staticmethod
    def find_last_import_line(cell_source):
        """
        Finds the index of the last line with an import statement in a list of code lines,
        including multiline import statements.

        Args:
            cell_source (list): List of strings representing the code lines.

        Returns:
            int: The index of the last line with an import statement, or -1 if no import is found.
        """
        last_import_index = -1
        is_multiline_import = False  # Flag to track if we're inside a multiline import

        for i, line in enumerate(cell_source):
            stripped_line = line.strip()

            if is_multiline_import:
                # Continue tracking multiline import
                if stripped_line.endswith("\\") or (
                    stripped_line and not stripped_line.endswith(")")
                ):
                    last_import_index = i  # Update to current line
                    continue
                else:
                    is_multiline_import = False  # End of multiline import
                    last_import_index = i  # Update to current line

            # Check for single-line or start of multiline imports
            if stripped_line.startswith("import") or stripped_line.startswith("from"):
                last_import_index = i
                # Check if it's a multiline import
                if stripped_line.endswith("\\") or "(" in stripped_line:
                    is_multiline_import = True

        return last_import_index

    @staticmethod
    def extract_log_variables(cell):
        """Extracts log variables from the first cell."""
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
        for keys in question_groups.values():
            test_number = 1
            for i, key in enumerate(keys):
                cells_dict[key]["is_first"] = i == 0
                cells_dict[key]["is_last"] = i == len(keys) - 1
                cells_dict[key]["test_number"] = test_number
                test_number += 1

        return cells_dict

    def question_dict(self):
        notebook_path = Path(self.temp_notebook)
        if not notebook_path.exists():
            raise FileNotFoundError(f"The file {notebook_path} does not exist.")

        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        results_dict = {}

        for cell_index, cell in enumerate(notebook.get("cells", [])):
            if cell.get("cell_type") == "raw":
                source = "".join(cell.get("source", ""))
                if source.strip().startswith("# BEGIN QUESTION"):
                    question_name = re.search(r"name:\s*(.*)", source)
                    question_name = (
                        question_name.group(1).strip() if question_name else None
                    )

            elif cell.get("cell_type") == "code":
                source = "".join(cell.get("source", ""))

                if source.strip().startswith('""" # BEGIN TEST CONFIG'):
                    logging_variables = FastAPINotebookBuilder.extract_log_variables(
                        cell
                    )

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
                                full_assertion = full_assertion[
                                    : comment_match.start()
                                ].strip()

                            # Ensure proper parentheses closure
                            open_count = full_assertion.count("(")
                            close_count = full_assertion.count(")")
                            if open_count > close_count:
                                full_assertion += ")" * (open_count - close_count)

                            # Clean up the assertion
                            if full_assertion.startswith(
                                "("
                            ) and not full_assertion.endswith(")"):
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

                    # Add to results dictionary
                    results_dict[cell_index] = {
                        "assertions": assertions,
                        "comments": comments,
                        "question": question_name,
                        "points": points_value,
                        "logging_variables": logging_variables,
                    }

                    results_dict = FastAPINotebookBuilder.tag_questions(results_dict)

        return results_dict
