from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
import nbformat

from pykubegrader.build.config import DisplayQuestionCode, InitializationCell
from pykubegrader.build.notebooks.io import read_notebook, write_notebook
from pykubegrader.build.notebooks.search import find_first_code_cell
from pykubegrader.build.widget_questions.utils import (
    sanitize_string_for_python_variable,
)


def remove_assignment_config_cells(notebook_path: str) -> None:
    """
    Remove cells containing "# ASSIGNMENT CONFIG" from a Jupyter notebook.

    This function reads a Jupyter notebook from the specified path, filters out any cells
    that contain the string "# ASSIGNMENT CONFIG" in their source, and then saves the
    updated notebook back to the same path.

    Args:
        notebook_path (str): The path to the Jupyter notebook file to be modified.

    Returns:
        None

    Example:
        remove_assignment_config_cells("path/to/notebook.ipynb")
    """

    # Read the notebook
    notebook = read_notebook(notebook_path)

    # Filter out cells containing "# ASSIGNMENT CONFIG"
    notebook.cells = [
        cell
        for cell in notebook.cells
        if "# ASSIGNMENT CONFIG" not in cell.get("source", "")
    ]

    # Save the updated notebook
    write_notebook(notebook, notebook_path)


def write_validation_token_cell(
    notebook_path: str, require_key: bool, **kwargs
) -> None:
    """
    Adds a new code cell at the top of a Jupyter notebook if require_key is True.

    This function modifies a Jupyter notebook by inserting a new code cell at the top.
    The new cell contains a call to the `validate_token` function, which is used to
    validate a token provided by the instructor. The function only performs this action
    if the `require_key` parameter is set to True.

    Args:
        notebook_path (str): The path to the notebook file to modify.
        require_key (bool): Whether to add the validate_token cell.
        **kwargs: Additional keyword arguments that may include:
            - assignment_tag (str, optional): A tag for the assignment, which will be
              included in the validate_token call if provided.

    Returns:
        None

    Example:
        write_validation_token_cell("path/to/notebook.ipynb", True, assignment_tag="Week1")

    Behavior:
        - If `require_key` is False, the function will print a message and make no changes.
        - If `require_key` is True, a new code cell is added at the top of the notebook.
        - The new cell will import the `validate_token` function and call it with a placeholder
          for the key and the optional assignment tag.

    Raises:
        None: This function handles exceptions internally, if any arise from file operations.
    """
    if not require_key:
        print("require_key is False. No changes made to the notebook.")
        return

    write_validation_block(
        notebook_path,
        require_key,
        assignment_tag=kwargs.get("assignment_tag", None),
    )

    # Load the notebook
    notebook = read_notebook(notebook_path)
    
    validate_token = ValidateToken(kwargs).validate_token_line

    new_cell = nbformat.v4.new_code_cell(validate_token)

    # Add the new cell to the top of the notebook
    notebook.cells.insert(0, new_cell)

    # Save the modified notebook
    write_notebook(notebook, notebook_path)


def write_validation_block(
    notebook_path: str, require_key: bool, assignment_tag=None, **kwargs
) -> None:
    """
    Modifies the first code cell of a Jupyter notebook to add the validate_token call if require_key is True.

    Args:
        notebook_path (str): The path to the notebook file to modify.
        require_key (bool): Whether to add the validate_token cell.

    Returns:
        None
    """
    if not require_key:
        return

    # Load the notebook
    notebook = read_notebook(notebook_path)

    # Prepare the validation code
    validation_code = f"validate_token(assignment = '{assignment_tag}')\n"

    # Modify the first cell if it's a code cell, otherwise insert a new one
    if notebook.cells and notebook.cells[0].cell_type == "code":
        notebook.cells[0].source = validation_code + "\n" + notebook.cells[0].source
    else:
        new_cell = nbformat.v4.new_code_cell(validation_code)
        notebook.cells.insert(0, new_cell)

    # Save the modified notebook
    write_notebook(notebook, notebook_path)


def replace_cell_source(notebook_path: str, cell_index: int, new_source: str) -> None:
    """
    Replace the source code of a specific Jupyter notebook cell.

    Args:
        notebook_path (str): The path to the Jupyter notebook file.
        cell_index (int): Index of the cell to be modified (0-based).
        new_source (str): New source code to replace the cell's content.

    Returns:
        None

    Raises:
        IndexError: If the cell index is out of range for the notebook.
    """
    # Load the notebook
    notebook = read_notebook(notebook_path)

    # Check if the cell index is valid
    if cell_index >= len(notebook.cells) or cell_index < 0:
        raise IndexError(f"Cell index {cell_index} is out of range for this notebook.")

    # Replace the source code of the specified cell
    notebook.cells[cell_index]["source"] = new_source

    # Save the notebook
    write_notebook(notebook, notebook_path)


def write_initialization_code(
    notebook_path: str,
    week: str,
    assignment_type: str,
    require_key: bool = False,
    **kwargs: dict,
):
    """
    Inserts initialization code into the first code cell of a Jupyter notebook.

    This function modifies the first code cell of the specified notebook to include
    initialization code necessary for the assignment. If `require_key` is True, it also
    adds a validation token cell.

    Args:
        notebook_path (str): The path to the Jupyter notebook file.
        week (str): The week identifier for the assignment.
        assignment_type (str): The type of the assignment.
        require_key (bool, optional): If True, adds a validation token cell. Defaults to False.
        **kwargs: Additional keyword arguments, including:
            - assignment_tag (str, optional): The tag for the assignment, used if `require_key` is True.

    Returns:
        None
    """
    # Find the first code cell
    index, cell = find_first_code_cell(notebook_path)
    cell = cell["source"]
    import_text = InitializationCell(
        notebook_path, week, assignment_type
    ).initialization_cell
    cell = f"{import_text}\n" + cell
    replace_cell_source(notebook_path, index, cell)

    if require_key:
        write_validation_token_cell(
            notebook_path,
            require_key,
            assignment_tag=kwargs.get("assignment_tag", None),
        )


