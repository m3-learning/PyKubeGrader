import argparse
import json
import os

from nbformat.v4 import new_markdown_cell, new_notebook


class QuestionCollator:
    def __init__(self, root_folder: str, output_path: str):
        """
        Initializes the QuestionCollator with the root folder and output path.

        Args:
            root_folder (str): Path to the root folder containing the solution files.
            output_path (str): Path to save the collated notebook.
        """
        self.root_folder = root_folder
        self.output_path = output_path

    def find_solution_files(self):
        """
        Finds all files containing '_solution' in their names within the root folder.

        Returns:
            list: List of file paths.
        """
        solution_files = []
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                if "_solution" in file:
                    solution_files.append(os.path.join(root, file))
        return solution_files

    def extract_questions(self, file_path):
        """
        Extracts questions from a solution file and categorizes them by type.

        Args:
            file_path (str): Path to the solution file.

        Returns:
            dict: Dictionary of categorized questions.
        """
        with open(file_path, "r") as f:
            content = json.load(f)

        questions = {
            "multiple_choice": [],
            "select_many": [],
            "true_false": [],
            "other": [],
        }

        for cell in content["cells"]:
            if (
                cell["cell_type"] == "raw"
                and "# BEGIN MULTIPLE CHOICE" in cell["source"]
            ):
                questions["multiple_choice"].append(cell)
            elif cell["cell_type"] == "raw" and "# BEGIN SELECT MANY" in cell["source"]:
                questions["select_many"].append(cell)
            elif cell["cell_type"] == "raw" and "# BEGIN TF" in cell["source"]:
                questions["true_false"].append(cell)
            elif (
                cell["cell_type"] == "markdown"
                and "## question number:" in cell["source"]
            ):
                questions["other"].append(cell)

        return questions

    def create_collated_notebook(self, questions):
        """
        Creates a new notebook with questions organized by type.

        Args:
            questions (dict): Dictionary of categorized questions.

        Returns:
            Notebook: The collated notebook.
        """
        nb = new_notebook()

        # Add Multiple Choice Questions
        nb.cells.append(new_markdown_cell("# Multiple Choice Questions"))
        for q in questions["multiple_choice"]:
            nb.cells.append(new_markdown_cell(q["source"]))

        # Add Select Many Questions
        nb.cells.append(new_markdown_cell("# Select Many Questions"))
        for q in questions["select_many"]:
            nb.cells.append(new_markdown_cell(q["source"]))

        # Add True/False Questions
        nb.cells.append(new_markdown_cell("# True/False Questions"))
        for q in questions["true_false"]:
            nb.cells.append(new_markdown_cell(q["source"]))

        # Add Other Questions
        nb.cells.append(new_markdown_cell("# Other Questions"))
        for q in questions["other"]:
            nb.cells.append(new_markdown_cell(q["source"]))

        return nb

    def save_notebook(self, nb):
        """
        Saves the collated notebook to the specified output path.

        Args:
            nb (Notebook): The notebook to save.
        """
        import nbformat

        with open(self.output_path, "w") as f:
            nbformat.write(nb, f)

    def collate_questions(self):
        """
        Collates questions from all solution files and saves them to a new notebook.
        """
        solution_files = self.find_solution_files()
        all_questions = {
            "multiple_choice": [],
            "select_many": [],
            "true_false": [],
            "other": [],
        }

        for file in solution_files:
            questions = self.extract_questions(file)
            all_questions["multiple_choice"].extend(questions["multiple_choice"])
            all_questions["select_many"].extend(questions["select_many"])
            all_questions["true_false"].extend(questions["true_false"])
            all_questions["other"].extend(questions["other"])

        collated_nb = self.create_collated_notebook(all_questions)
        self.save_notebook(collated_nb)
        print(f"Collated notebook saved to {self.output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Collate questions from solution files into a single notebook."
    )
    parser.add_argument(
        "root_folder",
        type=str,
        help="Path to the root folder containing solution files",
    )
    parser.add_argument(
        "output_path", type=str, help="Path to save the collated notebook"
    )

    args = parser.parse_args()
    collator = QuestionCollator(
        root_folder=args.root_folder, output_path=args.output_path
    )
    collator.collate_questions()


if __name__ == "__main__":
    import sys

    sys.exit(main())
