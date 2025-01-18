import argparse
import os
import nbformat as nbf


class MarkdownToNotebook:
    def __init__(self, markdown_file: str):
        """
        Initializes the MarkdownToNotebook converter with the Markdown file path.

        Args:
            markdown_file (str): Path to the Markdown file to convert.
        """
        self.markdown_file = markdown_file

    def convert_and_save(self):
        """
        Converts the Markdown file into a Jupyter Notebook and saves it with the same name.
        """
        if not os.path.exists(self.markdown_file):
            print(f"Error: File '{self.markdown_file}' does not exist.")
            return

        notebook_name = os.path.splitext(self.markdown_file)[0] + ".ipynb"

        with open(self.markdown_file, "r") as f:
            content = f.read()

        # Split content into lines
        lines = content.splitlines()
        nb = nbf.v4.new_notebook()
        cells = []
        current_cell = ""
        current_type = None

        for line in lines:
            if line.startswith("# %%"):
                if current_cell:  # Save the previous cell
                    if current_type == "markdown":
                        cells.append(nbf.v4.new_markdown_cell(current_cell.strip()))
                    elif current_type == "code":
                        cells.append(nbf.v4.new_code_cell(current_cell.strip()))
                    elif current_type == "raw":
                        cells.append(nbf.v4.new_raw_cell(current_cell.strip()))

                # Start a new cell
                current_cell = ""
                if "[markdown]" in line:
                    current_type = "markdown"
                elif "# BEGIN" in line or "# END" in line:
                    current_type = "raw"
                else:
                    current_type = "code"
            else:
                # Append lines to the current cell
                if current_type == "markdown" and line.startswith("# "):
                    current_cell += line[2:] + "\n"
                else:
                    current_cell += line + "\n"

        # Save the last cell
        if current_cell:
            if current_type == "markdown":
                cells.append(nbf.v4.new_markdown_cell(current_cell.strip()))
            elif current_type == "code":
                cells.append(nbf.v4.new_code_cell(current_cell.strip()))
            elif current_type == "raw":
                cells.append(nbf.v4.new_raw_cell(current_cell.strip()))

        nb["cells"] = cells

        # Write the notebook
        with open(notebook_name, "w") as f:
            nbf.write(nb, f)

        print(f"Notebook saved as: {notebook_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Markdown file with Jupyter-style cells into a Jupyter Notebook."
    )
    parser.add_argument(
        "markdown_file", type=str, help="Path to the Markdown file to convert."
    )

    args = parser.parse_args()
    converter = MarkdownToNotebook(markdown_file=args.markdown_file)
    converter.convert_and_save()


if __name__ == "__main__":
    main()