def replace_cells_between_markers(data, markers, ipynb_file, output_file):
    """
    Replace cells between specified markers in a Jupyter Notebook (.ipynb file) with new content.

    This function identifies a block of cells in a Jupyter Notebook that are enclosed between
    specified BEGIN and END markers. It replaces these cells with new content provided in the
    form of replacement cells and writes the updated notebook to the specified output file.

    Args:
        data (list): A list of dictionaries, each containing data for constructing replacement cells.
        markers (tuple): A tuple containing two strings that denote the BEGIN and END markers.
        ipynb_file (str): The file path to the input Jupyter Notebook.
        output_file (str): The file path where the modified Jupyter Notebook will be saved.

    Returns:
        None: The function writes the modified notebook to the output file and does not return a value.
    """
    begin_marker, end_marker = markers
    file_name_ipynb = ipynb_file.split("/")[-1].replace("_temp.ipynb", "")

    file_name_ipynb = sanitize_string_for_python_variable(file_name_ipynb)

    # Iterate over each set of replacement data
    for data_ in data:
        dict_ = data_[next(iter(data_.keys()))]

        # Create the replacement cells
        replacement_cells = {
            "cell_type": "code",
            "metadata": {},
            "source": DisplayQuestionCode.build_code(file_name_ipynb, dict_),
            "outputs": [],
            "execution_count": None,
        }

        # Process the notebook cells
        new_cells = []
        inside_markers = False
        done = False

        # Load the notebook data
        notebook_data = read_notebook(ipynb_file)

        # Iterate over each cell in the notebook
        for cell in notebook_data["cells"]:
            # If the cell is a raw cell and not done, check if it contains the begin marker
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
        write_notebook(notebook_data, output_file)


@dataclass
class AddKeyRequirementImportBaseClass(ABC):
    @property
    @abstractmethod
    def code_cell(self):
        pass

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

        return self.code_cell


def ensure_imports(output_file, header_lines):
    """
    Ensures that the specified header lines are included at the beginning of the file.

    Parameters:
        output_file (str): The file path to be checked and potentially modified.
        header_lines (list of str): The lines that need to be present at the start of the file.

    Returns:
        str: The content of the file excluding the header lines.
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


def insert_into_source(
    cell_source: list[str], lines_to_insert: list[str], flag_to_insert: str
) -> list[str]:
    """
    Inserts a list of lines into a source list at a specified flag.

    This function searches for a specific flag within the cell source and inserts
    the provided lines immediately after the line containing the flag. If the flag
    is not found, a ValueError is raised.

    Args:
        cell_source (list[str]): The original list of source lines where the insertion will occur.
        lines_to_insert (list[str]): The lines to be inserted into the source.
        flag_to_insert (str): The flag indicating where to insert the lines.

    Returns:
        list[str]: The modified list of source lines with the new lines inserted.

    Raises:
        ValueError: If the flag is not found in the cell source.
    """
    for i, line in enumerate(cell_source):
        if flag_to_insert in line:
            # Insert the imports immediately after the current line
            cell_source[i + 1 : i + 1] = ["\n"] + lines_to_insert

            return cell_source  # Exit the loop once the imports are inserted

    raise ValueError("End of test configuration not found")


def add_text_after_octothorpe(
    markdown_source: list[str], insert_text: str, hash_prefix: str = "## "
) -> list[str]:
    """
    Inserts the specified text immediately after the first occurrence of the given hash prefix
    in the first line of the markdown source that starts with the hash prefix.

    This function is useful for modifying markdown cells by appending additional information
    to headings or subheadings.

    Args:
    - markdown_source (list of str): A list of strings representing the lines of a markdown cell.
    - insert_text (str): The text to be inserted after the hash prefix.
    - hash_prefix (str, optional): The prefix to look for at the start of a line. Defaults to "## ".

    Returns:
    - list of str: The modified markdown cell content with the inserted text.

    Example:
    Given a markdown source with lines starting with "##", this function will add the insert_text
    immediately after the first "##" in the first such line.
    """
    modified_source = []
    inserted = False

    for line in markdown_source:
        if not inserted and line.startswith(hash_prefix):
            modified_source.append(
                f"{hash_prefix}{insert_text} {line[len(hash_prefix) :]}"
            )  # Insert text after hash_prefix
            inserted = True  # Ensure it only happens once
        else:
            modified_source.append(line)

    return modified_source


def replace_notebook_cell_text(
    notebook_data: nbformat.NotebookNode, old_text: str, new_text: str
) -> None:
    """
    Replaces occurrences of a specified text within the source of each cell in a Jupyter Notebook.

    This function iterates over all cells in the provided notebook data and replaces all instances
    of `old_text` with `new_text` in the cell's source code.

    Args:
    - notebook_data (nbformat.NotebookNode): The notebook data containing cells to be processed.
    - old_text (str): The text to be replaced in the cell sources.
    - new_text (str): The text to replace the old text with in the cell sources.

    Returns:
    - None: This function modifies the notebook data in place and does not return a value.
    """
    for cell in notebook_data.get("cells", []):
        if "source" in cell:
            # Replace occurrences of old_text in the cell source
            cell["source"] = [
                line.replace(old_text, new_text) for line in cell["source"]
            ]
