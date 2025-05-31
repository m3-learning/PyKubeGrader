from pykubegrader.build.notebooks.io import read_notebook, write_notebook


def lock_cells_from_students(notebook_path: str, logger=None) -> None:
    """
    Processes a Jupyter notebook to remove specific cells and update the metadata of Markdown and code cells.

    This function reads a notebook from the given path, removes cells containing specific submission-related
    text, and updates the metadata of Markdown cells to make them non-editable and non-deletable. It also
    tags code cells to skip execution. The modified notebook is then saved back to the original path.

    Args:
        notebook_path (str): The file path to the Jupyter notebook to be processed.
        logger (optional): A logger object for logging messages. If not provided, messages will be printed.

    Raises:
        Exception: If an error occurs during the processing of the notebook, it will be logged or printed.
    """
    try:
        notebook = read_notebook(notebook_path)

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
                (f"Removed cell: {cell.source.strip()[:50]}...")

        notebook.cells = cleaned_cells

        write_notebook(notebook, notebook_path)

        if logger is not None:
            logger.print_and_log(f"Cleaned notebook: {notebook_path}")
        else:
            print(f"Cleaned notebook: {notebook_path}")

    except Exception as e:
        if logger is not None:
            logger.print_and_log(f"Error cleaning notebook {notebook_path}: {e}")
        else:
            print(f"Error cleaning notebook {notebook_path}: {e}")