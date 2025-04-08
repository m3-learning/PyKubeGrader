import nbformat

from pykubegrader.build.build_folder import NotebookProcessor
from pykubegrader.build.notebooks.search import find_first_code_cell


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


def write_validation_token_cell(
        notebook_path: str, require_key: bool, **kwargs
    ) -> None:
        """
        Adds a new code cell at the top of a Jupyter notebook if require_key is True.

        Args:
            notebook_path (str): The path to the notebook file to modify.
            require_key (bool): Whether to add the validate_token cell.

        Returns:
            None
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
    # finds the first code cell
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