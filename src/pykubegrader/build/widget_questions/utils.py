import json
import re

from pykubegrader.build.build_folder import WidgetQuestionParser

def extract_question(text):
    
    #TODO: this was the original for for TF
    # TODO: Delete if not needed
    # question_text_match = re.search(
    #                             r"^###\s*\*\*(.+)\*\*", markdown_content, re.MULTILINE
    #                         )
    
    # Regular expression to capture the multiline title
    match = re.search(r"###\s+(.*?)\s+####", text, re.DOTALL)
    if match:
        # Stripping unnecessary whitespace and asterisks
        return match.group(1).strip().strip("**")
    return None


def extract_options(markdown_content):
    """
    Extracts the options from the given markdown content.

    Args:
        markdown_content (str): The markdown content to search for the options.

    Returns:
        list: A list of extracted options if found, otherwise an empty list.
    """
    options_match = re.search(
        r"####\s*options\s*(.+?)(?=####|$)",
        markdown_content,
        re.DOTALL | re.IGNORECASE,
    )
    options = (
        [
            line.strip()
            for line in options_match.group(1).strip().splitlines()
            if line.strip()
        ]
        if options_match
        else []
    )

    return options

def extract_title(markdown_content):
    """
    Extracts the title from the given markdown content.

    Args:
        markdown_content (str): The markdown content to search for the title.

    Returns:
        str: The extracted title if found, otherwise None.
    """
    title_match = re.search(r"^##\s*(.+)", markdown_content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else None
    return title

def extract_solutions(markdown_content):
        """
        Extracts the solution from the given markdown content.

        Args:
            markdown_content (str): The markdown content to search for the solution.

        Returns:
            str: The extracted solution if found, otherwise None.
        """
        # solution_match = re.search(
        #     r"####\s*SOLUTION\s*(.+)", markdown_content, re.IGNORECASE
        # )
        # solution = (
        #     solution_match.group(1).strip() if solution_match else None
        # )
        
        # return solution
        
        #TODO: This was replaced with the original method to be compatible with the select many questions
        solution_start = markdown_content.find("#### SOLUTION")
        if solution_start != -1:
            solution = []
            lines = markdown_content[solution_start:].splitlines()
            for line in lines[1:]:  # Skip the "#### SOLUTION" line
                if line.strip():  # Non-blank line after trimming spaces
                    solution.append(line.strip())
                else:
                    break
            return solution
        return []
            
def process_widget_questions(ipynb_file, start_tag, end_tag):
    """
    Processes widget questions in a Jupyter notebook file, extracting sections
    of questions marked by specific start and end tags.

    Args:
        ipynb_file (str): The path to the Jupyter notebook file (.ipynb) to process.
        start_tag (str): The tag indicating the start of a section to process.
        end_tag (str): The tag indicating the end of a section to process.

    Returns:
        list: A list of sections, each containing details of questions extracted
              from the notebook. Each section is represented as a dictionary with
              question titles, subquestion numbers, question text, options, and solutions.
    """
    try:
        # Load the notebook file
        with open(ipynb_file, "r", encoding="utf-8") as f:
            notebook_data = json.load(f)

        cells = notebook_data.get("cells", [])

        parser = WidgetQuestionParser(start_tag=start_tag, end_tag=end_tag)

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
                title = extract_title(markdown_content)

                if title:
                    parser.increment_subquestion_number()

                    # Extract question text, options, and solution
                    question_text = extract_question(markdown_content)
                    options = extract_options(markdown_content)
                    solution = extract_solutions(markdown_content)

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
        print("Invalid JSON in notebook file.")
        return []


def sanitize_string(input_string):
    """
    Converts a string into a valid Python variable name.

    Args:
        input_string (str): The string to convert.

    Returns:
        str: A valid Python variable name.
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r"\W|^(?=\d)", "_", input_string)
    return sanitized