import re

def extract_question(text):
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
        solution_match = re.search(
            r"####\s*SOLUTION\s*(.+)", markdown_content, re.IGNORECASE
        )
        solution = (
            solution_match.group(1).strip() if solution_match else None
        )
        
        return solution