import nbformat

from pykubegrader.build.notebooks.io import read_notebook


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


def check_for_heading(notebook_path, search_strings, logger=None):
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
        notebook = read_notebook(notebook_path)
        for cell in notebook.cells:
            if cell.cell_type == "raw" and cell.source.startswith("#"):
                if any(
                    search_string in cell.source for search_string in search_strings
                ):
                    return True
    except Exception as e:
        if logger is not None:
            logger.print_and_log(f"Error reading notebook {notebook_path}: {e}")
        else:
            print(f"Error reading notebook {notebook_path}: {e}")
    return False


def has_assignment(notebook_path, *tags):
    """
    Determines if a Jupyter notebook contains any of the specified configuration tags.

    This method checks for the presence of specific content in a Jupyter notebook
    to identify whether it includes any of the required headings or tags.

    Args:
        notebook_path (str): The file path to the Jupyter notebook to be checked.
        *tags (str): Variable-length argument list of tags to search for.
                    Defaults to ("# ASSIGNMENT CONFIG", "# BEGIN MULTIPLE CHOICE").

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
    return check_for_heading(notebook_path, list(tags))


def extract_question_points(raw, i, _data, grade_=None):
    """
    Extracts point values and grade information from raw metadata.

    This method processes the 'points' field from raw metadata and converts it
    to a list of point values that can be assigned to individual questions.
    It also extracts grade information if present.

    Args:
        raw (list): A list of dictionaries containing raw metadata.
        i (int): The index of the current metadata entry in the raw list.
        _data (dict): A dictionary containing question data.
        grade_ (list, optional): A list to store grade information. Defaults to None.

    Returns:
        tuple: A tuple containing:
            - points_ (list): A list of point values for each question.
            - grade_ (list or None): A list containing grade information if present,
                otherwise None.
    """
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