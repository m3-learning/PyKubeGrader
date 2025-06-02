import nbformat

def write_notebook(notebook: nbformat.NotebookNode, save_path: str) -> None:
    """
    Writes a Jupyter notebook to a specified file path.

    This function takes a notebook object and writes it to the given file path
    in the Jupyter notebook format.

    Args:
        notebook (nbformat.NotebookNode): The notebook object to be written to a file.
        save_path (str): The file path where the notebook will be saved.

    Returns:
        None
    """
    with open(save_path, "w") as nb_file:
        nbformat.write(notebook, nb_file)


def read_notebook(input_file: str) -> nbformat.NotebookNode:
    """
    Reads a Jupyter notebook from a specified file path and returns it as a notebook object.

    This function opens the specified file, reads its contents, and converts them into a
    Jupyter notebook object using the nbformat library.

    Args:
        input_file (str): The file path to the Jupyter notebook to be read.

    Returns:
        nbformat.NotebookNode: The notebook object representing the contents of the file.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=nbformat.NO_CONVERT)
    return notebook


def get_cell_source(notebook_path: str, cell_index: int) -> str | None:
    """
    Retrieve the source code of a specific cell from a Jupyter notebook.

    This function opens a Jupyter notebook from the specified file path and extracts the
    source code of the cell located at the given index. If the index is out of range or
    the notebook does not contain any cells, the function returns None.

    Args:
        notebook_path (str): The file path to the Jupyter notebook.
        cell_index (int): The zero-based index of the cell whose source code is to be retrieved.

    Returns:
        str | None: The source code of the specified cell if it exists, otherwise None.
    """
    notebook = read_notebook(notebook_path)
    
    if "cells" in notebook and len(notebook["cells"]) > cell_index:
        return notebook["cells"][cell_index]
    else:
        return None


def modify_notebook_cell(notebook_path: str, cell_index: int, new_source: str | list[str]) -> None:
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
