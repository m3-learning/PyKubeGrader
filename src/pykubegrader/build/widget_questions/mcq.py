from pykubegrader.build.build_folder import NotebookProcessor, WidgetQuestionParser


import json

from pykubegrader.build.widget_questions.utils import extract_question


def extract(ipynb_file):
    """
    Extracts multiple-choice questions from markdown cells within sections marked by
    `# BEGIN MULTIPLE CHOICE` and `# END MULTIPLE CHOICE`.

    Args:
        ipynb_file (str): Path to the .ipynb file.

    Returns:
        list: A list of dictionaries, where each dictionary corresponds to questions within
            a section. Each dictionary contains parsed questions with details like
            'name', 'subquestion_number', 'question_text', 'OPTIONS', and 'solution'.
    """
    try:

        # Load the notebook file
        with open(ipynb_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        cells = notebook_data.get("cells", [])

        parser = WidgetQuestionParser()

        for cell in cells:
            if cell.get("cell_type") == "raw":
                # Check for the start and end labels in raw cells
                raw_content = "".join(cell.get("source", []))

                flag = parser.process_raw_cell(raw_content)

                if flag:
                    continue

            if parser.within_section and cell.get("cell_type") == "markdown":
                # Parse markdown cell content
                markdown_content = "".join(cell.get("source", []))

                # Extract title (## heading)
                title = NotebookProcessor.extract_widget_title(markdown_content)

                if title:
                    parser.increment_subquestion_number()

                    # Extract question text enable multiple lines
                    question_text = extract_question(markdown_content)

                    # Extract OPTIONS (lines after #### options)
                    options = NotebookProcessor.extract_widget_options(markdown_content)

                    # Extract solution (line after #### SOLUTION)
                    solution = NotebookProcessor.extract_solutions(markdown_content)

                    #TODO: better to have as part of a class
                    # Add question details to the current section
                    parser.current_section[title] = {
                        "name": title,
                        "subquestion_number": parser.subquestion_number,
                        "question_text": question_text,
                        "OPTIONS": options,
                        "solution": solution,
                    }

        return parser.sections

    except FileNotFoundError:
        print(f"File {ipynb_file} not found.")
        return []
    except json.JSONDecodeError:
        print("5 Invalid JSON in notebook file.")
        return []