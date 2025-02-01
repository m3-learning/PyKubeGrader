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

    def find_solution_folders(self):
        """
        Finds all immediate subdirectories inside '_solution*' folders that contain notebooks.

        Returns:
            list: List of folder paths containing notebooks.
        """
        solution_folders = []

        # Look for _solution* folders inside the root_folder
        for dir_name in os.listdir(self.root_folder):
            solution_folder_path = os.path.join(self.root_folder, dir_name)

            if os.path.isdir(solution_folder_path) and dir_name.startswith("_solution"):
                print(f"Found solution folder: {solution_folder_path}")  # Debug output

                # Now, look for immediate subdirectories inside this _solution* folder
                for sub_dir in os.listdir(solution_folder_path):
                    sub_dir_path = os.path.join(solution_folder_path, sub_dir)

                    if os.path.isdir(sub_dir_path):
                        # Check if this subdirectory contains at least one .ipynb file
                        if any(f.endswith(".ipynb") for f in os.listdir(sub_dir_path)):
                            solution_folders.append(sub_dir_path)

        print(f"Final list of solution subfolders: {solution_folders}")  # Debug output
        return solution_folders

    def extract_questions(self, folder_path):
        """
        Extracts questions from all notebooks in the solution folder.

        Args:
            folder_path (str): Path to the solution folder.

        Returns:
            dict: Dictionary of categorized questions.
        """
        questions = {
            "multiple_choice": [],
            "select_many": [],
            "true_false": [],
            "other": [],
        }

        for file in os.listdir(folder_path):
            if file.endswith(".ipynb"):
                file_path = os.path.join(folder_path, file)
                print(
                    f"Processing notebook: {file_path}"
                )  # Print the full path of the notebook
                with open(file_path, "r") as f:
                    content = json.load(f)

                # Track whether we are inside a question block
                in_question_block = False
                current_question_content = []

                for cell in content["cells"]:
                    if "# BEGIN MULTIPLE CHOICE" in cell["source"]:
                        # Start of a question block
                        in_question_block = True
                        current_question_content = []
                    elif "# END MULTIPLE CHOICE" in cell["source"]:
                        # End of a question block
                        in_question_block = False
                        if current_question_content:
                            questions["multiple_choice"].append(
                                {"source": "\n".join(current_question_content)}
                            )
                        current_question_content = []
                    elif in_question_block and cell["cell_type"] == "markdown":
                        # Capture markdown cells within the question block
                        current_question_content.append(cell["source"])

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
        Collates questions from all solution folders and saves them to a new notebook.
        """
        solution_folders = self.find_solution_folders()
        all_questions = {
            "multiple_choice": [],
            "select_many": [],
            "true_false": [],
            "other": [],
        }

        for folder in solution_folders:
            questions = self.extract_questions(folder)
            all_questions["multiple_choice"].extend(questions["multiple_choice"])
            all_questions["select_many"].extend(questions["select_many"])
            all_questions["true_false"].extend(questions["true_false"])
            all_questions["other"].extend(questions["other"])

        collated_nb = self.create_collated_notebook(all_questions)
        self.save_notebook(collated_nb)
        print(f"Collated notebook saved to {self.output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Collate questions from solution folders into a single notebook."
    )
    parser.add_argument(
        "root_folder",
        type=str,
        help="Path to the root folder containing solution folders",
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
