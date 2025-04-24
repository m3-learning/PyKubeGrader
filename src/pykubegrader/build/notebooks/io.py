import nbformat


def write_notebook(notebook, save_path):
    with open(save_path, "w") as nb_file:
        nbformat.write(notebook, nb_file)


def read_notebook(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)
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

    Raises:
        IndexError: If the cell_index is out of range for the notebook's cells.
        KeyError: If the 'cells' key is not present in the notebook structure.
    """
    notebook = read_notebook(notebook_path)
    return notebook["cells"][cell_index]["source"]
