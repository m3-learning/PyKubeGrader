import nbformat

from pykubegrader.build.build_folder import NotebookProcessor, sanitize_string
from pykubegrader.build.config import DisplayQuestionCode
from pykubegrader.build.notebooks.search import find_first_code_cell


def remove_assignment_config_cells(notebook_path):
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
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Create the new code cell
        if kwargs.get("assignment_tag", None):
            new_cell = nbformat.v4.new_code_cell(
                "from pykubegrader.tokens.validate_token import validate_token\n"
                f"validate_token('type the key provided by your instructor here', assignment = '{kwargs.get('assignment_tag')}')\n"
            )
        else:
            new_cell = nbformat.v4.new_code_cell(
                "from pykubegrader.tokens.validate_token import validate_token\n"
                "validate_token('type the key provided by your instructor here')\n"
            )

        # Add the new cell to the top of the notebook
        notebook.cells.insert(0, new_cell)

        # Save the modified notebook
        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)


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
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        # Prepare the validation code
        validation_code = f"validate_token(assignment = '{assignment_tag}')\n"

        # Modify the first cell if it's a code cell, otherwise insert a new one
        if notebook.cells and notebook.cells[0].cell_type == "code":
            notebook.cells[0].source = validation_code + "\n" + notebook.cells[0].source
        else:
            new_cell = nbformat.v4.new_code_cell(validation_code)
            notebook.cells.insert(0, new_cell)

        # Save the modified notebook
        with open(notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(notebook, f)


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


def write_initialization_code(
    notebook_path,
    week,
    assignment_type,
    require_key=False,
    **kwargs,
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
    import_text = "# You must make sure to run all cells in sequence using shift + enter or you might encounter errors\n"
    import_text += "from pykubegrader.initialize import initialize_assignment\n"
    import_text += f'\nresponses = initialize_assignment("{os.path.splitext(os.path.basename(notebook_path))[0]}", "{week}", "{assignment_type}" )\n'
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
            "source": DisplayQuestionCode.build_code(file_name_ipynb, dict_),
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
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(notebook_data, f, indent=2)
            
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
  