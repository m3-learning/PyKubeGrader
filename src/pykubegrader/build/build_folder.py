from dataclasses import dataclass, field
import os
import shutil
import nbformat
import subprocess
import sys
import argparse
import logging
import json
import re

@dataclass
class NotebookProcessor:
    root_folder: str
    solutions_folder: str = field(init=False)
    verbose: bool = False
    log: bool = True

    def __post_init__(self):
        # Define the folder to store solutions
        self.solutions_folder = os.path.join(self.root_folder, "_solutions")
        os.makedirs(self.solutions_folder, exist_ok=True)
        
        # Configure logging
        log_file_path = os.path.join(self.solutions_folder, "notebook_processor.log")
        logging.basicConfig(
            filename=log_file_path,  # Name of the log file
            level=logging.INFO,  # Logging level
            format="%(asctime)s - %(levelname)s - %(message)s"  # Log format
        )

        global logger
        logger = logging.getLogger(__name__)  # Get a logger instance
        self.logger = logger

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
        Print a message and log it to the logger.
        """
        if self.verbose:
            print(message)
        
        if self.log:    
            self.logger.info(message)


    def _process_single_notebook(self, notebook_path):
        
        logging.info(f"Processing notebook: {notebook_path}")
        notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
        notebook_subfolder = os.path.join(self.solutions_folder, notebook_name)
        os.makedirs(notebook_subfolder, exist_ok=True)

        new_notebook_path = os.path.join(notebook_subfolder, os.path.basename(notebook_path))
        
        # makes a temp copy of the notebook
        temp_notebook_path = os.path.join(notebook_subfolder, f"{notebook_name}_temp.ipynb")
        shutil.copy(notebook_path, temp_notebook_path)
        
        # Determine the path to the autograder folder
        autograder_path = os.path.join(notebook_subfolder,f"dist/autograder/")
        os.makedirs(autograder_path, exist_ok=True)
        
        if os.path.abspath(notebook_path) != os.path.abspath(new_notebook_path):
            shutil.move(notebook_path, new_notebook_path)
            self._print_and_log(f"Moved: {notebook_path} -> {new_notebook_path}")
        else:
            self._print_and_log(f"Notebook already in destination: {new_notebook_path}")
            
        if self.has_assignment(temp_notebook_path, '# BEGIN MULTIPLE CHOICE'):
            self._print_and_log(f"Notebook {temp_notebook_path} has multiple choice questions")
            
            # Extract raw cells and multiple choice questions
            raw = extract_raw_cells(temp_notebook_path)
            
            # Extract multiple choice questions
            data = extract_MCQ(temp_notebook_path)
            
            # determine the output file path
            solution_path = f"{new_notebook_path.strip('.ipynb')}.py"
            
            # Generate the solution file
            self.generate_solution_MCQ(raw, data, output_file=solution_path)
            
        
        if self.has_assignment(temp_notebook_path, "# ASSIGNMENT CONFIG"):
            self.run_otter_assign(temp_notebook_path, os.path.join(notebook_subfolder, "dist"))
            student_notebook = os.path.join(notebook_subfolder, "dist", "student", f"{notebook_name}.ipynb")
            self.clean_notebook(student_notebook)
            shutil.copy(student_notebook, self.root_folder)
            self._print_and_log(f"Copied and cleaned student notebook: {student_notebook} -> {self.root_folder}")
            
     
        # Move the solution file to the autograder folder
        if 'solution_path' in locals():
            shutil.move(solution_path, autograder_path)
        
        # Remove the temp copy of the notebook
        os.remove(temp_notebook_path)

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
            tags = ["# ASSIGNMENT CONFIG"]

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
            NotebookProcessor.remove_test_postfix(dist_folder)
            
        except subprocess.CalledProcessError as e:
            logger.info(f"Error running `otter assign` for {notebook_path}: {e}")
        except Exception as e:
            logger.info(f"Unexpected error during `otter assign` for {notebook_path}: {e}")

    @staticmethod
    def generate_solution_MCQ(raw, data, output_file="output.py"):
        """
        Generates a Python file with a predefined structure based on the input dictionary.

        Args:
            raw (dict): A dictionary with raw metadata extracted from the notebook.
            data (dict): A nested dictionary with question metadata.
            output_file (str): Path to the output Python file.
        """
        with open(output_file, "w", encoding="utf-8") as f:
            # Write imports
            f.write("from typing import Any\n\n")

            # Calculate total points (assuming 2 points per question)
            total_questions = len(data)
            if len(raw["points"]) == 1:
                points_ = f"[{raw['points']}] * {total_questions}"
            else:
                points_ = raw["points"]

            f.write(f"points: list[int] = {points_}\n\n")

            # Write solutions dictionary
            f.write("solution: dict[str, Any] = {\n")
            for title, question_data in data.items():
                key = f"q{raw['question number']}-{question_data['subquestion_number']}-{title}"
                solution = question_data["solution"]
                f.write(f'    "{key}": "{solution}",\n')
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
                    title_match = re.search(r"^##\s*(.+)", markdown_content, re.MULTILINE)
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
    def remove_test_postfix(dist_folder, suffix="_temp"):
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

def extract_raw_cells(ipynb_file):
        """
        Extracts raw cells from a Jupyter Notebook file.

        Args:
            ipynb_file (str): Path to the .ipynb file.

        Returns:
            list of str: Contents of all raw cells.
        """
        try:
            with open(ipynb_file, "r", encoding="utf-8") as f:
                notebook_data = json.load(f)

            # Extract raw cell content
            raw_cells = [
                cell["source"]
                for cell in notebook_data.get("cells", [])
                if cell.get("cell_type") == "raw"
            ]

            # Join multiline sources into single strings
            return parse_raw(["".join(cell) for cell in raw_cells])

        except FileNotFoundError:
            print(f"File {ipynb_file} not found.")
            return []
        except json.JSONDecodeError:
            print("Invalid JSON in notebook file.")
            return []

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
                title_match = re.search(r"^##\s*(.+)", markdown_content, re.MULTILINE)
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

def check_for_heading(notebook_path, search_strings):
    """
    Checks if a Jupyter notebook contains a heading cell whose source matches any of the given strings.
    """
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == "raw" and cell.source.startswith("#"):
                    if any(search_string in cell.source for search_string in search_strings):
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
                print(f"Removed cell: {cell.source.strip()[:50]}...")

        notebook.cells = cleaned_cells

        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)
        logger.info(f"Cleaned notebook: {notebook_path}")

    except Exception as e:
        logger.info(f"Error cleaning notebook {notebook_path}: {e}")
        
def parse_raw(raw_list):
    """
    Converts a list of raw strings into key-value pairs for multiple-choice metadata.

    Args:
        raw_list (list of str): List containing raw strings of multiple-choice metadata.

    Returns:
        dict: Dictionary of extracted key-value pairs.
    """
    metadata = {}

    for line in raw_list:
        # Check if line contains # BEGIN MULTIPLE CHOICE
        if line.startswith("# BEGIN MULTIPLE CHOICE"):
            lines = line.split("\n")
            for item in lines:
                if item.startswith("##"):
                    # Extract key and value from lines
                    key, value = item[3:].split(":", 1)
                    metadata[key.strip()] = value.strip()

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Recursively process Jupyter notebooks with '# ASSIGNMENT CONFIG', move them to a solutions folder, and run otter assign."
    )
    parser.add_argument("root_folder", type=str, help="Path to the root folder to process")
    args = parser.parse_args()

    processor = NotebookProcessor(args.root_folder)
    processor.process_notebooks()


if __name__ == "__main__":
    sys.exit(main())
