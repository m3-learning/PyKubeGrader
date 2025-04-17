import json
import re

from pykubegrader.build.build_folder import WidgetQuestionParser
from pykubegrader.build.notebooks.io import read_notebook

def extract_question(text, regex = r"^###\s+(.*?)\s+####"):
    """
    Extracts the question text from the given markdown content.
    
    This function searches for text between a level 3 heading (###) and 
    the next level 4 heading (####) using regular expressions. It then 
    cleans the extracted text by removing unnecessary whitespace and 
    asterisks.
    
    Args:
        text (str): The markdown content to search for the question text.
        regex (str, optional): Regular expression pattern to match the question text.
            Defaults to r"^###\s+(.*?)\s+####".
            
    Returns:
        str or None: The extracted question text if found, otherwise None.
    """
    
    #TODO: this was the original for for TF
    # TODO: Delete if not needed
    # question_text_match = re.search(
    #                             r"^###\s*\*\*(.+)\*\*", markdown_content, re.MULTILINE
    #                         )
    
    # Regular expression to capture the multiline title
    match = re.search(regex, text, re.DOTALL)
    if match:
        # Stripping unnecessary whitespace and asterisks
        return match.group(1).strip().strip("**")
    return None


def extract_options(markdown_content, regex = r"####\s*options\s*(.+?)(?=####|$)"):
    """
    Extracts the options from the given markdown content.

    Args:
        markdown_content (str): The markdown content to search for the options.
        regex (str, optional): Regular expression pattern to match the options.
            Defaults to r"####\s*options\s*(.+?)(?=####|$)".

    Returns:
        list: A list of extracted options if found, otherwise an empty list.
    """
    options_match = re.search(regex, markdown_content, re.DOTALL | re.IGNORECASE)
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

def extract_title(markdown_content, title_regex = r"^##\s*(.+)"):
    """
    Extracts the title from the given markdown content.

    Args:
        markdown_content (str): The markdown content to search for the title.
        title_regex (str, optional): Regular expression pattern to match the title.
            Defaults to r"^##\s*(.+)".

    Returns:
        str: The extracted title if found, otherwise None.
    """
    title_match = re.search(title_regex, markdown_content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else None
    return title

def extract_solutions(markdown_content):
    """
    Extracts the solution from the given markdown content.
    
    This function searches for a section marked with "#### SOLUTION" in the markdown content
    and extracts all non-empty lines following it until the first empty line is encountered.
    
    Args:
        markdown_content (str): The markdown content to search for the solution.
            This should be the full text content of a markdown cell.
            
    Returns:
        list: A list of solution lines if found, otherwise an empty list.
              Each item in the list is a trimmed line from the solution section.
    """
    
    # solution_match = re.search(
    #     r"####\s*SOLUTION\s*(.+)", markdown_content, re.IGNORECASE
    # )
    # solution = (
    #     solution_match.group(1).strip() if solution_match else None
    # )
    
    # return solution
    
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
        notebook_data = read_notebook(ipynb_file)

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