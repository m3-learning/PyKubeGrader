import nbformat


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