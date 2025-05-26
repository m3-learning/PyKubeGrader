import nbformat


def write_notebook(notebook, save_path):
    with open(save_path, "w") as nb_file:
        nbformat.write(notebook, nb_file)


def read_notebook(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=nbformat.NO_CONVERT)
    return notebook


def get_cell_source(notebook_path, cell_index):
    """
    Retrieves the source code of a specific cell from a Jupyter notebook.

    This function reads a Jupyter notebook from the given path and returns the source code
    of the cell at the specified index.

    Args:
        notebook_path (str): The file path to the Jupyter notebook.
        cell_index (int): The index of the cell whose source code is to be retrieved.

    Returns:
        str: The source code of the specified cell.
    """
    notebook = read_notebook(notebook_path)
    
    if "cells" in notebook and len(notebook["cells"]) > cell_index:
            return notebook["cells"][cell_index]
    else:
        return None


def modify_notebook_cell(notebook_path, cell_index, new_source):
    """
    Modifies the source code of a specific cell in a Jupyter notebook.

    This function reads a Jupyter notebook from the specified path, updates the source
    code of the cell at the given index, and saves the changes back to the notebook.

    Args:
        notebook_path (str): The file path to the Jupyter notebook.
        cell_index (int): The index of the cell to be modified.
        new_source (str or list of str): The new source code to replace the cell's content.

    Raises:
        IndexError: If the cell_index is out of range for the notebook's cells.
    """
    notebook = read_notebook(notebook_path)

    # Check if the cell index is valid
    if cell_index >= len(notebook.cells) or cell_index < 0:
        raise IndexError(f"Cell index {cell_index} is out of range for this notebook.")

    # Replace the source code of the specified cell
    notebook.cells[cell_index]["source"] = new_source

    # Save the notebook
    write_notebook(notebook, notebook_path)
