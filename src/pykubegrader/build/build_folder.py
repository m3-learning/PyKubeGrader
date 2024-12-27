import argparse
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
import nbformat
from .api_notebook_builder import FastAPINotebookBuilder


@dataclass
class NotebookProcessor:
    """
    A class for processing Jupyter notebooks in a directory and its subdirectories.

    Attributes:
        root_folder (str): The root directory containing notebooks to process.
        solutions_folder (str): The directory where processed notebooks and solutions are stored.
        verbose (bool): Flag for verbose output to the console.
        log (bool): Flag to enable or disable logging.
    """

    root_folder: str
    solutions_folder: str = field(init=False)
    verbose: bool = False
    log: bool = True

    def __post_init__(self):
        """
        Post-initialization method for setting up the `NotebookProcessor` instance.

        This method is automatically called after the instance is created. It performs the following tasks:
            1. Creates a solutions folder within the root directory to store processed outputs.
            2. Configures logging to capture detailed information about the processing.

        Raises:
            OSError: If the solutions folder cannot be created due to permissions or other filesystem issues.
        """
        # Define the folder to store solutions and ensure it exists
        self.solutions_folder = os.path.join(self.root_folder, "_solutions")
        os.makedirs(
            self.solutions_folder, exist_ok=True
        )  # Create the folder if it doesn't exist

        # Configure logging to store log messages in the solutions folder
        log_file_path = os.path.join(self.solutions_folder, "notebook_processor.log")
        logging.basicConfig(
            filename=log_file_path,  # Path to the log file
            level=logging.INFO,  # Log messages at INFO level and above will be recorded
            format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format: timestamp, level, and message
        )

        # Initialize a global logger for the class
        global logger
        logger = logging.getLogger(
            __name__
        )  # Create a logger instance specific to this module
        self.logger = logger  # Assign the logger instance to the class for use in instance methods

    def process_notebooks(self):
        """
        Recursively processes Jupyter notebooks in a given folder and its subfolders.

        The function performs the following steps:
        1. Iterates through all files within the root folder and subfolders.
        2. Identifies Jupyter notebooks by checking file extensions (.ipynb).
        3. Checks if each notebook contains assignment configuration metadata.
        4. Processes notebooks that meet the criteria using `otter assign` or other defined steps.

        Prerequisites:
            - The `has_assignment` method should be implemented to check if a notebook
            contains the required configuration for assignment processing.
            - The `_process_single_notebook` method should handle the specific processing
            of a single notebook, including moving it to a new folder or running
            additional tools like `otter assign`.

        Raises:
            - OSError: If an issue occurs while accessing files or directories.

        Example:
            class NotebookProcessor:
                def __init__(self, root_folder):
                    self.root_folder = root_folder

                def has_assignment(self, notebook_path):
                    # Implementation to check for assignment configuration
                    return True  # Replace with actual check logic

                def _process_single_notebook(self, notebook_path):
                    # Implementation to process a single notebook
                    self._print_and_log(f"Processing notebook: {notebook_path}")

            processor = NotebookProcessor("/path/to/root/folder")
            processor.process_notebooks()
        """
        ipynb_files = []

        # Walk through the root folder and its subfolders
        for dirpath, _, filenames in os.walk(self.root_folder):
            for filename in filenames:
                # Check if the file is a Jupyter notebook
                if filename.endswith(".ipynb"):
                    notebook_path = os.path.join(dirpath, filename)
                    ipynb_files.append(notebook_path)

        for notebook_path in ipynb_files:
            # Check if the notebook has the required assignment configuration
            if self.has_assignment(notebook_path):
                self._print_and_log(f"notebook_path = {notebook_path}")

                # Process the notebook if it meets the criteria
                self._process_single_notebook(notebook_path)

    def _print_and_log(self, message):
        """
        Logs a message and optionally prints it to the console.

        This method is used for logging important information and optionally
        displaying it in the console based on the `verbose` and `log` attributes.

        Args:
            message (str): The message to be logged and/or printed.

        Behavior:
            - If `self.verbose` is True, the message will be printed to the console.
            - If `self.log` is True, the message will be logged using the class's logger.

        Example:
            self._print_and_log("Processing completed successfully.")

        Raises:
            None: This method handles exceptions internally, if any arise from logging or printing.
        """

        # Print the message to the console if verbosity is enabled
        if self.verbose:
            print(message)

        # Log the message if logging is enabled
        if self.log:
            self.logger.info(message)

    def _process_single_notebook(self, notebook_path):
        """
        Processes a single Jupyter notebook.

        This method handles the preparation, validation, and processing of a given notebook. It:
        1. Moves the notebook to a subfolder within the solutions folder.
        2. Creates temporary and destination folders for autograder and student files.
        3. Identifies and processes multiple-choice questions (MCQs).
        4. Runs assignment-specific tasks like executing `otter assign` and cleaning notebooks.
        5. Generates solution and question files and moves them to appropriate folders.

        Args:
            notebook_path (str): The file path to the Jupyter notebook to be processed.

        Raises:
            FileNotFoundError: If the notebook file or intermediate files are not found.
            OSError: If there are issues creating or moving files/directories.
            Exception: For unexpected errors during processing.

        Returns:
            None
        """

        print(f"Processing notebook: {notebook_path}")

        logging.info(f"Processing notebook: {notebook_path}")
        notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
        notebook_subfolder = os.path.join(self.solutions_folder, notebook_name)
        os.makedirs(notebook_subfolder, exist_ok=True)

        new_notebook_path = os.path.join(
            notebook_subfolder, os.path.basename(notebook_path)
        )

        # makes a temp copy of the notebook
        temp_notebook_path = os.path.join(
            notebook_subfolder, f"{notebook_name}_temp.ipynb"
        )
        shutil.copy(notebook_path, temp_notebook_path)

        # Determine the path to the autograder folder
        autograder_path = os.path.join(notebook_subfolder, "dist/autograder/")
        os.makedirs(autograder_path, exist_ok=True)

        # Determine the path to the student folder
        student_path = os.path.join(notebook_subfolder, "dist/student/")
        os.makedirs(student_path, exist_ok=True)

        if os.path.abspath(notebook_path) != os.path.abspath(new_notebook_path):
            shutil.move(notebook_path, new_notebook_path)
            self._print_and_log(f"Moved: {notebook_path} -> {new_notebook_path}")
        else:
            self._print_and_log(f"Notebook already in destination: {new_notebook_path}")

        solution_path_1, question_path = self.multiple_choice_parser(
            temp_notebook_path, new_notebook_path
        )
        solution_path_2, question_path = self.true_false_parser(
            temp_notebook_path, new_notebook_path
        )
        solution_path_3, question_path = self.select_many_parser(
            temp_notebook_path, new_notebook_path
        )

        if any([solution_path_1, solution_path_2, solution_path_3]) is not None:
            solution_path = solution_path_1 or solution_path_2 or solution_path_3

        student_notebook = self.free_response_parser(
            temp_notebook_path, notebook_subfolder, notebook_name
        )

        # If Otter does not run, move the student file to the main directory
        if student_notebook is None:
            path_ = shutil.copy(temp_notebook_path, self.root_folder)
            self._print_and_log(
                f"Copied and cleaned student notebook: {path_} -> {self.root_folder}"
            )

        # Move the solution file to the autograder folder
        if solution_path is not None:
            # gets importable file name
            importable_file_name = sanitize_string(
                os.path.splitext(os.path.basename(solution_path))[0]
            )

            # Move the solution file to the autograder folder
            os.rename(
                solution_path,
                os.path.join(autograder_path, f"{importable_file_name}.py"),
            )

        if question_path is not None:
            shutil.move(question_path, student_path)

        # Remove the temp copy of the notebook
        os.remove(temp_notebook_path)

        # Remove all postfix from filenames in dist
        NotebookProcessor.remove_postfix(autograder_path, "_solutions")
        NotebookProcessor.remove_postfix(student_path, "_questions")
        NotebookProcessor.remove_postfix(self.root_folder, "_temp")

        ### CODE TO ENSURE THAT STUDENT NOTEBOOK IS IMPORTABLE
        if question_path is not None:
            # question_root_path = os.path.dirname(question_path)
            question_file_name = os.path.basename(question_path)
            question_file_name_sanitized = sanitize_string(
                question_file_name.replace("_questions", "")
            )
            if question_file_name_sanitized.endswith("_py"):
                question_file_name_sanitized = question_file_name_sanitized[:-3] + ".py"

            # Rename the file
            os.rename(
                os.path.join(
                    student_path, question_file_name.replace("_questions", "")
                ),
                os.path.join(student_path, question_file_name_sanitized),
            )

            # Ensure the "questions" folder exists
            questions_folder_jbook = os.path.join(self.root_folder, "questions")
            os.makedirs(questions_folder_jbook, exist_ok=True)

            # Copy the renamed file to the "questions" folder
            shutil.copy(
                os.path.join(student_path, question_file_name_sanitized),
                os.path.join(questions_folder_jbook, question_file_name_sanitized),
            )

    def free_response_parser(
        self, temp_notebook_path, notebook_subfolder, notebook_name
    ):
        if self.has_assignment(temp_notebook_path, "# ASSIGNMENT CONFIG"):
            # TODO: This is hardcoded for now, but should be in a configuration file.
            client_private_key = os.path.join(
                notebook_subfolder,
                ".client_private_key.bin",
            )
            server_public_key = os.path.join(
                notebook_subfolder,
                ".server_public_key.bin",
            )

            shutil.copy("./keys/.client_private_key.bin", client_private_key)
            shutil.copy("./keys/.server_public_key.bin", server_public_key)

            FastAPINotebookBuilder(notebook_path=temp_notebook_path)

            debug_notebook = os.path.join(
                notebook_subfolder,
                "dist",
                "autograder",
                os.path.basename(temp_notebook_path).replace("_temp", "_debugger"),
            )

            self.run_otter_assign(
                temp_notebook_path, os.path.join(notebook_subfolder, "dist")
            )

            print(f"Copying {temp_notebook_path} to {debug_notebook}")

            shutil.copy(temp_notebook_path, debug_notebook)

            NotebookProcessor.remove_assignment_config_cells(debug_notebook)

            student_notebook = os.path.join(
                notebook_subfolder, "dist", "student", f"{notebook_name}.ipynb"
            )

            NotebookProcessor.add_initialization_code(student_notebook)

            self.clean_notebook(student_notebook)

            NotebookProcessor.replace_temp_in_notebook(
                student_notebook, student_notebook
            )
            autograder_notebook = os.path.join(
                notebook_subfolder, "dist", "autograder", f"{notebook_name}.ipynb"
            )
            NotebookProcessor.replace_temp_in_notebook(
                autograder_notebook, autograder_notebook
            )
            shutil.copy(student_notebook, self.root_folder)
            self._print_and_log(
                f"Copied and cleaned student notebook: {student_notebook} -> {self.root_folder}"
            )

            # Remove the keys
            os.remove(client_private_key)
            os.remove(server_public_key)

            return student_notebook
        else:
            NotebookProcessor.add_initialization_code(temp_notebook_path)
            return None

    @staticmethod
    def remove_assignment_config_cells(notebook_path):
        # Read the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=nbformat.NO_CONVERT)

        # Filter out cells containing "# ASSIGNMENT CONFIG"
        notebook.cells = [
            cell
            for cell in notebook.cells
            if "# ASSIGNMENT CONFIG" not in cell.get("source", "")
        ]

        # Save the updated notebook
        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)

    @staticmethod
    def add_initialization_code(notebook_path):
        # finds the first code cell
        index, cell = find_first_code_cell(notebook_path)
        cell = cell["source"]
        import_text = "from pykubegrader.initialize import initialize_assignment\n"
        cell = f"{import_text}\n" + cell
        cell += f'\nresponses = initialize_assignment("{os.path.splitext(os.path.basename(notebook_path))[0]}")\n'
        replace_cell_source(notebook_path, index, cell)

    def multiple_choice_parser(self, temp_notebook_path, new_notebook_path):
        ### Parse the notebook for multiple choice questions
        if self.has_assignment(temp_notebook_path, "# BEGIN MULTIPLE CHOICE"):
            self._print_and_log(
                f"Notebook {temp_notebook_path} has multiple choice questions"
            )

            # Extract all the multiple choice questions
            data = extract_MCQ(temp_notebook_path)

            # determine the output file path
            solution_path = f"{os.path.splitext(new_notebook_path)[0]}_solutions.py"

            # Extract the first value cells
            value = extract_raw_cells(temp_notebook_path)

            data = NotebookProcessor.merge_metadata(value, data)

            for data_ in data:
                # Generate the solution file
                self.generate_solution_MCQ(data, output_file=solution_path)

                question_path = (
                    f"{new_notebook_path.replace(".ipynb", "")}_questions.py"
                )

            generate_mcq_file(data, output_file=question_path)

            markers = ("# BEGIN MULTIPLE CHOICE", "# END MULTIPLE CHOICE")

            replace_cells_between_markers(
                data, markers, temp_notebook_path, temp_notebook_path
            )

            return solution_path, question_path
        else:
            return None, None

    def true_false_parser(self, temp_notebook_path, new_notebook_path):
        ### Parse the notebook for TF questions
        if self.has_assignment(temp_notebook_path, "# BEGIN TF"):
            markers = ("# BEGIN TF", "# END TF")

            self._print_and_log(
                f"Notebook {temp_notebook_path} has True False questions"
            )

            # Extract all the multiple choice questions
            data = extract_TF(temp_notebook_path)

            # determine the output file path
            solution_path = f"{os.path.splitext(new_notebook_path)[0]}_solutions.py"

            # Extract the first value cells
            value = extract_raw_cells(temp_notebook_path, markers[0])

            data = NotebookProcessor.merge_metadata(value, data)

            # for data_ in data:
            # Generate the solution file
            self.generate_solution_MCQ(data, output_file=solution_path)

            question_path = f"{new_notebook_path.replace(".ipynb", "")}_questions.py"

            generate_tf_file(data, output_file=question_path)

            replace_cells_between_markers(
                data, markers, temp_notebook_path, temp_notebook_path
            )

            return solution_path, question_path
        else:
            return None, None

    def select_many_parser(self, temp_notebook_path, new_notebook_path):
        ### Parse the notebook for select_many questions
        if self.has_assignment(temp_notebook_path, "# BEGIN SELECT MANY"):
            markers = ("# BEGIN SELECT MANY", "# END SELECT MANY")

            self._print_and_log(
                f"Notebook {temp_notebook_path} has True False questions"
            )

            # Extract all the multiple choice questions
            data = extract_SELECT_MANY(temp_notebook_path)

            # determine the output file path
            solution_path = f"{os.path.splitext(new_notebook_path)[0]}_solutions.py"

            # Extract the first value cells
            value = extract_raw_cells(temp_notebook_path, markers[0])

            data = NotebookProcessor.merge_metadata(value, data)

            # for data_ in data:
            # Generate the solution file
            self.generate_solution_MCQ(data, output_file=solution_path)

            question_path = f"{new_notebook_path.replace(".ipynb", "")}_questions.py"

            generate_select_many_file(data, output_file=question_path)

            replace_cells_between_markers(
                data, markers, temp_notebook_path, temp_notebook_path
            )

            return solution_path, question_path
        else:
            return None, None

    @staticmethod
    def replace_temp_in_notebook(input_file, output_file):
        """
        Replaces occurrences of '_temp.ipynb' with '.ipynb' in a Jupyter Notebook.

        Parameters:
        input_file (str): Path to the input Jupyter Notebook file.
        output_file (str): Path to the output Jupyter Notebook file.

        Returns:
        None: Writes the modified notebook to the output file.
        """
        # Load the notebook data
        with open(input_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        # Iterate through each cell and update its content
        for cell in notebook_data.get("cells", []):
            if "source" in cell:
                # Replace occurrences of '_temp.ipynb' in the cell source
                cell["source"] = [
                    line.replace("_temp.ipynb", ".ipynb") for line in cell["source"]
                ]

        # Write the updated notebook to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(notebook_data, f, indent=2)

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
        # merged_data = []

        # Loop through each question set in the data
        for i, _data in enumerate(data):
            # Handle 'points' from raw metadata: convert single string value to a list if necessary
            if isinstance(raw[i]["points"], str):
                points_ = [float(raw[i]["points"])] * len(
                    _data
                )  # Distribute the same point value
            else:
                points_ = raw[i]["points"]  # Use provided list of points

            # Remove 'points' from raw metadata to avoid overwriting
            raw[i].pop("points", None)

            # Handle 'grade' from raw metadata
            if "grade" in raw[i]:
                grade_ = [raw[i]["grade"]]

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
    def has_assignment(notebook_path, *tags):
        """
        Determines if a Jupyter notebook contains any of the specified configuration tags.

        This method checks for the presence of specific content in a Jupyter notebook
        to identify whether it includes any of the required headings or tags.

        Args:
            notebook_path (str): The file path to the Jupyter notebook to be checked.
            *tags (str): Variable-length argument list of tags to search for.
                        Defaults to ("# ASSIGNMENT CONFIG",).

        Returns:
            bool: True if the notebook contains any of the specified tags, False otherwise.

        Dependencies:
            - The `check_for_heading` function must be implemented. It should search
            for specific headings or content in a notebook file and return a boolean
            value indicating if any of the tags exist.

        Example:
            def check_for_heading(notebook_path, keywords):
                # Mock implementation of content check
                with open(notebook_path, 'r') as file:
                    content = file.read()
                return any(keyword in content for keyword in keywords)

            notebook_path = "path/to/notebook.ipynb"
            # Check for default tags
            contains_config = has_assignment(notebook_path)
            self._print_and_log(f"Contains assignment config: {contains_config}")

            # Check for custom tags
            contains_custom = has_assignment(notebook_path, "# CUSTOM CONFIG", "# ANOTHER CONFIG")
            self._print_and_log(f"Contains custom config: {contains_custom}")
        """
        # Default tags if none are provided
        if not tags:
            tags = ["# ASSIGNMENT CONFIG", "# BEGIN MULTIPLE CHOICE"]

        # Use the helper function to check for the presence of any specified tag
        return check_for_heading(notebook_path, tags)

    @staticmethod
    def run_otter_assign(notebook_path, dist_folder):
        """
        Runs `otter assign` on the given notebook and outputs to the specified distribution folder.
        """
        try:
            os.makedirs(dist_folder, exist_ok=True)
            command = ["otter", "assign", notebook_path, dist_folder]
            subprocess.run(command, check=True)
            logger.info(f"Otter assign completed: {notebook_path} -> {dist_folder}")

            # Remove all postfix _test from filenames in dist_folder
            NotebookProcessor.remove_postfix(dist_folder)

        except subprocess.CalledProcessError as e:
            logger.info(f"Error running `otter assign` for {notebook_path}: {e}")
        except Exception as e:
            logger.info(
                f"Unexpected error during `otter assign` for {notebook_path}: {e}"
            )

    @staticmethod
    def generate_solution_MCQ(data_list, output_file="output.py"):
        """
        Generates a Python file with solutions and total points based on the input data.
        If the file already exists, it appends new solutions to the existing solution dictionary.

        Args:
            data_list (list): A list of dictionaries containing question metadata.
            output_file (str): Path to the output Python file.
        """

        solutions = {}
        total_points = []

        # If the output file exists, load the existing solutions and total_points
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

        # Process new question data and update solutions and total_points
        for question_set in data_list:
            for key, question_data in question_set.items():
                solution_key = f"q{question_data['question number']}-{question_data['subquestion_number']}-{key}"
                solutions[solution_key] = question_data["solution"]
                total_points.extend([question_data["points"]])

        # Write updated total_points and solutions back to the file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("from typing import Any\n\n")
            f.write(f"total_points: float = {total_points}\n\n")

            f.write("solutions: dict[str, Any] = {\n")
            for key, solution in solutions.items():
                # For safety, we assume solutions are strings, but if not, repr would be safer
                f.write(f'    "{key}": {repr(solution)},\n')
            f.write("}\n")

    def extract_MCQ(ipynb_file):
        """
        Extracts questions from markdown cells and organizes them as a nested dictionary,
        including subquestion numbers.

        Args:
            ipynb_file (str): Path to the .ipynb file.

        Returns:
            dict: A nested dictionary where the first-level key is the question name (text after ##),
                and the value is a dictionary with keys: 'name', 'subquestion_number',
                'question_text', 'OPTIONS', and 'solution'.
        """
        try:
            # Load the notebook file
            with open(ipynb_file, "r", encoding="utf-8") as f:
                notebook_data = json.load(f)

            cells = notebook_data.get("cells", [])
            results = {}
            within_section = False
            subquestion_number = 0  # Counter for subquestions

            for cell in cells:
                if cell.get("cell_type") == "raw":
                    # Check for the start and end labels in raw cells
                    raw_content = "".join(cell.get("source", []))
                    if "# BEGIN MULTIPLE CHOICE" in raw_content:
                        within_section = True
                        subquestion_number = (
                            0  # Reset counter at the start of a new section
                        )
                        continue
                    elif "# END MULTIPLE CHOICE" in raw_content:
                        within_section = False
                        continue

                if within_section and cell.get("cell_type") == "markdown":
                    # Parse markdown cell content
                    markdown_content = "".join(cell.get("source", []))

                    # Extract title (## heading)
                    title_match = re.search(
                        r"^##\s*(.+)", markdown_content, re.MULTILINE
                    )
                    title = title_match.group(1).strip() if title_match else None

                    if title:
                        subquestion_number += (
                            1  # Increment the subquestion number for each question
                        )

                        # Extract question text (### heading)
                        question_text_match = re.search(
                            r"^###\s*\*\*(.+)\*\*", markdown_content, re.MULTILINE
                        )
                        question_text = (
                            question_text_match.group(1).strip()
                            if question_text_match
                            else None
                        )

                        # Extract OPTIONS (lines after #### options)
                        options_match = re.search(
                            r"####\s*options\s*(.+?)(?=####|$)",
                            markdown_content,
                            re.DOTALL | re.IGNORECASE,
                        )
                        options = (
                            [
                                line.strip()
                                for line in options_match.group(1).strip().splitlines()
                                if line.strip()
                            ]
                            if options_match
                            else []
                        )

                        # Extract solution (line after #### SOLUTION)
                        solution_match = re.search(
                            r"####\s*SOLUTION\s*(.+)", markdown_content, re.IGNORECASE
                        )
                        solution = (
                            solution_match.group(1).strip() if solution_match else None
                        )

                        # Create nested dictionary for the question
                        results[title] = {
                            "name": title,
                            "subquestion_number": subquestion_number,
                            "question_text": question_text,
                            "OPTIONS": options,
                            "solution": solution,
                        }

            return results

        except FileNotFoundError:
            print(f"File {ipynb_file} not found.")
            return {}
        except json.JSONDecodeError:
            print("Invalid JSON in notebook file.")
            return {}

    @staticmethod
    def remove_postfix(dist_folder, suffix="_temp"):
        logging.info(f"Removing postfix '{suffix}' from filenames in {dist_folder}")
        for root, _, files in os.walk(dist_folder):
            for file in files:
                if suffix in file:
                    old_file_path = os.path.join(root, file)
                    new_file_path = os.path.join(root, file.replace(suffix, ""))
                    os.rename(old_file_path, new_file_path)
                    logging.info(f"Renamed: {old_file_path} -> {new_file_path}")

    @staticmethod
    def clean_notebook(notebook_path):
        """
        Cleans a Jupyter notebook to remove unwanted cells and set cell metadata.
        """
        clean_notebook(notebook_path)


def extract_raw_cells(ipynb_file, heading="# BEGIN MULTIPLE CHOICE"):
    """
    Extracts all metadata from value cells in a Jupyter Notebook file for a specified heading.

    Args:
        ipynb_file (str): Path to the .ipynb file.
        heading (str): The heading to search for in value cells.

    Returns:
        list of dict: A list of dictionaries containing extracted metadata for each heading occurrence.
    """
    try:
        with open(ipynb_file, "r", encoding="utf-8") as f:
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
            metadata_list.extend(_extract_metadata_from_heading(raw_cell, heading))

        return metadata_list

    except FileNotFoundError:
        print(f"File {ipynb_file} not found.")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in notebook file.")
        return []


def _extract_metadata_from_heading(raw_cell, heading="# BEGIN MULTIPLE CHOICE"):
    """
    Extracts metadata for a single value cell string each time the heading is found.

    Args:
        raw_cell (str): String containing value cell content.
        heading (str): The heading to identify sections.

    Returns:
        list of dict: A list of dictionaries containing extracted key-value pairs.
    """
    metadata_list = []
    lines = raw_cell.split("\n")
    current_metadata = None

    for line in lines:
        if line.startswith(heading):
            if current_metadata:
                metadata_list.append(current_metadata)  # Save previous metadata
            current_metadata = {}  # Start new metadata block
        elif line.startswith("##") and current_metadata is not None:
            # Extract key and value from lines
            key, value = line[3:].split(":", 1)
            current_metadata[key.strip()] = value.strip()

    if current_metadata:  # Append the last metadata block
        metadata_list.append(current_metadata)

    return metadata_list


def extract_SELECT_MANY(ipynb_file):
    """
    Extracts questions marked by `# BEGIN SELECT MANY` and `# END SELECT MANY` in markdown cells,
    including all lines under the SOLUTION header until the first blank line or whitespace-only line.

    Args:
        ipynb_file (str): Path to the .ipynb file.

    Returns:
        list: A list of dictionaries, where each dictionary corresponds to questions within
              a section. Each dictionary contains parsed questions with details like
              'name', 'subquestion_number', 'question_text', and 'solution'.
    """
    try:
        # Load the notebook file
        with open(ipynb_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        cells = notebook_data.get("cells", [])
        sections = []  # List to store results for each section
        current_section = {}  # Current section being processed
        within_section = False
        subquestion_number = 0  # Counter for subquestions

        for cell in cells:
            if cell.get("cell_type") == "raw":
                # Check for the start and end labels in raw cells
                raw_content = "".join(cell.get("source", []))
                if "# BEGIN SELECT MANY" in raw_content:
                    within_section = True
                    subquestion_number = (
                        0  # Reset counter at the start of a new section
                    )
                    current_section = {}  # Prepare a new section dictionary
                    continue
                elif "# END SELECT MANY" in raw_content:
                    within_section = False
                    if current_section:
                        sections.append(current_section)  # Save the current section
                    continue

            if within_section and cell.get("cell_type") == "markdown":
                # Parse markdown cell content
                markdown_content = "".join(cell.get("source", []))

                # Extract title (## heading)
                title_match = re.search(r"^##\s*(.+)", markdown_content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else None

                if title:
                    subquestion_number += (
                        1  # Increment subquestion number for each question
                    )

                    # Extract question text (### heading)
                    question_text_match = re.search(
                        r"^###\s*\*\*(.+)\*\*", markdown_content, re.MULTILINE
                    )
                    question_text = (
                        question_text_match.group(1).strip()
                        if question_text_match
                        else None
                    )

                    # Extract OPTIONS (lines after #### options)
                    options_match = re.search(
                        r"####\s*options\s*(.+?)(?=####|$)",
                        markdown_content,
                        re.DOTALL | re.IGNORECASE,
                    )
                    options = (
                        [
                            line.strip()
                            for line in options_match.group(1).strip().splitlines()
                            if line.strip()
                        ]
                        if options_match
                        else []
                    )

                    # Extract all lines under the SOLUTION header
                    solution_start = markdown_content.find("#### SOLUTION")
                    if solution_start != -1:
                        solution = []
                        lines = markdown_content[solution_start:].splitlines()
                        for line in lines[1:]:  # Skip the "#### SOLUTION" line
                            if line.strip():  # Non-blank line after trimming spaces
                                solution.append(line.strip())
                            else:
                                break

                    # Add question details to the current section
                    current_section[title] = {
                        "name": title,
                        "subquestion_number": subquestion_number,
                        "question_text": question_text,
                        "solution": solution,
                        "OPTIONS": options,
                    }

        return sections

    except FileNotFoundError:
        print(f"File {ipynb_file} not found.")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in notebook file.")
        return []


def extract_TF(ipynb_file):
    """
    Extracts True False questions from markdown cells within sections marked by
    `# BEGIN TF` and `# END TF`.

    Args:
        ipynb_file (str): Path to the .ipynb file.

    Returns:
        list: A list of dictionaries, where each dictionary corresponds to questions within
              a section. Each dictionary contains parsed questions with details like
              'name', 'subquestion_number', 'question_text', and 'solution'.
    """
    try:
        # Load the notebook file
        with open(ipynb_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        cells = notebook_data.get("cells", [])
        sections = []  # List to store results for each section
        current_section = {}  # Current section being processed
        within_section = False
        subquestion_number = 0  # Counter for subquestions

        for cell in cells:
            if cell.get("cell_type") == "raw":
                # Check for the start and end labels in raw cells
                raw_content = "".join(cell.get("source", []))
                if "# BEGIN TF" in raw_content:
                    within_section = True
                    subquestion_number = (
                        0  # Reset counter at the start of a new section
                    )
                    current_section = {}  # Prepare a new section dictionary
                    continue
                elif "# END TF" in raw_content:
                    within_section = False
                    if current_section:
                        sections.append(current_section)  # Save the current section
                    continue

            if within_section and cell.get("cell_type") == "markdown":
                # Parse markdown cell content
                markdown_content = "".join(cell.get("source", []))

                # Extract title (## heading)
                title_match = re.search(r"^##\s*(.+)", markdown_content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else None

                if title:
                    subquestion_number += (
                        1  # Increment subquestion number for each question
                    )

                    # Extract question text (### heading)
                    question_text_match = re.search(
                        r"^###\s*\*\*(.+)\*\*", markdown_content, re.MULTILINE
                    )
                    question_text = (
                        question_text_match.group(1).strip()
                        if question_text_match
                        else None
                    )

                    # Extract solution (line after #### SOLUTION)
                    solution_match = re.search(
                        r"####\s*SOLUTION\s*(.+)", markdown_content, re.IGNORECASE
                    )
                    solution = (
                        solution_match.group(1).strip() if solution_match else None
                    )

                    # Add question details to the current section
                    current_section[title] = {
                        "name": title,
                        "subquestion_number": subquestion_number,
                        "question_text": question_text,
                        "solution": solution,
                    }

        return sections

    except FileNotFoundError:
        print(f"File {ipynb_file} not found.")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in notebook file.")
        return []


def extract_MCQ(ipynb_file):
    """
    Extracts multiple-choice questions from markdown cells within sections marked by
    `# BEGIN MULTIPLE CHOICE` and `# END MULTIPLE CHOICE`.

    Args:
        ipynb_file (str): Path to the .ipynb file.

    Returns:
        list: A list of dictionaries, where each dictionary corresponds to questions within
              a section. Each dictionary contains parsed questions with details like
              'name', 'subquestion_number', 'question_text', 'OPTIONS', and 'solution'.
    """
    try:
        # Load the notebook file
        with open(ipynb_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        cells = notebook_data.get("cells", [])
        sections = []  # List to store results for each section
        current_section = {}  # Current section being processed
        within_section = False
        subquestion_number = 0  # Counter for subquestions

        for cell in cells:
            if cell.get("cell_type") == "raw":
                # Check for the start and end labels in raw cells
                raw_content = "".join(cell.get("source", []))
                if "# BEGIN MULTIPLE CHOICE" in raw_content:
                    within_section = True
                    subquestion_number = (
                        0  # Reset counter at the start of a new section
                    )
                    current_section = {}  # Prepare a new section dictionary
                    continue
                elif "# END MULTIPLE CHOICE" in raw_content:
                    within_section = False
                    if current_section:
                        sections.append(current_section)  # Save the current section
                    continue

            if within_section and cell.get("cell_type") == "markdown":
                # Parse markdown cell content
                markdown_content = "".join(cell.get("source", []))

                # Extract title (## heading)
                title_match = re.search(r"^##\s*(.+)", markdown_content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else None

                if title:
                    subquestion_number += (
                        1  # Increment subquestion number for each question
                    )

                    # Extract question text (### heading)
                    question_text_match = re.search(
                        r"^###\s*\*\*(.+)\*\*", markdown_content, re.MULTILINE
                    )
                    question_text = (
                        question_text_match.group(1).strip()
                        if question_text_match
                        else None
                    )

                    # Extract OPTIONS (lines after #### options)
                    options_match = re.search(
                        r"####\s*options\s*(.+?)(?=####|$)",
                        markdown_content,
                        re.DOTALL | re.IGNORECASE,
                    )
                    options = (
                        [
                            line.strip()
                            for line in options_match.group(1).strip().splitlines()
                            if line.strip()
                        ]
                        if options_match
                        else []
                    )

                    # Extract solution (line after #### SOLUTION)
                    solution_match = re.search(
                        r"####\s*SOLUTION\s*(.+)", markdown_content, re.IGNORECASE
                    )
                    solution = (
                        solution_match.group(1).strip() if solution_match else None
                    )

                    # Add question details to the current section
                    current_section[title] = {
                        "name": title,
                        "subquestion_number": subquestion_number,
                        "question_text": question_text,
                        "OPTIONS": options,
                        "solution": solution,
                    }

        return sections

    except FileNotFoundError:
        print(f"File {ipynb_file} not found.")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in notebook file.")
        return []


def check_for_heading(notebook_path, search_strings):
    """
    Checks if a Jupyter notebook contains a heading cell whose source matches any of the given strings.
    """
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == "raw" and cell.source.startswith("#"):
                    if any(
                        search_string in cell.source for search_string in search_strings
                    ):
                        return True
    except Exception as e:
        logger.info(f"Error reading notebook {notebook_path}: {e}")
    return False


def clean_notebook(notebook_path):
    """
    Removes specific cells and makes Markdown cells non-editable and non-deletable by updating their metadata.
    """
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        cleaned_cells = []
        for cell in notebook.cells:
            if not hasattr(cell, "cell_type") or not hasattr(cell, "source"):
                continue

            if (
                "## Submission" not in cell.source
                and "# Save your notebook first," not in cell.source
            ):
                if cell.cell_type == "markdown":
                    cell.metadata["editable"] = cell.metadata.get("editable", False)
                    cell.metadata["deletable"] = cell.metadata.get("deletable", False)
                if cell.cell_type == "code":
                    cell.metadata["tags"] = cell.metadata.get("tags", [])
                    if "skip-execution" not in cell.metadata["tags"]:
                        cell.metadata["tags"].append("skip-execution")

                cleaned_cells.append(cell)
            else:
                (f"Removed cell: {cell.source.strip()[:50]}...")

        notebook.cells = cleaned_cells

        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        logger.info(f"Cleaned notebook: {notebook_path}")

    except Exception as e:
        logger.info(f"Error cleaning notebook {notebook_path}: {e}")


def ensure_imports(output_file, header_lines):
    """
    Ensures specified header lines are present at the top of the file.

    Args:
        output_file (str): The path of the file to check and modify.
        header_lines (list of str): Lines to ensure are present at the top.

    Returns:
        str: The existing content of the file (without the header).
    """
    existing_content = ""
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing_content = f.read()

    # Determine missing lines
    missing_lines = [line for line in header_lines if line not in existing_content]

    # Write the updated content back to the file
    with open(output_file, "w", encoding="utf-8") as f:
        # Add missing lines at the top
        f.writelines(missing_lines)
        # Retain the existing content
        f.write(existing_content)

    return existing_content


def replace_cells_between_markers(data, markers, ipynb_file, output_file):
    """
    Replaces the cells between specified markers in a Jupyter Notebook (.ipynb file)
    with provided replacement cells and writes the result to the output file.

    Parameters:
    data (list): A list of dictionaries with data for creating replacement cells.
    markers (tuple): A tuple containing two strings: the BEGIN and END markers.
    ipynb_file (str): Path to the input Jupyter Notebook file.
    output_file (str): Path to the output Jupyter Notebook file.

    Returns:
    None: Writes the modified notebook to the output file.
    """
    begin_marker, end_marker = markers
    file_name_ipynb = ipynb_file.split("/")[-1].replace("_temp.ipynb", "")

    file_name_ipynb = sanitize_string(file_name_ipynb)

    # Iterate over each set of replacement data
    for data_ in data:
        dict_ = data_[next(iter(data_.keys()))]

        # Create the replacement cells
        replacement_cells = {
            "cell_type": "code",
            "metadata": {},
            "source": [
                "# Run this block of code by pressing Shift + Enter to display the question\n",
                f"from questions.{file_name_ipynb} import Question{dict_['question number']}\n",
                f"Question{dict_['question number']}().show()\n",
            ],
            "outputs": [],
            "execution_count": None,
        }

        # Process the notebook cells
        new_cells = []
        inside_markers = False
        done = False

        # Load the notebook data
        with open(ipynb_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        for cell in notebook_data["cells"]:
            if cell.get("cell_type") == "raw" and not done:
                if any(begin_marker in line for line in cell.get("source", [])):
                    # Enter the marked block
                    inside_markers = True
                    new_cells.append(replacement_cells)
                    continue
                elif inside_markers:
                    if any(end_marker in line for line in cell.get("source", [])):
                        # Exit the marked block
                        inside_markers = False
                        done = True
                        continue
                    else:
                        continue
                else:
                    new_cells.append(cell)
            elif inside_markers:
                # Skip cells inside the marked block
                continue
            else:
                new_cells.append(cell)
                continue

            if done:
                # Add cells outside the marked block
                new_cells.append(cell)
                continue

        # Update the notebook with modified cells, preserving metadata
        notebook_data["cells"] = new_cells

        # Write the modified notebook to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(notebook_data, f, indent=2)

        # Update ipynb_file to the output file for subsequent iterations
        ipynb_file = output_file


def generate_mcq_file(data_dict, output_file="mc_questions.py"):
    """
    Generates a Python file defining an MCQuestion class from a dictionary.

    Args:
        data_dict (dict): A nested dictionary containing question metadata.
        output_file (str): The path for the output Python file.

    Returns:
        None
    """

    # Define header lines
    header_lines = [
        "from pykubegrader.widgets.multiple_choice import MCQuestion, MCQ\n",
        "import pykubegrader.initialize\n",
        "import panel as pn\n\n",
        "pn.extension()\n\n",
    ]

    # Ensure header lines are present
    _existing_content = ensure_imports(output_file, header_lines)

    for question_dict in data_dict:
        with open(output_file, "a", encoding="utf-8") as f:
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                if i == 0:
                    # Write the MCQuestion class
                    f.write(
                        f"class Question{q_value['question number']}(MCQuestion):\n"
                    )
                    f.write("    def __init__(self):\n")
                    f.write("        super().__init__(\n")
                    f.write(f"            title=f'{q_value['question_text']}',\n")
                    f.write("            style=MCQ,\n")
                    f.write(
                        f"            question_number={q_value['question number']},\n"
                    )
                break

            keys = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write keys
                keys.append(f"q{q_value['subquestion_number']}-{q_value['name']}")

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


def generate_select_many_file(data_dict, output_file="select_many_questions.py"):
    """
    Generates a Python file defining an MCQuestion class from a dictionary.

    Args:
        data_dict (dict): A nested dictionary containing question metadata.
        output_file (str): The path for the output Python file.

    Returns:
        None
    """

    # Define header lines
    header_lines = [
        "from pykubegrader.widgets.select_many import MultiSelect, SelectMany\n",
        "import pykubegrader.initialize\n",
        "import panel as pn\n\n",
        "pn.extension()\n\n",
    ]

    # Ensure header lines are present
    _existing_content = ensure_imports(output_file, header_lines)

    for question_dict in data_dict:
        with open(output_file, "a", encoding="utf-8") as f:
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                if i == 0:
                    # Write the MCQuestion class
                    f.write(
                        f"class Question{q_value['question number']}(SelectMany):\n"
                    )
                    f.write("    def __init__(self):\n")
                    f.write("        super().__init__(\n")
                    f.write(f"            title=f'{q_value['question_text']}',\n")
                    f.write("            style=MultiSelect,\n")
                    f.write(
                        f"            question_number={q_value['question number']},\n"
                    )
                break

            keys = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write keys
                keys.append(f"q{q_value['subquestion_number']}-{q_value['name']}")

            f.write(f"            keys={keys},\n")

            descriptions = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write descriptions
                descriptions.append(q_value["question_text"])
            f.write(f"            descriptions={descriptions},\n")

            options = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write options
                options.append(q_value["OPTIONS"])

            f.write(f"            options={options},\n")

            points = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write points
                points.append(q_value["points"])

            f.write(f"            points={points},\n")

            first_key = next(iter(question_dict))
            if "grade" in question_dict[first_key]:
                grade = question_dict[first_key]["grade"]
                f.write(f"            grade={grade},\n")

            f.write("        )\n")


def generate_tf_file(data_dict, output_file="tf_questions.py"):
    """
    Generates a Python file defining an MCQuestion class from a dictionary.

    Args:
        data_dict (dict): A nested dictionary containing question metadata.
        output_file (str): The path for the output Python file.

    Returns:
        None
    """

    # Define header lines
    header_lines = [
        "from pykubegrader.widgets.true_false import TFQuestion, TrueFalse_style\n",
        "import pykubegrader.initialize\n",
        "import panel as pn\n\n",
        "pn.extension()\n\n",
    ]

    # Ensure header lines are present
    _existing_content = ensure_imports(output_file, header_lines)

    for question_dict in data_dict:
        with open(output_file, "a", encoding="utf-8") as f:
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                if i == 0:
                    # Write the MCQuestion class
                    f.write(
                        f"class Question{q_value['question number']}(TFQuestion):\n"
                    )
                    f.write("    def __init__(self):\n")
                    f.write("        super().__init__(\n")
                    f.write(f"            title=f'{q_value['question_text']}',\n")
                    f.write("            style=TrueFalse_style,\n")
                    f.write(
                        f"            question_number={q_value['question number']},\n"
                    )
                break

            keys = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write keys
                keys.append(f"q{q_value['subquestion_number']}-{q_value['name']}")

            f.write(f"            keys={keys},\n")

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


def sanitize_string(input_string):
    """
    Converts a string into a valid Python variable name.

    Args:
        input_string (str): The string to convert.

    Returns:
        str: A valid Python variable name.
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r"\W|^(?=\d)", "_", input_string)
    return sanitized


def find_first_code_cell(notebook_path):
    """
    Finds the first Python code cell in a Jupyter notebook and its index.

    Args:
        notebook_path (str): Path to the Jupyter notebook file.

    Returns:
        tuple: A tuple containing the index of the first code cell and the cell dictionary,
            or (None, None) if no code cell is found.
    """
    # Load the notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    # Iterate through the cells to find the first code cell
    for index, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") == "code":
            return index, cell  # Return the index and the first code cell

    return None, None  # No code cell found


def replace_cell_source(notebook_path, cell_index, new_source):
    """
    Replace the source code of a specific Jupyter notebook cell.

    Args:
        cell_index (int): Index of the cell to be modified (0-based).
        new_source (str): New source code to replace the cell's content.
    """
    # Load the notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    # Check if the cell index is valid
    if cell_index >= len(notebook.cells) or cell_index < 0:
        raise IndexError(f"Cell index {cell_index} is out of range for this notebook.")

    # Replace the source code of the specified cell
    notebook.cells[cell_index]["source"] = new_source

    # Save the notebook
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(notebook, f)


def main():
    parser = argparse.ArgumentParser(
        description="Recursively process Jupyter notebooks with '# ASSIGNMENT CONFIG', move them to a solutions folder, and run otter assign."
    )
    parser.add_argument(
        "root_folder", type=str, help="Path to the root folder to process"
    )
    args = parser.parse_args()

    processor = NotebookProcessor(args.root_folder)
    processor.process_notebooks()


if __name__ == "__main__":
    sys.exit(main())
