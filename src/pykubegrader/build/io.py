import json
import os


def remove_file_suffix(dist_folder, suffix="_temp", logger = None):
    if logger is not None:
        logger.print_and_log(f"Removing postfix '{suffix}' from filenames in {dist_folder}")
    for root, _, files in os.walk(dist_folder):
        for file in files:
            if suffix in file:

                old_file_path = os.path.join(root, file)
                new_file_path = os.path.join(root, file.replace(suffix, ""))
                os.rename(old_file_path, new_file_path)

                if logger is not None:
                    logger.print_and_log(f"Renamed: {old_file_path} -> {new_file_path}")


def get_notebooks_recursively(root_folder, **kwargs):
    """
    Recursively retrieves all Jupyter notebook files (.ipynb) from the root folder and its subfolders.

    This method walks through the directory tree starting from the root folder, identifies all files
    with a .ipynb extension, and collects their paths in a list.

    Returns:
        list: A list of file paths to Jupyter notebook files found within the root folder and its subfolders.
    """
    extension = kwargs.get("extension", ".ipynb")

    files = []

    # Walk through the root folder and its subfolders
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # Check if the file is a Jupyter notebook
            if filename.endswith(extension):
                notebook_path = os.path.join(dirpath, filename)
                files.append(notebook_path)
    return files


def write_JSON(**kwargs):
    """
    Writes the provided information to a JSON file.

    This method takes in keyword arguments to specify the base folder, information to be written,
    and the indentation level for the JSON file. It constructs the file path for the JSON file
    and writes the information to it.

    Args:
        **kwargs: Arbitrary keyword arguments.
            - base_folder (str): The base folder where the JSON file will be saved.
            - information (dict): The information to be written to the JSON file.
            - indent (int): The indentation level for the JSON file (default is 2).

    Returns:
        None
    """
    base_folder = kwargs.get("base_folder", None)
    information = kwargs.get("information", None)
    indent = kwargs.get("indent", 2)

    path = os.path.join(base_folder, "total_points.json")

    with open(path, "w") as json_file:
        json.dump(
            information, json_file, indent=indent
        )


def check_if_file_in_folder(folder, file):
    """
    Checks if a specific file exists within a given folder or its subdirectories.

    Args:
        folder (str): The path to the folder to search within.
        file (str): The name of the file to search for.

    Returns:
        bool: True if the file is found, False otherwise.
    """
    for root, _, files in os.walk(folder):
        if file in files:
            return True
    return False