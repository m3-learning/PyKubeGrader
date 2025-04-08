### Note


import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime

import requests
import yaml
from dateutil import parser

from pykubegrader.build.io import remove_file_suffix
from pykubegrader.build.notebooks.writers import remove_assignment_config_cells
from pykubegrader.build.notebooks.writers import write_initialization_code
from pykubegrader.build.widget_questions.types import (
    MultipleChoice,
    SelectMany,
    TrueFalse,
)

from pykubegrader.utils.logging import Logger  # For robust datetime parsing

try:
    from pykubegrader.build.passwords import password, user
except:  # noqa: E722
    print("Passwords not found, cannot access database")

from typing import Optional

import nbformat

from .api_notebook_builder import FastAPINotebookBuilder

os.environ["JUPYTERHUB_USER"] = "jca92"
os.environ["TOKEN"] = "token"
os.environ["DB_URL"] = "https://engr-131-api.eastus.cloudapp.azure.com/"
os.environ["keys_student"] = "capture"
os.environ["user_name_student"] = "student"

from pykubegrader.tokens.tokens import add_token

add_token("token", duration=20)


@dataclass
class NotebookProcessor(Logger):
    """
    A class for processing Jupyter notebooks in a directory and its subdirectories.

    Attributes:
        root_folder (str): The root directory containing notebooks to process.
        assignment_tag (str): Tag for the assignment being processed.
        solutions_folder (str): The directory where processed notebooks and solutions are stored.
        verbose (bool): Flag for verbose output to the console.
        log (bool): Flag to enable or disable logging.
        require_key (bool): Flag to require a key for processing.
        bonus_points (float): Additional points to be added to the assignment.
        kwargs:
            log_name (str): The name of the log file.

    Methods:
        __post_init__(self, **kwargs):
            Post-initialization method for setting up the `NotebookProcessor` instance.

        initialize_logger(self, **kwargs):
            Configures the logger for the NotebookProcessor class.

        initialize_info(self):
            Initializes the information for the NotebookProcessor instance.

        add_notebook(self, notebook_name, total_points):
            Adds a notebook record to the database.

        add_submission_cells(self, notebook_path, output_path):
            Adds submission cells to the notebook.

        add_final_submission_cells(self, notebook_path, output_path):
            Adds final submission cells to the notebook.

        remove_empty_cells(notebook_path):
            Removes empty cells from the notebook.

        duplicate_files(self, notebook_path, notebook_name, solution_notebook_path):
            Duplicates a Jupyter notebook into a specified solution directory, creating necessary subdirectories and temporary files for further processing.

        merge_metadata(raw, data):
            Merges raw metadata with extracted question data.

        extract_question_points(raw, i, _data, grade_=None):
            Extracts question points from raw metadata.

        has_assignment(notebook_path, *tags):
            Determines if a Jupyter notebook contains any of the specified configuration tags.

        run_otter_assign(notebook_path, dist_folder):
            Runs the Otter Assign command on the notebook.
    """

    root_folder: str
    assignment_tag: str = field(default="")
    solutions_folder: str = field(init=False)
    api_url: str = field(default="https://engr-131-api.eastus.cloudapp.azure.com")
    verbose: bool = False
    log: bool = True
    require_key: bool = False
    bonus_points: float = 0

    def __post_init__(self, **kwargs):
        """
        Post-initialization method for setting up the `NotebookProcessor` instance.

        This method is automatically called after the instance is created. It performs the following tasks:
            1. Creates a solutions folder within the root directory to store processed outputs.
            2. Configures logging to capture detailed information about the processing.

        Raises:
            OSError: If the solutions folder cannot be created due to permissions or other filesystem issues.
        """
        
        super().__init__(verbose=self.verbose, log=self.log, **kwargs)
        
        # Initialize the info for the class
        self.initialize_info()

        os.makedirs(
            self.solutions_folder, exist_ok=True
        )  # Create the folder if it doesn't exist

    def initialize_info(self):
        """
        Initializes the NotebookProcessor instance with assignment information.

        This method performs the following tasks:
        1. Checks if an 'assignment_config.yaml' file exists in the root folder.
        2. If the YAML file exists, it initializes the instance using the YAML content.
        3. If the YAML file does not exist, it initializes the instance using the assignment tag.
        4. Sets the week number and week string based on the assignment tag.
        5. Defines the folder to store solutions and ensures it exists.
        6. Initializes the total points for the assignment and a log for total points.

        Raises:
            None
        """
        if self.check_if_file_in_folder("assignment_config.yaml"):
            # Parse the YAML content
            self.initialize_from_assignment_yaml()
        else:
            self.assignment_type = self.assignment_tag.split("-")[0].lower()
            self.week_num = self.assignment_tag.split("-")[-1]
            self.assignment_tag = f"week{self.week_num}-{self.assignment_type}"

        self.week = f"week_{self.week_num}"

        # Define the folder to store solutions and ensure it exists
        self.solutions_folder = os.path.join(self.root_folder, "_solutions")
        self.assignment_total_points = 0
        self.total_point_log = {}

    def initialize_from_assignment_yaml(self):
        """
        Initializes the NotebookProcessor instance from the 'assignment_config.yaml' file.

        This method performs the following tasks:
        1. Opens and reads the 'assignment_config.yaml' file located in the root folder.
        2. Parses the YAML content to extract assignment details.
        3. Sets the week number, assignment type, bonus points, requirement key, final submission flag, and assignment tag.

        Raises:
            FileNotFoundError: If the 'assignment_config.yaml' file does not exist.
            yaml.YAMLError: If there is an error parsing the YAML content.
        """
        
        # TODO: make robust to no week number set?
        with open(f"{self.root_folder}/assignment_config.yaml", "r") as file:
            data = yaml.safe_load(file)

            # Extract assignment details
            assignment = data.get("assignment", {})
            self.week_num = assignment.get("week")
            self.assignment_type = assignment.get("assignment_type")
            self.bonus_points = assignment.get("bonus_points", 0)
            self.require_key = assignment.get("require_key", False)
            self.final_submission = assignment.get("final_submission", False)
            self.assignment_tag = assignment.get(
                "assignment_tag",
                f"week{assignment.get('week')}-{self.assignment_type}",
            )

    def process_notebooks(self):
        """
        Processes Jupyter notebooks within the root folder and its subfolders.

        This method performs the following actions:
        1. Collects all Jupyter notebook files (.ipynb) from the root folder and its subdirectories.
        2. Verifies if each notebook contains the necessary assignment configuration metadata.
        3. Processes notebooks that meet the criteria using the `_process_single_notebook` method.

        Prerequisites:
            - The `has_assignment` method must be implemented to verify the presence of assignment configuration in a notebook.
            - The `_process_single_notebook` method should be defined to handle the processing of individual notebooks.

        Raises:
            - OSError: If there is an error accessing files or directories.
        """
        # 1. Collects all Jupyter notebook files (.ipynb) from the root folder and its subdirectories.
        ipynb_files = self.get_notebooks_recursively()

        # 2. Verifies if each notebook contains the necessary assignment configuration.
        for notebook_path in ipynb_files:
            # Check if the notebook has the required assignment configuration
            if self.has_assignment(notebook_path):
                self.print_and_log(f"notebook_path = {notebook_path}")

                # 3. Process the notebook if it meets the criteria
                self._process_single_notebook(notebook_path)

        # Write the dictionary to a JSON file
        with open(f"{self.solutions_folder}/total_points.json", "w") as json_file:
            json.dump(
                self.total_point_log, json_file, indent=4
            )  # `indent=4` for pretty formatting

        if self.check_if_file_in_folder("assignment_config.yaml"):
            self.put_assignment()

        self.update_initialize_function()

    def get_notebooks_recursively(self):
        """
        Recursively retrieves all Jupyter notebook files (.ipynb) from the root folder and its subfolders.

        This method walks through the directory tree starting from the root folder, identifies all files
        with a .ipynb extension, and collects their paths in a list.

        Returns:
            list: A list of file paths to Jupyter notebook files found within the root folder and its subfolders.
        """
        ipynb_files = []

        # Walk through the root folder and its subfolders
        for dirpath, _, filenames in os.walk(self.root_folder):
            for filename in filenames:
                # Check if the file is a Jupyter notebook
                if filename.endswith(".ipynb"):
                    notebook_path = os.path.join(dirpath, filename)
                    ipynb_files.append(notebook_path)
        return ipynb_files

    def update_initialize_function(self):
        """
        Updates the initialization function for each notebook in the total point log.

        This method iterates through the total point log, constructs the notebook path,
        and updates the initialization assignment with the corresponding points and tag.

        The `update_initialize_assignment` function is called for each notebook to
        perform the update.

        Args:
            None

        Returns:
            None
        """
        for key, value in self.total_point_log.items():
            update_initialize_assignment(
                notebook_path=os.path.join(self.root_folder, key + ".ipynb"),
                assignment_points=value,
                assignment_tag=self.assignment_tag,
            )

    def build_payload_notebook(self, yaml_content, notebook_title, total_points):
        # Parse the YAML content
        with open(yaml_content, "r") as file:
            data = yaml.safe_load(file)

        # Extract assignment details
        assignment = data.get("assignment", {})

        week_num = self.week_num
        assignment_type = self.assignment_type
        due_date = self.get_due_date(assignment)

        return {
            "title": notebook_title,
            "week_number": week_num,
            "assignment_type": assignment_type,
            "due_date": due_date,
            "max_score": total_points,
        }

    def build_payload(self, yaml_content):
        """
        Reads YAML content for an assignment and returns Python variables.

        Args:
            yaml_content (str): The YAML file path to parse.

        Returns:
            dict: A dictionary containing the parsed assignment data.
        """
        # Parse the YAML content
        with open(yaml_content, "r") as file:
            data = yaml.safe_load(file)

        # Extract assignment details
        assignment = data.get("assignment", {})
        week = assignment.get("week")
        assignment_type = assignment.get("assignment_type")
        due_date = self.get_due_date(assignment)

        title = f"Week {week} - {assignment_type}"

        # Return the extracted details as a dictionary
        return {
            "title": title,
            "description": str(week),
            "week_number": week,
            "assignment_type": assignment_type,
            "due_date": due_date,
            "max_score": self.assignment_total_points - self.bonus_points,
        }

    @staticmethod
    def get_due_date(assignment):
        due_date_str = assignment.get("due_date")

        # Convert due_date to a datetime object if available
        due_date = None
        if due_date_str:
            try:
                due_date = parser.parse(due_date_str)  # Automatically handles timezones
            except ValueError as e:
                print(f"Error parsing due_date: {e}")
        return due_date

    def put_notebook(self, notebook_title, total_points):
        """
        Sends a POST request to add a notebook.
        """
        # Define the URL
        url = os.path.join(self.api_url, "notebook")

        # Build the payload
        payload = self.build_payload_notebook(
            yaml_content=f"{self.root_folder}/assignment_config.yaml",
            notebook_title=notebook_title,
            total_points=total_points,
        )

        # Define HTTP Basic Authentication
        auth = (user(), password())

        # Define headers
        headers = {"Content-Type": "application/json"}

        # Serialize the payload with the custom JSON encoder
        serialized_payload = json.dumps(payload, default=self.json_serial)

        # Send the POST request
        response = requests.post(
            url, data=serialized_payload, headers=headers, auth=auth
        )

        # Print the response
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except ValueError:
            print(f"Response: {response.text}")

    def put_assignment(self):
        """
        Sends a POST request to add an assignment.
        """
        
        # Define the URL
        url = os.path.join(self.api_url, "assignments")

        # Build the payload
        payload = self.build_payload(f"{self.root_folder}/assignment_config.yaml")

        # Define HTTP Basic Authentication
        auth = (user(), password())

        # Define headers
        headers = {"Content-Type": "application/json"}

        # Serialize the payload with the custom JSON encoder
        serialized_payload = json.dumps(payload, default=self.json_serial)

        # Send the POST request
        response = requests.post(
            url, data=serialized_payload, headers=headers, auth=auth
        )

        # Print the response
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except ValueError:
            print(f"Response: {response.text}")

    def check_if_file_in_folder(self, file):
        for root, _, files in os.walk(self.root_folder):
            if file in files:
                return True
        return False

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

        # 1. Initialize variables
        self.select_many_total_points = 0
        self.mcq_total_points = 0
        self.tf_total_points = 0
        self.otter_total_points = 0

        self.print_and_log(f"Processing notebook: {notebook_path}")

        # 1. Get the notebook name and solution folder path
        notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
        solution_notebook_folder_path = os.path.join(
            self.solutions_folder, notebook_name
        )

        # 2. Create temporary and autograder notebooks and files
        new_notebook_path, temp_notebook_path, autograder_path, student_path = (
            self.duplicate_files(
                notebook_path, notebook_name, solution_notebook_folder_path
            )
        )

        solution_path, question_path = self.widget_question_parser(
            new_notebook_path, temp_notebook_path
        )

        student_notebook, self.otter_total_points = self.free_response_parser(
            temp_notebook_path, solution_notebook_folder_path, notebook_name
        )

        # If Otter does not run, move the student file to the main directory
        if student_notebook is None:
            clean_notebook(temp_notebook_path)
            path_ = shutil.copy(temp_notebook_path, self.root_folder)
            path_2 = shutil.move(
                question_path,
                os.path.join(
                    os.path.dirname(temp_notebook_path), os.path.basename(question_path)
                ),
            )
            self.print_and_log(
                f"Copied and cleaned student notebook: {path_} -> {self.root_folder}"
            )
            self.print_and_log(
                f"Copied Questions to: {path_2} -> {os.path.join(os.path.dirname(temp_notebook_path), os.path.basename(question_path))}"
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
        remove_file_suffix(autograder_path, "_solutions", logger=self.logger)
        remove_file_suffix(student_path, "_questions", logger=self.logger)
        remove_file_suffix(self.root_folder, "_temp", logger=self.logger)

        ### CODE TO ENSURE THAT STUDENT NOTEBOOK IS IMPORTABLE
        
        self.importable_file_name(student_path, question_path)

        total_points = (
            self.select_many_total_points
            + self.mcq_total_points
            + self.tf_total_points
            + self.otter_total_points
        )

        # creates the assignment record in the database
        self.put_notebook(notebook_name, total_points)

        self.assignment_total_points += total_points

        self.total_point_log.update({notebook_name: total_points})

        student_file_path = os.path.join(self.root_folder, notebook_name + ".ipynb")
        self.add_submission_cells(student_file_path, student_file_path)
        self.add_final_submission_cells(student_file_path, student_file_path)
        self.remove_empty_cells(student_file_path)

    def importable_file_name(self, student_path, question_path):
        """
        Ensures that the question file is importable by sanitizing its name and moving it to the appropriate directory.

        This method performs the following steps:
        1. Sanitizes the question file name by removing the "_questions" suffix and ensuring it has a ".py" extension.
        2. Renames the question file in the student directory to its sanitized version.
        3. Ensures the existence of a "questions" folder in the root directory.
        4. Copies the renamed question file to the "questions" folder.

        Parameters:
            student_path (str): The path to the student directory where the question file is located.
            question_path (str): The path to the question file that needs to be sanitized and moved.
        """
        if question_path is not None:
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

    def widget_question_parser(self, new_notebook_path, temp_notebook_path):
        """
        Parses widget questions from a temporary notebook and returns paths to solution and question files.

        This method processes multiple choice, true/false, and select-many type questions from the given
        temporary notebook path and generates corresponding solution and question files in the new notebook path.

        Parameters:
            new_notebook_path (str): The path where the new notebook is located.
            temp_notebook_path (str): The path to the temporary notebook containing widget questions.

        Returns:
            tuple: A tuple containing the path to the solution file and the path to the question file.
                   If no questions are found, both paths will be None.
        """

        # TODO: Make it so we can have a list of objects in config to loop through
        solution_path_1, question_path_1 = MultipleChoice(
            ipynb_file=new_notebook_path, temp_notebook_path=temp_notebook_path
        ).run()

        solution_path_2, question_path_2 = TrueFalse(
            ipynb_file=new_notebook_path, temp_notebook_path=temp_notebook_path
        ).run()

        solution_path_3, question_path_3 = SelectMany(
            ipynb_file=new_notebook_path, temp_notebook_path=temp_notebook_path
        ).run()

        if any([solution_path_1, solution_path_2, solution_path_3]) is not None:
            solution_path = solution_path_1 or solution_path_2 or solution_path_3

        if any([question_path_1, question_path_2, question_path_3]) is not None:
            question_path = question_path_1 or question_path_2 or question_path_3

        return solution_path, question_path

    def duplicate_files(self, notebook_path, notebook_name, solution_notebook_path):
        """
        Duplicates a Jupyter notebook into a specified solution directory, creating necessary subdirectories
        and temporary files for further processing.

        Parameters:
            notebook_path (str): The path to the original Jupyter notebook.
            notebook_name (str): The name of the notebook, used for naming temporary files.
            solution_notebook_path (str): The path where the solution and related directories will be created.

        Returns:
            tuple: A tuple containing paths to the new notebook, temporary notebook, autograder directory,
                   and student directory.
        """

        # 1. Create the subfolder if it doesn't exist
        os.makedirs(solution_notebook_path, exist_ok=True)

        # 2. Create a new notebook path in the subfolder
        new_notebook_path = os.path.join(
            solution_notebook_path, os.path.basename(notebook_path)
        )

        # 3. Create a temp copy of the notebook
        temp_notebook_path = os.path.join(
            solution_notebook_path, f"{notebook_name}_temp.ipynb"
        )
        shutil.copy(notebook_path, temp_notebook_path)

        # 4. Create the autograder folder
        autograder_path = os.path.join(solution_notebook_path, "dist/autograder/")
        os.makedirs(autograder_path, exist_ok=True)

        # 5. Create the student folder
        student_path = os.path.join(solution_notebook_path, "dist/student/")
        os.makedirs(student_path, exist_ok=True)

        # 6. Move the notebook to the new path if it's not already there
        if os.path.abspath(notebook_path) != os.path.abspath(new_notebook_path):
            shutil.move(notebook_path, new_notebook_path)
            self.print_and_log(f"Moved: {notebook_path} -> {new_notebook_path}")
        else:
            self.print_and_log(f"Notebook already in destination: {new_notebook_path}")
        return new_notebook_path, temp_notebook_path, autograder_path, student_path

    def remove_empty_cells(self, notebook_path, output_path=None):
        """
        Removes empty cells from a Jupyter Notebook and saves the updated notebook.

        Parameters:
            notebook_path (str): Path to the input Jupyter Notebook.
            output_path (str): Path to save the updated Jupyter Notebook. If None, it overwrites the original file.
        """
        try:
            # Load the notebook
            with open(notebook_path, "r") as nb_file:
                notebook = nbformat.read(nb_file, as_version=4)

            # Filter out empty cells
            non_empty_cells = [cell for cell in notebook.cells if cell.source.strip()]

            # Update the notebook cells
            notebook.cells = non_empty_cells

            # Save the updated notebook
            save_path = output_path if output_path else notebook_path
            with open(save_path, "w") as nb_file:
                nbformat.write(notebook, nb_file)

            self.print_and_log(f"Empty cells removed. Updated notebook saved at: {save_path}")

        except Exception as e:
            self.print_and_log(f"An error occurred: {e}")

    def add_submission_cells(self, notebook_path: str, output_path: str) -> None:
        """
        Adds submission cells to the end of a Jupyter notebook.

        Args:
            notebook_path (str): Path to the input notebook.
            output_path (str): Path to save the modified notebook.
        """
        # Load the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Define the Markdown cell
        markdown_cell = nbformat.v4.new_markdown_cell(
            "## Submitting Assignment\n\n"
            "Please run the following block of code using `shift + enter` to submit your assignment, "
            "you should see your score."
        )

        code_cell = self.add_key_requirement_import(notebook_path)

        # Make the code cell non-editable and non-deletable
        code_cell.metadata = {"editable": True, "deletable": False}
        code_cell.metadata["tags"] = ["skip-execution"]

        # Add the cells to the notebook
        notebook.cells.append(markdown_cell)
        notebook.cells.append(code_cell)

        # Save the modified notebook
        with open(output_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)

    def add_key_requirement_import(self, notebook_path):
        """
        Creates a code cell for the notebook that includes the necessary import statements for assignment submission.
        
        If the `require_key` attribute is set to True, the code cell will include an import and call to `validate_token`.
        This ensures that the assignment is validated with a token before submission.

        Args:
            notebook_path (str): The path to the notebook file.

        Returns:
            nbformat.NotebookNode: A new code cell with the required import statements for submission.
        """
        if self.require_key:
            # Add an additional line for validate_token()
            validate_token_line = (
                f"from pykubegrader.tokens.validate_token import validate_token\n"
                f"validate_token(assignment = '{self.assignment_tag}')\n"
            )

            # Define the Code cell
            code_cell = nbformat.v4.new_code_cell(
                f"{validate_token_line}\n\n"
                "from pykubegrader.submit.submit_assignment import submit_assignment\n\n"
                f'submit_assignment("{self.assignment_tag}", "{os.path.basename(notebook_path).replace(".ipynb", "")}")'
            )
        else:
            # Define the Code cell without validate_token()
            code_cell = nbformat.v4.new_code_cell(
                "from pykubegrader.submit.submit_assignment import submit_assignment\n\n"
                f'submit_assignment("{self.assignment_tag}", "{os.path.basename(notebook_path).replace(".ipynb", "")}")'
            )
            
        return code_cell

    def add_final_submission_cells(self, notebook_path: str, output_path: str) -> None:
        """
        Adds final submission cells to the end of a Jupyter notebook.

        Args:
            notebook_path (str): Path to the input notebook.
            output_path (str): Path to save the modified notebook.
        """
        # If the assignment is not a final submission, do not add the cells
        if not self.final_submission:
            return

        # Load the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Define the Markdown cell
        markdown_cell = nbformat.v4.new_markdown_cell(
            "## Submitting Final Assignment\n\n"
            "Please run this cell with the provided token to identify your submission as final. Once your submission is final, you will not be able to make any changes to your assignment. "
        )

        # Define the Code cell
        code_cell = nbformat.v4.new_code_cell(
            "from pykubegrader.submit.final_submission import final_submission\n\n"
            f"final_submission(assignment='{self.assignment_tag}', assignment_type='{self.assignment_type}', token='replace your token here', week_number = {self.week_num})"
        )

        # Make the code cell non-editable and non-deletable
        code_cell.metadata = {"editable": True, "deletable": False}
        code_cell.metadata["tags"] = ["skip-execution"]

        # Add the cells to the notebook
        notebook.cells.append(markdown_cell)
        notebook.cells.append(code_cell)

        # Save the modified notebook
        with open(output_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)

    def free_response_parser(
        self, temp_notebook_path, notebook_subfolder, notebook_name
    ):
        if self.has_assignment(temp_notebook_path, "# ASSIGNMENT CONFIG"):

            client_private_key, server_public_key = self.transfer_encryption_keys(temp_notebook_path)

            # Extract the assignment config
            config = extract_config_from_notebook(temp_notebook_path)

            files = extract_files(config)

            if files:
                for file in files:
                    print(f"Copying {file} to {os.path.join(notebook_subfolder, file)}")
                    shutil.copy(
                        os.path.join(self.root_folder, file),
                        os.path.join(notebook_subfolder, file),
                    )
                    
            client_private_key, server_public_key = self.transfer_encryption_keys(notebook_subfolder)

            out = FastAPINotebookBuilder(
                notebook_path=temp_notebook_path,
                assignment_tag=self.assignment_tag,
                require_key=self.require_key,
            )

            debug_notebook = os.path.join(
                notebook_subfolder,
                "dist",
                "autograder",
                os.path.basename(temp_notebook_path).replace("_temp", "_debugger"),
            )

            self.run_otter_assign(
                temp_notebook_path, os.path.join(notebook_subfolder, "dist")
            )

            self.print_and_log(f"Copying {temp_notebook_path} to {debug_notebook}")
            shutil.copy(temp_notebook_path, debug_notebook)

            remove_assignment_config_cells(debug_notebook)

            student_notebook = os.path.join(
                notebook_subfolder, "dist", "student", f"{notebook_name}.ipynb"
            )

            write_initialization_code(
                student_notebook,
                self.week,
                self.assignment_type,
                require_key=self.require_key,
                assignment_tag=self.assignment_tag,
            )

            NotebookProcessor.replace_temp_in_notebook(
                student_notebook, student_notebook
            )
            autograder_notebook = os.path.join(
                notebook_subfolder, "dist", "autograder", f"{notebook_name}.ipynb"
            )
            NotebookProcessor.replace_temp_in_notebook(
                autograder_notebook, autograder_notebook
            )

            clean_notebook(student_notebook)

            shutil.copy(student_notebook, self.root_folder)
            self.print_and_log(
                f"Copied and cleaned student notebook: {student_notebook} -> {self.root_folder}"
            )

            # Remove the keys
            os.remove(client_private_key)
            os.remove(server_public_key)

            return student_notebook, out.total_points
        else:
            write_initialization_code(
                temp_notebook_path,
                self.week,
                self.assignment_type,
                require_key=self.require_key,
                assignment_tag=self.assignment_tag,
            )
            NotebookProcessor.replace_temp_no_otter(
                temp_notebook_path, temp_notebook_path
            )
            return None, 0

    def transfer_encryption_keys(self, temp_notebook_path):
        client_private_key = os.path.join(
                os.path.dirname(temp_notebook_path),
                ".client_private_key.bin",
            )
        server_public_key = os.path.join(
                os.path.dirname(temp_notebook_path),
                ".server_public_key.bin",
            )

        shutil.copy("./keys/.client_private_key.bin", client_private_key)
        shutil.copy("./keys/.server_public_key.bin", server_public_key)
        
        return client_private_key, server_public_key

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    #TODO: Check if we can combine this with replace_temp_in_notebook
    @staticmethod
    def replace_temp_no_otter(input_file, output_file):
        # Load the notebook
        with open(input_file, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Iterate through the cells and modify `cell.source`
        for cell in notebook.cells:
            if cell.cell_type == "code":  # Only process code cells
                if "responses = initialize_assignment(" in cell.source:
                    cell.source = cell.source.replace("_temp", "")

        # Save the modified notebook
        with open(output_file, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)

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
    def extract_question_points(raw, i, _data, grade_=None):
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
        return points_, grade_

    def run_otter_assign(self, notebook_path, dist_folder):
        """
        Runs `otter assign` on the given notebook and outputs to the specified distribution folder.
        """
        try:
            os.makedirs(dist_folder, exist_ok=True)
            command = ["otter", "assign", notebook_path, dist_folder]
            subprocess.run(command, check=True)
            self.print_and_log(f"Otter assign completed: {notebook_path} -> {dist_folder}")

            # Remove all postfix _test from filenames in dist_folder
            remove_file_suffix(dist_folder, logger=self.logger)

        except subprocess.CalledProcessError as e:
            self.print_and_log(f"Error running `otter assign` for {notebook_path}: {e}")
        except Exception as e:
            self.print_and_log(
                f"Unexpected error during `otter assign` for {notebook_path}: {e}"
            )

@dataclass
class WidgetQuestionParser:
    sections: list = field(default_factory=list)
    current_section: dict = field(default_factory=dict)
    within_section: bool = False
    subquestion_number: int = 0
    start_label: str = "# BEGIN MULTIPLE CHOICE"
    end_label: str = "# END MULTIPLE CHOICE"

    def process_raw_cell(self, raw_content):
        if self.start_label in raw_content:
            self.start_new_section()
            return True
        elif self.end_label in raw_content:
            self.end_current_section()
            return True
        return False

    def start_new_section(self):
        self.within_section = True
        self.subquestion_number = 0
        self.current_section = {}

    def end_current_section(self):
        self.within_section = False
        if self.current_section:
            self.sections.append(self.current_section)

    def increment_subquestion_number(self):
        self.subquestion_number += 1


def check_for_heading(self, notebook_path, search_strings):
    """
    Checks if a Jupyter notebook contains a heading cell whose source matches any of the given strings.

    Args:
        notebook_path (str): The file path to the Jupyter notebook to be checked.
        search_strings (list of str): A list of strings to search for in the heading cells.

    Returns:
        bool: True if any of the search strings are found in the heading cells, False otherwise.

    Example:
        search_strings = ["# ASSIGNMENT CONFIG", "# BEGIN MULTIPLE CHOICE"]
        result = check_for_heading("path/to/notebook.ipynb", search_strings)
        if result:
            print("Heading found.")
        else:
            print("Heading not found.")
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
        self.print_and_log(f"Error reading notebook {notebook_path}: {e}")
    return False


def clean_notebook(self, notebook_path):
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
        self.print_and_log(f"Cleaned notebook: {notebook_path}")

    except Exception as e:
        self.print_and_log(f"Error cleaning notebook {notebook_path}: {e}")


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


question_class_type = {
    "MCQuestion": {"class_type": "MCQuestion", "style": "MCQ"},
    "SelectMany": {"class_type": "SelectMany", "style": "MultiSelect"},
    "TFQuestion": {"class_type": "TFQuestion", "style": "TFStyle"},
}


def write_question_class(f, q_value, class_name):
    class_type_ = question_class_type[class_name]

    f.write(
        f"class Question{q_value['question number']}({class_type_['class_type']}):\n"
    )
    f.write("    def __init__(self):\n")
    f.write("        super().__init__(\n")
    f.write(f'            title=f"{q_value["title"]}",\n')
    f.write(f"            style={class_type_['style']},\n")
    f.write(f"            question_number={q_value['question number']},\n")


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
                    f.write(f'            title=f"{q_value["title"]}",\n')
                    f.write("            style=MultiSelect,\n")
                    f.write(
                        f"            question_number={q_value['question number']},\n"
                    )
                break

            keys = []
            for i, (q_key, q_value) in enumerate(question_dict.items()):
                # Write keys
                keys.append(
                    f"q{q_value['question number']}-{q_value['subquestion_number']}-{q_value['name']}"
                )

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


def update_initialize_assignment(
    notebook_path: str,
    assignment_points: Optional[float] = None,
    assignment_tag: Optional[str] = None,
) -> None:
    """
    Search for a specific line in a Jupyter Notebook and update it with additional input variables.

    Args:
        notebook_path (str): The path to the Jupyter Notebook file (.ipynb).
        assignment_points (Optional[float]): The assignment points variable to add (default is None).
        assignment_tag (Optional[str]): The assignment tag variable to add (default is None).

    Returns:
        None
    """
    # Load the notebook content
    with open(notebook_path, "r", encoding="utf-8") as file:
        notebook_data = json.load(file)

    # Pattern to match the specific initialize_assignment line
    pattern = re.compile(r"responses\s*=\s*initialize_assignment\((.*?)\)")

    # Collect additional variables
    additional_variables = []
    if assignment_points is not None:
        additional_variables.append(f"assignment_points = {assignment_points}")
    if assignment_tag is not None:
        additional_variables.append(f"assignment_tag = '{assignment_tag}'")

    # Join additional variables into a string
    additional_variables_str = ", ".join(additional_variables)

    # Flag to check if any replacements were made
    updated = False

    # Iterate through notebook cells
    for cell in notebook_data.get("cells", []):
        if cell.get("cell_type") == "code":  # Only modify code cells
            source_code = cell.get("source", [])
            for i, line in enumerate(source_code):
                match = pattern.search(line)
                if match:
                    # Extract existing arguments
                    existing_args = match.group(1).strip()
                    # Replace with the updated line
                    if additional_variables_str:
                        updated_line = f"responses = initialize_assignment({existing_args}, {additional_variables_str})\n"
                    else:
                        updated_line = (
                            f"responses = initialize_assignment({existing_args})\n"
                        )
                    source_code[i] = updated_line
                    updated = True

    # If updated, save the notebook
    if updated:
        with open(notebook_path, "w", encoding="utf-8") as file:
            json.dump(notebook_data, file, indent=2)
        print(f"Notebook '{notebook_path}' has been updated.")
    else:
        print(f"No matching lines found in '{notebook_path}'.")


def extract_config_from_notebook(notebook_path):
    """
    Extract configuration text from a Jupyter Notebook.

    Parameters:
        notebook_path (str): Path to the Jupyter Notebook file.

    Returns:
        str: The configuration text if found, otherwise an empty string.
    """
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook_data = json.load(f)

    # Iterate through cells to find the configuration text
    config_text = ""
    for cell in notebook_data.get("cells", []):
        if cell.get("cell_type") == "raw":  # Check for code cells
            source = "".join(cell.get("source", []))
            if "# ASSIGNMENT CONFIG" in source:
                config_text = source
                break

    return config_text


def extract_files(config_text):
    """
    Extract the list of files from the given configuration text, excluding .bin files.

    Parameters:
        config_text (str): The configuration text to process.

    Returns:
        list: A list of file names excluding .bin files.
    """
    # Regular expression to extract files list
    file_pattern = re.search(r"files:\s*\[(.*?)\]", config_text, re.DOTALL)

    if file_pattern:
        files = file_pattern.group(1)
        # Split the list into individual file names and exclude .bin files
        file_list = [
            file.strip()
            for file in files.split(",")
            if not file.strip().endswith(".bin")
        ]
        return file_list
    else:
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Recursively process Jupyter notebooks with '# ASSIGNMENT CONFIG', move them to a solutions folder, and run otter assign."
    )
    parser.add_argument(
        "root_folder", type=str, help="Path to the root folder to process"
    )

    parser.add_argument(
        "--assignment-tag",
        type=str,
        help="assignment-tag used for calculating grades",
        default="Reading-Week-X",
    )

    parser.add_argument(
        "--require-key",
        type=bool,
        help="Require a key to be generated for the assignment",
        default=False,
    )

    args = parser.parse_args()
    processor = NotebookProcessor(
        root_folder=args.root_folder,
        assignment_tag=args.assignment_tag,
        require_key=args.require_key,
    )
    processor.process_notebooks()


if __name__ == "__main__":
    sys.exit(main())

